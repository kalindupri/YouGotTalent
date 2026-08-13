import json
import logging
import time
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
        _add_reaction(settings.DISCORD_MARKETING_CHANNEL_ID, message_id, emoji)

    return message_id


def _add_reaction(channel_id: str, message_id: str, emoji: str) -> None:
    """Discord's reaction endpoint has a tight per-channel rate limit — adding two reactions
    back-to-back (as post_draft_for_approval does) can trip it under moderate traffic. Retries
    once, honoring the exact wait Discord tells us to use via the 429 body's retry_after.
    """
    url = f"{DISCORD_API}/channels/{channel_id}/messages/{message_id}/reactions/{quote(emoji)}/@me"
    resp = httpx.put(url, headers=_headers(), timeout=10.0)
    if resp.status_code == 429:
        retry_after = float(resp.json().get("retry_after", 1.0))
        time.sleep(retry_after + 0.1)
        resp = httpx.put(url, headers=_headers(), timeout=10.0)
    resp.raise_for_status()


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


def create_thread(channel_id: str, name: str, initial_message: str) -> tuple[str, str]:
    """Creates a new public thread under channel_id (no starter message required — type 11 is
    GUILD_PUBLIC_THREAD) and posts initial_message into it. Returns (thread_id, message_id); the
    thread id works interchangeably with a channel id for every other function in this module,
    since Discord's message endpoints treat threads as channels. Raises on failure — the caller
    (starting a live-chat handoff) needs to know immediately if this didn't work, not silently
    drop the customer's request.
    """
    resp = httpx.post(
        f"{DISCORD_API}/channels/{channel_id}/threads",
        headers=_headers(),
        json={"name": name[:100], "type": 11, "auto_archive_duration": 1440},
        timeout=10.0,
    )
    resp.raise_for_status()
    thread_id = resp.json()["id"]

    msg_resp = httpx.post(
        f"{DISCORD_API}/channels/{thread_id}/messages",
        headers=_headers(),
        json={"content": initial_message},
        timeout=10.0,
    )
    msg_resp.raise_for_status()
    return thread_id, msg_resp.json()["id"]


def get_new_human_messages(channel_id: str, after_message_id: str | None) -> list[dict]:
    """Like get_human_replies_after, but returns {"id", "content"} pairs instead of just text —
    the id is needed so the caller can track how far it's already synced and only ask for what's
    new on the next poll. If after_message_id is None (a brand-new thread), fetches the most
    recent messages instead of erroring on a missing anchor.
    """
    bot_user_id = _bot_user_id()
    params: dict = {"limit": 50}
    if after_message_id:
        params["after"] = after_message_id
    resp = httpx.get(
        f"{DISCORD_API}/channels/{channel_id}/messages",
        headers=_headers(),
        params=params,
        timeout=10.0,
    )
    resp.raise_for_status()
    human_messages = [
        m for m in resp.json() if m["author"]["id"] != bot_user_id and not m["author"].get("bot")
    ]
    human_messages.sort(key=lambda m: int(m["id"]))
    return [
        {"id": m["id"], "content": m.get("content", "").strip()}
        for m in human_messages
        if m.get("content", "").strip()
    ]


def notify_channel(content: str) -> None:
    """Best-effort status note to the marketing channel (e.g. 'posted to Facebook', 'draft
    generation failed') — failures here are logged, not raised, since this is a courtesy
    message, not the core approval flow.
    """
    if not is_configured():
        return
    post_to_channel(settings.DISCORD_MARKETING_CHANNEL_ID, content)
