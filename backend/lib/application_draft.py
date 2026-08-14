"""Deterministic evidence-backed application draft helpers."""

from __future__ import annotations

from typing import Any

from lib.application_grounding import field_values


def supported_requirement(requirement: Any) -> bool:
    return (
        str(getattr(requirement, "match_strength", "")).lower() in {"strong", "partial"}
        and bool(getattr(requirement, "evidence_ids", []) or [])
    )


def _supporting_facts(card: Any, evidence_id: str) -> list[dict[str, str]]:
    facts: list[dict[str, str]] = []
    for field in ("task", "actions", "authority_context", "outcome", "reflection"):
        for value in field_values(card, field):
            facts.append({"evidence_id": evidence_id, "field": field, "text": value})
            if len(facts) >= 6:
                return facts
    return facts


def deterministic_paragraph(requirement: Any, requirement_index: int, card: Any, evidence_id: str) -> dict[str, Any] | None:
    facts = _supporting_facts(card, evidence_id)
    action_facts = [fact for fact in facts if fact["field"] in {"task", "actions", "authority_context"}]
    if not action_facts:
        return None

    sentences: list[str] = []
    title = str(getattr(card, "title", "") or "").strip()
    if title:
        sentences.append(f"A relevant example for this requirement is {title}.")

    task = field_values(card, "task")
    if task:
        sentences.append(task[0])
    actions = field_values(card, "actions")
    sentences.extend(actions[:2])
    authority = field_values(card, "authority_context")
    if authority:
        sentences.append(authority[0])
    outcome = field_values(card, "outcome")
    if outcome:
        sentences.append(outcome[0])

    text = " ".join(sentence.strip() for sentence in sentences if sentence.strip())
    if not text:
        return None
    return {
        "text": text,
        "requirement_indices": [requirement_index],
        "evidence_ids": [evidence_id],
        "supporting_facts": facts,
        "grounding_status": "grounded",
    }


def deterministic_draft(requirements: list[Any], cards_by_id: dict[str, Any], role_title: str) -> list[dict[str, Any]]:
    paragraphs: list[dict[str, Any]] = []
    for index, requirement in enumerate(requirements):
        if not supported_requirement(requirement):
            continue
        for evidence_id in getattr(requirement, "evidence_ids", []) or []:
            card = cards_by_id.get(str(evidence_id))
            if card is None:
                continue
            paragraph = deterministic_paragraph(requirement, index, card, str(evidence_id))
            if paragraph:
                paragraphs.append(paragraph)
                break
    return paragraphs


def coverage(requirements: list[Any], paragraphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    covered_indices = {
        index
        for paragraph in paragraphs
        for index in paragraph.get("requirement_indices", [])
    }
    result: list[dict[str, Any]] = []
    for index, requirement in enumerate(requirements):
        strength = str(getattr(requirement, "match_strength", "missing") or "missing").lower()
        if index in covered_indices:
            status = "covered" if strength == "strong" else "partially-covered"
        elif strength in {"weak", "missing"}:
            status = "evidence-gap"
        else:
            status = "not-used"
        result.append(
            {
                "requirement": str(getattr(requirement, "text", "")),
                "category": str(getattr(requirement, "category", "essential")),
                "match_strength": strength,
                "status": status,
                "evidence_ids": [str(value) for value in (getattr(requirement, "evidence_ids", []) or [])],
            }
        )
    return result


def word_count(paragraphs: list[dict[str, Any]]) -> int:
    return sum(len(str(paragraph.get("text", "")).split()) for paragraph in paragraphs)
