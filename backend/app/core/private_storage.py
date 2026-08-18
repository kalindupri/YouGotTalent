"""Storage for identity documents -- guardian ID, a child's birth certificate.

Deliberately separate from storage.py. That module's contract is "bytes in, PUBLIC URL out",
which only works because AZURE_STORAGE_CONTAINER is provisioned with public blob access. These
files must never be reachable without an authorization check, so this module returns an opaque
storage KEY that means nothing on its own; app/api/routes/documents.py is the only way to read
one back, and only for an admin holding a short-lived signed token.

The local-dev fallback writes to a directory that main.py deliberately does NOT mount, unlike
LOCAL_MEDIA_DIR which is served unauthenticated at /media.
"""
import uuid
from pathlib import Path
from typing import Iterator

from app.core.config import settings

LOCAL_PRIVATE_DIR = Path(__file__).resolve().parent.parent.parent / "private_uploads"


def upload_private_file(data: bytes, extension: str, content_type: str) -> str:
    """Store bytes privately and return an opaque storage key (never a URL)."""
    key = f"{uuid.uuid4()}{extension}"

    if settings.AZURE_STORAGE_CONNECTION_STRING:
        from azure.storage.blob import BlobServiceClient, ContentSettings

        service = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        container = service.get_container_client(settings.AZURE_PRIVATE_CONTAINER)
        container.get_blob_client(key).upload_blob(data, content_settings=ContentSettings(content_type=content_type))
        return key

    LOCAL_PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    (LOCAL_PRIVATE_DIR / key).write_bytes(data)
    return key


def open_private_file(key: str) -> Iterator[bytes]:
    """Stream a stored document back. Raises FileNotFoundError if it's gone."""
    _reject_traversal(key)

    if settings.AZURE_STORAGE_CONNECTION_STRING:
        from azure.core.exceptions import ResourceNotFoundError
        from azure.storage.blob import BlobServiceClient

        service = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        blob = service.get_container_client(settings.AZURE_PRIVATE_CONTAINER).get_blob_client(key)
        try:
            return blob.download_blob().chunks()
        except ResourceNotFoundError as exc:
            raise FileNotFoundError(key) from exc

    path = LOCAL_PRIVATE_DIR / key
    if not path.is_file():
        raise FileNotFoundError(key)
    return iter([path.read_bytes()])


def delete_private_file(key: str) -> None:
    """Best-effort cleanup, matching delete_media_file's contract -- a document that's already
    gone shouldn't fail the request deleting the record that pointed at it.
    """
    try:
        _reject_traversal(key)
        if settings.AZURE_STORAGE_CONNECTION_STRING:
            from azure.storage.blob import BlobServiceClient

            service = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
            service.get_container_client(settings.AZURE_PRIVATE_CONTAINER).get_blob_client(key).delete_blob()
        else:
            (LOCAL_PRIVATE_DIR / key).unlink(missing_ok=True)
    except Exception:
        pass


def _reject_traversal(key: str) -> None:
    """Keys are generated as bare uuid4 + extension, so anything with a separator in it did not
    come from upload_private_file and must not be used to build a path.
    """
    if not key or "/" in key or "\\" in key or ".." in key:
        raise ValueError("Invalid storage key")
