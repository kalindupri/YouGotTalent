from datetime import datetime

from app.core.email import send_email

# Centralizes the copy for every billing lifecycle email so the wording stays consistent
# between the dunning sweep, webhook handlers, and the cancel/retention endpoints.


def _fmt(dt: datetime) -> str:
    return dt.strftime("%B %d, %Y")


def send_payment_failed_email(to: str, plan_label: str, grace_days: int) -> None:
    send_email(
        to,
        "We couldn't process your YouGotTalent payment",
        f"Your renewal payment for {plan_label} didn't go through.\n\n"
        f"Your Premium access is still active for now — please update your payment method within "
        f"{grace_days} days to avoid losing it. If it isn't resolved by then, your account will "
        "automatically switch to the Free plan.",
    )


def send_payment_failed_reminder_email(to: str, plan_label: str, days_left: int) -> None:
    send_email(
        to,
        "Reminder: your YouGotTalent payment is still unresolved",
        f"Just a reminder — we still haven't been able to process your renewal payment for {plan_label}.\n\n"
        f"You have {days_left} day{'s' if days_left != 1 else ''} left to update your payment method before "
        "your account switches to the Free plan.",
    )


def send_downgraded_to_free_email(to: str, plan_label: str) -> None:
    send_email(
        to,
        "Your YouGotTalent account has moved to the Free plan",
        f"We weren't able to collect payment for {plan_label}, so your account has switched to the Free "
        "plan. You can resubscribe any time from your dashboard — no data has been lost.",
    )


def send_cancellation_scheduled_email(to: str, plan_label: str, period_end: datetime) -> None:
    send_email(
        to,
        "Your YouGotTalent subscription is set to end",
        f"We've scheduled your {plan_label} subscription to cancel. You'll keep full Premium access "
        f"until {_fmt(period_end)} — you won't be charged again after that.\n\n"
        "Changed your mind? You can reactivate any time before then from your dashboard.",
    )


def send_retention_offer_applied_email(to: str, plan_label: str, discount_percent: int, discount_expires_at: datetime) -> None:
    send_email(
        to,
        "Your YouGotTalent discount is active",
        f"Good news — your {plan_label} subscription now has {discount_percent}% off, through "
        f"{_fmt(discount_expires_at)}. Thanks for staying with us!",
    )


def send_subscription_ended_email(to: str, plan_label: str) -> None:
    send_email(
        to,
        "Your YouGotTalent subscription has ended",
        f"Your {plan_label} subscription has ended as scheduled, and your account is now on the Free "
        "plan. We'd love to have you back — you can resubscribe any time from your dashboard.",
    )
