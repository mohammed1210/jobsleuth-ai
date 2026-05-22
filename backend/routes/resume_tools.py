"""Resume improvement and cover-letter routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from lib.settings import settings

router = APIRouter(tags=["resume_tools"])


def _resume_fallback() -> dict[str, Any]:
    return {
        "ok": True,
        "provider": "fallback",
        "suggestions": [
            "Lead with role-relevant achievements and measurable outcomes.",
            "Mirror the strongest job keywords where they match real experience.",
            "Move recent technical skills and tools into the first third of the resume.",
        ],
    }


def _cover_letter_fallback(request: "CoverLetterRequest") -> dict[str, Any]:
    job_title = request.job.get("title", "the role")
    company = request.job.get("company", "your team")
    return {
        "ok": True,
        "provider": "fallback",
        "letter": (
            f"Dear Hiring Manager,\n\nI am excited to apply for {job_title} at {company}. "
            f"My background aligns with the role through {request.resume_summary}.\n\n"
            "I would welcome the chance to discuss how I can contribute to your team.\n\nSincerely,"
        ),
    }


class ResumeImproveRequest(BaseModel):
    resume_text: str
    job: dict[str, Any] | None = None


class CoverLetterRequest(BaseModel):
    resume_summary: str
    job: dict[str, Any]


@router.post("/resume/improve")
async def improve_resume(request: ResumeImproveRequest) -> dict[str, Any]:
    if not settings.OPENAI_API_KEY:
        return _resume_fallback()
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Improve this resume for the job. Resume: {request.resume_text}\nJob: {request.job}"}],
            max_tokens=400,
            temperature=0.4,
        )
        return {"ok": True, "provider": "openai", "suggestions": response.choices[0].message.content}
    except Exception:
        return _resume_fallback()


@router.post("/cover-letter")
async def cover_letter(request: CoverLetterRequest) -> dict[str, Any]:
    if not settings.OPENAI_API_KEY:
        return _cover_letter_fallback(request)
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Write a concise cover letter. Candidate: {request.resume_summary}\nJob: {request.job}"}],
            max_tokens=450,
            temperature=0.5,
        )
        return {"ok": True, "provider": "openai", "letter": response.choices[0].message.content}
    except Exception:
        return _cover_letter_fallback(request)