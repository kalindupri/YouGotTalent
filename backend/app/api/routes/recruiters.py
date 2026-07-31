import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_recruiter_profile, require_recruiter
from app.crud import subscription as subscription_crud
from app.crud.casting_call import get_recruiter_analytics
from app.crud.recruiter_profile import (
    create_recruiter_profile,
    get_recruiter_profile,
    get_recruiter_profile_by_user,
    request_verification,
)
from app.crud.review import get_recruiter_review_summary, list_reviews_for_recruiter
from app.crud.saved_search import create_saved_search, delete_saved_search, get_saved_search, list_saved_searches
from app.crud.saved_talent import list_saved_talents
from app.db.session import get_db
from app.models.recruiter_profile import RecruiterProfile
from app.models.user import User
from app.schemas.analytics import RecruiterAnalytics
from app.schemas.recruiter_profile import RecruiterProfileCreate, RecruiterProfileRead
from app.schemas.review import RecruiterReviewSummary, ReviewRead
from app.schemas.saved_search import SavedSearchCreate, SavedSearchRead
from app.schemas.talent_profile import TalentProfileRead

router = APIRouter(prefix="/recruiters", tags=["recruiters"])


@router.post("/me", response_model=RecruiterProfileRead, status_code=status.HTTP_201_CREATED)
def create_my_recruiter_profile(
    profile_in: RecruiterProfileCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_recruiter),
):
    if get_recruiter_profile_by_user(db, user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recruiter profile already exists")
    return create_recruiter_profile(db, user.id, profile_in)


@router.get("/me", response_model=RecruiterProfileRead)
def read_my_recruiter_profile(
    db: Session = Depends(get_db),
    user: User = Depends(require_recruiter),
):
    profile = get_recruiter_profile_by_user(db, user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter profile not found")
    return profile


@router.get("/me/analytics", response_model=RecruiterAnalytics)
def read_my_analytics(
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    return get_recruiter_analytics(db, recruiter.id)


@router.get("/me/reviews", response_model=list[ReviewRead])
def read_my_reviews(
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    return list_reviews_for_recruiter(db, recruiter.id)


@router.get("/me/saved-talents", response_model=list[TalentProfileRead])
def read_my_saved_talents(
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    return list_saved_talents(db, recruiter.id)


@router.post("/me/request-verification", response_model=RecruiterProfileRead)
def request_my_verification(
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    return request_verification(db, recruiter)


@router.post("/me/upgrade", response_model=RecruiterProfileRead)
def upgrade_my_tier(
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    # Starts (or reactivates) a real trial-backed subscription — see app/crud/subscription.py.
    # For a paid, non-trial checkout use POST /billing/checkout instead.
    subscription_crud.start_trial(db, recruiter_profile=recruiter)
    db.refresh(recruiter)
    return recruiter


@router.get("/me/saved-searches", response_model=list[SavedSearchRead])
def read_my_saved_searches(
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    return list_saved_searches(db, recruiter.id)


@router.post("/me/saved-searches", response_model=SavedSearchRead, status_code=status.HTTP_201_CREATED)
def create_my_saved_search(
    search_in: SavedSearchCreate,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    if recruiter.tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Saved searches are a Premium feature. Upgrade your organizer account to use them.",
        )
    return create_saved_search(db, recruiter.id, search_in)


@router.delete("/me/saved-searches/{saved_search_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_saved_search(
    saved_search_id: uuid.UUID,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    saved_search = get_saved_search(db, saved_search_id)
    if saved_search is None or saved_search.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")
    delete_saved_search(db, saved_search)


# These two routes must stay below every /me* route above — {recruiter_id} would otherwise
# swallow "/me" as an invalid UUID path param before the literal route gets a chance to match.
@router.get("/{recruiter_id}", response_model=RecruiterProfileRead)
def get_recruiter(recruiter_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = get_recruiter_profile(db, recruiter_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter profile not found")
    return profile


@router.get("/{recruiter_id}/reviews", response_model=RecruiterReviewSummary)
def get_recruiter_reviews(recruiter_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = get_recruiter_profile(db, recruiter_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter profile not found")
    return get_recruiter_review_summary(db, recruiter_id)
