"""AI job scoring routes with deterministic fallback."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from lib.settings import settings

router = APIRouter(tags=["ai_scoring"])


class AIScoreRequest(BaseModel):
    resume_text: str | None = None
    candidate_profile: dict[str, Any] | None = None
    job: dict[str, Any]


def fallback_score(request: AIScoreRequest) -> dict[str, Any]:
    text = " ".join(
        [
            request.resume_text or "",
            " ".join(str(value) for value in (request.candidate_profile or {}).values()),
        ]
    ).lower()
    job_text = " ".join(str(value) for value in request.job.values()).lower()
    keywords = {word.strip(".,:;()[]") for word in job_text.split() if len(word) > 4}
    matches = sorted({word for word in keywords if word in text})[:8]
    skills_score = min(100, 45 + len(matches) * 7)
    salary_score = 72 if any(token in job_text for token in ["salary", "$", "£", "remote"]) else 58
    role_score = min(95, skills_score + 8)
    overall = round((skills_score * 0.5) + (salary_score * 0.2) + (role_score * 0.3))
    return {
        "ok": True,
        "provider": "fallback",
        "score": overall,
        "breakdown": {
            "skills_fit": skills_score,
            "salary_fit": salary_score,
            "role_fit": role_score,
        },
        "matched_keywords": matches,
        "summary": "Deterministic match score generated without OpenAI configured.",
    }


@router.post("/ai-score")
async def ai_score(request: AIScoreRequest) -> dict[str, Any]:
    if not settings.OPENAI_API_KEY:
        return fallback_score(request)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Score this candidate/job fit as concise JSON."},
                {"role": "user", "content": f"Candidate: {request.resume_text or request.candidate_profile}\nJob: {request.job}"},
            ],
            temperature=0.2,
            max_tokens=300,
        )
        return {"ok": True, "provider": "openai", "result": response.choices[0].message.content}
    except Exception:
        return fallback_score(request)