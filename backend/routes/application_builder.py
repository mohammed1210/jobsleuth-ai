"""Evidence-backed application drafting API."""

from __future__ import annotations

import re
from typing import Any, Literal

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from lib.application_ai import semantic_application_draft
from lib.application_draft import coverage, deterministic_draft
from routes.saved_jobs import verify_supabase_user

router = APIRouter(prefix="/application-builder", tags=["application_builder"])

_META_VERBS = r"demonstrates|shows|illustrates|supports|underpins|evidences|addresses|highlights"
_META_COMMENTARY_RE = re.compile(
    rf"(?i)\(?\s*(?:this paragraph|this evidence|this example|the above)\s+(?:{_META_VERBS})\b[^.!?)]*(?:[.!?]\s*\)?|\))?"
)


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


def _clean_meta_commentary(text: str) -> str:
    """Remove assessor-facing narration while preserving the candidate's evidence prose."""
    cleaned = _META_COMMENTARY_RE.sub("", text)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip(" \t\n;,-")


def _normalise_paragraphs(paragraphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalised: list[dict[str, Any]] = []
    for paragraph in paragraphs:
        item = dict(paragraph)
        text = _clean_meta_commentary(str(item.get("text", "")))
        if not text:
            continue
        item["text"] = text
        normalised.append(item)
    return normalised


def _compose_draft(paragraphs: list[dict[str, Any]]) -> str:
    """Compose only evidence-bearing prose; avoid generic opening/closing filler."""
    return "\n\n".join(paragraph["text"].strip() for paragraph in paragraphs if paragraph.get("text", "").strip())


@router.post("")
async def build_application(
    request: ApplicationBuilderRequest,
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    await verify_supabase_user(authorization)

    role_title = str(request.job.get("title", "the role") or "the role").strip()[:300]
    organisation = str(request.job.get("organisation", request.job.get("company", "")) or "").strip()[:300]
    cards_by_id = {card.id: card for card in request.evidence_cards if card.id}

    paragraphs, semantic_status = semantic_application_draft(
        request.requirements,
        cards_by_id,
        role_title,
        organisation,
        request.application_type,
        request.word_limit,
    )
    if paragraphs:
        paragraphs = _normalise_paragraphs(paragraphs)
    provider = "openai-grounded-v1" if paragraphs else "deterministic-grounded-v2"
    fallback_reason: str | None = None if paragraphs else semantic_status

    semantic_draft = _compose_draft(paragraphs or [])
    if paragraphs and len(semantic_draft.split()) > request.word_limit:
        fallback_reason = "semantic_over_word_limit"
        paragraphs = None

    if not paragraphs:
        paragraphs = deterministic_draft(
            request.requirements,
            cards_by_id,
            role_title,
            word_limit=request.word_limit,
        )
        paragraphs = _normalise_paragraphs(paragraphs)
        provider = "deterministic-grounded-v2"

    requirement_coverage = coverage(request.requirements, paragraphs)
    draft = _compose_draft(paragraphs)
    total_words = len(draft.split()) if draft else 0

    warnings: list[str] = []
    for item in requirement_coverage:
        if item["category"] == "essential" and item["status"] == "evidence-gap":
            warnings.append(f"Essential requirement not drafted because supporting evidence is insufficient: {item['requirement']}")
        elif item["category"] == "essential" and item["status"] == "partially-covered":
            warnings.append(f"Partial evidence is being used for this essential requirement and should be reviewed carefully: {item['requirement']}")
    if total_words > request.word_limit:
        warnings.append(f"Draft is {total_words} words, above the requested {request.word_limit}-word limit. Edit before submitting.")
    elif paragraphs and request.word_limit >= 300 and total_words < int(request.word_limit * 0.65):
        warnings.append(
            f"Draft uses only {total_words} of {request.word_limit} available words. "
            "If more verified evidence is available, strengthen the Evidence Bank rather than padding the statement with unsupported detail."
        )
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
