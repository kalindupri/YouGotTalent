"""Content-type validation for uploaded identity documents.

The rest of the app has no upload type checking at all -- it leans on ffmpeg failing loudly on
anything that isn't media. That doesn't work here (a PDF is a legitimate document but ffmpeg
can't read one), and it isn't good enough anyway for files an admin will open in a browser.

Everything below is decided from the file's own leading bytes. The client-supplied filename
and Content-Type are never trusted: both are attacker-controlled, and a mismatch between them
and the real content is exactly how a "profile photo" turns out to be an HTML page.
"""
import os

from fastapi import HTTPException, status

from app.core.config import settings

# Magic-byte prefix -> (canonical content type, canonical extension).
_SIGNATURES: list[tuple[bytes, str, str]] = [
    (b"%PDF-", "application/pdf", ".pdf"),
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
]

ALLOWED_DOCUMENT_DESCRIPTION = "PDF, JPEG, or PNG"


def sniff_document(data: bytes) -> tuple[str, str]:
    """Return (content_type, extension) derived from the bytes themselves.

    Raises 400 if the content isn't one of the allowed document types.
    """
    for prefix, content_type, extension in _SIGNATURES:
        if data.startswith(prefix):
            return content_type, extension
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Upload a {ALLOWED_DOCUMENT_DESCRIPTION} file. We couldn't read this one as any of those.",
    )


def enforce_document_size(size: int) -> None:
    if size > settings.MAX_DOCUMENT_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"That file is too large (max {settings.MAX_DOCUMENT_SIZE_BYTES // (1024 * 1024)}MB).",
        )


def read_document_upload(upload) -> bytes:
    """Size-check an UploadFile by seeking, then read it.

    Deliberately measures before reading. Starlette spools a large upload to a temp file, so
    calling .read() first would pull the whole thing into memory -- a 2GB upload would cost 2GB
    of RAM before the size limit was ever consulted. Seeking to the end costs nothing.
    """
    upload.file.seek(0, os.SEEK_END)
    size = upload.file.tell()
    upload.file.seek(0)
    enforce_document_size(size)
    return upload.file.read()


def is_image(content_type: str) -> bool:
    """Images get re-encoded before storage, which strips EXIF (including GPS) and destroys
    any script payload smuggled alongside the image data. PDFs are stored byte-for-byte.
    """
    return content_type in {"image/jpeg", "image/png"}
