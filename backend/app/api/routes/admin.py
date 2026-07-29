import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.crud.admin import (
    approve_recruiter_verification,
    approve_talent_verification,
    get_financial_overview,
    get_stats,
    get_user,
    list_all_casting_calls,
    list_pending_recruiter_verifications,
    list_pending_talent_verifications,
    list_users,
    reject_recruiter_verification,
    reject_talent_verification,
    set_casting_call_status,
    set_user_active,
)
from app.crud.casting_call import get_casting_call
from app.crud.recruiter_profile import get_recruiter_profile
from app.crud.talent_profile import get_talent_profile
from app.db.session import get_db
from app.models.casting_call import CastingCallStatus
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminCastingCallRead,
    AdminStats,
    AdminUserDetail,
    CastingCallStatusUpdate,
    FinancialOverview,
    UserStatusUpdate,
)
from app.schemas.recruiter_profile import RecruiterProfileRead
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
