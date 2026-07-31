from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.pricing import PricingVersion
from app.models.subscription import BillingCycle, SubscriptionPlan

_SETTINGS_DEFAULTS = {
    SubscriptionPlan.TALENT_PREMIUM: lambda: settings.PREMIUM_TALENT_PRICE_LKR,
    SubscriptionPlan.RECRUITER_PREMIUM: lambda: settings.PREMIUM_RECRUITER_PRICE_LKR,
}


def current_monthly_price_lkr(db: Session, plan: SubscriptionPlan) -> int:
    """The current admin-configured monthly price for a plan — its most recent PricingVersion
    row. Falls back to the settings default only if no version has ever been recorded (shouldn't
    happen in a migrated database, since the pricing_versions migration seeds one per plan).
    """
    latest = (
        db.query(PricingVersion)
        .filter(PricingVersion.plan == plan)
        .order_by(PricingVersion.created_at.desc())
        .first()
    )
    if latest is not None:
        return latest.monthly_price_lkr
    return _SETTINGS_DEFAULTS[plan]()


def price_lkr_for(db: Session, plan: SubscriptionPlan, billing_cycle: BillingCycle) -> int:
    monthly = current_monthly_price_lkr(db, plan)
    if billing_cycle == BillingCycle.ANNUAL:
        return monthly * settings.ANNUAL_BILLING_MONTHS_CHARGED
    return monthly
