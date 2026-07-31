import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.crud.admin import (
    approve_recruiter_verification,
    approve_talent_verification,
    get_churn_reasons,
    get_financial_overview,
    get_stats,
    get_subscription,
    get_user,
    list_all_casting_calls,
    list_all_subscriptions,
    list_pending_recruiter_verifications,
    list_pending_talent_verifications,
    list_subscription_payments,
    list_users,
    reject_recruiter_verification,
    reject_talent_verification,
    set_casting_call_status,
    set_user_active,
)
from app.crud import discussion as discussion_crud
from app.crud import pricing as pricing_crud
from app.crud import title as title_crud
from app.crud.casting_call import get_casting_call
from app.crud.recruiter_profile import get_recruiter_profile
from app.crud.report import get_report, list_reports, update_report_status
from app.crud.subscription import run_dunning_sweep
from app.crud.talent_profile import get_talent_profile
from app.db.session import get_db
from app.models.casting_call import CastingCallStatus
from app.models.report import ReportCategory, ReportStatus
from app.models.subscription import SubscriptionStatus
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminCastingCallRead,
    AdminStats,
    AdminSubscriptionRead,
    AdminUserDetail,
    CastingCallStatusUpdate,
    ChurnReasons,
    DunningSweepResult,
    FinancialOverview,
    UserStatusUpdate,
)
from app.schemas.pricing import AdminPricingOverview, CurrentPricing, PricingUpdateRequest, PricingVersionRead
from app.schemas.recruiter_profile import RecruiterProfileRead
from app.schemas.report import ReportRead, ReportStatusUpdate, ReportWithReporter
from app.schemas.subscription import PaymentRead
from app.schemas.talent_profile import TalentProfileRead
from app.schemas.user import UserRead

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStats)
def read_stats(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return get_stats(db)


@router.get("/users", response_model=list[UserRead])
def read_users(
    role: UserRole | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return list_users(db, role, q)


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def read_user_detail(user_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/users/{user_id}/status", response_model=UserRead)
def update_user_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if user_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change your own account's active status")
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return set_user_active(db, user, payload.is_active)


@router.get("/verification-requests/talents", response_model=list[TalentProfileRead])
def read_pending_talent_verifications(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return list_pending_talent_verifications(db)


@router.post("/verification-requests/talents/{talent_id}/approve", response_model=TalentProfileRead)
def approve_talent(talent_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    profile = get_talent_profile(db, talent_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")
    return approve_talent_verification(db, profile)


@router.post("/verification-requests/talents/{talent_id}/reject", response_model=TalentProfileRead)
def reject_talent(talent_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    profile = get_talent_profile(db, talent_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")
    return reject_talent_verification(db, profile)


@router.get("/verification-requests/recruiters", response_model=list[RecruiterProfileRead])
def read_pending_recruiter_verifications(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return list_pending_recruiter_verifications(db)


@router.post("/verification-requests/recruiters/{recruiter_id}/approve", response_model=RecruiterProfileRead)
def approve_recruiter(recruiter_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    profile = get_recruiter_profile(db, recruiter_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter profile not found")
    return approve_recruiter_verification(db, profile)


@router.post("/verification-requests/recruiters/{recruiter_id}/reject", response_model=RecruiterProfileRead)
def reject_recruiter(recruiter_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    profile = get_recruiter_profile(db, recruiter_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter profile not found")
    return reject_recruiter_verification(db, profile)


@router.get("/casting-calls", response_model=list[AdminCastingCallRead])
def read_all_casting_calls(
    status_filter: CastingCallStatus | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return list_all_casting_calls(db, status_filter)


@router.patch("/casting-calls/{casting_call_id}/status", response_model=AdminCastingCallRead)
def update_casting_call_status(
    casting_call_id: uuid.UUID,
    payload: CastingCallStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    call = get_casting_call(db, casting_call_id)
    if call is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Casting call not found")
    return set_casting_call_status(db, call, payload.status)


@router.get("/financial-overview", response_model=FinancialOverview)
def read_financial_overview(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return get_financial_overview(db)


def _to_report_with_reporter(report) -> ReportWithReporter:
    return ReportWithReporter(**ReportRead.model_validate(report).model_dump(), reporter_email=report.reporter.email)


@router.get("/reports", response_model=list[ReportWithReporter])
def read_reports(
    status_filter: ReportStatus | None = None,
    category: ReportCategory | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    reports = list_reports(db, status_filter, category)
    return [_to_report_with_reporter(r) for r in reports]


@router.patch("/reports/{report_id}", response_model=ReportWithReporter)
def update_report(
    report_id: uuid.UUID,
    payload: ReportStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    report = get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return _to_report_with_reporter(update_report_status(db, report, payload))


@router.get("/subscriptions", response_model=list[AdminSubscriptionRead])
def read_subscriptions(
    status_filter: SubscriptionStatus | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return list_all_subscriptions(db, status_filter)


@router.get("/subscriptions/{subscription_id}/payments", response_model=list[PaymentRead])
def read_subscription_payments(subscription_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if get_subscription(db, subscription_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return list_subscription_payments(db, subscription_id)


@router.get("/churn-reasons", response_model=ChurnReasons)
def read_churn_reasons(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return get_churn_reasons(db)


@router.post("/billing/run-dunning-sweep", response_model=DunningSweepResult)
def trigger_dunning_sweep(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Processes every subscription's pending trial/period/past-due transitions in one pass.

    There's no cron/queue in this app, so time-based billing emails (payment-failed reminders,
    final downgrade notices) only go out when this runs — either an admin clicking a button, or
    ideally an external scheduler (Azure Container Apps scheduled job, a GitHub Actions cron, or
    a service like cron-job.org) hitting this endpoint daily.
    """
    return run_dunning_sweep(db)


@router.delete("/community/titles/{title_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_title(title_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    title = title_crud.get_title(db, title_id)
    if title is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Title not found")
    title_crud.delete_title(db, title)


@router.delete("/community/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_title_review(review_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    review = title_crud.get_review(db, review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    title_crud.delete_review(db, review)


@router.delete("/community/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_discussion_thread(thread_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    thread = discussion_crud.get_thread(db, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discussion not found")
    discussion_crud.delete_thread(db, thread)


@router.delete("/community/replies/{reply_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_discussion_reply(reply_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    reply = discussion_crud.get_reply(db, reply_id)
    if reply is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reply not found")
    discussion_crud.delete_reply(db, reply)


def _to_pricing_version_read(version) -> PricingVersionRead:
    return PricingVersionRead(
        id=version.id,
        plan=version.plan,
        monthly_price_lkr=version.monthly_price_lkr,
        created_at=version.created_at,
        created_by_name=version.created_by.full_name if version.created_by else None,
    )


@router.get("/pricing", response_model=AdminPricingOverview)
def read_pricing(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return AdminPricingOverview(
        current=CurrentPricing(**pricing_crud.current_prices(db)),
        history=[_to_pricing_version_read(v) for v in pricing_crud.list_versions(db)],
    )


@router.post("/pricing", response_model=AdminPricingOverview, status_code=status.HTTP_201_CREATED)
def update_pricing(payload: PricingUpdateRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    pricing_crud.create_version(db, payload.plan, payload.monthly_price_lkr, admin.id)
    return AdminPricingOverview(
        current=CurrentPricing(**pricing_crud.current_prices(db)),
        history=[_to_pricing_version_read(v) for v in pricing_crud.list_versions(db)],
    )
