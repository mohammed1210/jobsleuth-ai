"""Graceful email helpers for JobSleuth AI."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

from lib.settings import settings


async def send_digest_email(to_email: str, jobs: list[dict[str, Any]] | None = None) -> bool:
    """Send a digest email, or no-op when SMTP is not configured."""
    jobs = jobs or []
    if not (settings.EMAIL_SERVER and settings.EMAIL_USER and settings.EMAIL_PASSWORD):
        return False

    message = EmailMessage()
    message["Subject"] = "Your JobSleuth AI digest"
    message["From"] = settings.EMAIL_FROM
    message["To"] = to_email
    lines = ["Here are your latest JobSleuth matches:", ""]
    lines.extend(f"- {job.get('title', 'Role')} at {job.get('company', 'Company')}" for job in jobs[:10])
    message.set_content("\n".join(lines))

    try:
        with smtplib.SMTP(settings.EMAIL_SERVER, 587, timeout=10) as server:
            server.starttls()
            server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            server.send_message(message)
        return True
    except Exception:
        return False


class Emailer:
    """Compatibility wrapper retained for older imports."""

    async def send_job_digest(self, to_email: str, user_name: str, jobs: list[dict[str, Any]], period: str = "daily") -> bool:
        return await send_digest_email(to_email, jobs)


_emailer = None


def get_emailer() -> Emailer:
    """Get or create the emailer singleton."""
    global _emailer
    if _emailer is None:
        _emailer = Emailer()
    return _emailer
