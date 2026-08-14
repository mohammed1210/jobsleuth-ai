"""Structured, source-grounded vacancy intelligence API."""

from __future__ import annotations

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


@router.post("")
async def vacancy_intelligence(
    request: VacancyIntelligenceRequest,
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    await verify_supabase_user(authorization)

    items = semantic_extract(request.vacancy_text)
    provider = "openai-grounded-v2"
    if not items:
        items = deterministic_extract(request.vacancy_text)
        provider = "deterministic-v2"

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
