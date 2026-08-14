"""Grounded vacancy text extraction with deterministic fallback heuristics."""

from __future__ import annotations

import re
from typing import Any, Literal

Category = Literal["eligibility", "essential", "desirable", "trainable", "practical"]


def _clean_line(value: str) -> str:
    return re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", value).strip()


def _confidence(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)


def _item(text: str, category: Category, confidence: float, *, explicit_blocker: bool = False) -> dict[str, Any]:
    return {
        "text": text,
        "category": category,
        "source_text": text,
        "confidence": _confidence(confidence),
        "explicit_blocker": explicit_blocker,
    }


def deterministic_extract(vacancy_text: str) -> list[dict[str, Any]]:
    """Extract grounded criteria from vacancy text without external services.

    The fallback deliberately prefers omission over invention. Every returned item
    is tied to a source line from the supplied advert.
    """

    items: list[dict[str, Any]] = []
    section: Category = "essential"

    headings: list[tuple[Category, tuple[str, ...]]] = [
        ("eligibility", ("eligibility", "who can apply", "nationality requirements", "security clearance")),
        ("desirable", ("desirable", "nice to have", "preferred", "it would be great")),
        ("trainable", ("training", "learning and development")),
        ("practical", ("working pattern", "working arrangements", "hours", "location", "travel requirements", "hybrid working")),
        ("essential", ("essential criteria", "essential requirements", "person specification", "what you will need", "skills and experience")),
    ]

    eligibility_cues = (
        "right to work",
        "eligible to",
        "eligibility",
        "nationality",
        "security clearance",
        "security check",
        "vetting",
        "must hold",
        "must have",
        "required qualification",
        "driving licence",
        "driving license",
    )
    practical_cues = (
        "hours per week",
        "days per week",
        "working pattern",
        "working arrangements",
        "office attendance",
        "hybrid",
        "travel",
        "location",
        "shift",
        "weekend",
        "full-time training",
        "full time training",
        "minimum hours",
    )
    trainable_cues = (
        "training will be provided",
        "training is provided",
        "full training provided",
        "training provided",
        "will receive training",
        "will be trained",
        "will be taught",
        "taught during training",
        "taught as part of training",
    )
    criterion_cues = (
        "experience",
        "knowledge",
        "ability to",
        "able to",
        "skill",
        "competence",
        "qualification",
        "required",
        "essential",
        "desirable",
        "demonstrate",
    )
    hard_blocker_cues = (
        "cannot apply",
        "only open to",
        "must hold",
        "must have the right to work",
        "required qualification",
        "mandatory qualification",
        "security clearance",
        "security check",
        "vetting",
    )

    for raw in vacancy_text.splitlines():
        line = _clean_line(raw)
        if not line:
            continue
        lowered = line.lower().rstrip(":")
        is_bullet = bool(re.match(r"^\s*(?:[-*•]|\d+[.)])", raw))

        if not is_bullet and len(line) <= 100:
            heading_match = next((category for category, cues in headings if any(cue in lowered for cue in cues)), None)
            if heading_match and (raw.strip().endswith(":") or len(line.split()) <= 8):
                section = heading_match
                continue

        explicit_blocker = any(token in lowered for token in hard_blocker_cues)

        if any(cue in lowered for cue in trainable_cues):
            items.append(_item(line, "trainable", 0.96))
            continue
        if any(cue in lowered for cue in eligibility_cues):
            items.append(_item(line, "eligibility", 0.9, explicit_blocker=explicit_blocker))
            continue
        if any(cue in lowered for cue in practical_cues):
            items.append(_item(line, "practical", 0.86, explicit_blocker=explicit_blocker))
            continue

        looks_like_criterion = any(cue in lowered for cue in criterion_cues)
        if not is_bullet and not looks_like_criterion:
            continue
        if len(line) > 420:
            continue

        category: Category = section
        if category not in {"essential", "desirable", "trainable"}:
            category = "essential"
        if "desirable" in lowered or "ideally" in lowered or "preferred" in lowered:
            category = "desirable"

        # Experience/competency criteria are evidence gaps, not eligibility blockers.
        # Reserve hard blockers for eligibility/practical constraints that make the
        # candidate unable to take or be considered for the role.
        items.append(_item(line, category, 0.82 if is_bullet else 0.72, explicit_blocker=False))

    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item["category"], item["text"].lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    return unique[:40]
