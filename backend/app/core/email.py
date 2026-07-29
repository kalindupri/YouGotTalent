import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger("app.email")


def send_email(to: str, subject: str, body: str) -> None:
    """Send an email, or log it if no SMTP server is configured.

    Safe default for local/dev environments: without SMTP_HOST set, nothing is actually
    sent over the network — the content is logged instead so the notification flow can
    still be exercised and verified.
    """
    if not settings.SMTP_HOST:
        logger.info("EMAIL (SMTP not configured, logging instead of sending)\nTo: %s\nSubject: %s\n\n%s", to, subject, body)
        return

    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)
