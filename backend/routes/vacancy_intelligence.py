"""Structured, source-grounded vacancy intelligence API."""

from __future__ import annotations

import re
from typing import Any, Literal

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from lib.vacancy_ai import semantic_extract
from lib.vacancy_extraction import deterministic_extract
from routes.saved_jobs import verify_supabase_user

router = APIRouter(prefix="/vacancy-intelligence", tags=["vacancy_intelligence"])


class VacancyIntelligenceRequest(BaseModel):
    vacancy_text: str = Field(min_length=40, max_length=30000)


class ExtractedItem(BaseModel):
    text: str
    category: Literal["eligibility", "essential", "desirable", "trainable", "practical"]
    source_text: str
    confidence: float = Field(ge=0, le=1)
    explicit_blocker: bool = False


def _group(items: list[dict[str, Any]], category: str) -> list[dict[str, Any]]:
    return [item for item in items if item.get("category") == category]


def _normalise(value: str) -> str:
    return re.sub(r"\W+", " ", value.lower()).strip()


def _same_requirement(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left.get("category") != right.get("category"):
        return False
    left_text = _normalise(str(left.get("text", "")))
    right_text = _normalise(str(right.get("text", "")))
    if not left_text or not right_text:
        return False
    return left_text == right_text or left_text in right_text or right_text in left_text


def _dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    for candidate in items:
        if any(_same_requirement(candidate, existing) for existing in deduped):
            continue
        deduped.append(candidate)
    return deduped


def _reconcile_items(
    semantic_items: list[dict[str, Any]] | None,
    deterministic_items: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    """Prefer semantic extraction, then supplement clearly grounded omissions.

    Semantic extraction is useful for interpreting prose-heavy adverts, while the
    deterministic extractor is intentionally conservative and strong at explicit
    sectioned criteria. Using both prevents a model from silently dropping most of
    an Essential/Desirable/Training section while retaining source grounding.
    """

    deterministic_items = _dedupe_items(deterministic_items)
    if not semantic_items:
        return deterministic_items, "deterministic-v2"

    merged = _dedupe_items(semantic_items)
    supplemented = False
    for candidate in deterministic_items:
        if any(_same_requirement(candidate, existing) for existing in merged):
            continue
        merged.append(candidate)
        supplemented = True

    return _dedupe_items(merged)[:40], "hybrid-grounded-v3" if supplemented else "openai-grounded-v3"


@router.post("")
async def vacancy_intelligence(
    request: VacancyIntelligenceRequest,
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    await verify_supabase_user(authorization)

    semantic_items = semantic_extract(request.vacancy_text)
    deterministic_items = deterministic_extract(request.vacancy_text)
    items, provider = _reconcile_items(semantic_items, deterministic_items)

    typed_items = [ExtractedItem(**item).model_dump() for item in items]
    requirements = [item for item in typed_items if item["category"] in {"essential", "desirable", "trainable"}]
    low_confidence = sum(1 for item in typed_items if item["confidence"] < 0.65)

    return {
        "ok": True,
        "provider": provider,
        "eligibility": _group(typed_items, "eligibility"),
        "requirements": requirements,
        "practical": _group(typed_items, "practical"),
        "summary": {
            "items": len(typed_items),
            "eligibility": len(_group(typed_items, "eligibility")),
            "requirements": len(requirements),
            "practical": len(_group(typed_items, "practical")),
            "low_confidence": low_confidence,
        },
    }
