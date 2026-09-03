"""
HTTPS-first email service supporting Google Apps Script (Gmail MailApp over HTTPS),
Resend API, and legacy SMTP fallback with graceful error handling.

Priority:
1. Google Apps Script Web App HTTPS API (if APPS_SCRIPT_EMAIL_URL is configured)
2. Resend HTTPS API (if RESEND_API_KEY is configured)
3. SMTP (if SMTP_HOST is configured)
4. Dev Mode Fallback (returns tokens in response if no email provider is configured)
"""
import logging
import smtplib
from email.mime.text import MIMEText
import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


def is_email_configured() -> bool:
    """Checks if any email provider (Google Apps Script, Resend, or SMTP) is configured."""
    has_apps_script = bool(settings.APPS_SCRIPT_EMAIL_URL)
    has_resend = bool(settings.RESEND_API_KEY)
    has_smtp = bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)
    return has_apps_script or has_resend or has_smtp


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Sends an email via Google Apps Script (preferred), Resend, or SMTP.

    Returns True if successfully sent, False if skipped or failed. Handles all
    network/API exceptions gracefully so application flows never crash with 500.
    """
    if not is_email_configured():
        logger.info("Email sending skipped: No email provider configured.")
        return False

    # 1. Preferred: Google Apps Script Web App HTTPS API
    if settings.APPS_SCRIPT_EMAIL_URL:
        try:
            payload = {
                "secret": settings.APPS_SCRIPT_SHARED_SECRET,
                "recipient": to_email,
                "subject": subject,
                "body": body,
            }
            # Google Apps Script web apps return a 302 redirect on success;
            # allow_redirects=True follows it to 200 OK.
            resp = requests.post(
                settings.APPS_SCRIPT_EMAIL_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                allow_redirects=True,
                timeout=10,
            )

            # Check response status or JSON output
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if isinstance(data, dict) and data.get("status") == "error":
                        logger.error("Google Apps Script returned error: %s", data.get("message"))
                        return False
                except Exception:
                    pass  # Non-JSON 200 response still indicates request reached endpoint
                logger.info("Email successfully sent via Google Apps Script to %s", to_email)
                return True
            else:
                logger.error("Google Apps Script email request failed (status %s): %s", resp.status_code, resp.text)
                return False
        except Exception as exc:
            logger.exception("Failed to send email via Google Apps Script HTTPS API to %s: %s", to_email, str(exc))
            return False

    # 2. Resend HTTPS API
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
                logger.error("Resend API email error (status %s): %s", resp.status_code, resp.text)
                return False
        except Exception as exc:
            logger.exception("Failed to send email via Resend HTTPS API to %s: %s", to_email, str(exc))
            return False

    # 3. SMTP Fallback
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
