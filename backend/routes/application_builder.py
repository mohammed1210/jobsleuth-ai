"""Evidence-backed application drafting API."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from lib.application_ai import semantic_application_draft
from lib.application_draft import coverage, deterministic_draft
from routes.saved_jobs import verify_supabase_user

router = APIRouter(prefix="/application-builder", tags=["application_builder"])


class ApplicationRequirement(BaseModel):
    text: str
    category: Literal["essential", "desirable", "trainable"] = "essential"
    match_strength: Literal["strong", "partial", "weak", "missing", "trainable"] = "missing"
    evidence_ids: list[str] = Field(default_factory=list)


class ApplicationEvidence(BaseModel):
    id: str
    title: str = ""
    situation: str = ""
    task: str = ""
    actions: list[str] = Field(default_factory=list)
    outcome: str = ""
    reflection: str = ""
    tags: list[str] = Field(default_factory=list)
    behaviours: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    authority_context: str | None = None
    confidence: int = Field(default=70, ge=0, le=100)


class ApplicationBuilderRequest(BaseModel):
    job: dict[str, Any] = Field(default_factory=dict)
    application_type: Literal["statement_of_suitability", "criteria_response"] = "statement_of_suitability"
    word_limit: int = Field(default=500, ge=150, le=1500)
    requirements: list[ApplicationRequirement] = Field(default_factory=list)
    evidence_cards: list[ApplicationEvidence] = Field(default_factory=list)


def _opening(role_title: str, organisation: str) -> str:
    destination = f" with {organisation}" if organisation else ""
    return f"I am applying for {role_title}{destination} and have focused this statement on the experience most relevant to the role."


def _closing() -> str:
    return "I would welcome the opportunity to discuss this evidence and its relevance to the role further."


def _compose_draft(paragraphs: list[dict[str, Any]], role_title: str, organisation: str) -> str:
    if not paragraphs:
        return ""
    body = "\n\n".join(paragraph["text"] for paragraph in paragraphs)
    return f"{_opening(role_title, organisation)}\n\n{body}\n\n{_closing()}"


def _body_budget(word_limit: int, role_title: str, organisation: str) -> int:
    framing_words = len((_opening(role_title, organisation) + " " + _closing()).split())
    return max(30, word_limit - framing_words)


@router.post("")
async def build_application(
    request: ApplicationBuilderRequest,
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    await verify_supabase_user(authorization)

    role_title = str(request.job.get("title", "the role") or "the role").strip()[:300]
    organisation = str(request.job.get("organisation", request.job.get("company", "")) or "").strip()[:300]
    cards_by_id = {card.id: card for card in request.evidence_cards if card.id}
    body_budget = _body_budget(request.word_limit, role_title, organisation)

    paragraphs, semantic_status = semantic_application_draft(
        request.requirements,
        cards_by_id,
        role_title,
        organisation,
        request.application_type,
        request.word_limit,
    )
    provider = "openai-grounded-v1" if paragraphs else "deterministic-grounded-v2"
    fallback_reason: str | None = None if paragraphs else semantic_status

    semantic_draft = _compose_draft(paragraphs or [], role_title, organisation)
    if paragraphs and len(semantic_draft.split()) > request.word_limit:
        fallback_reason = "semantic_over_word_limit"
        paragraphs = None

    if not paragraphs:
        paragraphs = deterministic_draft(
            request.requirements,
            cards_by_id,
            role_title,
            word_limit=body_budget,
        )
        provider = "deterministic-grounded-v2"

    requirement_coverage = coverage(request.requirements, paragraphs)
    draft = _compose_draft(paragraphs, role_title, organisation)
    total_words = len(draft.split()) if draft else 0

    warnings: list[str] = []
    for item in requirement_coverage:
        if item["category"] == "essential" and item["status"] == "evidence-gap":
            warnings.append(f"Essential requirement not drafted because supporting evidence is insufficient: {item['requirement']}")
        elif item["category"] == "essential" and item["status"] == "partially-covered":
            warnings.append(f"Partial evidence is being used for this essential requirement and should be reviewed carefully: {item['requirement']}")
    if total_words > request.word_limit:
        warnings.append(f"Draft is {total_words} words, above the requested {request.word_limit}-word limit. Edit before submitting.")
    if not paragraphs:
        warnings.append("No Strong or Partial matched evidence is available to build a supported draft.")

    return {
        "ok": True,
        "can_generate": bool(paragraphs),
        "provider": provider,
        "fallback_reason": fallback_reason,
        "application_type": request.application_type,
        "word_limit": request.word_limit,
        "word_count": total_words,
        "draft": draft,
        "paragraphs": paragraphs,
        "coverage": requirement_coverage,
        "warnings": warnings,
    }
