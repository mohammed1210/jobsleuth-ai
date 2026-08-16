"""Grounding helpers for evidence-backed application drafting."""

from __future__ import annotations

import re
from typing import Any

_ALLOWED_FIELDS = {
    "title",
    "situation",
    "task",
    "actions",
    "outcome",
    "reflection",
    "authority_context",
    "skills",
    "behaviours",
    "tags",
}
_ACTION_FIELDS = {"actions", "task", "authority_context"}
_AUTHORITY_PHRASES = {
    "i led": ("lead", "led"),
    "i managed": ("manage", "managed"),
    "i approved": ("approve", "approved"),
    "i authorised": ("authorise", "authorised", "authorize", "authorized"),
    "i authorized": ("authorise", "authorised", "authorize", "authorized"),
    "i decided": ("decide", "decided"),
    "i supervised": ("supervise", "supervised"),
    "i directed": ("direct", "directed"),
    "i owned": ("own", "owned", "ownership"),
}


def field_values(card: Any, field: str) -> list[str]:
    value = getattr(card, field, None)
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def card_facts(card: Any) -> dict[str, list[str]]:
    return {field: field_values(card, field) for field in _ALLOWED_FIELDS if field_values(card, field)}


def grounded_fact(card: Any, raw: Any) -> dict[str, str] | None:
    if not isinstance(raw, dict):
        return None
    field = str(raw.get("field", "")).strip()
    text = str(raw.get("text", "")).strip()
    if field not in _ALLOWED_FIELDS or not text:
        return None

    wanted = " ".join(text.lower().split())
    for source in field_values(card, field):
        source_normalised = " ".join(source.lower().split())
        if wanted and wanted in source_normalised:
            return {"field": field, "text": text[:700]}
    return None


def _numbers(value: str) -> set[str]:
    return set(re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?", value))


def _authority_claims_supported(paragraph: str, facts: list[dict[str, str]]) -> bool:
    lowered = paragraph.lower()
    source = " ".join(fact["text"].lower() for fact in facts)
    for phrase, support_terms in _AUTHORITY_PHRASES.items():
        if phrase in lowered and not any(term in source for term in support_terms):
            return False
    return True


def validate_ai_paragraph_detailed(
    raw: Any,
    cards_by_id: dict[str, Any],
    requirement_count: int,
) -> tuple[dict[str, Any] | None, str]:
    """Validate one generated paragraph and return a non-sensitive rejection reason."""

    if not isinstance(raw, dict):
        return None, "invalid_shape"
    text = str(raw.get("text", "")).strip()
    if not text:
        return None, "empty_text"

    requirement_indices: list[int] = []
    for value in raw.get("requirement_indices", []):
        try:
            index = int(value)
        except (TypeError, ValueError):
            continue
        if 0 <= index < requirement_count and index not in requirement_indices:
            requirement_indices.append(index)
    if not requirement_indices:
        return None, "invalid_requirement_indices"

    evidence_ids = [str(value).strip() for value in raw.get("evidence_ids", []) if str(value).strip()]
    evidence_ids = list(dict.fromkeys(evidence_ids))
    if not evidence_ids or any(evidence_id not in cards_by_id for evidence_id in evidence_ids):
        return None, "invalid_evidence_ids"

    facts: list[dict[str, str]] = []
    action_fact_found = False
    for raw_fact in raw.get("supporting_facts", []):
        if not isinstance(raw_fact, dict):
            continue
        evidence_id = str(raw_fact.get("evidence_id", "")).strip()
        card = cards_by_id.get(evidence_id)
        if card is None or evidence_id not in evidence_ids:
            continue
        fact = grounded_fact(card, raw_fact)
        if fact is None:
            continue
        fact["evidence_id"] = evidence_id
        facts.append(fact)
        if fact["field"] in _ACTION_FIELDS:
            action_fact_found = True

    if not facts:
        return None, "no_grounded_facts"
    if not action_fact_found:
        return None, "missing_action_fact"

    source_text = " ".join(fact["text"] for fact in facts)
    if _numbers(text) - _numbers(source_text):
        return None, "unsupported_number"
    if not _authority_claims_supported(text, facts):
        return None, "authority_upgrade"

    return {
        "text": text[:5000],
        "requirement_indices": requirement_indices,
        "evidence_ids": evidence_ids[:5],
        "supporting_facts": facts[:8],
        "grounding_status": "grounded",
    }, "ok"


def validate_ai_paragraph(raw: Any, cards_by_id: dict[str, Any], requirement_count: int) -> dict[str, Any] | None:
    """Validate one generated paragraph against exact Evidence Card facts."""
    paragraph, _ = validate_ai_paragraph_detailed(raw, cards_by_id, requirement_count)
    return paragraph
