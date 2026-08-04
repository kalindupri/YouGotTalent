import os
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_recruiter_profile, get_current_talent_profile
from app.core.config import settings
from app.core.email import send_email
from app.core.media_processing import MediaProcessingError, compress_audio, compress_video
from app.core.storage import upload_media_file
from app.crud.application import (
    create_application,
    get_application,
    list_applications_for_casting_call,
    list_applications_for_talent,
    update_application_status,
)
from app.crud.casting_call import get_casting_call
from app.db.session import get_db
from app.models.recruiter_profile import RecruiterProfile
from app.models.talent_profile import TalentProfile
from app.schemas.application import ApplicationCreate, ApplicationRead, ApplicationStatusUpdate

router = APIRouter(tags=["applications"])

UPLOADABLE_SUBMISSION_TYPES = {"video", "audio"}


def _create_application_and_notify(
    db: Session,
    background_tasks: BackgroundTasks,
    casting_call_id: uuid.UUID,
    talent: TalentProfile,
    application_in: ApplicationCreate,
):
    call = get_casting_call(db, casting_call_id)
    if call is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Casting call not found")
    if not any(r.id == application_in.role_id for r in call.roles):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That role doesn't belong to this casting call")
    if call.premium_talent_only and talent.tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This talent hunt is open to Premium talent only. Upgrade your account to apply.",
        )

    try:
        application = create_application(db, casting_call_id, talent.id, application_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You've already applied to this role")

    background_tasks.add_task(
        send_email,
        call.recruiter.user.email,
        f"New application for {call.title}",
        f"{talent.display_name} just applied to your talent hunt \"{call.title}\".\n\n"
        f"Review it here: {settings.FRONTEND_URL}/dashboard/casting-calls/{call.id}",
    )
    return application


@router.post("/casting-calls/{casting_call_id}/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def apply_to_casting_call(
    casting_call_id: uuid.UUID,
    application_in: ApplicationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    talent: TalentProfile = Depends(get_current_talent_profile),
):
    return _create_application_and_notify(db, background_tasks, casting_call_id, talent, application_in)


@router.post("/casting-calls/{casting_call_id}/applications/upload", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def apply_to_casting_call_with_upload(
    casting_call_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    role_id: uuid.UUID = Form(...),
    media_type: str = Form(...),
    message: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    talent: TalentProfile = Depends(get_current_talent_profile),
):
    if media_type not in UPLOADABLE_SUBMISSION_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only video or audio files can be uploaded directly")

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
    application_in = ApplicationCreate(role_id=role_id, message=message or None, submission_url=url)
    return _create_application_and_notify(db, background_tasks, casting_call_id, talent, application_in)


@router.get("/casting-calls/{casting_call_id}/applications", response_model=list[ApplicationRead])
def list_casting_call_applications(
    casting_call_id: uuid.UUID,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    call = get_casting_call(db, casting_call_id)
    if call is None or call.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Casting call not found")
    return list_applications_for_casting_call(db, casting_call_id, score=recruiter.tier == "premium")


@router.get("/talents/me/applications", response_model=list[ApplicationRead])
def list_my_applications(
    db: Session = Depends(get_db),
    talent: TalentProfile = Depends(get_current_talent_profile),
):
    return list_applications_for_talent(db, talent.id)


@router.patch("/applications/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: uuid.UUID,
    status_in: ApplicationStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    recruiter: RecruiterProfile = Depends(get_current_recruiter_profile),
):
    application = get_application(db, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    call = get_casting_call(db, application.casting_call_id)
    if call is None or call.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your casting call")
    updated = update_application_status(db, application, status_in.status)

    background_tasks.add_task(
        send_email,
        application.talent.user.email,
        f"Your application for {call.title} was updated",
        f"Your application for \"{call.title}\" is now: {status_in.status.value}.\n\n"
        f"View it here: {settings.FRONTEND_URL}/casting-calls/{call.id}",
    )
    return updated