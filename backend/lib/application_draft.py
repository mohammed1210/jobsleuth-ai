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
            if len(facts) >= 8:
                return facts
    return facts


def _sentence_candidates(card: Any) -> list[str]:
    candidates: list[str] = []
    task = field_values(card, "task")
    if task:
        candidates.append(task[0])
    candidates.extend(field_values(card, "actions")[:3])
    authority = field_values(card, "authority_context")
    if authority:
        candidates.append(authority[0])
    outcome = field_values(card, "outcome")
    if outcome:
        candidates.append(outcome[0])
    reflection = field_values(card, "reflection")
    if reflection:
        candidates.append(reflection[0])
    return [value.strip() for value in candidates if value.strip()]


def _fit_sentences(candidates: list[str], word_budget: int) -> str:
    selected: list[str] = []
    used = 0
    for sentence in candidates:
        words = len(sentence.split())
        if selected and used + words > word_budget:
            continue
        if not selected and words > word_budget:
            # A useful grounded sentence is better than returning no draft; keep the
            # first sentence only when the configured budget is exceptionally small.
            selected.append(" ".join(sentence.split()[:word_budget]))
            break
        selected.append(sentence)
        used += words
        if used >= word_budget:
            break
    return " ".join(selected).strip()


def deterministic_draft(
    requirements: list[Any],
    cards_by_id: dict[str, Any],
    role_title: str,
    word_limit: int = 500,
) -> list[dict[str, Any]]:
    """Compose one grounded paragraph per Evidence Card, not per criterion.

    A single real example often supports several vacancy requirements. Grouping by
    evidence source prevents repetitive STAR retelling and lets the coverage audit
    show every criterion supported by the same paragraph.
    """
    grouped: dict[str, list[int]] = {}
    for index, requirement in enumerate(requirements):
        if not supported_requirement(requirement):
            continue
        evidence_ids = [str(value) for value in (getattr(requirement, "evidence_ids", []) or [])]
        evidence_id = next((value for value in evidence_ids if value in cards_by_id), None)
        if evidence_id:
            grouped.setdefault(evidence_id, []).append(index)

    if not grouped:
        return []

    # Evidence supporting more essential criteria is drafted first. This matters
    # when multiple cards compete for a tight word budget.
    def priority(item: tuple[str, list[int]]) -> tuple[int, int]:
        _, indices = item
        essential = sum(
            1 for index in indices
            if str(getattr(requirements[index], "category", "essential")) == "essential"
        )
        return (essential, len(indices))

    ordered = sorted(grouped.items(), key=priority, reverse=True)
    paragraphs: list[dict[str, Any]] = []
    remaining = max(1, int(word_limit))

    for position, (evidence_id, indices) in enumerate(ordered):
        card = cards_by_id[evidence_id]
        groups_left = max(1, len(ordered) - position)
        paragraph_budget = max(35, remaining // groups_left)
        text = _fit_sentences(_sentence_candidates(card), paragraph_budget)
        if not text:
            continue
        text_words = len(text.split())
        if text_words > remaining and paragraphs:
            continue

        paragraphs.append(
            {
                "text": text,
                "requirement_indices": indices,
                "evidence_ids": [evidence_id],
                "supporting_facts": _supporting_facts(card, evidence_id),
                "grounding_status": "grounded",
            }
        )
        remaining -= min(remaining, text_words)
        if remaining <= 0:
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
