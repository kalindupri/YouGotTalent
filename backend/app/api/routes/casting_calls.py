import os
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_recruiter_profile
from app.core.config import settings
from app.core.email import send_email
from app.core.media_processing import MediaProcessingError, compress_audio, probe_video_duration
from app.core.storage import upload_media_file
from app.crud.casting_call import (
    create_casting_call,
    delete_casting_call,
    get_casting_call,
    increment_view_count,
    list_casting_calls,
    update_casting_call,
)
from app.crud.follow import list_follower_talents
from app.crud.recruiter_profile import count_open_casting_calls
from app.crud.talent_profile import list_talent_profiles_for_job_alert
from app.db.session import get_db
from app.models.recruiter_profile import RecruiterProfile
from app.models.talent_profile import TalentCategory
from app.schemas.casting_call import CastingCallCreate, CastingCallRead, CastingCallUpdate

router = APIRouter(prefix="/casting-calls", tags=["casting-calls"])

# Both the guide track and the instrumental a talent sings along to must be short excerpts, not
# full songs -- same cap as the sung take a talent records against them.
MAX_AUDITION_TRACK_SECONDS = 30


@router.post("/audio-tracks/upload")
def upload_audition_track(
    file: UploadFile = File(...),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    """Uploads a guide/instrumental track for the singing-audition flow and returns its URL --
    not tied to a specific role yet, since roles are only created as part of the casting call
    creation payload (see CastingCallRoleCreate.guide_track_url / instrumental_track_url).
    """
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File is too large (max {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB)",
        )

    raw_suffix = Path(file.filename or "").suffix or ".m4a"
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_path = os.path.join(tmpdir, f"raw{raw_suffix}")
        with open(raw_path, "wb") as out:
            out.write(file.file.read())

        compressed_path = os.path.join(tmpdir, "compressed.m4a")
        try:
            duration = probe_video_duration(raw_path)
            if duration > MAX_AUDITION_TRACK_SECONDS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Audition tracks must be {MAX_AUDITION_TRACK_SECONDS} seconds or shorter (this one is {int(duration)}s).",
                )
            compress_audio(raw_path, compressed_path)
        except MediaProcessingError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not process this file — make sure it's a valid audio file.",
            )

        compressed_bytes = Path(compressed_path).read_bytes()

    url = upload_media_file(compressed_bytes, ".m4a", "audio/mp4")
    return {"url": url}


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
    if call_in.premium_talent_only and recruiter.tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Restricting a talent hunt to Premium talent is a Premium feature. Upgrade your organizer account to use it.",
        )
    if len(call_in.roles) > 1 and recruiter.tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Posting multiple roles in one talent hunt is a Premium feature. Upgrade your organizer account, or post each role as a separate talent hunt.",
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


def _get_own_casting_call(db: Session, casting_call_id: uuid.UUID, recruiter: RecruiterProfile):
    call = get_casting_call(db, casting_call_id)
    if call is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Casting call not found")
    if call.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't own this talent hunt")
    return call


@router.patch("/{casting_call_id}", response_model=CastingCallRead)
def update_my_casting_call(
    casting_call_id: uuid.UUID,
    call_in: CastingCallUpdate,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    call = _get_own_casting_call(db, casting_call_id, recruiter)
    if call_in.premium_talent_only and recruiter.tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Restricting a talent hunt to Premium talent is a Premium feature. Upgrade your organizer account to use it.",
        )
    return update_casting_call(db, call, call_in)


@router.delete("/{casting_call_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_casting_call(
    casting_call_id: uuid.UUID,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    call = _get_own_casting_call(db, casting_call_id, recruiter)
    delete_casting_call(db, call)
