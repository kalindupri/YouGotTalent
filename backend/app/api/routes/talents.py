import os
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_recruiter_profile, get_current_talent_profile, require_talent
from app.core.config import settings
from app.core.media_processing import MediaProcessingError, compress_audio, compress_video
from app.core.storage import upload_media_file
from app.crud.credit import create_credit, delete_credit, get_credit
from app.crud.review import get_talent_review_summary
from app.crud.saved_talent import get_saved_talent, save_talent, unsave_talent
from app.crud.talent_profile import (
    add_media,
    count_media,
    count_media_by_type,
    create_talent_profile,
    get_talent_profile,
    get_talent_profile_by_user,
    list_talent_profiles,
    request_verification,
    set_tier,
    update_talent_profile,
)
from app.db.session import get_db
from app.models.media import MediaType
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

UPLOADABLE_MEDIA_TYPES = {"video", "audio"}

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


@router.post("/me/media/upload", response_model=MediaRead, status_code=status.HTTP_201_CREATED)
def upload_my_media(
    media_type: str = Form(...),
    title: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    if media_type not in UPLOADABLE_MEDIA_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only video or audio files can be uploaded directly")

    if media_type == "video":
        video_limit = settings.PREMIUM_TIER_VIDEO_LIMIT if profile.tier == "premium" else settings.FREE_TIER_VIDEO_LIMIT
        if count_media_by_type(db, profile.id, MediaType.VIDEO) >= video_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"You've reached the limit of {video_limit} audition video(s) for your account."
                    + (" Upgrade to Premium for more." if profile.tier != "premium" else "")
                ),
            )
    elif profile.tier != "premium" and count_media(db, profile.id) >= settings.FREE_TIER_MEDIA_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Free accounts can add up to {settings.FREE_TIER_MEDIA_LIMIT} portfolio items. Upgrade to Premium for unlimited auditions.",
        )

    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File is too large (max {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB)",
        )

    raw_suffix = Path(file.filename or "").suffix or (".mp4" if media_type == "video" else ".m4a")
    out_suffix = ".mp4" if media_type == "video" else ".m4a"
    content_type = "video/mp4" if media_type == "video" else "audio/mp4"

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_path = os.path.join(tmpdir, f"raw{raw_suffix}")
        with open(raw_path, "wb") as out:
            out.write(file.file.read())

        compressed_path = os.path.join(tmpdir, f"compressed{out_suffix}")
        try:
            if media_type == "video":
                compress_video(raw_path, compressed_path)
            else:
                compress_audio(raw_path, compressed_path)
        except MediaProcessingError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not process this file — make sure it's a valid video/audio file.",
            )

        compressed_bytes = Path(compressed_path).read_bytes()

    url = upload_media_file(compressed_bytes, out_suffix, content_type)
    media_in = MediaCreate(url=url, media_type=MediaType(media_type), title=title or None)
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
