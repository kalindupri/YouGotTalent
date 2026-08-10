from app.core import email
from app.core.config import settings
from app.core.email_template import _text_to_html_paragraphs, render_branded_email


def test_send_email_via_smtp_includes_both_plain_and_html_parts(monkeypatch):
    monkeypatch.setattr(settings, "AZURE_COMMUNICATION_CONNECTION_STRING", None)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_USER", None)
    monkeypatch.setattr(settings, "SMTP_PASSWORD", None)
    monkeypatch.setattr(settings, "SMTP_USE_TLS", False)

    sent = {}

    class FakeSMTP:
        def __init__(self, host, port):
            sent["host"] = host

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def send_message(self, message):
            sent["message"] = message

    monkeypatch.setattr(email.smtplib, "SMTP", FakeSMTP)

    email.send_email("talent@example.com", "You got a reply", "Hello there.\n\nSecond paragraph.")

    message = sent["message"]
    assert message.is_multipart()
    content_types = {part.get_content_type() for part in message.walk()}
    assert "text/plain" in content_types
    assert "text/html" in content_types

    plain_part = next(p for p in message.walk() if p.get_content_type() == "text/plain")
    html_part = next(p for p in message.walk() if p.get_content_type() == "text/html")
    assert "Hello there." in plain_part.get_content()
    assert "Hello there." in html_part.get_content()
    assert "YouGotTalent" in html_part.get_content()


def test_send_email_via_acs_payload_includes_html_key(monkeypatch):
    monkeypatch.setattr(settings, "AZURE_COMMUNICATION_CONNECTION_STRING", "endpoint=https://fake;accesskey=fake")
    monkeypatch.setattr(settings, "SMTP_HOST", None)

    captured = {}

    class FakePoller:
        def result(self):
            return None

    class FakeEmailClient:
        @staticmethod
        def from_connection_string(conn_str):
            return FakeEmailClient()

        def begin_send(self, message):
            captured["message"] = message
            return FakePoller()

    import sys
    import types

    fake_module = types.ModuleType("azure.communication.email")
    fake_module.EmailClient = FakeEmailClient
    monkeypatch.setitem(sys.modules, "azure.communication.email", fake_module)

    email.send_email("recruiter@example.com", "New application", "Someone applied.")

    assert "html" in captured["message"]["content"]
    assert "plainText" in captured["message"]["content"]
    assert "YouGotTalent" in captured["message"]["content"]["html"]


def test_text_to_html_paragraphs_escapes_user_supplied_content():
    body = "A message with <script>alert('x')</script> in it.\n\nSecond paragraph."
    rendered = _text_to_html_paragraphs(body)
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered


def test_render_branded_email_includes_subject_and_wordmark():
    rendered = render_branded_email("Application accepted", "<p>Congrats.</p>")
    assert "Application accepted" in rendered
    assert "YouGotTalent" in rendered
    assert "<p>Congrats.</p>" in rendered
