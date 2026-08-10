import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.email_template import _text_to_html_paragraphs, render_branded_email

logger = logging.getLogger("app.email")


def send_email(to: str, subject: str, body: str) -> None:
    """Send an email via Azure Communication Services (production), SMTP (local/dev), or log
    it if neither is configured.

    Safe default for local/dev environments: without any mail provider configured, nothing
    is actually sent over the network — the content is logged instead so the notification
    flow can still be exercised and verified.

    `body` stays the single source of truth (plain text, blank-line-separated paragraphs) so
    none of this app's ~10 call sites need to change — the branded HTML part is derived from
    it automatically.
    """
    html_body = render_branded_email(subject, _text_to_html_paragraphs(body))
    if settings.AZURE_COMMUNICATION_CONNECTION_STRING:
        _send_via_acs(to, subject, body, html_body)
    elif settings.SMTP_HOST:
        _send_via_smtp(to, subject, body, html_body)
    else:
        logger.info("EMAIL (no mail provider configured, logging instead of sending)\nTo: %s\nSubject: %s\n\n%s", to, subject, body)


def _send_via_acs(to: str, subject: str, body: str, html_body: str) -> None:
    from azure.communication.email import EmailClient

    client = EmailClient.from_connection_string(settings.AZURE_COMMUNICATION_CONNECTION_STRING)
    message = {
        "senderAddress": settings.EMAIL_FROM,
        "recipients": {"to": [{"address": to}]},
        "content": {"subject": subject, "plainText": body, "html": html_body},
    }
    poller = client.begin_send(message)
    poller.result()


def _send_via_smtp(to: str, subject: str, body: str, html_body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)
