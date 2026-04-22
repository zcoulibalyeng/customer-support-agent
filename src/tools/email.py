"""
Email tool — sends confirmation and follow-up emails.

When SMTP is configured (via env vars), sends real emails.
Otherwise, logs the email to stdout for development.
"""

import smtplib
from email.mime.text import MIMEText

from langchain_core.tools import tool

from src.utils.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a customer. Use for order confirmations, refund notifications, and follow-ups."""

    if not SMTP_HOST:
        # Development mode — just log it
        print(f"\n  [Email - DEV MODE] To: {to}")
        print(f"  Subject: {subject}")
        print(f"  Body: {body[:200]}...")
        return f"Email logged (dev mode) — To: {to}, Subject: {subject}"

    # Production mode — send real email
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = to

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, to, msg.as_string())

        return f"Email sent successfully to {to}: {subject}"

    except Exception as e:
        return f"Failed to send email: {e}"
