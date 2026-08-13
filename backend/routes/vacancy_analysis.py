"""Evidence-based vacancy analysis route."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from routes.saved_jobs import verify_supabase_user

router = APIRouter(prefix="/vacancy-analysis", tags=["vacancy_analysis"])


class Requirement(BaseModel):
    text: str
    category: Literal["essential", "desirable", "trainable"] = "essential"
    blocker: bool = False


class Evidence(BaseModel):
    id: str | None = None
    title: str = ""
    tags: list[str] = Field(default_factory=list)
    behaviours: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    outcome: str = ""


class AnalysisRequest(BaseModel):
    job: dict[str, Any]
    requirements: list[Requirement] = Field(default_factory=list)
    evidence_cards: list[Evidence] = Field(default_factory=list)
    practical_issues: list[str] = Field(default_factory=list)


def _words(value: str) -> set[str]:
    return {word.strip(".,:;()[]").lower() for word in value.split() if len(word) > 3}


def _evidence_words(card: Evidence) -> set[str]:
    return _words(" ".join([card.title, *card.tags, *card.behaviours, *card.skills, *card.actions, card.outcome]))


@router.post("")
async def vacancy_analysis(request: AnalysisRequest, authorization: str | None = Header(None)) -> dict[str, Any]:
    await verify_supabase_user(authorization)
    analysed = []
    for requirement in request.requirements:
        wanted = _words(requirement.text)
        matches = []
        for card in request.evidence_cards:
            overlap = sorted(wanted & _evidence_words(card))
            if overlap:
                matches.append({"id": card.id, "title": card.title, "matched_terms": overlap})
        status = "trainable" if requirement.category == "trainable" else ("met" if matches else "gap")
        analysed.append({
            "requirement": requirement.text,
            "category": requirement.category,
            "blocker": requirement.blocker,
            "status": status,
            "evidence": matches[:3],
        })

    hard_gap = any(item["status"] == "gap" and item["blocker"] for item in analysed)
    essential_gap = any(item["status"] == "gap" and item["category"] == "essential" for item in analysed)
    if hard_gap:
        decision = "SKIP"
    elif essential_gap or request.practical_issues:
        decision = "CONSIDER"
    else:
        decision = "APPLY"

    return {
        "ok": True,
        "analysis_provider": "evidence-v1",
        "decision": decision,
        "requirements": analysed,
        "practical_fit": {"status": "concern" if request.practical_issues else "fit", "issues": request.practical_issues},
    }
