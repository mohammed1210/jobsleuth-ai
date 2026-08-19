import pytest
from fastapi import HTTPException

from routes.evidence_bank import _looks_like_vacancy_text, _reject_vacancy_contamination


GOOD_EVIDENCE = {
    "title": "High-risk freight examination and relocation decision",
    "situation": "During a freight examination at Heathrow I needed to help determine how a secure examination could continue.",
    "task": "I gathered reliable information, assessed options and contributed to a recommendation to senior management.",
    "actions": [
        "I contacted Higher Officers and other teams to establish what equipment was available.",
        "I confirmed an alternative location had suitable specialist equipment.",
    ],
    "outcome": "The shipment was relocated and the examination progressed under operational control.",
    "reflection": "I learned to verify assumptions using independent information.",
}

VACANCY_AS_EVIDENCE = {
    "title": "Counter Fraud Investigation Officer Home Office Role summary",
    "situation": """
Role summary
We are looking for an Investigation Officer who can analyse complex information.
Eligibility
Applicants must have the right to work in the UK.
Essential criteria
You must be able to make timely evidence-based decisions.
Desirable criteria
Previous investigation experience is desirable.
Trainable requirements
Successful candidates will receive training.
Practical requirements
The role requires regular office attendance.
""",
    "task": "",
    "actions": [],
    "outcome": "",
    "reflection": "",
}


def test_genuine_personal_evidence_is_allowed():
    assert _looks_like_vacancy_text(GOOD_EVIDENCE) is False
    _reject_vacancy_contamination(GOOD_EVIDENCE)


def test_obvious_vacancy_text_is_rejected():
    assert _looks_like_vacancy_text(VACANCY_AS_EVIDENCE) is True

    with pytest.raises(HTTPException) as exc:
        _reject_vacancy_contamination(VACANCY_AS_EVIDENCE)

    assert exc.value.status_code == 422
    assert "looks like a vacancy advert" in str(exc.value.detail)


def test_single_candidate_phrase_does_not_false_positive():
    evidence = dict(GOOD_EVIDENCE)
    evidence["reflection"] = "I wanted the successful candidate experience to be clear when presenting my evidence."

    assert _looks_like_vacancy_text(evidence) is False