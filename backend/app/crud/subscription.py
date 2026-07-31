import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.payments.base import CheckoutSession, PaymentGateway, WebhookEvent
from app.core.pricing import price_lkr_for
from app.crud.recruiter_profile import set_tier as set_recruiter_tier
from app.crud.talent_profile import set_tier as set_talent_tier
from app.models.recruiter_profile import RecruiterProfile
from app.models.subscription import BillingCycle, PaymentGatewayName, Subscription, SubscriptionPlan, SubscriptionStatus
from app.models.talent_profile import TalentProfile

# Statuses under which the subscriber keeps premium access. PAST_DUE stays premium — a short
# grace period after a failed renewal is friendlier than an instant downgrade mid-billing-cycle.
_PREMIUM_STATUSES = {SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE}


def get_for_talent(db: Session, talent_profile_id: uuid.UUID) -> Subscription | None:
    return db.query(Subscription).filter(Subscription.talent_profile_id == talent_profile_id).first()


def get_for_recruiter(db: Session, recruiter_profile_id: uuid.UUID) -> Subscription | None:
    return db.query(Subscription).filter(Subscription.recruiter_profile_id == recruiter_profile_id).first()


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
        price_lkr=price_lkr_for(plan, BillingCycle.MONTHLY),
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
    price = price_lkr_for(plan, billing_cycle)

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
    db.commit()
    db.refresh(subscription)

    checkout = gateway.start_checkout(subscription, return_url)

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

    subscription.status = SubscriptionStatus(event.status)
    if event.current_period_end:
        subscription.current_period_end = event.current_period_end
    elif subscription.status == SubscriptionStatus.ACTIVE and subscription.current_period_end is None:
        subscription.current_period_end = _period_end(subscription.billing_cycle)

    db.commit()
    db.refresh(subscription)
    _sync_tier(db, subscription)
    return subscription


def cancel(db: Session, gateway: PaymentGateway, subscription: Subscription) -> Subscription:
    gateway.cancel(subscription)
    subscription.status = SubscriptionStatus.CANCELED
    subscription.canceled_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(subscription)
    _sync_tier(db, subscription)
    return subscription


def sync_if_expired(db: Session, subscription: Subscription | None) -> None:
    """Lazily reconciles a lapsed trial/period on read, since there's no cron/queue in this app
    yet. Called from the auth dependencies that already load the talent/recruiter profile on
    every request, so tier never drifts from reality for more than one request.
    """
    if subscription is None or subscription.status not in (SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE):
        return
    deadline = subscription.trial_end if subscription.status == SubscriptionStatus.TRIALING else subscription.current_period_end
    if deadline is None:
        return
    now = datetime.now(timezone.utc)
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if now >= deadline:
        subscription.status = SubscriptionStatus.EXPIRED
        db.commit()
        db.refresh(subscription)
        _sync_tier(db, subscription)
