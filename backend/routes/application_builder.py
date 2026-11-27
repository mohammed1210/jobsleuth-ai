"""Evidence-backed application drafting API."""

from __future__ import annotations

import logging
import re
from typing import Any, Literal

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from lib.application_ai import semantic_application_draft
from lib.application_draft import coverage, deterministic_draft
from lib.application_readiness import missing_direct_school_experience
from lib.vacancy_extraction import is_non_requirement_text
from routes.saved_jobs import verify_supabase_user

router = APIRouter(prefix="/application-builder", tags=["application_builder"])
logger = logging.getLogger(__name__)

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
    application_type: Literal["statement_of_suitability", "criteria_response", "cover_letter"] = "statement_of_suitability"
    word_limit: int = Field(default=500, ge=100, le=5000)
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
    # Defence in depth: saved assessments or older clients may still send
    # employer perks, deadlines and contact information as fake essentials.
    requirements = [item for item in request.requirements if not is_non_requirement_text(item.text)]

    # A school-workplace experience requirement is not met by generic
    # transferable operations skills. Return useful gaps rather than an
    # unrelated submission-style narrative, even if a client supplies an
    # optimistic match_strength. Other role types remain unaffected.
    role_experience_gaps = missing_direct_school_experience(requirements, cards_by_id)
    if role_experience_gaps:
        return {
            "ok": True,
            "can_generate": False,
            "provider": "role-readiness-guard-v1",
            "fallback_reason": "missing_direct_school_experience",
            "application_type": request.application_type,
            "word_limit": request.word_limit,
            "word_count": 0,
            "draft": "",
            "paragraphs": [],
            "coverage": coverage(requirements, []),
            "warnings": [
                "A full role-specific application draft is paused because direct school-setting experience "
                "required by the vacancy is not verified in the linked Evidence Bank examples. "
                "Transferable experience may still be useful, but it does not establish this requirement.",
                *[f"Add a genuine, verifiable example for: {item}" for item in role_experience_gaps[:5]],
                "You can still review the employer's instructions and strengthen your evidence; this is not "
                "a determination of whether the employer will consider your application.",
            ],
        }

    paragraphs, semantic_status = semantic_application_draft(
        requirements,
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

    fallback_used = not paragraphs
    # Deterministic fallback is a collection of copied evidence, not a
    # role-tailored letter. With only Partial/Weak/Missing matches, publishing
    # a full-length freight narrative for an unrelated receptionist vacancy
    # is misleading even when the applicant clicked "use current evidence".
    # A grounded semantic draft can still proceed when it passes validation.
    has_essential_requirements = any(item.category == "essential" for item in requirements)
    strong_role_evidence = any(
        item.match_strength == "strong"
        and (item.category == "essential" or not has_essential_requirements)
        and any(evidence_id in cards_by_id for evidence_id in item.evidence_ids)
        for item in requirements
    )
    if fallback_used and not strong_role_evidence:
        return {
            "ok": True,
            "can_generate": False,
            "provider": "evidence-readiness-guard-v2",
            "fallback_reason": "no_strong_essential_evidence",
            "application_type": request.application_type,
            "word_limit": request.word_limit,
            "word_count": 0,
            "draft": "",
            "paragraphs": [],
            "coverage": coverage(requirements, []),
            "warnings": [
                "A relevant application draft could not be prepared from the current evidence. "
                "The recorded examples do not strongly demonstrate an essential requirement, "
                "and the assisted drafting service did not return a verified role-specific draft.",
                "Add or strengthen a genuine example that demonstrates the advertised role's "
                "essential skills, then try again. You can still review the employer's advert.",
            ],
        }
    cover_letter_intro = ""
    cover_letter_closing = ""
    if request.application_type == "cover_letter":
        organisation_phrase = f" at {organisation}" if organisation else ""
        cover_letter_intro = f"I am applying for the {role_title} role{organisation_phrase}."
        cover_letter_closing = "Thank you for considering my application."

    if not paragraphs:
        fallback_budget = request.word_limit
        if request.application_type == "cover_letter":
            framing_words = len(cover_letter_intro.split()) + len(cover_letter_closing.split())
            fallback_budget = max(1, request.word_limit - framing_words)
        paragraphs = deterministic_draft(
            requirements,
            cards_by_id,
            role_title,
            word_limit=fallback_budget,
        )
        paragraphs = _normalise_paragraphs(paragraphs)
        provider = "deterministic-grounded-v2"

    requirement_coverage = coverage(requirements, paragraphs)
    draft = _compose_draft(paragraphs)
    if draft and fallback_used and request.application_type == "cover_letter":
        draft = f"{cover_letter_intro}\n\n{draft}\n\n{cover_letter_closing}"
        provider = "deterministic-grounded-cover-letter-v1"
    total_words = len(draft.split()) if draft else 0

    warnings: list[str] = []
    if fallback_used and paragraphs:
        warnings.append(
            "This fallback assembles recorded Evidence Bank facts rather than writing a role-tailored statement. "
            "It is a working excerpt, not a submission-ready application: review relevance to the advertised role, "
            "mandatory qualifications and employer instructions before using it."
        )
    evidence_gaps = [
        item for item in requirement_coverage
        if item["category"] == "essential" and item["status"] in {"evidence-gap", "partially-covered"}
    ]
    for item in evidence_gaps[:4]:
        if item["status"] == "evidence-gap":
            warnings.append(f"Essential requirement not drafted because supporting evidence is insufficient: {item['requirement']}")
        else:
            warnings.append(f"Partial evidence is being used for this essential requirement and should be reviewed carefully: {item['requirement']}")
    if len(evidence_gaps) > 4:
        warnings.append(f"{len(evidence_gaps) - 4} additional essential requirements need review; see the full criteria coverage for details.")
    if total_words > request.word_limit:
        warnings.append(f"Draft is {total_words} words, above the requested {request.word_limit}-word limit. Edit before submitting.")
    elif paragraphs and request.word_limit >= 300 and total_words < int(request.word_limit * 0.65):
        warnings.append(
            f"Draft uses only {total_words} of {request.word_limit} available words. "
            "If more verified evidence is available, strengthen the Evidence Bank rather than padding the statement with unsupported detail."
        )
    if not paragraphs:
        warnings.append("No Strong or Partial matched evidence is available to build a supported draft.")

    # Operational metadata only; never log draft text or applicant evidence.
    logger.warning("application_builder completed generated=%s provider=%s words=%d paragraphs=%d",
                   bool(paragraphs), provider, total_words, len(paragraphs))

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
