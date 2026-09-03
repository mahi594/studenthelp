"""
HTTPS-first email service (Resend API) with graceful error handling & SMTP fallback.

Supports sending via Resend HTTP API (https://api.resend.com/emails) over standard
HTTPS (port 443), eliminating Render's outbound SMTP port blocking issues (ports 25, 465, 587).
"""
import logging
import smtplib
from email.mime.text import MIMEText
import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


def is_email_configured() -> bool:
    """Checks if either Resend API or SMTP is configured."""
    has_resend = bool(settings.RESEND_API_KEY)
    has_smtp = bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)
    return has_resend or has_smtp


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Sends an email via Resend HTTPS API (preferred) or SMTP fallback.

    Returns True if successfully sent, False if skipped or failed. Handles
    network/API exceptions gracefully so application flows never crash.
    """
    if not is_email_configured():
        logger.info("Email sending skipped: No email provider configured.")
        return False

    # 1. Preferred: Resend HTTPS API (works on Render free tier, standard HTTPS port 443)
    if settings.RESEND_API_KEY:
        try:
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            }
            from_addr = settings.RESEND_FROM_EMAIL or "StudentHelp <onboarding@resend.dev>"
            payload = {
                "from": from_addr,
                "to": [to_email],
                "subject": subject,
                "text": body,
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code in (200, 201):
                logger.info("Email successfully sent via Resend API to %s", to_email)
                return True
            else:
                logger.error(
                    "Resend API email error (status %s): %s",
                    resp.status_code,
                    resp.text,
                )
                return False
        except Exception as exc:
            logger.exception("Failed to send email via Resend HTTPS API to %s: %s", to_email, str(exc))
            return False

    # 2. Fallback: SMTP (if configured and RESEND_API_KEY is unset)
    if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
            msg["To"] = to_email

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info("Email successfully sent via SMTP to %s", to_email)
            return True
        except Exception as exc:
            logger.exception("Failed to send email via SMTP to %s: %s", to_email, str(exc))
            return False

    return False


def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    body = f"""Someone requested a password reset for your StudentHelp account.

If this was you, click the link below to set a new password. This link
expires in 30 minutes.

{reset_link}

If you didn't request this, you can safely ignore this email."""
    return send_email(to_email, "Reset your StudentHelp password", body)


def send_verification_email(to_email: str, verify_link: str) -> bool:
    body = f"""Welcome to StudentHelp!

Verify your email to finish setting up your account. This link expires in
24 hours.

{verify_link}

If you didn't create this account, you can safely ignore this email."""
    return send_email(to_email, "Verify your StudentHelp email", body)
