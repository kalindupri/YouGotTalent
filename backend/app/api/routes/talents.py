import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_recruiter_profile, get_current_talent_profile, require_talent
from app.core.config import settings
from app.crud.credit import create_credit, delete_credit, get_credit
from app.crud.review import get_talent_review_summary
from app.crud.saved_talent import get_saved_talent, save_talent, unsave_talent
from app.crud.talent_profile import (
    add_media,
    count_media,
    create_talent_profile,
    get_talent_profile,
    get_talent_profile_by_user,
    list_talent_profiles,
    request_verification,
    set_tier,
    update_talent_profile,
)
from app.db.session import get_db
from app.models.recruiter_profile import RecruiterProfile
from app.models.talent_profile import TalentCategory, TalentProfile
from app.models.user import User
from app.schemas.credit import CreditCreate, CreditRead
from app.schemas.review import TalentReviewSummary
from app.schemas.talent_profile import (
    MediaCreate,
    MediaRead,
    TalentProfileCreate,
    TalentProfileRead,
    TalentProfileUpdate,
)

router = APIRouter(prefix="/talents", tags=["talents"])


@router.get("", response_model=list[TalentProfileRead])
def browse_talents(
    category: TalentCategory | None = None,
    city: str | None = None,
    q: str | None = None,
    experience_min: int | None = None,
    experience_max: int | None = None,
    verified_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return list_talent_profiles(db, category, city, q, skip, limit, experience_min, experience_max, verified_only)


@router.get("/me", response_model=TalentProfileRead)
def read_my_profile(profile: TalentProfile = Depends(get_current_talent_profile)):
    return profile


@router.get("/{talent_id}", response_model=TalentProfileRead)
def get_talent(talent_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = get_talent_profile(db, talent_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")
    return profile


@router.get("/{talent_id}/reviews", response_model=TalentReviewSummary)
def read_talent_reviews(talent_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = get_talent_profile(db, talent_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")
    return get_talent_review_summary(db, talent_id)


@router.post("/me", response_model=TalentProfileRead, status_code=status.HTTP_201_CREATED)
def create_my_profile(
    profile_in: TalentProfileCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_talent),
):
    if get_talent_profile_by_user(db, user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Talent profile already exists")
    return create_talent_profile(db, user.id, profile_in)


@router.patch("/me", response_model=TalentProfileRead)
def update_my_profile(
    profile_in: TalentProfileUpdate,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    return update_talent_profile(db, profile, profile_in)


@router.post("/me/media", response_model=MediaRead, status_code=status.HTTP_201_CREATED)
def add_my_media(
    media_in: MediaCreate,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    if profile.tier != "premium" and count_media(db, profile.id) >= settings.FREE_TIER_MEDIA_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Free accounts can add up to {settings.FREE_TIER_MEDIA_LIMIT} portfolio items. Upgrade to Premium for unlimited auditions.",
        )
    return add_media(db, profile.id, media_in)


@router.post("/me/request-verification", response_model=TalentProfileRead)
def request_my_verification(
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    return request_verification(db, profile)


@router.post("/me/upgrade", response_model=TalentProfileRead)
def upgrade_my_tier(
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    # Placeholder for real billing (e.g. Stripe) — flips the tier flag directly with no
    # payment collected. Wire up a real checkout flow before using this in production.
    return set_tier(db, profile, "premium")


@router.post("/me/credits", response_model=CreditRead, status_code=status.HTTP_201_CREATED)
def add_my_credit(
    credit_in: CreditCreate,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    return create_credit(db, profile.id, credit_in)


@router.delete("/me/credits/{credit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_credit(
    credit_id: uuid.UUID,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    credit = get_credit(db, credit_id)
    if credit is None or credit.talent_profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit not found")
    delete_credit(db, credit)


@router.post("/{talent_id}/save", status_code=status.HTTP_204_NO_CONTENT)
def save_talent_profile(
    talent_id: uuid.UUID,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    if get_talent_profile(db, talent_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")
    if get_saved_talent(db, recruiter.id, talent_id) is None:
        save_talent(db, recruiter.id, talent_id)


@router.delete("/{talent_id}/save", status_code=status.HTTP_204_NO_CONTENT)
def unsave_talent_profile(
    talent_id: uuid.UUID,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    saved = get_saved_talent(db, recruiter.id, talent_id)
    if saved is not None:
        unsave_talent(db, saved)
