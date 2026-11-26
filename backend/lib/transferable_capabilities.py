"""Conservative action-grounded fallback for common transferable job criteria.

When semantic reassessment is unavailable, lexical overlap alone can miss
relevant documented administrative experience. These rules require personal
actions and a recorded outcome; they never infer licences, qualifications,
sector-specific experience or a claimed result from a skill label alone.
"""
from __future__ import annotations

import re
from typing import Any


def _match(pattern: str, value: str) -> bool:
    return bool(re.search(pattern, value, flags=re.IGNORECASE))


def _action_text(card: Any) -> str:
    actions = [
        str(item).strip()
        for item in (getattr(card, "actions", []) or [])
        if str(item).strip()
    ]
    # A phrase disclaiming an action must not supply positive proof for it.
    return " ".join(
        action for action in actions
        if not _match(r"\b(?:I|we)\s+(?:did\s+not|didn't|never|could\s+not)\b", action)
    )



def has_compound_accuracy_deadline_gap(requirement: str, card: Any) -> bool:
    """An accurate audit does not prove deadline delivery on its own."""
    if not (_match(r"\b(?:attention\s+to\s+detail|accurac\w*|accurat\w*)\b", requirement)
            and _match(r"\b(?:deadlines?|timel\w*)\b", requirement)):
        return False
    actions = _action_text(card)
    outcome = str(getattr(card, "outcome", "") or "")
    deadline_action = _match(
        r"\b(?:prioriti[sz]\w*|updat\w*|deliver\w*|report\w*|plan\w*|complet\w*|met\b|meet\b)\b",
        actions,
    )
    deadline_context = _match(
        r"\b(?:deadlines?|midday|time.sensitive|on\s+time|before\s+midday)\b",
        f"{actions} {outcome}",
    )
    return not (deadline_action and deadline_context)

def transferable_action_support(requirement: str, card: Any) -> tuple[float, str] | None:
    """Return a cautious score floor and explanation for concrete actions.

    This complements (rather than replaces) the ordinary lexical/concept
    matching. A complete STAR-like card must demonstrate what *I did*, in a
    situation or task, and record an outcome. Broad labels and CV summaries
    are insufficient.
    """
    actions = _action_text(card)
    outcome = str(getattr(card, "outcome", "") or "").strip()
    context = " ".join([
        str(getattr(card, "situation", "") or ""),
        str(getattr(card, "task", "") or ""),
    ])
    if not actions or not outcome or not context.strip() or not _match(r"\bI\s+", actions):
        return None

    combined = f"{actions} {outcome}"

    if _match(r"\b(?:organi[sz]\w*|planning\s+skills|time\s+management)\b", requirement):
        if (_match(r"\b(?:prioriti[sz]\w*|allocat\w*|plan\w*|schedul\w*|organi[sz]\w*|roster\w*|coordinat\w*)\b", actions)
                and _match(r"\b(?:task|staff|roster|team|workload|priority|priorities|report|deadline|meeting|training)\b", actions)):
            return 75.0, "organising and prioritising real work"

    if _match(r"\b(?:administrat\w*|office\s+support|clerical)\b", requirement):
        if (_match(r"\b(?:used|maintain\w*|prepar\w*|produc\w*|compil\w*|updat\w*|record\w*|audit\w*|check\w*|review\w*|arrang\w*|manag\w*)\b", actions)
                and _match(r"\b(?:spreadsheet|roster|staffing\s+figure|record|report|audit|sickness|HR|meeting|Outlook|email|document|training)\w*\b", actions)):
            return 75.0, "carrying out administrative record-keeping and reporting tasks"

    if _match(r"\b(?:flexib\w*|can.do\s+approach|changing\s+(?:needs|priorities)|adaptab\w*)\b", requirement):
        if (_match(r"\b(?:adapt\w*|alternat\w*|resum\w*|switch\w*|reorgan\w*|adjust\w*|re-prioriti[sz]\w*|return\w*)\b", actions)
                and _match(r"\b(?:interrupt\w*|operational|workload|changing|urgent|priorit\w*|location|task|duties|demand)\b", actions)):
            return 75.0, "adapting work as priorities and demands changed"

    if _match(r"\b(?:attention\s+to\s+detail|accurac\w*|accurat\w*)\b", requirement):
        accurate = (_match(r"\b(?:audit\w*|cross.check\w*|verif\w*|review\w*|correct\w*|identif\w*|reconcil\w*)\b", actions)
                    and _match(r"\b(?:record|document|discrepanc\w*|error|audit|detail|data|information)\w*\b", actions))
        deadline_requested = _match(r"\b(?:deadlines?|time\s+pressure|timel\w*)\b", requirement)
        deadline = (_match(r"\b(?:prioriti[sz]\w*|updat\w*|deliver\w*|report\w*|plan\w*|complet\w*|met\b|meet\b)\b", actions)
                    and _match(r"\b(?:deadline|midday|urgent|time.sensitive|on\s+time|before\s+midday)\b", combined))
        if accurate and (deadline or not deadline_requested):
            return 75.0, "checking records carefully and meeting time-sensitive work"
        if accurate or (deadline_requested and deadline):
            return 60.0, "one documented aspect of accuracy and deadline management"

    if _match(r"\b(?:communicat\w*|liais\w*|interpersonal)\b", requirement):
        if (_match(r"\b(?:explain\w*|communicat\w*|liais\w*|inform\w*|brief\w*|email\w*|contact\w*|spoke\b|speak\b)\b", actions)
                and _match(r"\b(?:staff|colleague|partner|stakeholder|passenger|visitor|student|team|manager|HMRC|client|customer)\w*\b", combined)):
            # School reception requires communicating with students/visitors;
            # cross-sector communication alone should not assert that setting.
            specialised_audience = _match(r"\b(?:students?\s+and\s+visitors?|staff,\s*students?\s+and\s+visitors?)\b", requirement)
            has_audience = _match(r"\b(?:students?|visitors?)\b", actions)
            return (65.0 if specialised_audience and not has_audience else 75.0), "adapting communication and liaising with other people"

    if _match(r"\b(?:telephone|phone)\b", requirement):
        if (_match(r"\b(?:phone|telephone|calls?)\b", actions)
                and _match(r"\b(?:contact\w*|maintain\w*|call\w*|spoke\b|answer\w*|handl\w*)\b", actions)):
            return 56.0, "making real telephone contact; front-desk call handling is not yet established"

    if (_match(r"\bindependen\w*\b", requirement)
            and _match(r"\bteam\b", requirement)):
        initiative = _match(r"\bI\s+(?:identif\w*|propos\w*|plan\w*|develop\w*|review\w*|assess\w*|coordinat\w*|implement\w*|arrang\w*)\b", actions)
        collaboration = _match(r"\b(?:with\s+(?:colleague|staff|team|partner)|colleagues|stakeholders|team\s+members|worked\s+together|liais\w*)\b", actions)
        if initiative and collaboration:
            return 75.0, "taking initiative and working collaboratively"
        if initiative or collaboration:
            return 58.0, "one documented aspect of independent and team working"

    return None
