import logging

import pytest

from app.core import error_monitoring as em


@pytest.fixture(autouse=True)
def _clear_alert_cache():
    em._last_alerted.clear()
    yield
    em._last_alerted.clear()


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
