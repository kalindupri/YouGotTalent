import logging

import pytest

from app.core import error_monitoring as em
from app.core.config import settings


@pytest.fixture(autouse=True)
def _clear_alert_cache():
    em._last_alerted.clear()
    yield
    em._last_alerted.clear()


@pytest.fixture(autouse=True)
def _no_dedicated_error_channel_by_default(monkeypatch):
    # Local/CI .env may have DISCORD_BOT_TOKEN and DISCORD_ERROR_CHANNEL_ID genuinely set (for
    # the marketing pipeline / real error alerts) — without this, tests here would silently make
    # live calls to Discord instead of testing the send_discord_message() fallback path. Tests
    # that specifically want the bot path override these themselves.
    monkeypatch.setattr(settings, "DISCORD_BOT_TOKEN", None)
    monkeypatch.setattr(settings, "DISCORD_ERROR_CHANNEL_ID", None)


def _attach_handler(logger_name: str) -> tuple[logging.Logger, em.DiscordErrorHandler]:
    logger = logging.getLogger(logger_name)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    handler = em.DiscordErrorHandler(level=logging.ERROR)
    logger.addHandler(handler)
    return logger, handler


def test_error_triggers_discord_alert(monkeypatch):
    sent = []
    monkeypatch.setattr(em, "send_discord_message", lambda msg: sent.append(msg))
    logger, handler = _attach_handler("test.error_monitoring.basic")

    logger.error("Something broke")

    assert len(sent) == 1
    assert "Something broke" in sent[0]
    logger.removeHandler(handler)


def test_repeated_identical_error_is_deduped(monkeypatch):
    sent = []
    monkeypatch.setattr(em, "send_discord_message", lambda msg: sent.append(msg))
    logger, handler = _attach_handler("test.error_monitoring.dedupe")

    logger.error("Something broke")
    logger.error("Something broke")
    logger.error("Something broke")

    assert len(sent) == 1
    logger.removeHandler(handler)


def test_distinct_errors_both_alert(monkeypatch):
    sent = []
    monkeypatch.setattr(em, "send_discord_message", lambda msg: sent.append(msg))
    logger, handler = _attach_handler("test.error_monitoring.distinct")

    logger.error("First problem")
    logger.error("Second problem")

    assert len(sent) == 2
    logger.removeHandler(handler)


def test_info_level_does_not_alert(monkeypatch):
    sent = []
    monkeypatch.setattr(em, "send_discord_message", lambda msg: sent.append(msg))
    logger, handler = _attach_handler("test.error_monitoring.info")

    logger.info("Just some info")
    logger.warning("Just a warning")

    assert sent == []
    logger.removeHandler(handler)


def test_unhandled_exception_traceback_is_included(monkeypatch):
    sent = []
    monkeypatch.setattr(em, "send_discord_message", lambda msg: sent.append(msg))
    logger, handler = _attach_handler("test.error_monitoring.exc")

    try:
        raise ValueError("boom")
    except ValueError:
        logger.exception("Unhandled exception on POST /talents/me/media/upload")

    assert len(sent) == 1
    assert "ValueError: boom" in sent[0]
    logger.removeHandler(handler)


def test_error_posts_to_dedicated_channel_via_bot_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "DISCORD_BOT_TOKEN", "fake-token")
    monkeypatch.setattr(settings, "DISCORD_ERROR_CHANNEL_ID", "999888777")

    webhook_sent = []
    bot_sent = []
    monkeypatch.setattr(em, "send_discord_message", lambda msg: webhook_sent.append(msg))
    monkeypatch.setattr(em.discord_bot, "post_to_channel", lambda channel_id, msg: bot_sent.append((channel_id, msg)))
    logger, handler = _attach_handler("test.error_monitoring.dedicated_channel")

    logger.error("Something broke")

    assert webhook_sent == []
    assert len(bot_sent) == 1
    assert bot_sent[0][0] == "999888777"
    assert "Something broke" in bot_sent[0][1]
    logger.removeHandler(handler)


def test_same_exception_type_from_different_handler_calls_is_deduped(monkeypatch):
    sent = []
    monkeypatch.setattr(em, "send_discord_message", lambda msg: sent.append(msg))
    logger, handler = _attach_handler("test.error_monitoring.exc_dedupe")

    for _ in range(3):
        try:
            raise RuntimeError("db connection lost")
        except RuntimeError:
            logger.exception("Exception in ASGI application")

    assert len(sent) == 1
    logger.removeHandler(handler)
