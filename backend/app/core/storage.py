"""Stores an uploaded media file and returns its public URL.

Uses Azure Blob Storage when configured; otherwise falls back to local disk (served by this
app at /media) so uploads work in local dev without any Azure credentials.
"""
import uuid
from pathlib import Path

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
        if settings.AZURE_STORAGE_CONNECTION_STRING and settings.AZURE_STORAGE_CONTAINER in url:
            from azure.storage.blob import BlobServiceClient

            blob_name = url.rsplit("/", 1)[-1]
            service = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
            service.get_container_client(settings.AZURE_STORAGE_CONTAINER).get_blob_client(blob_name).delete_blob()
        elif url.startswith(f"{settings.BACKEND_PUBLIC_URL}/media/"):
            blob_name = url.rsplit("/", 1)[-1]
            (LOCAL_MEDIA_DIR / blob_name).unlink(missing_ok=True)
    except Exception:
        pass
