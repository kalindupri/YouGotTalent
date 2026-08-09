import httpx

from app.core.config import settings

GRAPH_API = "https://graph.facebook.com/v19.0"


class FacebookPostError(Exception):
    pass


def is_configured() -> bool:
    return bool(settings.FACEBOOK_PAGE_ID and settings.FACEBOOK_PAGE_ACCESS_TOKEN)


def _resolve_page_token() -> str:
    """FACEBOOK_PAGE_ACCESS_TOKEN is a long-lived *user* token with page permissions granted
    (that's what Meta's token generator hands out), not a Page token — posting as the Page
    requires exchanging it for the Page's own token via this lookup. Done on every call rather
    than cached/stored, since it's a cheap read and avoids ever needing to persist the derived
    secret anywhere.
    """
    resp = httpx.get(
        f"{GRAPH_API}/{settings.FACEBOOK_PAGE_ID}",
        params={"fields": "access_token", "access_token": settings.FACEBOOK_PAGE_ACCESS_TOKEN},
        timeout=15.0,
    )
    body = resp.json()
    if resp.status_code >= 400 or "error" in body or "access_token" not in body:
        detail = body.get("error", {}).get("message", resp.text)
        raise FacebookPostError(f"Could not resolve Page access token: {detail}")
    return body["access_token"]


def publish_page_post(message: str, image_bytes: bytes) -> str:
    """Publishes a photo post (branded template image + caption) to the configured Facebook
    Page. Returns the new post's id.

    Raises FacebookPostError with the Graph API's own error message on failure — the caller
    stores that on the MarketingPost row (status=failed) rather than losing the reason.
    """
    page_token = _resolve_page_token()
    resp = httpx.post(
        f"{GRAPH_API}/{settings.FACEBOOK_PAGE_ID}/photos",
        data={"caption": message, "access_token": page_token},
        files={"source": ("marketing-post.png", image_bytes, "image/png")},
        timeout=20.0,
    )
    body = resp.json()
    if resp.status_code >= 400 or "error" in body:
        detail = body.get("error", {}).get("message", resp.text)
        raise FacebookPostError(detail)
    return body.get("post_id") or body["id"]
