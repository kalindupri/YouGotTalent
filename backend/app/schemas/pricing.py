import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.subscription import SubscriptionPlan


class CurrentPricing(BaseModel):
    talent_premium_monthly_lkr: int
    talent_premium_annual_lkr: int
    recruiter_premium_monthly_lkr: int
    recruiter_premium_annual_lkr: int


class PricingVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan: SubscriptionPlan
    monthly_price_lkr: int
    created_at: datetime
    created_by_name: str | None = None


class AdminPricingOverview(BaseModel):
    current: CurrentPricing
    history: list[PricingVersionRead]


class PricingUpdateRequest(BaseModel):
    plan: SubscriptionPlan
    monthly_price_lkr: int = Field(gt=0)
