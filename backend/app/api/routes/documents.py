"""Serving identity documents to reviewers.

Browsers can't attach an Authorization header to an <img src> or an <iframe src>, so viewing a
document needs a URL that carries its own authority. That's a short-lived, app-signed token
scoped to one document id -- not an Azure SAS, which would leak the blob URL into history and
referrers, couldn't be revoked before expiry, and would behave differently in local dev.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.private_storage import is_private_ref, key_from_ref, open_private_file
from app.core.security import decode_document_token
from app.crud.guardian_consent import get_document
from app.db.session import get_db
from app.models.media import Media

router = APIRouter(prefix="/documents", tags=["documents"])


def _stream(storage_key: str, content_type: str) -> StreamingResponse:
    try:
        stream = open_private_file(storage_key)
    except (FileNotFoundError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return StreamingResponse(
        stream,
        media_type=content_type,
        headers={
            "Content-Disposition": "inline",
            # Stored files are attacker-influenced content. Don't let the browser sniff a
            # different type, don't let an embedded PDF run script, and don't cache it.
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "sandbox",
            "Cache-Control": "no-store, private",
        },
    )


@router.get("/{document_id}")
def read_document(document_id: uuid.UUID, t: str, db: Session = Depends(get_db)):
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="This link is invalid or has expired."
    )
    granted_id = decode_document_token(t)
    # The id is inside the signed payload, so editing the path can't point a valid link at a
    # different document.
    if granted_id is None or granted_id != str(document_id):
        raise unauthorized

    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return _stream(document.storage_key, document.content_type)


@router.get("/media/{media_id}")
def read_private_media(media_id: uuid.UUID, t: str, db: Session = Depends(get_db)):
    """Serve a portfolio item belonging to a minor whose guardian consent isn't approved yet.

    Their media is kept out of the public container until consent is granted, so it needs the
    same signed-link treatment as the consent documents. The link is minted per-request when
    the profile is serialized for someone entitled to see it.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="This link is invalid or has expired."
    )
    granted_id = decode_document_token(t)
    if granted_id is None or granted_id != str(media_id):
        raise unauthorized

    media = db.query(Media).filter(Media.id == media_id).first()
    if media is None or not is_private_ref(media.url):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    return _stream(key_from_ref(media.url), _content_type_for(media))


def _content_type_for(media: Media) -> str:
    return {
        "photo": "image/jpeg",
        "video": "video/mp4",
        "audio": "audio/mp4",
    }.get(media.media_type, "application/octet-stream")
