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

from app.core.private_storage import open_private_file
from app.core.security import decode_document_token
from app.crud.guardian_consent import get_document
from app.db.session import get_db

router = APIRouter(prefix="/documents", tags=["documents"])


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

    try:
        stream = open_private_file(document.storage_key)
    except (FileNotFoundError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return StreamingResponse(
        stream,
        media_type=document.content_type,
        headers={
            "Content-Disposition": "inline",
            # A stored file is attacker-influenced content. Don't let the browser sniff a
            # different type, don't let an embedded PDF run script, and don't cache it.
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "sandbox",
            "Cache-Control": "no-store, private",
        },
    )
