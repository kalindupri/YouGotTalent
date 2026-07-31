from app.core.config import settings
from app.models.subscription import BillingCycle, SubscriptionPlan


def price_lkr_for(plan: SubscriptionPlan, billing_cycle: BillingCycle) -> int:
    monthly = settings.PREMIUM_TALENT_PRICE_LKR if plan == SubscriptionPlan.TALENT_PREMIUM else settings.PREMIUM_RECRUITER_PRICE_LKR
    if billing_cycle == BillingCycle.ANNUAL:
        return monthly * settings.ANNUAL_BILLING_MONTHS_CHARGED
    return monthly
