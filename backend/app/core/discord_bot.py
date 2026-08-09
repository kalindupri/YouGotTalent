import json
import logging
from urllib.parse import quote

import httpx

from app.core.config import settings

logger = logging.getLogger("app.discord_bot")

DISCORD_API = "https://discord.com/api/v10"
APPROVE_EMOJI = "✅"  # white_check_mark
REJECT_EMOJI = "❌"  # x

# Distinct from app/core/discord.py's fire-and-forget webhook (used for internal error/report
# alerts, send-only). This talks to the Discord bot REST API instead, because reading back a
# reaction requires a bot with its own token/identity — a webhook has neither.


def is_configured() -> bool:
    return bool(settings.DISCORD_BOT_TOKEN and settings.DISCORD_MARKETING_CHANNEL_ID)


def _headers() -> dict:
    return {"Authorization": f"Bot {settings.DISCORD_BOT_TOKEN}"}


def post_draft_for_approval(content: str, image_bytes: bytes) -> str:
    """Posts the draft (with its branded template image) to the marketing channel and adds the
    two reaction options. Returns the Discord message ID so it can be checked later. Raises on
    failure — the caller (a cron-triggered endpoint) should surface that as a failed draft
    generation, not swallow it.
    """
    resp = httpx.post(
        f"{DISCORD_API}/channels/{settings.DISCORD_MARKETING_CHANNEL_ID}/messages",
        headers=_headers(),
        data={
            "payload_json": json.dumps(
                {"content": f"**Marketing post draft — react ✅ to post to Facebook, ❌ to discard:**\n\n{content}"}
            )
        },
        files={"files[0]": ("marketing-post.png", image_bytes, "image/png")},
        timeout=15.0,
    )
    resp.raise_for_status()
    message_id = resp.json()["id"]

    for emoji in (APPROVE_EMOJI, REJECT_EMOJI):
        react_resp = httpx.put(
            f"{DISCORD_API}/channels/{settings.DISCORD_MARKETING_CHANNEL_ID}/messages/{message_id}/reactions/{quote(emoji)}/@me",
            headers=_headers(),
            timeout=10.0,
        )
        react_resp.raise_for_status()

    return message_id


def post_topic_prompt(text: str) -> str:
    """Posts a plain status message (no attachment, no reactions) and returns its message id,
    so a later poll can look for a human reply posted after it. Raises on failure, same as
    post_draft_for_approval — this is the start of the core flow, not a courtesy notice.
    """
    resp = httpx.post(
        f"{DISCORD_API}/channels/{settings.DISCORD_MARKETING_CHANNEL_ID}/messages",
        headers=_headers(),
        json={"content": text},
        timeout=10.0,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def get_latest_human_reply(channel_id: str, after_message_id: str) -> str | None:
    """Returns the text of the earliest human (non-bot) message posted after after_message_id,
    or None if nobody has replied yet. Message IDs are Discord snowflakes (time-ordered), so
    comparing them as integers reliably finds the first reply without relying on the API's
    response ordering.
    """
    bot_user_id = _bot_user_id()
    resp = httpx.get(
        f"{DISCORD_API}/channels/{channel_id}/messages",
        headers=_headers(),
        params={"after": after_message_id, "limit": 50},
        timeout=10.0,
    )
    resp.raise_for_status()
    human_messages = [
        m for m in resp.json() if m["author"]["id"] != bot_user_id and not m["author"].get("bot")
    ]
    if not human_messages:
        return None
    earliest = min(human_messages, key=lambda m: int(m["id"]))
    return earliest.get("content", "").strip() or None


def get_human_replies_after(channel_id: str, after_message_id: str) -> list[str]:
    """Returns the text of every human (non-bot) message posted after after_message_id,
    oldest-to-newest. Unlike get_latest_human_reply (which returns only the single earliest
    reply — correct for "what's the answer to the prompt I just posted"), this returns all of
    them so a caller scanning for a specific format (e.g. a manual Header:/Body: request) isn't
    permanently stuck on an old, non-matching message that happens to be the earliest one after
    that anchor.
    """
    bot_user_id = _bot_user_id()
    resp = httpx.get(
        f"{DISCORD_API}/channels/{channel_id}/messages",
        headers=_headers(),
        params={"after": after_message_id, "limit": 50},
        timeout=10.0,
    )
    resp.raise_for_status()
    human_messages = [
        m for m in resp.json() if m["author"]["id"] != bot_user_id and not m["author"].get("bot")
    ]
    human_messages.sort(key=lambda m: int(m["id"]))
    return [m.get("content", "").strip() for m in human_messages if m.get("content", "").strip()]


def get_human_reaction(channel_id: str, message_id: str) -> str | None:
    """Returns "approved", "rejected", or None if no human has reacted yet.

    Only counts a reaction from a real user, not the bot's own reaction it added when posting
    the draft (Discord's reaction-users endpoint includes the reacting bot itself).
    """
    bot_user_id = _bot_user_id()

    for emoji, result in ((APPROVE_EMOJI, "approved"), (REJECT_EMOJI, "rejected")):
        resp = httpx.get(
            f"{DISCORD_API}/channels/{channel_id}/messages/{message_id}/reactions/{quote(emoji)}",
            headers=_headers(),
            timeout=10.0,
        )
        resp.raise_for_status()
        users = resp.json()
        if any(u["id"] != bot_user_id for u in users):
            return result
    return None


_cached_bot_user_id: str | None = None


def _bot_user_id() -> str:
    global _cached_bot_user_id
    if _cached_bot_user_id is None:
        resp = httpx.get(f"{DISCORD_API}/users/@me", headers=_headers(), timeout=10.0)
        resp.raise_for_status()
        _cached_bot_user_id = resp.json()["id"]
    return _cached_bot_user_id


def post_to_channel(channel_id: str, content: str) -> None:
    """Best-effort message post to an arbitrary channel via the bot — failures are logged, not
    raised, since this is used for status notes and alerts, not flows with a required outcome.
    Requires only DISCORD_BOT_TOKEN (not the marketing channel id), so it also works for
    channels unrelated to the marketing pipeline, e.g. error alerts.
    """
    if not settings.DISCORD_BOT_TOKEN:
        return
    try:
        httpx.post(
            f"{DISCORD_API}/channels/{channel_id}/messages",
            headers=_headers(),
            json={"content": content},
            timeout=10.0,
        )
    except httpx.HTTPError:
        logger.exception("Failed to post message to Discord channel %s", channel_id)


def notify_channel(content: str) -> None:
    """Best-effort status note to the marketing channel (e.g. 'posted to Facebook', 'draft
    generation failed') — failures here are logged, not raised, since this is a courtesy
    message, not the core approval flow.
    """
    if not is_configured():
        return
    post_to_channel(settings.DISCORD_MARKETING_CHANNEL_ID, content)
