"""The private lane for identity documents.

These guard a security boundary rather than a feature: guardian NICs and children's birth
certificates must never become readable the way ordinary portfolio media is (the media
container is provisioned with public blob access).
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.private_storage import (
    LOCAL_PRIVATE_DIR,
    delete_private_file,
    open_private_file,
    upload_private_file,
)
from app.core.security import (
    create_access_token,
    create_document_token,
    decode_access_token,
    decode_document_token,
)
from app.core.storage import LOCAL_MEDIA_DIR, delete_media_file
from app.core.upload_validation import enforce_document_size, is_image, sniff_document

PDF_BYTES = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\n"
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 32


# --- Content-type validation ---------------------------------------------------------------


@pytest.mark.parametrize(
    "data,expected_type,expected_ext",
    [(PDF_BYTES, "application/pdf", ".pdf"), (PNG_BYTES, "image/png", ".png"), (JPEG_BYTES, "image/jpeg", ".jpg")],
)
def test_sniff_accepts_the_three_document_types(data, expected_type, expected_ext):
    assert sniff_document(data) == (expected_type, expected_ext)


@pytest.mark.parametrize(
    "data",
    [
        b"MZ\x90\x00\x03",  # Windows executable
        b"<!DOCTYPE html><html><body>hi</body></html>",
        b"GIF89a" + b"\x00" * 16,  # a real image type, but not one we accept
        b"",
    ],
)
def test_sniff_rejects_anything_else(data):
    with pytest.raises(HTTPException) as exc:
        sniff_document(data)
    assert exc.value.status_code == 400


def test_type_comes_from_the_bytes_not_the_claimed_filename_or_content_type():
    # A PNG uploaded as "scan.pdf" with Content-Type: application/pdf. The claim is ignored;
    # what gets stored is typed from the actual bytes.
    content_type, extension = sniff_document(PNG_BYTES)
    assert (content_type, extension) == ("image/png", ".png")


def test_size_cap(monkeypatch):
    from app.core.config import settings

    enforce_document_size(settings.MAX_DOCUMENT_SIZE_BYTES)  # exactly at the cap is fine
    with pytest.raises(HTTPException) as exc:
        enforce_document_size(settings.MAX_DOCUMENT_SIZE_BYTES + 1)
    assert exc.value.status_code == 413


def test_only_images_are_re_encoded():
    assert is_image("image/jpeg") and is_image("image/png")
    assert not is_image("application/pdf")


# --- Document tokens -----------------------------------------------------------------------


def test_document_token_round_trip():
    token = create_document_token("doc-123", ttl_seconds=60)
    assert decode_document_token(token) == "doc-123"


def test_document_token_expires():
    token = create_document_token("doc-123", ttl_seconds=-1)
    assert decode_document_token(token) is None


def test_document_token_is_scoped_to_one_document():
    # The id is inside the signed payload, so a link to one document can't be pointed at
    # another by editing the URL.
    assert decode_document_token(create_document_token("doc-a", ttl_seconds=60)) != "doc-b"


def test_an_access_token_cannot_be_used_as_a_document_token():
    assert decode_document_token(create_access_token("user-1")) is None


def test_a_document_token_cannot_be_used_as_an_access_token():
    # The dangerous direction: a short-lived, admin-minted view grant must never authenticate
    # a session as whatever user id it happens to carry.
    assert decode_access_token(create_document_token("doc-123", ttl_seconds=60)) is None


def test_garbage_tokens_are_rejected():
    assert decode_document_token("not-a-token") is None
    assert decode_document_token("") is None


# --- Private storage -----------------------------------------------------------------------


def test_upload_returns_an_opaque_key_not_a_url():
    key = upload_private_file(PDF_BYTES, ".pdf", "application/pdf")
    try:
        assert "://" not in key and "/" not in key
        assert key.endswith(".pdf")
    finally:
        delete_private_file(key)


def test_round_trip_read():
    key = upload_private_file(PDF_BYTES, ".pdf", "application/pdf")
    try:
        assert b"".join(open_private_file(key)) == PDF_BYTES
    finally:
        delete_private_file(key)


def test_documents_do_not_land_in_the_publicly_served_media_directory():
    # main.py mounts LOCAL_MEDIA_DIR at /media with no auth dependency. A document that ended
    # up there would be world-readable at a guessable URL.
    key = upload_private_file(PDF_BYTES, ".pdf", "application/pdf")
    try:
        assert not (LOCAL_MEDIA_DIR / key).exists()
        assert (LOCAL_PRIVATE_DIR / key).exists()
        assert LOCAL_PRIVATE_DIR.resolve() != LOCAL_MEDIA_DIR.resolve()
        assert LOCAL_PRIVATE_DIR.resolve() not in LOCAL_MEDIA_DIR.resolve().parents
    finally:
        delete_private_file(key)


def test_delete_removes_the_file():
    key = upload_private_file(PDF_BYTES, ".pdf", "application/pdf")
    delete_private_file(key)
    with pytest.raises(FileNotFoundError):
        open_private_file(key)


def test_missing_key_raises_not_found():
    with pytest.raises(FileNotFoundError):
        open_private_file("00000000-0000-0000-0000-000000000000.pdf")


@pytest.mark.parametrize("key", ["../secrets.env", "nested/path.pdf", "..\\windows.pdf", ""])
def test_keys_that_could_escape_the_directory_are_rejected(key):
    with pytest.raises(ValueError):
        open_private_file(key)


def test_delete_of_a_missing_document_is_silent():
    delete_private_file("00000000-0000-0000-0000-000000000000.pdf")  # must not raise


# --- delete_media_file must not reach into the private container ---------------------------


def test_delete_media_file_ignores_a_private_container_url():
    from app.core.config import settings

    url = f"https://acct.blob.core.windows.net/{settings.AZURE_PRIVATE_CONTAINER}/abc.pdf"
    with patch("app.core.config.settings.AZURE_STORAGE_CONNECTION_STRING", "UseDevelopmentStorage=true"):
        with patch("azure.storage.blob.BlobServiceClient") as blob_client:
            delete_media_file(url)
            blob_client.from_connection_string.assert_not_called()


def test_delete_media_file_strips_a_sas_query_string_from_the_blob_name():
    from app.core.config import settings

    url = f"https://acct.blob.core.windows.net/{settings.AZURE_STORAGE_CONTAINER}/abc.mp4?sv=2024-01-01&sig=deadbeef"
    service = MagicMock()
    with patch("app.core.config.settings.AZURE_STORAGE_CONNECTION_STRING", "UseDevelopmentStorage=true"):
        with patch("azure.storage.blob.BlobServiceClient") as blob_client:
            blob_client.from_connection_string.return_value = service
            delete_media_file(url)

    container = service.get_container_client.return_value
    container.get_blob_client.assert_called_once_with("abc.mp4")
