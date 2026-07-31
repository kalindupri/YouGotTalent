import logging

import httpx

from app.core.config import settings

logger = logging.getLogger("app.discord")


def send_discord_message(content: str) -> None:
    """Post a message to the configured Discord webhook, or log it if none is configured.

    Best-effort only: a Discord outage or bad webhook URL should never block the request
    that triggered the notification (e.g. a user filing a report), so failures are swallowed.
    """
    if not settings.DISCORD_WEBHOOK_URL:
        logger.info("DISCORD (webhook not configured, logging instead of sending)\n%s", content)
        return

    try:
        httpx.post(settings.DISCORD_WEBHOOK_URL, json={"content": content}, timeout=5.0)
    except httpx.HTTPError:
        logger.exception("Failed to post Discord notification")
