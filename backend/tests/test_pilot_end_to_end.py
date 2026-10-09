"""End-to-end backend pilot journey.

This keeps one representative vacancy moving through the same stages as the Apply
page: extraction -> fit analysis -> grounded application draft.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from lib.vacancy_extraction import deterministic_extract

client = TestClient(app)
HEADERS = {"Authorization": "Bearer valid_token"}


VACANCY = """
Prisoner Escort & Custody Officer

We operate early and late shifts and you may need to work beyond contracted hours.

Requirements of the role:
Full UK driving licence essential
Strong communication skills (written and verbal)
Ability to stay calm and make decisions under pressure
Confidence managing behaviour and de-escalating conflict
Teamwork and the ability to follow processes accurately
Professionalism, integrity, and respect for confidentiality

You will receive full training.

Eligibility checks and further information:
You must have the right to work in the UK.
"""


EVIDENCE = [
    {
        "id": "ev-communication",
        "title": "Multi-agency operational incident",
        "situation": "An operational incident required coordination with partner agencies.",
        "task": "I was responsible for communicating updates and following the agreed process.",
        "actions": [
            "I maintained clear communication with police and operational colleagues as circumstances changed.",
            "I recorded the relevant information and followed the required operational process.",
        ],
        "outcome": "The incident was managed safely and the required records were completed.",
        "skills": ["communication", "teamwork", "process compliance"],
    },
    {
        "id": "ev-pressure",
        "title": "Decision under pressure",
        "situation": "A time-sensitive operational issue required a prompt response.",
        "task": "I needed to assess the available information and act within my authority.",
        "actions": [
            "I reviewed the available information, assessed the operational risk and made a measured decision.",
            "I stayed calm while coordinating the next steps with colleagues.",
        ],
        "outcome": "The issue was resolved safely.",
        "skills": ["decision making", "risk assessment"],
    },
]


def _analysis_requirements(items):
    result = []
    for item in items:
        if item["category"] not in {"eligibility", "essential", "desirable", "trainable"}:
            continue
        requirement = {
            "text": item["text"],
            "category": item["category"],
            "blocker": item["explicit_blocker"],
        }
        if item["category"] == "eligibility":
            requirement["eligibility_answer"] = "yes"
        result.append(requirement)
    return result


def test_pilot_vacancy_to_grounded_draft_journey(monkeypatch):
    monkeypatch.setattr("routes.vacancy_analysis.semantic_assess_batch", lambda _entries: None)
    monkeypatch.setattr(
        "routes.application_builder.semantic_application_draft",
        lambda *args, **kwargs: (None, "no_api_key"),
    )

    extracted = deterministic_extract(VACANCY)

    assert any(
        item["category"] == "eligibility" and "driving licence" in item["text"].lower()
        for item in extracted
    )
    assert any(
        item["category"] == "essential" and "communication skills" in item["text"].lower()
        for item in extracted
    )
    assert any(item["category"] == "trainable" for item in extracted)

    analysis_payload = {
        "job": {"title": "Prisoner Escort & Custody Officer", "organisation": "Example Justice Services"},
        "requirements": _analysis_requirements(extracted),
        "evidence_cards": EVIDENCE,
        "practical_issues": [],
    }
    analysis_response = client.post("/vacancy-analysis", headers=HEADERS, json=analysis_payload)
    assert analysis_response.status_code == 200
    analysis = analysis_response.json()

    # We have useful evidence, but deliberately leave de-escalation/confidentiality
    # unsupported so the recommendation must remain cautious.
    assert analysis["decision"] == "CONSIDER"

    communication = next(
        item for item in analysis["requirements"] if "communication skills" in item["requirement"].lower()
    )
    assert communication["match_strength"] in {"partial", "strong"}
    assert communication["evidence"]

    deescalation = next(
        item for item in analysis["requirements"] if "de-escalating conflict" in item["requirement"].lower()
    )
    assert deescalation["match_strength"] in {"weak", "missing"}

    builder_requirements = []
    for item in analysis["requirements"]:
        if item["category"] in {"eligibility", "trainable"}:
            continue
        builder_requirements.append(
            {
                "text": item["requirement"],
                "category": item["category"],
                "match_strength": item["match_strength"],
                "evidence_ids": [e["id"] for e in item.get("evidence", []) if e.get("id")],
            }
        )

    build_payload = {
        "job": {"title": "Prisoner Escort & Custody Officer", "organisation": "Example Justice Services"},
        "application_type": "statement_of_suitability",
        "word_limit": 500,
        "requirements": builder_requirements,
        "evidence_cards": EVIDENCE,
    }
    build_response = client.post("/application-builder", headers=HEADERS, json=build_payload)
    assert build_response.status_code == 200
    draft = build_response.json()

    assert draft["can_generate"] is True
    assert draft["word_count"] <= 500
    assert draft["provider"] == "deterministic-grounded-v2"

    # Supported evidence must appear; unsupported criteria must be reported rather
    # than invented into the draft.
    assert "maintained clear communication with police" in draft["draft"].lower()
    assert any(
        item["status"] == "evidence-gap" and "de-escalating conflict" in item["requirement"].lower()
        for item in draft["coverage"]
    )
    assert any("de-escalating conflict" in warning.lower() for warning in draft["warnings"])
