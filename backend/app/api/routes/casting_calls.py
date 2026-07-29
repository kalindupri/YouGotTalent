import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_recruiter_profile
from app.core.config import settings
from app.core.email import send_email
from app.crud.casting_call import create_casting_call, get_casting_call, increment_view_count, list_casting_calls
from app.crud.follow import list_follower_talents
from app.crud.recruiter_profile import count_open_casting_calls
from app.crud.talent_profile import list_talent_profiles_for_job_alert
from app.db.session import get_db
from app.models.recruiter_profile import RecruiterProfile
from app.models.talent_profile import TalentCategory
from app.schemas.casting_call import CastingCallCreate, CastingCallRead

router = APIRouter(prefix="/casting-calls", tags=["casting-calls"])


@router.get("", response_model=list[CastingCallRead])
def browse_casting_calls(
    category: TalentCategory | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return list_casting_calls(db, category, skip, limit)


@router.get("/{casting_call_id}", response_model=CastingCallRead)
def get_casting_call_detail(casting_call_id: uuid.UUID, db: Session = Depends(get_db)):
    call = get_casting_call(db, casting_call_id)
    if call is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Casting call not found")
    return call


@router.post("/{casting_call_id}/view", status_code=status.HTTP_204_NO_CONTENT)
def track_casting_call_view(casting_call_id: uuid.UUID, db: Session = Depends(get_db)):
    call = get_casting_call(db, casting_call_id)
    if call is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Casting call not found")
    increment_view_count(db, call)


@router.post("", response_model=CastingCallRead, status_code=status.HTTP_201_CREATED)
def create_new_casting_call(
    call_in: CastingCallCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    if recruiter.tier != "premium" and count_open_casting_calls(db, recruiter.id) >= settings.FREE_TIER_OPEN_CASTING_CALL_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Free accounts can have up to {settings.FREE_TIER_OPEN_CASTING_CALL_LIMIT} open talent hunts at a time. Upgrade to Premium for unlimited postings.",
        )
    call = create_casting_call(db, recruiter.id, call_in)
    notified_emails: set[str] = set()

    categories = {call.category} | {role.category for role in call.roles if role.category}
    for talent in list_talent_profiles_for_job_alert(db, categories):
        category_label = talent.category.replace("_", " ").title()
        background_tasks.add_task(
            send_email,
            talent.user.email,
            f"New {category_label} opportunity: {call.title}",
            f"A new talent hunt matching your profile was just posted on YouGotTalent.\n\n"
            f"View it here: {settings.FRONTEND_URL}/casting-calls/{call.id}\n\n"
            f"Don't want these emails? Turn them off from your dashboard.",
        )
        notified_emails.add(talent.user.email)

    for talent in list_follower_talents(db, recruiter.id):
        if talent.user.email in notified_emails:
            continue
        background_tasks.add_task(
            send_email,
            talent.user.email,
            f"{recruiter.company_name} posted a new talent hunt: {call.title}",
            f"A recruiter you follow, {recruiter.company_name}, just posted a new talent hunt.\n\n"
            f"View it here: {settings.FRONTEND_URL}/casting-calls/{call.id}",
        )

    return call
