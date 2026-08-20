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


_SECTION_HEADINGS: dict[str, Category] = {
    "eligibility": "eligibility",
    "who can apply": "eligibility",
    "nationality requirements": "eligibility",
    "security clearance": "eligibility",
    "additional security checks": "eligibility",
    "essential criteria": "essential",
    "essential requirements": "essential",
    "what you will need": "essential",
    "skills and experience": "essential",
    "desirable criteria": "desirable",
    "desirable": "desirable",
    "nice to have": "desirable",
    "preferred": "desirable",
    "training": "trainable",
    "learning and development": "trainable",
    "working pattern": "practical",
    "working patterns": "practical",
    "working arrangements": "practical",
    "hybrid working": "practical",
    "location preferences": "practical",
}

# These headings deliberately terminate any criteria section. Civil Service adverts
# contain a lot of candidate guidance and process text after the person specification;
# leaving the previous section active turns dates, guidance and contact details into
# fake requirements.
_IGNORED_SECTION_HEADINGS = {
    "contents",
    "location",
    "about the job",
    "job summary",
    "job description",
    "responsibilities",
    "person specification",
    "behaviours",
    "technical skills",
    "benefits",
    "things you need to know",
    "artificial intelligence",
    "selection process details",
    "problems during the application process",
    "further information",
    "reserve list",
    "breaking tied scores",
    "standards",
    "criminal record check",
}

_LEAD_INS = {
    "you must be able to demonstrate experience of",
    "you must demonstrate experience of",
    "we'll assess you against these behaviours during the selection process",
    "we will assess you against these behaviours during the selection process",
    "we'll assess you against these technical skills during the selection process",
    "we will assess you against these technical skills during the selection process",
}

_NON_REQUIREMENT_PREFIXES = (
    "apply before ",
    "application – by ",
    "application - by ",
    "sift – from ",
    "sift - from ",
    "interview – from ",
    "interview - from ",
    "your cv should ",
    "the personal statement should ",
    "for guidance ",
    "if you experience problems accessing ",
    "do not create or attempt to submit ",
    "please note travel expenses incurred by attending an interview ",
    "reserve lists will be held ",
    "candidates will be appointed in merit order ",
    "the behaviour, technical and experience skills have been ranked ",
    "we believe a positive, open and supportive culture ",
    "we value diversity ",
    "sign-up on our website ",
)


def is_non_requirement_text(value: str) -> bool:
    """Return True for advert/process copy that must never become candidate criteria."""

    text = " ".join(value.strip().split())
    if not text:
        return True
    lowered = text.lower().rstrip(":")
    if lowered in _IGNORED_SECTION_HEADINGS or lowered in _SECTION_HEADINGS or lowered in _LEAD_INS:
        return True
    if any(lowered.startswith(prefix) for prefix in _NON_REQUIREMENT_PREFIXES):
        return True
    if "@" in lowered and ("contact" in lowered or "email" in lowered or "problems" in lowered):
        return True
    return False


def _heading_section(line: str, raw: str, is_bullet: bool) -> Category | Literal["ignore"] | None:
    if is_bullet or len(line) > 120:
        return None
    lowered = line.lower().rstrip(":").strip()
    looks_like_heading = raw.strip().endswith(":") or len(line.split()) <= 8
    if not looks_like_heading:
        return None
    if lowered in _SECTION_HEADINGS:
        return _SECTION_HEADINGS[lowered]
    if lowered in _IGNORED_SECTION_HEADINGS:
        return "ignore"
    return None


def deterministic_extract(vacancy_text: str) -> list[dict[str, Any]]:
    """Extract grounded criteria from vacancy text without external services.

    The fallback deliberately prefers omission over invention. Every returned item
    is tied to a source line from the supplied advert. Explicit Essential/Desirable
    sections are treated as authoritative; process/admin sections terminate that
    scope so they cannot leak into matching.
    """

    items: list[dict[str, Any]] = []
    section: Category | None = None

    eligibility_cues = (
        "right to work",
        "eligible to apply",
        "nationality requirement",
        "security clearance",
        "security check",
        "security vetting",
        "uk security vetting",
        "mandatory qualification",
        "required driving licence",
        "required driving license",
    )
    practical_cues = (
        "hours per week",
        "days per week",
        "working pattern",
        "working arrangements",
        "office attendance",
        "working time in an office",
        "hybrid working",
        "only available on a full-time basis",
        "only available on a full time basis",
        "minimum hours",
        "required to travel",
        "travel is required",
        "travel will be required",
        "shift pattern",
        "weekend working",
        "full-time training",
        "full time training",
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
    hard_blocker_cues = (
        "cannot apply",
        "only open to",
        "must have the right to work",
        "mandatory qualification",
        "security clearance",
        "security check",
        "security vetting",
        "uk security vetting",
    )

    for raw in vacancy_text.splitlines():
        line = _clean_line(raw)
        if not line:
            continue
        lowered = line.lower().rstrip(":")
        is_bullet = bool(re.match(r"^\s*(?:[-*•]|\d+[.)])", raw))

        heading = _heading_section(line, raw, is_bullet)
        if heading is not None:
            section = None if heading == "ignore" else heading
            continue

        if is_non_requirement_text(line):
            continue

        explicit_blocker = any(token in lowered for token in hard_blocker_cues)

        if any(cue in lowered for cue in trainable_cues):
            items.append(_item(line, "trainable", 0.96))
            continue
        if any(cue in lowered for cue in eligibility_cues):
            items.append(_item(line, "eligibility", 0.9, explicit_blocker=explicit_blocker))
            continue
        if any(cue in lowered for cue in practical_cues):
            items.append(_item(line, "practical", 0.9, explicit_blocker=explicit_blocker))
            continue

        # Inside explicit criteria sections, the section heading itself is the
        # evidence that each following short line is a criterion. This recovers
        # criteria such as "Developing and delivering proposals and presentations"
        # that do not contain generic words like "experience" or "ability".
        if section in {"essential", "desirable"}:
            if len(line) <= 420 and lowered not in _LEAD_INS:
                items.append(_item(line.rstrip(";"), section, 0.9 if is_bullet else 0.86, explicit_blocker=False))
            continue

        # Outside a labelled criteria section, accept only self-identifying criteria.
        if len(line) <= 420 and (
            " is essential" in lowered
            or " is desirable" in lowered
            or lowered.startswith("must demonstrate ")
            or lowered.startswith("you must demonstrate ")
            or lowered.startswith("you must be able to ")
        ):
            category: Category = "desirable" if "desirable" in lowered else "essential"
            items.append(_item(line, category, 0.78, explicit_blocker=False))

    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item["category"], item["text"].lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    return unique[:40]
