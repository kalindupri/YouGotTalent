"""Stores an uploaded media file and returns its public URL.

Uses Azure Blob Storage when configured; otherwise falls back to local disk (served by this
app at /media) so uploads work in local dev without any Azure credentials.
"""
import uuid
from pathlib import Path
from urllib.parse import unquote, urlsplit

from app.core.config import settings

LOCAL_MEDIA_DIR = Path(__file__).resolve().parent.parent.parent / "media_uploads"


def upload_media_file(data: bytes, extension: str, content_type: str) -> str:
    blob_name = f"{uuid.uuid4()}{extension}"

    if settings.AZURE_STORAGE_CONNECTION_STRING:
        from azure.storage.blob import BlobServiceClient, ContentSettings

        service = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        container = service.get_container_client(settings.AZURE_STORAGE_CONTAINER)
        blob = container.get_blob_client(blob_name)
        blob.upload_blob(data, content_settings=ContentSettings(content_type=content_type))
        return blob.url

    LOCAL_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    (LOCAL_MEDIA_DIR / blob_name).write_bytes(data)
    return f"{settings.BACKEND_PUBLIC_URL}/media/{blob_name}"


def delete_media_file(url: str) -> None:
    """Best-effort cleanup of a previously-uploaded file — failures here shouldn't block the
    request that's replacing it (e.g. a stale/already-deleted blob, or a URL that was never
    ours to begin with, like a pasted external link).
    """
    try:
        # Match the container as a whole path segment, not a bare substring: a substring test
        # also matches any *other* container whose name contains this one, and would then
        # delete a same-named blob from the wrong container.
        if settings.AZURE_STORAGE_CONNECTION_STRING and f"/{settings.AZURE_STORAGE_CONTAINER}/" in urlsplit(url).path:
            from azure.storage.blob import BlobServiceClient

            blob_name = _blob_name_from(url)
            service = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
            service.get_container_client(settings.AZURE_STORAGE_CONTAINER).get_blob_client(blob_name).delete_blob()
        elif url.startswith(f"{settings.BACKEND_PUBLIC_URL}/media/"):
            (LOCAL_MEDIA_DIR / _blob_name_from(url)).unlink(missing_ok=True)
    except Exception:
        pass


def _blob_name_from(url: str) -> str:
    """Last path segment, ignoring any query string.

    Splitting the raw URL on "/" would fold a trailing "?sv=...&sig=..." into the blob name,
    so a signed URL would resolve to a blob that doesn't exist.
    """
    return unquote(urlsplit(url).path.rsplit("/", 1)[-1])
