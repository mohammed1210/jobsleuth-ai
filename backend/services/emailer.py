"""Email service for JobSleuth AI."""


from lib.settings import settings

try:
    import resend

    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False


async def send_email(
    to: str,
    subject: str,
    html: str,
    from_email: str | None = None,
) -> bool:
    """Send an email using Resend or Mailgun.

    Returns True if sent successfully, False otherwise.
    """
    from_addr = from_email or settings.EMAIL_FROM

    # Try Resend first
    if RESEND_AVAILABLE and settings.RESEND_API_KEY:
        try:
            resend.api_key = settings.RESEND_API_KEY

            params = {
                "from": from_addr,
                "to": [to],
                "subject": subject,
                "html": html,
            }

            resend.Emails.send(params)
            return True
        except Exception:
            pass  # Fall through to Mailgun or fail

    # Try Mailgun
    if settings.MAILGUN_API_KEY and settings.MAILGUN_DOMAIN:
        try:
            import requests

            response = requests.post(
                f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
                auth=("api", settings.MAILGUN_API_KEY),
                data={
                    "from": from_addr,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
                timeout=10,
            )

            return response.status_code == 200
        except Exception:
            pass

    # No email service configured
    return False


async def send_digest_email(user_email: str, jobs: list[dict]) -> bool:
    """Send a job digest email to a user."""
    if not jobs:
        return False

    # Build simple HTML email
    jobs_html = ""
    for job in jobs[:10]:  # Limit to 10 jobs
        jobs_html += f"""
        <div style="margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
            <h3 style="margin: 0 0 10px 0;">{job.get("title", "N/A")}</h3>
            <p style="margin: 5px 0;"><strong>Company:</strong> {job.get("company", "N/A")}</p>
            <p style="margin: 5px 0;"><strong>Location:</strong> {job.get("location", "N/A")}</p>
            <p style="margin: 5px 0;"><strong>Salary:</strong> {job.get("salary_text", "Not specified")}</p>
            <a href="{job.get("url", "#")}" style="display: inline-block; margin-top: 10px; padding: 8px 16px; background-color: #0070f3; color: white; text-decoration: none; border-radius: 4px;">View Job</a>
        </div>
        """

    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #333;">Your JobSleuth AI Digest</h1>
            <p>Here are {len(jobs)} new jobs that match your preferences:</p>
            {jobs_html}
            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 14px;">
                This is your JobSleuth AI job digest. To manage your preferences, visit your account settings.
            </p>
        </body>
    </html>
    """

    return await send_email(
        to=user_email,
        subject=f"Your JobSleuth Digest: {len(jobs)} New Jobs",
        html=html,
    )
