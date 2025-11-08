"""Resume and cover letter generation routes."""

from typing import Any

from fastapi import APIRouter, HTTPException
from lib.settings import settings
from pydantic import BaseModel

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

router = APIRouter(prefix="/resume", tags=["resumes"])


class ResumeSuggestRequest(BaseModel):
    """Request for resume bullet suggestions."""

    resumeText: str  # noqa: N815
    job: dict[str, Any]


class CoverLetterRequest(BaseModel):
    """Request for cover letter generation."""

    resumeSummary: str  # noqa: N815
    job: dict[str, Any]


@router.post("/suggest")
async def suggest_resume_bullets(request: ResumeSuggestRequest):
    """Generate resume bullet point suggestions tailored to a job."""
    if not OPENAI_AVAILABLE or not settings.OPENAI_API_KEY:
        # Fallback response without AI
        return {
            "suggestions": [
                "Highlight relevant technical skills mentioned in the job description",
                "Quantify your achievements with specific metrics",
                "Emphasize experience with similar technologies or tools",
            ]
        }

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        job_title = request.job.get("title", "")
        job_desc = (
            request.job.get("raw", {}).get("description", "")
            if isinstance(request.job.get("raw"), dict)
            else ""
        )

        prompt = f"""Given this job posting:

Job Title: {job_title}
Description: {job_desc[:500]}

And this resume excerpt:
{request.resumeText[:1000]}

Suggest 3-5 bullet points to add or improve on the resume to better match this job. Be specific and actionable.
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )

        suggestions_text = response.choices[0].message.content or ""

        # Parse into list (split by newlines/bullets)
        suggestions = [
            line.strip().lstrip("-•*").strip()
            for line in suggestions_text.split("\n")
            if line.strip() and len(line.strip()) > 10
        ]

        return {"suggestions": suggestions[:5]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")


@router.post("/cover-letter")
async def generate_cover_letter(request: CoverLetterRequest):
    """Generate a tailored cover letter for a job."""
    if not OPENAI_AVAILABLE or not settings.OPENAI_API_KEY:
        # Fallback response
        job_title = request.job.get("title", "the position")
        company = request.job.get("company", "your company")

        return {
            "letter": f"""Dear Hiring Manager,

I am writing to express my interest in the {job_title} position at {company}.

{request.resumeSummary}

I am excited about the opportunity to contribute to your team and would welcome the chance to discuss how my skills and experience align with your needs.

Thank you for your consideration.

Sincerely,
[Your Name]"""
        }

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        job_title = request.job.get("title", "")
        company = request.job.get("company", "")
        job_desc = (
            request.job.get("raw", {}).get("description", "")
            if isinstance(request.job.get("raw"), dict)
            else ""
        )

        prompt = f"""Write a short, professional cover letter (3-4 paragraphs) for:

Job: {job_title} at {company}
Description: {job_desc[:500]}

Candidate summary:
{request.resumeSummary[:500]}

Keep it concise, professional, and enthusiastic. Focus on relevant skills and experience.
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )

        letter = response.choices[0].message.content or ""

        return {"letter": letter}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate cover letter: {str(e)}")
