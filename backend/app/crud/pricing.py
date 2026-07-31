import uuid

from sqlalchemy.orm import Session

from app.core.pricing import price_lkr_for
from app.models.pricing import PricingVersion
from app.models.subscription import BillingCycle, SubscriptionPlan


def list_versions(db: Session) -> list[PricingVersion]:
    return db.query(PricingVersion).order_by(PricingVersion.created_at.desc()).all()


def create_version(db: Session, plan: SubscriptionPlan, monthly_price_lkr: int, admin_user_id: uuid.UUID) -> PricingVersion:
    version = PricingVersion(plan=plan, monthly_price_lkr=monthly_price_lkr, created_by_user_id=admin_user_id)
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def current_prices(db: Session) -> dict:
    return {
        "talent_premium_monthly_lkr": price_lkr_for(db, SubscriptionPlan.TALENT_PREMIUM, BillingCycle.MONTHLY),
        "talent_premium_annual_lkr": price_lkr_for(db, SubscriptionPlan.TALENT_PREMIUM, BillingCycle.ANNUAL),
        "recruiter_premium_monthly_lkr": price_lkr_for(db, SubscriptionPlan.RECRUITER_PREMIUM, BillingCycle.MONTHLY),
        "recruiter_premium_annual_lkr": price_lkr_for(db, SubscriptionPlan.RECRUITER_PREMIUM, BillingCycle.ANNUAL),
    }
