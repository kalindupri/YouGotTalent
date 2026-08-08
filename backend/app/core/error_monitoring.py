import logging
import time

from app.core.discord import send_discord_message

# Uncaught exceptions bubble up through Starlette's ServerErrorMiddleware and get logged by
# uvicorn on the "uvicorn.error" logger, which propagates to root — so a single handler on the
# root logger catches both those and any explicit logger.error()/logger.exception() call
# anywhere in the app, without needing a custom FastAPI exception handler (which would swallow
# exceptions before pytest's TestClient can re-raise them, breaking test debuggability).
_ALERT_COOLDOWN_SECONDS = 300
_last_alerted: dict[str, float] = {}


def _signature(record: logging.LogRecord) -> str:
    """Identify "the same error happening again" so a crash loop doesn't flood Discord.

    Keyed on the exception type + message where available (e.g. repeated unhandled exceptions,
    which all share uvicorn's generic "Exception in ASGI application" log message and would
    otherwise be indistinguishable from each other).
    """
    if record.exc_info and record.exc_info[1] is not None:
        exc = record.exc_info[1]
        return f"{record.name}:{type(exc).__name__}:{exc}"
    return f"{record.name}:{record.getMessage()}"


class DiscordErrorHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            signature = _signature(record)
            now = time.monotonic()
            # A default of 0 here would falsely look "recent" (within the cooldown window)
            # for any signature seen for the first time during the first 5 minutes after
            # process start, since time.monotonic() itself starts near 0 at boot — silencing
            # every alert right after a deploy/restart. -inf means "never alerted" always fires.
            if now - _last_alerted.get(signature, float("-inf")) < _ALERT_COOLDOWN_SECONDS:
                return
            _last_alerted[signature] = now

            message = self.format(record)
            if len(message) > 1800:
                message = message[:1800] + "\n… (truncated)"
            send_discord_message(f"🔥 **Server error** (`{record.name}`)\n```{message}```")
        except Exception:
            pass  # alerting must never be the thing that breaks request handling


def setup_error_monitoring() -> None:
    handler = DiscordErrorHandler(level=logging.ERROR)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logging.getLogger().addHandler(handler)
    # uvicorn's own logging config sets the "uvicorn" logger to propagate=False, so unhandled
    # ASGI exceptions (logged on "uvicorn.error", a child of "uvicorn") never reach the root
    # handler above — attach directly here too so those are still caught.
    logging.getLogger("uvicorn.error").addHandler(handler)
