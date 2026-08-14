"""Optional OpenAI-backed vacancy extraction with source grounding."""

from __future__ import annotations

import json
from typing import Any

from lib.settings import settings

_ALLOWED_CATEGORIES = {"eligibility", "essential", "desirable", "trainable", "practical"}
_BLOCKER_CUES = ("must ", "required", "only open to", "cannot apply", "need to hold", "need to have")


def _source_is_grounded(source: str, vacancy_text: str) -> bool:
    source_norm = " ".join(source.lower().split())
    vacancy_norm = " ".join(vacancy_text.lower().split())
    return bool(source_norm) and source_norm in vacancy_norm


def _validate_item(raw: Any, vacancy_text: str) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    category = str(raw.get("category", "")).strip().lower()
    text = str(raw.get("text", "")).strip()
    source = str(raw.get("source_text", "")).strip()
    if category not in _ALLOWED_CATEGORIES or not text or not _source_is_grounded(source, vacancy_text):
        return None
    try:
        confidence = round(max(0.0, min(1.0, float(raw.get("confidence", 0.7)))), 2)
    except (TypeError, ValueError):
        confidence = 0.7
    source_lower = source.lower()
    explicit_blocker = bool(raw.get("explicit_blocker")) and any(cue in source_lower for cue in _BLOCKER_CUES)
    return {
        "text": text[:500],
        "category": category,
        "source_text": source[:700],
        "confidence": confidence,
        "explicit_blocker": explicit_blocker,
    }


def semantic_extract(vacancy_text: str) -> list[dict[str, Any]] | None:
    """Return grounded semantic extraction, or None when AI is unavailable."""

    if not settings.OPENAI_API_KEY:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract requirements from a job vacancy. Return JSON with an items array. "
                        "Each item must contain text, category, source_text, confidence, explicit_blocker. "
                        "category must be one of eligibility, essential, desirable, trainable, practical. "
                        "source_text must be copied from the supplied vacancy and must directly support the item. "
                        "Do not infer candidate facts, do not invent requirements, and prefer omission when uncertain. "
                        "Set explicit_blocker true only where the advert explicitly makes the requirement mandatory."
                    ),
                },
                {"role": "user", "content": vacancy_text[:24000]},
            ],
            temperature=0,
            max_tokens=2200,
        )
        content = response.choices[0].message.content or "{}"
        payload = json.loads(content)
        raw_items = payload.get("items", []) if isinstance(payload, dict) else []
        validated = [item for raw in raw_items if (item := _validate_item(raw, vacancy_text)) is not None]
        return validated[:40] or None
    except Exception:
        return None
