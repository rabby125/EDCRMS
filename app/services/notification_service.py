"""
Simple SMTP email sender + in-app notification writer.

If SMTP_HOST is not configured in .env, send_email() silently no-ops
(useful for local dev) but still logs to the in-app `notifications` table.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.log_model import Notification


def send_email(to_email: str, subject: str, body: str) -> bool:
    if not settings.SMTP_HOST:
        # SMTP not configured — skip actual sending (dev mode)
        return False

    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
        return True
    except Exception:
        # In production, log this properly instead of swallowing it
        return False


def notify_user(db: Session, user_id: int, message: str, email: Optional[str] = None,
                 email_subject: str = "EDCRMS Notification"):
    """Writes an in-app notification and, if email is provided, also emails it."""
    note = Notification(user_id=user_id, message=message)
    db.add(note)
    db.commit()

    if email:
        send_email(email, email_subject, f"<p>{message}</p>")


def notify_warranty_expiring(db: Session, admin_emails: list[str], device_hostname: str, expiry_date):
    message = f"Device '{device_hostname}' warranty expires on {expiry_date}."
    subject = f"⚠️ Warranty Alert: {device_hostname}"
    for email in admin_emails:
        send_email(email, subject, f"<p>{message}</p>")
