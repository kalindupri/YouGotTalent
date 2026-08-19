import os
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_optional_current_user, get_current_talent_profile, get_optional_viewer_role
from app.core.config import settings
from app.core.content_visibility import is_visible_to
from app.core.talent_eligibility import require_engageable
from app.core.media_processing import MediaProcessingError, compress_audio, compress_photo, compress_video, probe_video_duration
from app.core.storage import delete_media_file, upload_media_file
from app.crud.library_item import create_library_item, delete_library_item, get_library_item, list_library_items
from app.crud.talent_profile import get_talent_profile
from app.db.session import get_db
from app.models.talent_profile import TalentProfile
from app.models.user import User, UserRole
from app.schemas.library_item import LibraryItemCreate, LibraryItemRead

router = APIRouter(tags=["library"])

UPLOADABLE_LIBRARY_TYPES = {"video", "audio", "photo"}

_PREMIUM_REQUIRED_DETAIL = (
    "A work library is a Premium feature — upgrade your account to build a permanent, "
    "public showcase of your work."
)


def _require_premium(profile: TalentProfile) -> None:
    if profile.tier != "premium":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_PREMIUM_REQUIRED_DETAIL)


@router.get("/talents/me/library", response_model=list[LibraryItemRead])
def read_my_library(db: Session = Depends(get_db), profile: TalentProfile = Depends(get_current_talent_profile)):
    return list_library_items(db, profile.id)


@router.post("/talents/me/library", response_model=LibraryItemRead, status_code=status.HTTP_201_CREATED)
def add_my_library_item(
    item_in: LibraryItemCreate,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    _require_premium(profile)
    return create_library_item(db, profile.id, item_in)


@router.post("/talents/me/library/upload", response_model=LibraryItemRead, status_code=status.HTTP_201_CREATED)
def upload_my_library_item(
    media_type: str = Form(...),
    title: str = Form(...),
    description: str | None = Form(None),
    visibility: str = Form("public"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    _require_premium(profile)
    if media_type not in UPLOADABLE_LIBRARY_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only photo, video, or audio files can be uploaded directly")

    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File is too large (max {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB)",
        )

    raw_suffix = Path(file.filename or "").suffix or {"video": ".mp4", "audio": ".m4a", "photo": ".jpg"}[media_type]
    out_suffix = {"video": ".mp4", "audio": ".m4a", "photo": ".jpg"}[media_type]
    content_type = {"video": "video/mp4", "audio": "audio/mp4", "photo": "image/jpeg"}[media_type]

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
            elif media_type == "audio":
                compress_audio(raw_path, compressed_path)
            else:
                compress_photo(raw_path, compressed_path)
        except MediaProcessingError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not process this file — make sure it's a valid photo/video/audio file.",
            )

        compressed_bytes = Path(compressed_path).read_bytes()

    url = upload_media_file(compressed_bytes, out_suffix, content_type)
    item_in = LibraryItemCreate(title=title, description=description, media_type=media_type, url=url, visibility=visibility)
    return create_library_item(db, profile.id, item_in)


@router.delete("/talents/me/library/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_my_library_item(
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    profile: TalentProfile = Depends(get_current_talent_profile),
):
    item = get_library_item(db, item_id)
    if item is None or item.talent_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library item not found")
    delete_media_file(item.url)
    delete_library_item(db, item)


@router.get("/talents/{talent_id}/library", response_model=list[LibraryItemRead])
def read_talent_library(
    talent_id: uuid.UUID,
    db: Session = Depends(get_db),
    viewer_role: UserRole | None = Depends(get_optional_viewer_role),
    viewer_user: User | None = Depends(get_optional_current_user),
):
    talent = get_talent_profile(db, talent_id)
    if talent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")
    require_engageable(talent)
    is_owner = viewer_user is not None and viewer_user.id == talent.user_id
    items = list_library_items(db, talent_id)
    return [item for item in items if is_visible_to(item.visibility, viewer_role, is_owner=is_owner)]
