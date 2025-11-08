"""
Email service for sending digests and notifications.

Uses Resend API for transactional emails.
"""

from typing import Dict, List, Optional
import httpx

from backend.lib.settings import settings


async def send_email(
    to: str,
    subject: str,
    html: str,
    from_email: Optional[str] = None
) -> Dict:
    """
    Send an email using Resend API.
    
    Args:
        to: Recipient email address
        subject: Email subject
        html: HTML email body
        from_email: Optional sender email (defaults to settings.EMAIL_FROM)
        
    Returns:
        API response dictionary
        
    Raises:
        Exception: If email sending fails
    """
    if not settings.RESEND_API_KEY:
        raise Exception("RESEND_API_KEY not configured")
    
    from_addr = from_email or settings.EMAIL_FROM
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": from_addr,
                "to": [to],
                "subject": subject,
                "html": html
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to send email: {response.text}")
        
        return response.json()


async def send_job_digest(
    user_email: str,
    jobs: List[Dict],
    cadence: str = "weekly"
) -> Dict:
    """
    Send a job digest email to a user.
    
    Args:
        user_email: User's email address
        jobs: List of job dictionaries
        cadence: Digest cadence (daily, weekly, monthly)
        
    Returns:
        API response dictionary
    """
    # Build HTML email
    jobs_html = ""
    for job in jobs[:10]:  # Limit to 10 jobs
        salary = job.get('salary_text', 'Salary not specified')
        location = job.get('location', 'Location not specified')
        
        jobs_html += f"""
        <div style="margin-bottom: 20px; padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <h3 style="margin: 0 0 10px 0; color: #1a1a1a;">
                <a href="{job.get('url', '#')}" style="color: #2563eb; text-decoration: none;">
                    {job.get('title', 'Untitled Position')}
                </a>
            </h3>
            <p style="margin: 5px 0; color: #666;">
                <strong>{job.get('company', 'Company')}</strong> • {location}
            </p>
            <p style="margin: 5px 0; color: #666;">
                💰 {salary}
            </p>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #1a1a1a; margin: 0;">🔍 JobSleuth AI</h1>
            <p style="color: #666; margin: 10px 0;">Your {cadence.capitalize()} Job Digest</p>
        </div>
        
        <p>Hi there! We've found <strong>{len(jobs)} new jobs</strong> that match your preferences.</p>
        
        <div style="margin: 30px 0;">
            {jobs_html}
        </div>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; text-align: center; color: #666; font-size: 14px;">
            <p>Want to adjust your digest settings? <a href="https://jobsleuth.ai/account" style="color: #2563eb;">Manage your preferences</a></p>
            <p style="margin-top: 10px;">To unsubscribe, <a href="https://jobsleuth.ai/unsubscribe" style="color: #666;">click here</a></p>
        </div>
    </body>
    </html>
    """
    
    subject = f"JobSleuth AI: {len(jobs)} New Job{'s' if len(jobs) != 1 else ''} Matching Your Profile"
    
    return await send_email(user_email, subject, html)


async def send_welcome_email(user_email: str) -> Dict:
    """
    Send a welcome email to a new user.
    
    Args:
        user_email: User's email address
        
    Returns:
        API response dictionary
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #1a1a1a; margin: 0;">🎉 Welcome to JobSleuth AI!</h1>
        </div>
        
        <p>Thank you for joining JobSleuth AI! We're excited to help you find your dream job.</p>
        
        <h2 style="color: #1a1a1a; margin-top: 30px;">Getting Started</h2>
        <ol style="padding-left: 20px;">
            <li style="margin: 10px 0;">Browse thousands of job listings</li>
            <li style="margin: 10px 0;">Save jobs you're interested in</li>
            <li style="margin: 10px 0;">Get AI-powered job fit scores (Pro feature)</li>
            <li style="margin: 10px 0;">Receive personalized job alerts</li>
        </ol>
        
        <div style="text-align: center; margin: 40px 0;">
            <a href="https://jobsleuth.ai/jobs" style="display: inline-block; padding: 12px 30px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 6px; font-weight: 600;">
                Start Exploring Jobs
            </a>
        </div>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; text-align: center; color: #666; font-size: 14px;">
            <p>Questions? Reply to this email or visit our <a href="https://jobsleuth.ai/help" style="color: #2563eb;">Help Center</a></p>
        </div>
    </body>
    </html>
    """
    
    return await send_email(user_email, "Welcome to JobSleuth AI! 🎉", html)
