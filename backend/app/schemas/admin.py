from pydantic import BaseModel

from app.models.casting_call import CastingCallStatus
from app.schemas.casting_call import CastingCallRead
from app.schemas.recruiter_profile import RecruiterProfileRead
from app.schemas.subscription import SubscriptionRead
from app.schemas.talent_profile import TalentProfileRead
from app.schemas.user import UserRead


class AdminStats(BaseModel):
    total_users: int
    total_talents: int
    total_recruiters: int
    verified_talents: int
    verified_recruiters: int
    open_casting_calls: int
    closed_casting_calls: int
    total_applications: int
    total_invitations: int


class UserStatusUpdate(BaseModel):
    is_active: bool


class CastingCallStatusUpdate(BaseModel):
    status: CastingCallStatus


class AdminCastingCallRead(CastingCallRead):
    recruiter_company_name: str
    application_count: int
    invitation_count: int


class FinancialOverview(BaseModel):
    currency: str
    free_talents: int
    premium_talents: int
    free_recruiters: int
    premium_recruiters: int
    price_per_premium_talent: int
    price_per_premium_recruiter: int
    # Purely a projection from current premium counts × the configured prices above — includes
    # trial subscribers, who haven't paid anything yet.
    estimated_monthly_revenue: int
    # The real numbers, from actual Subscription rows with a paying (non-trial) status.
    trialing_subscriptions: int
    paying_subscriptions: int
    real_monthly_revenue_lkr: int


class AdminUserDetail(UserRead):
    # A list, not one profile: a guardian's account holds a profile per child.
    talent_profiles: list[TalentProfileRead] = []
    recruiter_profile: RecruiterProfileRead | None = None


class AdminSubscriptionRead(SubscriptionRead):
    subscriber_name: str
    subscriber_email: str


class ChurnReasons(BaseModel):
    counts: dict[str, int]
    recent_details: list[str]


class DunningSweepResult(BaseModel):
    checked: int
    transitions_applied: int
