"""Structured evidence-to-requirement matching with explainable fallback scoring."""

from __future__ import annotations

import re
from typing import Any

_STOPWORDS = {
    "able", "about", "across", "also", "and", "are", "been", "being", "can", "demonstrate",
    "for", "from", "have", "into", "must", "our", "required", "role", "that", "the", "their",
    "this", "through", "using", "with", "within", "work", "working", "you", "your",
}

_CONCEPTS: dict[str, set[str]] = {
    "analysis": {"analyse", "analyze", "analysis", "assess", "evaluate", "evidence", "information", "data"},
    "decision": {"decision", "decide", "judgement", "judgment", "recommend", "option", "risk", "tradeoff"},
    "stakeholder": {"stakeholder", "partner", "liaise", "consult", "engage", "relationship", "collaborate"},
    "communication": {"communicate", "communication", "brief", "explain", "present", "written", "verbal"},
    "teamwork": {"team", "teamwork", "colleague", "collaborate", "cooperate", "support"},
    "leadership": {"lead", "leader", "leadership", "manage", "supervise", "coach", "delegate"},
    "improvement": {"improve", "improvement", "change", "streamline", "process", "efficiency", "innovation"},
    "delivery": {"deliver", "delivery", "deadline", "priority", "prioritise", "prioritize", "target", "outcome"},
    "investigation": {"investigate", "investigation", "fraud", "enquiry", "inquiry", "casework", "intelligence"},
    "customer": {"customer", "service", "user", "client", "quality", "complaint"},
    "planning": {"plan", "planning", "organise", "organize", "coordinate", "resource", "logistics"},
    "risk": {"risk", "safety", "security", "control", "mitigate", "contingency", "threat"},
    "authority": {"authority", "accountability", "accountable", "escalate", "escalation", "approval", "approve", "authorise", "authorize", "recommend"},
    "public_service": {"government", "regulatory", "regulator", "public", "operational", "enforcement", "border", "civil", "department"},
}


def _normalise_token(token: str) -> str:
    token = token.lower().strip(".,:;()[]{}!?\"'")
    for suffix in ("ing", "ed", "es", "s"):
        if len(token) > 6 and token.endswith(suffix):
            token = token[: -len(suffix)]
            break
    return token


def _tokens(value: str) -> set[str]:
    return {
        normalised
        for raw in re.findall(r"[A-Za-z0-9'-]+", value)
        if len((normalised := _normalise_token(raw))) > 2 and normalised not in _STOPWORDS
    }


def _concepts(value: str) -> set[str]:
    words = _tokens(value)
    found: set[str] = set()
    for concept, vocabulary in _CONCEPTS.items():
        vocab = {_normalise_token(item) for item in vocabulary}
        if words & vocab:
            found.add(concept)
    return found


def _card_text(card: Any) -> str:
    return " ".join(
        [
            str(getattr(card, "title", "") or ""),
            str(getattr(card, "situation", "") or ""),
            str(getattr(card, "task", "") or ""),
            *[str(value) for value in (getattr(card, "actions", []) or [])],
            str(getattr(card, "outcome", "") or ""),
            str(getattr(card, "reflection", "") or ""),
            str(getattr(card, "authority_context", "") or ""),
            *[str(value) for value in (getattr(card, "tags", []) or [])],
            *[str(value) for value in (getattr(card, "behaviours", []) or [])],
            *[str(value) for value in (getattr(card, "skills", []) or [])],
        ]
    ).strip()


def _quality(card: Any) -> float:
    checks = [
        bool(str(getattr(card, "situation", "") or "").strip()),
        bool(str(getattr(card, "task", "") or "").strip()),
        bool(getattr(card, "actions", []) or []),
        bool(str(getattr(card, "outcome", "") or "").strip()),
        bool(str(getattr(card, "authority_context", "") or "").strip()),
        bool(str(getattr(card, "reflection", "") or "").strip()),
    ]
    return sum(checks) / len(checks)


def _support_signals(requirement: str, card: Any) -> dict[str, Any]:
    wanted = _tokens(requirement)
    card_words = _tokens(_card_text(card))
    overlap = sorted(wanted & card_words)
    wanted_concepts = _concepts(requirement)
    card_concepts = _concepts(_card_text(card))
    concept_overlap = sorted(wanted_concepts & card_concepts)

    tags_text = " ".join([
        *[str(value) for value in (getattr(card, "skills", []) or [])],
        *[str(value) for value in (getattr(card, "behaviours", []) or [])],
        *[str(value) for value in (getattr(card, "tags", []) or [])],
    ])
    tag_overlap = sorted(wanted & _tokens(tags_text))

    action_text = " ".join(str(value) for value in (getattr(card, "actions", []) or []))
    action_overlap = sorted(wanted & _tokens(action_text))
    outcome_overlap = sorted(wanted & _tokens(str(getattr(card, "outcome", "") or "")))
    authority_text = str(getattr(card, "authority_context", "") or "")
    authority_overlap = sorted(wanted & _tokens(authority_text))
    authority_concept_support = "authority" in wanted_concepts and "authority" in _concepts(authority_text)

    lexical_ratio = len(overlap) / max(1, min(len(wanted), 8))
    concept_ratio = len(concept_overlap) / max(1, len(wanted_concepts)) if wanted_concepts else 0.0
    quality = _quality(card)

    score = (
        min(1.0, lexical_ratio) * 26
        + min(1.0, concept_ratio) * 45
        + min(1.0, len(tag_overlap) / 2) * 10
        + min(1.0, len(action_overlap) / 2) * 10
        + min(1.0, len(outcome_overlap)) * 3
        + (15 if authority_concept_support else 0)
        + quality * 6
    )

    sparse_only = bool(overlap) and not (concept_overlap or tag_overlap or action_overlap or outcome_overlap or authority_overlap)
    if sparse_only:
        score = min(score, 39)

    return {
        "score": round(min(100.0, score), 1),
        "overlap": overlap,
        "concepts": concept_overlap,
        "tag_overlap": tag_overlap,
        "action_overlap": action_overlap,
        "outcome_overlap": outcome_overlap,
        "authority_overlap": authority_overlap,
        "authority_concept_support": authority_concept_support,
        "quality": round(quality, 2),
    }


def _strength(score: float) -> str:
    if score >= 72:
        return "strong"
    if score >= 48:
        return "partial"
    if score >= 24:
        return "weak"
    return "missing"


def requires_personal_management_scope(requirement: str) -> bool:
    """Return True only when the requirement asks for the candidate's own management scope."""
    return bool(
        re.search(
            r"\b(?:"
            r"management\s+(?:level|experience|responsibilit(?:y|ies))"
            r"|managerial(?:\s+(?:experience|responsibilit(?:y|ies)))?"
            r"|supervisory(?:\s+(?:experience|responsibilit(?:y|ies)))?"
            r"|supervision"
            r"|experience\s+as\s+(?:a\s+)?manager"
            r"|(?:people|team|staff)\s+(?:management|leadership)"
            r"|(?:manage|lead|supervise)\s+(?:a\s+)?(?:team|staff|people|employees|officers|direct\s+reports)"
            r")\b",
            requirement,
            flags=re.IGNORECASE,
        )
    )


def has_personal_management_scope(card: Any) -> bool:
    """Require evidence that the candidate personally managed people.

    Management verbs only count when they govern a team, staff, reports or a
    comparable group of people. Managing risks, cases, projects or operations
    therefore cannot bypass a people-management requirement.
    """
    values = [
        str(getattr(card, "task", "") or ""),
        *[str(value) for value in (getattr(card, "actions", []) or [])],
        str(getattr(card, "authority_context", "") or ""),
    ]
    person_scope = r"(?:team(?:\s+members)?|staff|people|employees|officers|colleagues|direct\s+reports|reports)"
    prefix = r"(?:^|[.!?]\s+|\bI\s+)(?:(?:have|had)\s+|(?:was|am)\s+responsible\s+for\s+)?"
    direct_management = re.compile(
        prefix
        + r"(?:managed?|managing|led|lead|leading|supervised?|supervising|coached?|coaching)\s+"
        + r"(?:(?:a|an|the|my|our)\s+)?(?:\d+\s+)?(?:[A-Za-z-]+\s+){0,3}"
        + person_scope
        + r"\b",
        flags=re.IGNORECASE,
    )
    delegated_to_people = re.compile(
        prefix
        + r"(?:delegated?|delegating)\b(?:\s+[A-Za-z0-9'-]+){0,5}\s+to\s+"
        + r"(?:(?:a|an|the|my|our)\s+)?"
        + person_scope
        + r"\b",
        flags=re.IGNORECASE,
    )
    return any(
        direct_management.search(value) or delegated_to_people.search(value)
        for value in values
        if value.strip()
    )


def deterministic_match(requirement: str, card: Any) -> dict[str, Any]:
    signals = _support_signals(requirement, card)
    score = signals["score"]

    # Scope-sensitive management requirements must be supported by the candidate's
    # own management/leadership actions, not merely by words such as "security",
    # "operations" or references to senior management in the surrounding context.
    management_requirement = requires_personal_management_scope(requirement)
    has_management_scope = has_personal_management_scope(card)
    if management_requirement and not has_management_scope:
        score = min(score, 39.0)

    strength = _strength(score)
    has_actions = bool(getattr(card, "actions", []) and any(str(value).strip() for value in getattr(card, "actions", []) or []))
    has_outcome = bool(str(getattr(card, "outcome", "") or "").strip())
    if strength == "strong" and not (has_actions and has_outcome):
        strength = "partial"
        score = min(score, 69.0)

    support_parts: list[str] = []
    if signals["concepts"]:
        support_parts.append("related capability: " + ", ".join(signals["concepts"][:3]))
    if signals["action_overlap"]:
        support_parts.append("personal actions align with: " + ", ".join(signals["action_overlap"][:4]))
    if signals["authority_concept_support"]:
        support_parts.append("recorded authority and escalation context supports the requirement")
    if signals["outcome_overlap"]:
        support_parts.append("the recorded outcome supports the requirement")
    if signals["tag_overlap"]:
        support_parts.append("explicit evidence labels align")
    if not support_parts and signals["overlap"]:
        support_parts.append("limited wording overlap only")

    gaps: list[str] = []
    if not has_actions:
        gaps.append("Personal actions are not recorded clearly enough.")
    if not has_outcome:
        gaps.append("Outcome or impact is not recorded.")
    if management_requirement and not has_management_scope:
        gaps.append("The evidence does not demonstrate management or supervisory responsibility at the required level.")
    if signals["concepts"] == [] and strength != "missing":
        gaps.append("The evidence does not clearly demonstrate the underlying capability, only related wording.")
    if strength == "missing":
        gaps.append("No sufficiently relevant evidence is recorded for this requirement.")

    why = "; ".join(support_parts) if support_parts else "No meaningful support found in this Evidence Card."
    confidence = round(min(0.96, 0.48 + (signals["quality"] * 0.2) + (abs(score - 50) / 100)), 2)

    return {
        "strength": strength,
        "score": round(score, 1),
        "confidence": confidence,
        "why": why,
        "gaps": gaps[:3],
        "supporting_facts": [],
        "signals": {
            "concepts": signals["concepts"],
            "matched_terms": signals["overlap"][:8],
            "evidence_quality": signals["quality"],
        },
    }


def rank_evidence(requirement: str, cards: list[Any]) -> list[tuple[Any, dict[str, Any]]]:
    ranked = [(card, deterministic_match(requirement, card)) for card in cards]
    return sorted(ranked, key=lambda item: item[1]["score"], reverse=True)
