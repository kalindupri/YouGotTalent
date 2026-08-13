from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query, status

router = APIRouter(prefix="/reels", tags=["reels"])


@router.get("/oembed")
def get_tiktok_oembed(url: str = Query(...)) -> dict:
    # This is a public, unauthenticated proxy — pin it to tiktok.com only so it can't be
    # abused as an open fetch-any-URL relay.
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        host = ""
    host = host.lower().removeprefix("www.")
    if host != "tiktok.com":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only tiktok.com URLs are supported.")

    try:
        resp = httpx.get("https://www.tiktok.com/oembed", params={"url": url}, timeout=10.0)
    except httpx.HTTPError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not reach TikTok.")

    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="TikTok could not embed this video.")

    return resp.json()
