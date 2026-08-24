"""
Minimal SMTP email sender. If SMTP isn't configured (no SMTP_HOST in .env),
sending is skipped and the caller is told so - the password reset endpoint
uses this to fall back to returning the reset token directly in the API
response for local development, since there's no email account to receive it.

For real deployment: any SMTP provider works (Gmail app password, SendGrid,
Postmark, AWS SES's SMTP interface, etc) - just fill in the four SMTP_*
settings in .env.
"""
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings


def is_email_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Returns True if actually sent, False if skipped (not configured)."""
    if not is_email_configured():
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
    msg["To"] = to_email

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)

    return True


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
