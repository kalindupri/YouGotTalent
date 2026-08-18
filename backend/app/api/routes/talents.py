import os
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_recruiter_profile,
    get_current_talent_profile,
    get_optional_current_user,
    get_optional_recruiter_profile,
    get_optional_viewer_role,
    require_talent,
)
from app.core.config import settings
from app.core.content_visibility import is_visible_to
from app.core.media_processing import MediaProcessingError, compress_audio, compress_photo, compress_video, probe_video_duration
from app.core.storage import delete_media_file, upload_media_file
from app.core.talent_eligibility import is_engageable, needs_guardian_consent
from app.core.talent_search_parse import parse_talent_search_query
from app.crud import subscription as subscription_crud
from app.crud.credit import create_credit, delete_credit, get_credit, update_credit
from app.crud.guardian_consent import mark_required
from app.crud.reel import count_reels, create_reel, delete_reel, get_reel
from app.crud.writing_sample import (
    count_published_writing_samples,
    create_writing_sample,
    delete_writing_sample,
    get_writing_sample,
    list_writing_samples_for_profile,
    to_read_schema as writing_sample_to_read_schema,
    update_writing_sample,
)
from app.crud.profile_view import count_profile_views, list_distinct_viewers, record_profile_view
from app.crud.review import get_talent_review_summary
from app.crud.saved_talent import get_saved_talent, save_talent, unsave_talent
from app.crud.talent_profile import (
    add_media,
    count_media,
    count_media_by_type,
    create_talent_profile,
    delete_media,
    get_cover_media,
    get_media,
    get_talent_profile,
    get_talent_profile_by_user,
    list_featured_talent,
    list_talent_profiles,
    request_verification,
    update_media,
    update_talent_profile,
)
from app.db.session import get_db
from app.models.media import MediaType
from app.models.recruiter_profile import RecruiterProfile
from app.models.talent_profile import TalentCategory, TalentProfile
from app.models.user import User, UserRole
from app.schemas.credit import CreditCreate, CreditRead, CreditUpdate
from app.schemas.reel import ReelCreate, ReelRead
from app.schemas.writing_sample import WritingSampleCreate, WritingSampleRead, WritingSampleUpdate
from app.models.writing_sample import WRITING_LANGUAGES, WRITING_TYPES
from app.schemas.profile_view import ProfileViewSummary
from app.schemas.review import TalentReviewSummary
from app.schemas.talent_profile import (
    TalentProfileOwnerRead,
    MediaCreate,
    MediaRead,
    MediaUpdate,
    ParsedTalentSearchQuery,
    TalentProfileCreate,
    TalentProfileRead,
    TalentProfileUpdate,
)

UPLOADABLE_MEDIA_TYPES = {"video", "audio"}

router = APIRouter(prefix="/talents", tags=["talents"])


@router.get("", response_model=list[TalentProfileRead])
def browse_talents(
    categories: list[TalentCategory] | None = Query(default=None),
    city: str | None = None,
    q: str | None = None,
    experience_min: int | None = None,
    experience_max: int | None = None,
    verified_only: bool = False,
    instruments: list[str] | None = Query(default=None),
    gender: str | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    min_tiktok_followers: int | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return list_talent_profiles(
        db,
        categories,
        city,
        q,
        skip,
        limit,
        experience_min,
        experience_max,
        verified_only,
        instruments,
        gender,
        age_min,
        age_max,
        min_tiktok_followers,
    )


@router.get("/parse-search-query", response_model=ParsedTalentSearchQuery)
def parse_search_query(q: str):
    """Turns a free-text recruiter query into structured filters the frontend can prefill
    into the normal browse/search filters (and show back to the recruiter as "detected:
    ..." chips) -- see app/core/talent_search_parse.py for how the parsing itself works.
    """
    return parse_talent_search_query(q)


@router.get("/me", response_model=TalentProfileOwnerRead)
def read_my_profile(profile: TalentProfile = Depends(get_current_talent_profile)):
    return profile


@router.get("/me/profile-views", response_model=ProfileViewSummary)
def read_my_profile_views(
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    count = count_profile_views(db, profile.id)
    viewers = list_distinct_viewers(db, profile.id) if profile.tier == "premium" else []
    return ProfileViewSummary(count=count, viewers=viewers)


@router.get("/featured", response_model=list[TalentProfileRead])
def read_featured_talent(db: Session = Depends(get_db)):
    return list_featured_talent(db, settings.PREMIUM_FEATURED_SLOT_LIMIT)


@router.get("/{talent_id}", response_model=TalentProfileRead)
def get_talent(
    talent_id: uuid.UUID,
    db: Session = Depends(get_db),
    viewer: RecruiterProfile | None = Depends(get_optional_recruiter_profile),
    viewer_role: UserRole | None = Depends(get_optional_viewer_role),
    viewer_user: User | None = Depends(get_optional_current_user),
):
    profile = get_talent_profile(db, talent_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")
    if viewer is not None:
        record_profile_view(db, profile.id, viewer.id)
    is_owner = viewer_user is not None and viewer_user.id == profile.user_id
    is_admin = viewer_user is not None and viewer_user.role == UserRole.ADMIN
    if not is_engageable(profile) and not (is_owner or is_admin):
        # 404, not 403: revealing "this exists but is hidden" would confirm a minor's profile
        # to anyone guessing ids.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")
    data = TalentProfileRead.model_validate(profile)
    data.media = [m for m in data.media if is_visible_to(m.visibility, viewer_role)]
    data.reels = [r for r in data.reels if is_visible_to(r.visibility, viewer_role)]
    # Drafts never leave the owner's own dashboard regardless of `visibility`; published ones
    # go through the normal visibility gate, and the body itself is truncated for non-owners
    # (see writing_sample_to_read_schema) so the full text is never actually sent to them.
    data.writing_samples = [
        writing_sample_to_read_schema(ws, is_owner=is_owner)
        for ws in profile.writing_samples
        if is_owner or (ws.is_published and is_visible_to(ws.visibility, viewer_role))
    ]
    return data


@router.get("/{talent_id}/reviews", response_model=TalentReviewSummary)
def read_talent_reviews(talent_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = get_talent_profile(db, talent_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")
    return get_talent_review_summary(db, talent_id)


@router.post("/me", response_model=TalentProfileOwnerRead, status_code=status.HTTP_201_CREATED)
def create_my_profile(
    profile_in: TalentProfileCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_talent),
):
    # The DB no longer enforces one-profile-per-account (a guardian may manage several
    # children), but nothing yet distinguishes a guardian, so keep ordinary talent to one
    # profile here. The guardian flow replaces this with a guardian-aware check.
    if get_talent_profile_by_user(db, user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Talent profile already exists")
    profile = create_talent_profile(db, user.id, profile_in)
    if needs_guardian_consent(profile):
        mark_required(db, profile)
    return profile


@router.patch("/me", response_model=TalentProfileOwnerRead)
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
    visibility: str = Form("public"),
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
                duration = probe_video_duration(raw_path)
                if duration > settings.MAX_VIDEO_DURATION_SECONDS:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Videos must be {settings.MAX_VIDEO_DURATION_SECONDS} seconds or shorter (this one is {int(duration)}s).",
                    )
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
    media_in = MediaCreate(url=url, media_type=MediaType(media_type), title=title or None, visibility=visibility)
    return add_media(db, profile.id, media_in)


@router.post("/me/cover-photo", response_model=MediaRead, status_code=status.HTTP_201_CREATED)
def upload_my_cover_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    existing_cover = get_cover_media(db, profile.id)

    # Only gate on the free-tier limit the first time a cover photo is set — replacing an
    # existing one deletes the old row first, so it never costs an extra slot.
    if existing_cover is None and profile.tier != "premium" and count_media(db, profile.id) >= settings.FREE_TIER_MEDIA_LIMIT:
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

    raw_suffix = Path(file.filename or "").suffix or ".jpg"

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_path = os.path.join(tmpdir, f"raw{raw_suffix}")
        with open(raw_path, "wb") as out:
            out.write(file.file.read())

        compressed_path = os.path.join(tmpdir, "compressed.jpg")
        try:
            compress_photo(raw_path, compressed_path)
        except MediaProcessingError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not process this file — make sure it's a valid image file.",
            )

        compressed_bytes = Path(compressed_path).read_bytes()

    url = upload_media_file(compressed_bytes, ".jpg", "image/jpeg")

    if existing_cover is not None:
        delete_media_file(existing_cover.url)
        delete_media(db, existing_cover)

    media_in = MediaCreate(url=url, media_type=MediaType.PHOTO, title="Profile photo", is_cover=True)
    return add_media(db, profile.id, media_in)


@router.patch("/me/media/{media_id}", response_model=MediaRead)
def update_my_media(
    media_id: uuid.UUID,
    media_in: MediaUpdate,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    media = get_media(db, media_id)
    if media is None or media.talent_profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media item not found")
    return update_media(db, media, media_in)


@router.delete("/me/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_media(
    media_id: uuid.UUID,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    media = get_media(db, media_id)
    if media is None or media.talent_profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media item not found")
    delete_media_file(media.url)
    delete_media(db, media)


@router.post("/me/intro-video", response_model=TalentProfileOwnerRead, status_code=status.HTTP_201_CREATED)
def upload_my_intro_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File is too large (max {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB)",
        )

    raw_suffix = Path(file.filename or "").suffix or ".mp4"

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_path = os.path.join(tmpdir, f"raw{raw_suffix}")
        with open(raw_path, "wb") as out:
            out.write(file.file.read())

        compressed_path = os.path.join(tmpdir, "compressed.mp4")
        try:
            duration = probe_video_duration(raw_path)
            if duration > settings.MAX_VIDEO_DURATION_SECONDS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Videos must be {settings.MAX_VIDEO_DURATION_SECONDS} seconds or shorter (this one is {int(duration)}s).",
                )
            compress_video(raw_path, compressed_path)
        except MediaProcessingError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not process this file — make sure it's a valid video file.",
            )

        compressed_bytes = Path(compressed_path).read_bytes()

    url = upload_media_file(compressed_bytes, ".mp4", "video/mp4")

    previous_url = profile.intro_video_url
    updated = update_talent_profile(db, profile, TalentProfileUpdate(intro_video_url=url))

    if previous_url:
        delete_media_file(previous_url)

    return updated


@router.post("/me/request-verification", response_model=TalentProfileOwnerRead)
def request_my_verification(
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    return request_verification(db, profile)


@router.post("/me/upgrade", response_model=TalentProfileOwnerRead)
def upgrade_my_tier(
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    # Starts (or reactivates) a real trial-backed subscription — see app/crud/subscription.py.
    # For a paid, non-trial checkout use POST /billing/checkout instead.
    subscription_crud.start_trial(db, talent_profile=profile)
    db.refresh(profile)
    return profile


@router.post("/me/credits", response_model=CreditRead, status_code=status.HTTP_201_CREATED)
def add_my_credit(
    credit_in: CreditCreate,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    return create_credit(db, profile.id, credit_in)


@router.patch("/me/credits/{credit_id}", response_model=CreditRead)
def update_my_credit(
    credit_id: uuid.UUID,
    credit_in: CreditUpdate,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    credit = get_credit(db, credit_id)
    if credit is None or credit.talent_profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit not found")
    return update_credit(db, credit, credit_in)


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


@router.post("/me/reels", response_model=ReelRead, status_code=status.HTTP_201_CREATED)
def add_my_reel(
    reel_in: ReelCreate,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    if profile.tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reels are a Premium feature. Upgrade to showcase your TikTok, Instagram, or Facebook Reels.",
        )
    if count_reels(db, profile.id) >= settings.PREMIUM_REEL_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You've reached the limit of {settings.PREMIUM_REEL_LIMIT} reels.",
        )
    try:
        return create_reel(db, profile.id, reel_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/me/reels/{reel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_reel(
    reel_id: uuid.UUID,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    reel = get_reel(db, reel_id)
    if reel is None or reel.talent_profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reel not found")
    delete_reel(db, reel)


@router.post("/me/writing-samples", response_model=WritingSampleRead, status_code=status.HTTP_201_CREATED)
def add_my_writing_sample(
    sample_in: WritingSampleCreate,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    if sample_in.writing_type not in WRITING_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"writing_type must be one of {WRITING_TYPES}")
    if sample_in.language not in WRITING_LANGUAGES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"language must be one of {WRITING_LANGUAGES}")
    if (
        sample_in.is_published
        and profile.tier != "premium"
        and count_published_writing_samples(db, profile.id) >= settings.FREE_TIER_WRITING_LIMIT
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Free accounts can publish up to {settings.FREE_TIER_WRITING_LIMIT} writing samples. Upgrade to publish more, or keep this one as a draft.",
        )
    sample = create_writing_sample(db, profile.id, sample_in)
    return writing_sample_to_read_schema(sample, is_owner=True)


@router.get("/me/writing-samples", response_model=list[WritingSampleRead])
def list_my_writing_samples(
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    samples = list_writing_samples_for_profile(db, profile.id, owner_view=True)
    return [writing_sample_to_read_schema(s, is_owner=True) for s in samples]


@router.patch("/me/writing-samples/{sample_id}", response_model=WritingSampleRead)
def update_my_writing_sample(
    sample_id: uuid.UUID,
    sample_in: WritingSampleUpdate,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    sample = get_writing_sample(db, sample_id)
    if sample is None or sample.talent_profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Writing sample not found")
    if sample_in.writing_type is not None and sample_in.writing_type not in WRITING_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"writing_type must be one of {WRITING_TYPES}")
    if sample_in.language is not None and sample_in.language not in WRITING_LANGUAGES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"language must be one of {WRITING_LANGUAGES}")
    wants_publish = sample_in.is_published and not sample.is_published
    if (
        wants_publish
        and profile.tier != "premium"
        and count_published_writing_samples(db, profile.id) >= settings.FREE_TIER_WRITING_LIMIT
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Free accounts can publish up to {settings.FREE_TIER_WRITING_LIMIT} writing samples. Upgrade to publish more.",
        )
    updated = update_writing_sample(db, sample, sample_in)
    return writing_sample_to_read_schema(updated, is_owner=True)


@router.delete("/me/writing-samples/{sample_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_writing_sample(
    sample_id: uuid.UUID,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    sample = get_writing_sample(db, sample_id)
    if sample is None or sample.talent_profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Writing sample not found")
    delete_writing_sample(db, sample)


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
