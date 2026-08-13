from app.core import discord_bot
from app.core.config import settings
from tests.conftest import auth_headers, register_and_verify


def _configure(monkeypatch):
    monkeypatch.setattr(settings, "DISCORD_BOT_TOKEN", "fake-token")
    monkeypatch.setattr(settings, "DISCORD_SUPPORT_CHANNEL_ID", "999")


def test_unavailable_when_not_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "DISCORD_SUPPORT_CHANNEL_ID", None)
    resp = client.get("/api/v1/support/available")
    assert resp.json() == {"available": False}

    start = client.post("/api/v1/support/start", json={"question": "help"})
    assert start.status_code == 503


def test_available_when_configured(client, monkeypatch):
    _configure(monkeypatch)
    resp = client.get("/api/v1/support/available")
    assert resp.json() == {"available": True}


def test_guest_starts_conversation_and_polls_for_reply(client, monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr(discord_bot, "create_thread", lambda channel_id, name, initial_message: ("thread-1", "100"))

    start = client.post("/api/v1/support/start", json={"question": "What is this platform?"})
    assert start.status_code == 200, start.text
    convo = start.json()
    assert convo["status"] == "open"
    assert len(convo["messages"]) == 1
    assert convo["messages"][0]["sender"] == "customer"
    assert convo["messages"][0]["content"] == "What is this platform?"

    # No agent reply yet
    monkeypatch.setattr(discord_bot, "get_new_human_messages", lambda channel_id, after_message_id: [])
    poll1 = client.get(f"/api/v1/support/{convo['id']}")
    assert len(poll1.json()["messages"]) == 1

    # Agent replies from Discord
    monkeypatch.setattr(
        discord_bot, "get_new_human_messages", lambda channel_id, after_message_id: [{"id": "101", "content": "Hi, how can I help?"}]
    )
    poll2 = client.get(f"/api/v1/support/{convo['id']}")
    messages = poll2.json()["messages"]
    assert len(messages) == 2
    assert messages[1]["sender"] == "agent"
    assert messages[1]["content"] == "Hi, how can I help?"


def test_logged_in_user_message_is_relayed_to_discord(client, db_session, monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr(discord_bot, "create_thread", lambda channel_id, name, initial_message: ("thread-2", "200"))
    monkeypatch.setattr(discord_bot, "get_new_human_messages", lambda channel_id, after_message_id: [])

    posted = []
    monkeypatch.setattr(discord_bot, "post_to_channel", lambda channel_id, content: posted.append((channel_id, content)))

    token = register_and_verify(client, db_session, "supportuser@example.com", full_name="Support User")
    headers = auth_headers(token)

    start = client.post("/api/v1/support/start", json={"question": "help please"}, headers=headers)
    convo_id = start.json()["id"]

    send = client.post(f"/api/v1/support/{convo_id}/messages", json={"content": "follow-up question"})
    assert send.status_code == 200, send.text
    contents = [m["content"] for m in send.json()["messages"]]
    assert contents == ["help please", "follow-up question"]
    assert posted == [("thread-2", "follow-up question")]


def test_discord_failure_on_start_returns_502(client, monkeypatch):
    import httpx

    _configure(monkeypatch)

    def _raise(*args, **kwargs):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr(discord_bot, "create_thread", _raise)
    resp = client.post("/api/v1/support/start", json={"question": "help"})
    assert resp.status_code == 502


def test_poll_unknown_conversation_404s(client, monkeypatch):
    _configure(monkeypatch)
    import uuid

    resp = client.get(f"/api/v1/support/{uuid.uuid4()}")
    assert resp.status_code == 404
