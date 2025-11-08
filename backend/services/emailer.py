"""Email service for JobSleuth using Resend or Mailgun.

Provides templated digest emails and simple transactional wrapper.
"""

import os
from typing import Any, Optional
from enum import Enum


class EmailProvider(Enum):
    """Supported email providers."""
    RESEND = "resend"
    MAILGUN = "mailgun"


class Emailer:
    """Email service wrapper for JobSleuth."""
    
    def __init__(self):
        """Initialize emailer with provider configuration."""
        provider_name = os.getenv("EMAIL_PROVIDER", "resend").lower()
        self.provider = EmailProvider(provider_name)
        self.api_key = os.getenv("EMAIL_API_KEY")
        self.from_email = os.getenv("EMAIL_FROM", "noreply@jobsleuth.ai")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "JobSleuth AI")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send a transactional email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.api_key:
            print("Email API key not configured")
            return False
        
        if self.provider == EmailProvider.RESEND:
            return self._send_resend(to_email, subject, html_content, text_content)
        elif self.provider == EmailProvider.MAILGUN:
            return self._send_mailgun(to_email, subject, html_content, text_content)
        
        return False
    
    def _send_resend(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str]
    ) -> bool:
        """Send email via Resend.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body
            
        Returns:
            Success status
        """
        try:
            import requests
            
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            
            if text_content:
                payload["text"] = text_content
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            print(f"Email sent successfully via Resend to {to_email}")
            return True
        except Exception as e:
            print(f"Failed to send email via Resend: {e}")
            return False
    
    def _send_mailgun(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str]
    ) -> bool:
        """Send email via Mailgun.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body
            
        Returns:
            Success status
        """
        try:
            import requests
            
            domain = os.getenv("MAILGUN_DOMAIN")
            if not domain:
                print("Mailgun domain not configured")
                return False
            
            url = f"https://api.mailgun.net/v3/{domain}/messages"
            
            data = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": to_email,
                "subject": subject,
                "html": html_content,
            }
            
            if text_content:
                data["text"] = text_content
            
            response = requests.post(
                url,
                auth=("api", self.api_key),
                data=data,
                timeout=10
            )
            response.raise_for_status()
            
            print(f"Email sent successfully via Mailgun to {to_email}")
            return True
        except Exception as e:
            print(f"Failed to send email via Mailgun: {e}")
            return False
    
    def send_job_digest(
        self,
        to_email: str,
        user_name: str,
        jobs: list[dict[str, Any]],
        period: str = "daily"
    ) -> bool:
        """Send a job digest email.
        
        Args:
            to_email: Recipient email
            user_name: User's name
            jobs: List of jobs to include
            period: Digest period (daily, weekly)
            
        Returns:
            Success status
        """
        subject = f"Your {period.capitalize()} Job Digest from JobSleuth"
        
        # Build HTML content
        html_content = self._build_digest_html(user_name, jobs, period)
        text_content = self._build_digest_text(user_name, jobs, period)
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """Send a welcome email to new user.
        
        Args:
            to_email: Recipient email
            user_name: User's name
            
        Returns:
            Success status
        """
        subject = "Welcome to JobSleuth AI!"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h1>Welcome to JobSleuth, {user_name}!</h1>
            <p>We're excited to help you find your next career opportunity.</p>
            <p>Here's what you can do next:</p>
            <ul>
                <li>Complete your profile to get better job matches</li>
                <li>Browse available jobs and save your favorites</li>
                <li>Set up job alerts to never miss an opportunity</li>
            </ul>
            <p>
                <a href="https://jobsleuth.ai/jobs" 
                   style="background-color: #4F46E5; color: white; padding: 10px 20px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Start Exploring Jobs
                </a>
            </p>
            <p>Happy job hunting!<br>The JobSleuth Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to JobSleuth, {user_name}!
        
        We're excited to help you find your next career opportunity.
        
        Here's what you can do next:
        - Complete your profile to get better job matches
        - Browse available jobs and save your favorites
        - Set up job alerts to never miss an opportunity
        
        Start exploring jobs: https://jobsleuth.ai/jobs
        
        Happy job hunting!
        The JobSleuth Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def _build_digest_html(
        self,
        user_name: str,
        jobs: list[dict[str, Any]],
        period: str
    ) -> str:
        """Build HTML content for job digest.
        
        Args:
            user_name: User's name
            jobs: List of jobs
            period: Digest period
            
        Returns:
            HTML content
        """
        job_items = ""
        for job in jobs[:10]:  # Limit to 10 jobs
            job_items += f"""
            <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <h3 style="margin: 0 0 8px 0;">{job.get('title', 'N/A')}</h3>
                <p style="margin: 4px 0; color: #6b7280;">{job.get('company', 'N/A')}</p>
                <p style="margin: 4px 0; color: #6b7280;">📍 {job.get('location', 'N/A')}</p>
                {f'<p style="margin: 4px 0; color: #6b7280;">💰 {job.get("salary", "")}</p>' if job.get('salary') else ''}
                <p style="margin: 12px 0 0 0;">
                    <a href="{job.get('url', '#')}" 
                       style="background-color: #4F46E5; color: white; padding: 8px 16px; 
                              text-decoration: none; border-radius: 4px; display: inline-block;">
                        View Job
                    </a>
                </p>
            </div>
            """
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <h1>Your {period.capitalize()} Job Digest</h1>
            <p>Hi {user_name},</p>
            <p>Here are {len(jobs)} new job opportunities matching your preferences:</p>
            {job_items}
            <p style="margin-top: 24px;">
                <a href="https://jobsleuth.ai/jobs" 
                   style="color: #4F46E5; text-decoration: none;">
                    View all jobs on JobSleuth →
                </a>
            </p>
            <p style="color: #6b7280; font-size: 14px; margin-top: 32px;">
                You're receiving this email because you signed up for job alerts on JobSleuth.
            </p>
        </body>
        </html>
        """
        
        return html
    
    def _build_digest_text(
        self,
        user_name: str,
        jobs: list[dict[str, Any]],
        period: str
    ) -> str:
        """Build plain text content for job digest.
        
        Args:
            user_name: User's name
            jobs: List of jobs
            period: Digest period
            
        Returns:
            Plain text content
        """
        job_items = ""
        for job in jobs[:10]:
            job_items += f"""
{job.get('title', 'N/A')}
{job.get('company', 'N/A')} - {job.get('location', 'N/A')}
{job.get('url', '')}

"""
        
        text = f"""
Your {period.capitalize()} Job Digest

Hi {user_name},

Here are {len(jobs)} new job opportunities matching your preferences:

{job_items}

View all jobs: https://jobsleuth.ai/jobs

---
You're receiving this email because you signed up for job alerts on JobSleuth.
"""
        
        return text


# Singleton instance
_emailer = None


def get_emailer() -> Emailer:
    """Get or create the emailer singleton.
    
    Returns:
        Emailer instance
    """
    global _emailer
    if _emailer is None:
        _emailer = Emailer()
    return _emailer
