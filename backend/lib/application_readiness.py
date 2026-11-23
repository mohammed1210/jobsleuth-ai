"""Conservative readiness checks before producing a role-specific application.

Do not mistake transferable skills for an explicit direct-workplace requirement.
These checks concern evidence completeness, not a decision on an applicant's
ultimate eligibility; the employer remains authoritative.
"""

from __future__ import annotations

from typing import Any

from lib.evidence_matching import has_school_setting_experience, requires_school_setting_experience


def missing_direct_school_experience(requirements: list[Any], cards_by_id: dict[str, Any]) -> list[str]:
    """Return explicit essential school-workplace experience criteria lacking proof.

    Only a named and matched Evidence Card documenting the applicant's own
    workplace can support the gate; arbitrary role titles or generic skills
    are not accepted as direct school-setting evidence.
    """
    missing: list[str] = []
    for requirement in requirements:
        if getattr(requirement, "category", None) != "essential":
            continue
        criterion = str(getattr(requirement, "text", "")).strip()
        if not requires_school_setting_experience(criterion):
            continue
        linked_cards = (
            cards_by_id.get(str(evidence_id))
            for evidence_id in (getattr(requirement, "evidence_ids", []) or [])
        )
        if not any(
            has_school_setting_experience(card)
            for card in linked_cards
            if card is not None
        ):
            missing.append(criterion)
    return missing
