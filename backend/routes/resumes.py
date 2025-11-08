"""
Resume tools API routes.

Endpoints for resume enhancement and cover letter generation.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.lib.settings import settings

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


router = APIRouter(tags=["resumes"])


class ResumeSuggestRequest(BaseModel):
    """Request body for resume suggestions."""
    resumeText: str
    job: Dict[str, Any]


class CoverLetterRequest(BaseModel):
    """Request body for cover letter generation."""
    resumeSummary: str
    job: Dict[str, Any]


@router.post("/resume/suggest")
async def suggest_resume_improvements(request: ResumeSuggestRequest) -> Dict[str, Any]:
    """
    Get AI-powered suggestions for resume bullet points.
    
    Args:
        request: Resume text and job details
        
    Returns:
        Dictionary with suggested bullet points
    """
    if not OPENAI_AVAILABLE or not settings.OPENAI_API_KEY:
        # Fallback: return basic suggestions
        return {
            "suggestions": [
                "Quantify your achievements with specific metrics and numbers",
                "Use strong action verbs to start each bullet point",
                "Highlight relevant technical skills mentioned in the job description",
                "Emphasize results and impact rather than just responsibilities"
            ],
            "method": "fallback"
        }
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        job_title = request.job.get('title', '')
        job_description = request.job.get('raw', {}).get('description', '') if request.job.get('raw') else ''
        
        prompt = f"""Given this resume and job posting, suggest 3-5 specific bullet points to add or improve.

Job Title: {job_title}
Job Description: {job_description[:500]}

Current Resume:
{request.resumeText[:1000]}

Provide actionable, specific suggestions for bullet points that would make this resume stronger for this job."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional resume writer and career coach."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        suggestions_text = response.choices[0].message.content
        
        # Parse suggestions (simple line-based parsing)
        suggestions = [
            line.strip().lstrip('•-*123456789. ')
            for line in suggestions_text.split('\n')
            if line.strip() and len(line.strip()) > 20
        ]
        
        return {
            "suggestions": suggestions[:5],
            "method": "ai"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")


@router.post("/cover-letter")
async def generate_cover_letter(request: CoverLetterRequest) -> Dict[str, str]:
    """
    Generate a tailored cover letter.
    
    Args:
        request: Resume summary and job details
        
    Returns:
        Dictionary with generated cover letter
    """
    if not OPENAI_AVAILABLE or not settings.OPENAI_API_KEY:
        # Fallback: return template
        company = request.job.get('company', 'the Company')
        title = request.job.get('title', 'this position')
        
        template = f"""Dear Hiring Manager,

I am writing to express my interest in the {title} position at {company}. With my background and skills, I believe I would be a strong fit for this role.

{request.resumeSummary}

I am excited about the opportunity to contribute to {company} and would welcome the chance to discuss how my experience aligns with your needs.

Thank you for your consideration.

Sincerely,
[Your Name]"""
        
        return {
            "cover_letter": template,
            "method": "template"
        }
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        job_title = request.job.get('title', '')
        company = request.job.get('company', '')
        job_description = request.job.get('raw', {}).get('description', '') if request.job.get('raw') else ''
        
        prompt = f"""Write a professional, concise cover letter (200-250 words) for this job application.

Job Title: {job_title}
Company: {company}
Job Description: {job_description[:500]}

Candidate Summary:
{request.resumeSummary}

The cover letter should be enthusiastic but professional, highlight relevant experience, and show genuine interest in the company."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        
        cover_letter = response.choices[0].message.content
        
        return {
            "cover_letter": cover_letter,
            "method": "ai"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate cover letter: {str(e)}")
