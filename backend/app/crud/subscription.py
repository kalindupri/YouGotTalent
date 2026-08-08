import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.billing_emails import (
    send_cancellation_scheduled_email,
    send_downgraded_to_free_email,
    send_payment_failed_email,
    send_payment_failed_reminder_email,
    send_retention_offer_applied_email,
    send_subscription_ended_email,
)
from app.core.config import settings
from app.core.payments.base import CheckoutSession, PaymentGateway, WebhookEvent
from app.core.pricing import price_lkr_for
from app.crud.recruiter_profile import set_tier as set_recruiter_tier
from app.crud.talent_profile import set_tier as set_talent_tier
from app.models.recruiter_profile import RecruiterProfile
from app.models.subscription import (
    BillingCycle,
    CancellationReason,
    PaymentGatewayName,
    PaymentStatus,
    Subscription,
    SubscriptionPayment,
    SubscriptionPlan,
    SubscriptionStatus,
)
from app.models.talent_profile import TalentProfile
from app.models.user import User

# Statuses under which the subscriber keeps premium access. PAST_DUE stays premium — a short
# grace period after a failed renewal is friendlier than an instant downgrade mid-billing-cycle.
_PREMIUM_STATUSES = {SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE}

_PLAN_LABELS = {
    SubscriptionPlan.TALENT_PREMIUM: "Talent Premium",
    SubscriptionPlan.RECRUITER_PREMIUM: "Recruiter Premium",
}


def get_for_talent(db: Session, talent_profile_id: uuid.UUID) -> Subscription | None:
    return db.query(Subscription).filter(Subscription.talent_profile_id == talent_profile_id).first()


def get_for_recruiter(db: Session, recruiter_profile_id: uuid.UUID) -> Subscription | None:
    return db.query(Subscription).filter(Subscription.recruiter_profile_id == recruiter_profile_id).first()


def list_payments(db: Session, subscription_id: uuid.UUID) -> list[SubscriptionPayment]:
    return db.query(SubscriptionPayment).filter(SubscriptionPayment.subscription_id == subscription_id).order_by(SubscriptionPayment.created_at.desc()).all()


def _profile(db: Session, subscription: Subscription) -> TalentProfile | RecruiterProfile | None:
    if subscription.talent_profile_id:
        return db.query(TalentProfile).filter(TalentProfile.id == subscription.talent_profile_id).first()
    if subscription.recruiter_profile_id:
        return db.query(RecruiterProfile).filter(RecruiterProfile.id == subscription.recruiter_profile_id).first()
    return None


def _user_email(db: Session, subscription: Subscription) -> str | None:
    profile = _profile(db, subscription)
    if profile is None:
        return None
    user = db.query(User).filter(User.id == profile.user_id).first()
    return user.email if user else None


def _plan_label(subscription: Subscription) -> str:
    return _PLAN_LABELS.get(subscription.plan, subscription.plan.value)


def _sync_tier(db: Session, subscription: Subscription) -> None:
    is_premium = subscription.status in _PREMIUM_STATUSES
    if subscription.talent_profile_id:
        profile = db.query(TalentProfile).filter(TalentProfile.id == subscription.talent_profile_id).first()
        if profile:
            set_talent_tier(db, profile, "premium" if is_premium else "free")
    elif subscription.recruiter_profile_id:
        profile = db.query(RecruiterProfile).filter(RecruiterProfile.id == subscription.recruiter_profile_id).first()
        if profile:
            set_recruiter_tier(db, profile, "premium" if is_premium else "free")


def record_payment(
    db: Session,
    subscription: Subscription,
    status: PaymentStatus,
    *,
    amount_lkr: int | None = None,
    gateway_reference: str | None = None,
    failure_reason: str | None = None,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
) -> SubscriptionPayment:
    payment = SubscriptionPayment(
        subscription_id=subscription.id,
        amount_lkr=amount_lkr if amount_lkr is not None else subscription.effective_price_lkr,
        status=status,
        gateway=subscription.gateway,
        gateway_reference=gateway_reference,
        period_start=period_start,
        period_end=period_end,
        failure_reason=failure_reason,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def start_trial(db: Session, *, talent_profile: TalentProfile | None = None, recruiter_profile: RecruiterProfile | None = None) -> Subscription:
    """Grants immediate premium access via a time-boxed trial — the mock-gateway-backed
    replacement for what used to be a bare tier flip. Safe to call repeatedly: a profile that
    already has a subscription just gets it re-synced to premium (useful for the mock gateway
    in dev/tests) rather than issuing a second trial.
    """
    assert (talent_profile is None) != (recruiter_profile is None), "exactly one profile must be given"

    existing = (
        get_for_talent(db, talent_profile.id) if talent_profile else get_for_recruiter(db, recruiter_profile.id)
    )
    if existing is not None:
        if existing.status not in _PREMIUM_STATUSES:
            existing.status = SubscriptionStatus.ACTIVE
            db.commit()
            db.refresh(existing)
            _sync_tier(db, existing)
        return existing

    plan = SubscriptionPlan.TALENT_PREMIUM if talent_profile else SubscriptionPlan.RECRUITER_PREMIUM
    trial_days = settings.TALENT_TRIAL_DAYS if talent_profile else settings.RECRUITER_TRIAL_DAYS
    trial_end = datetime.now(timezone.utc) + timedelta(days=trial_days)

    subscription = Subscription(
        talent_profile_id=talent_profile.id if talent_profile else None,
        recruiter_profile_id=recruiter_profile.id if recruiter_profile else None,
        plan=plan,
        billing_cycle=BillingCycle.MONTHLY,
        status=SubscriptionStatus.TRIALING,
        gateway=PaymentGatewayName.MOCK,
        price_lkr=price_lkr_for(db, plan, BillingCycle.MONTHLY),
        trial_end=trial_end,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    _sync_tier(db, subscription)
    return subscription


def start_checkout(
    db: Session,
    gateway: PaymentGateway,
    return_url: str,
    billing_cycle: BillingCycle,
    *,
    talent_profile: TalentProfile | None = None,
    recruiter_profile: RecruiterProfile | None = None,
) -> tuple[Subscription, CheckoutSession]:
    assert (talent_profile is None) != (recruiter_profile is None), "exactly one profile must be given"

    subscription = get_for_talent(db, talent_profile.id) if talent_profile else get_for_recruiter(db, recruiter_profile.id)
    plan = SubscriptionPlan.TALENT_PREMIUM if talent_profile else SubscriptionPlan.RECRUITER_PREMIUM
    price = price_lkr_for(db, plan, billing_cycle)

    # Trial-eligible only the first time a subscriber's checkout is actually confirmed — PENDING
    # (or no row at all) means no prior attempt ever got past "checkout started," so an abandoned
    # checkout doesn't burn the trial. Skipped entirely for gateways that activate immediately
    # (the mock gateway) since there's no real charge to defer with a trial in the first place.
    never_confirmed = subscription is None or subscription.status == SubscriptionStatus.PENDING
    trial_days = 0
    if never_confirmed and not gateway.activates_immediately:
        trial_days = settings.TALENT_TRIAL_DAYS if talent_profile else settings.RECRUITER_TRIAL_DAYS

    if subscription is None:
        subscription = Subscription(
            talent_profile_id=talent_profile.id if talent_profile else None,
            recruiter_profile_id=recruiter_profile.id if recruiter_profile else None,
            plan=plan,
            billing_cycle=billing_cycle,
            status=SubscriptionStatus.PENDING,
            gateway=gateway.name,
            price_lkr=price,
        )
        db.add(subscription)
    else:
        subscription.billing_cycle = billing_cycle
        subscription.gateway = gateway.name
        subscription.price_lkr = price
        subscription.status = SubscriptionStatus.PENDING
        # A fresh checkout supersedes any in-flight cancellation/discount from a previous cycle.
        subscription.cancel_at_period_end = False

    subscription.trial_end = datetime.now(timezone.utc) + timedelta(days=trial_days) if trial_days > 0 else None
    db.commit()
    db.refresh(subscription)

    checkout = gateway.start_checkout(subscription, return_url, trial_days=trial_days)

    if gateway.activates_immediately:
        period_end = _period_end(billing_cycle)
        apply_webhook_event(db, WebhookEvent(status="active", our_subscription_id=str(subscription.id), current_period_end=period_end))
        db.refresh(subscription)

    return subscription, checkout


def _period_end(billing_cycle: BillingCycle) -> datetime:
    days = 365 if billing_cycle == BillingCycle.ANNUAL else 30
    return datetime.now(timezone.utc) + timedelta(days=days)


def apply_webhook_event(db: Session, event: WebhookEvent) -> Subscription | None:
    subscription: Subscription | None = None
    if event.our_subscription_id:
        subscription = db.query(Subscription).filter(Subscription.id == event.our_subscription_id).first()
    if subscription is None and event.gateway_subscription_id:
        subscription = db.query(Subscription).filter(Subscription.gateway_subscription_id == event.gateway_subscription_id).first()
    if subscription is None:
        return None

    if event.gateway_subscription_id and not subscription.gateway_subscription_id:
        subscription.gateway_subscription_id = event.gateway_subscription_id

    event_status = event.status
    if event_status == "active" and subscription.trial_end:
        trial_end = subscription.trial_end
        if trial_end.tzinfo is None:
            trial_end = trial_end.replace(tzinfo=timezone.utc)
        if trial_end > datetime.now(timezone.utc):
            # checkout.session.completed fires as soon as the card is authorized, even when a
            # trial_period_days was set — the gateway hasn't actually charged anything yet, so
            # this is "trialing," not "active." The real invoice.paid webhook (sent once the
            # trial ends and Stripe charges the card) is what promotes this to active for real.
            event_status = "trialing"

    new_status = SubscriptionStatus(event_status)
    was_past_due = subscription.status == SubscriptionStatus.PAST_DUE
    subscription.status = new_status

    if new_status == SubscriptionStatus.ACTIVE:
        subscription.past_due_since = None
        subscription.past_due_reminder_sent_at = None
        if event.current_period_end:
            subscription.current_period_end = event.current_period_end
        elif subscription.current_period_end is None:
            subscription.current_period_end = _period_end(subscription.billing_cycle)
        db.commit()
        db.refresh(subscription)
        record_payment(db, subscription, PaymentStatus.SUCCEEDED, gateway_reference=subscription.gateway_subscription_id)
    elif new_status == SubscriptionStatus.PAST_DUE:
        if not was_past_due:
            subscription.past_due_since = datetime.now(timezone.utc)
            db.commit()
            db.refresh(subscription)
            record_payment(db, subscription, PaymentStatus.FAILED, failure_reason="Renewal payment failed", gateway_reference=subscription.gateway_subscription_id)
            email = _user_email(db, subscription)
            if email:
                send_payment_failed_email(email, _plan_label(subscription), settings.PAST_DUE_GRACE_DAYS)
        else:
            db.commit()
            db.refresh(subscription)
    elif new_status == SubscriptionStatus.CANCELED:
        subscription.canceled_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(subscription)
    else:
        db.commit()
        db.refresh(subscription)

    _sync_tier(db, subscription)
    return subscription


def request_cancellation(
    db: Session,
    gateway: PaymentGateway,
    subscription: Subscription,
    reason_category: CancellationReason,
    reason_detail: str | None,
) -> Subscription:
    """Schedules cancellation for the end of the current paid period — the subscriber keeps
    premium access until then rather than losing it immediately. The gateway is told to stop
    future recurring charges right away (real gateways bill the *next* period in advance, so
    waiting until period end to call this would risk one extra charge going through).
    """
    gateway.cancel(subscription)
    subscription.cancel_at_period_end = True
    subscription.canceled_requested_at = datetime.now(timezone.utc)
    subscription.cancellation_reason_category = reason_category
    subscription.cancellation_reason_detail = reason_detail
    db.commit()
    db.refresh(subscription)

    email = _user_email(db, subscription)
    if email:
        deadline = subscription.current_period_end or subscription.trial_end
        if deadline:
            send_cancellation_scheduled_email(email, _plan_label(subscription), deadline)
    return subscription


def reactivate(db: Session, subscription: Subscription) -> Subscription:
    """Undoes a pending cancellation before the period actually ends."""
    subscription.cancel_at_period_end = False
    subscription.canceled_requested_at = None
    subscription.cancellation_reason_category = None
    subscription.cancellation_reason_detail = None
    db.commit()
    db.refresh(subscription)
    return subscription


def retention_offer_status(subscription: Subscription) -> dict:
    return {
        "available": not subscription.retention_offer_used,
        "discount_percent": settings.RETENTION_DISCOUNT_PERCENT,
        "discount_months": settings.RETENTION_DISCOUNT_MONTHS,
    }


def accept_retention_offer(db: Session, subscription: Subscription) -> Subscription:
    subscription.discount_percent = settings.RETENTION_DISCOUNT_PERCENT
    subscription.discount_expires_at = datetime.now(timezone.utc) + timedelta(days=30 * settings.RETENTION_DISCOUNT_MONTHS)
    subscription.retention_offer_used = True
    # Accepting the offer means they're staying — clear any pending cancellation.
    subscription.cancel_at_period_end = False
    subscription.canceled_requested_at = None
    subscription.cancellation_reason_category = None
    subscription.cancellation_reason_detail = None
    db.commit()
    db.refresh(subscription)

    email = _user_email(db, subscription)
    if email:
        send_retention_offer_applied_email(email, _plan_label(subscription), subscription.discount_percent, subscription.discount_expires_at)
    return subscription


def cancel(db: Session, gateway: PaymentGateway, subscription: Subscription) -> Subscription:
    """Immediate cancellation — used by admins or the gateway-cancel path. Subscriber-initiated
    cancellation goes through request_cancellation instead, which respects the paid period.
    """
    gateway.cancel(subscription)
    subscription.status = SubscriptionStatus.CANCELED
    subscription.canceled_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(subscription)
    _sync_tier(db, subscription)
    return subscription


def _finalize_if_due(db: Session, subscription: Subscription) -> bool:
    """Applies one lifecycle transition if the subscription's current state has passed its
    deadline. Returns True if something changed, so callers can decide whether to keep checking.
    Shared by the lazy per-request sync and the bulk dunning sweep.
    """
    now = datetime.now(timezone.utc)

    def _aware(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)

    if subscription.status == SubscriptionStatus.TRIALING:
        deadline = _aware(subscription.trial_end)
        if deadline and now >= deadline:
            subscription.status = SubscriptionStatus.EXPIRED
            db.commit()
            db.refresh(subscription)
            _sync_tier(db, subscription)
            return True
        return False

    if subscription.status == SubscriptionStatus.ACTIVE:
        deadline = _aware(subscription.current_period_end)
        if deadline and now >= deadline:
            if subscription.cancel_at_period_end:
                subscription.status = SubscriptionStatus.CANCELED
                subscription.canceled_at = now
                db.commit()
                db.refresh(subscription)
                _sync_tier(db, subscription)
                email = _user_email(db, subscription)
                if email:
                    send_subscription_ended_email(email, _plan_label(subscription))
                return True
            if subscription.gateway == PaymentGatewayName.MOCK:
                # No real recurring charge exists for the mock gateway — simulate a
                # successful renewal so a healthy test subscription doesn't lapse on its own.
                subscription.current_period_end = _period_end(subscription.billing_cycle)
                db.commit()
                db.refresh(subscription)
                record_payment(db, subscription, PaymentStatus.SUCCEEDED)
                return True
            # A real gateway should have sent a renewal or failure webhook by now — treat
            # silence as a missed payment rather than silently expiring access.
            subscription.status = SubscriptionStatus.PAST_DUE
            subscription.past_due_since = now
            db.commit()
            db.refresh(subscription)
            _sync_tier(db, subscription)
            record_payment(db, subscription, PaymentStatus.FAILED, failure_reason="No renewal confirmation received by the gateway")
            email = _user_email(db, subscription)
            if email:
                send_payment_failed_email(email, _plan_label(subscription), settings.PAST_DUE_GRACE_DAYS)
            return True
        return False

    if subscription.status == SubscriptionStatus.PAST_DUE:
        since = _aware(subscription.past_due_since)
        if since is None:
            return False
        grace_deadline = since + timedelta(days=settings.PAST_DUE_GRACE_DAYS)
        reminder_deadline = since + timedelta(days=settings.PAST_DUE_REMINDER_AFTER_DAYS)

        if now >= grace_deadline:
            subscription.status = SubscriptionStatus.EXPIRED
            db.commit()
            db.refresh(subscription)
            _sync_tier(db, subscription)
            email = _user_email(db, subscription)
            if email:
                send_downgraded_to_free_email(email, _plan_label(subscription))
            return True

        if now >= reminder_deadline and subscription.past_due_reminder_sent_at is None:
            subscription.past_due_reminder_sent_at = now
            db.commit()
            db.refresh(subscription)
            days_left = max(0, (grace_deadline - now).days)
            email = _user_email(db, subscription)
            if email:
                send_payment_failed_reminder_email(email, _plan_label(subscription), days_left)
            return True

        return False

    return False


def sync_if_expired(db: Session, subscription: Subscription | None) -> None:
    """Lazily reconciles a lapsed trial/period/past-due state on read, since there's no
    cron/queue in this app — called from the auth dependencies that already load the talent or
    recruiter profile on every request, so tier never drifts from reality for more than one
    request. See run_dunning_sweep for the bulk equivalent meant to be triggered on a schedule.
    """
    if subscription is None:
        return
    # A subscription can pass through several deadlines back-to-back (e.g. past_due -> expired
    # happening to land in the same lazy check) — loop until nothing changes, capped so a bug
    # here can't spin forever.
    for _ in range(4):
        if not _finalize_if_due(db, subscription):
            break


def run_dunning_sweep(db: Session) -> dict:
    """Processes every subscription's pending lifecycle transitions in one pass — trial
    expiry, period-end renewal/cancellation, and past-due reminders/downgrades. Meant to be
    triggered on a schedule (e.g. a daily external cron hitting the admin endpoint) so
    time-based emails go out even if nobody happens to log in that day.
    """
    subscriptions = (
        db.query(Subscription)
        .filter(Subscription.status.in_([SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE]))
        .all()
    )
    processed = 0
    for subscription in subscriptions:
        for _ in range(4):
            if _finalize_if_due(db, subscription):
                processed += 1
            else:
                break
    return {"checked": len(subscriptions), "transitions_applied": processed}
