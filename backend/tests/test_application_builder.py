from fastapi.testclient import TestClient

from backend.lib.application_grounding import validate_ai_paragraph
from backend.main import app
from backend.routes.application_builder import ApplicationEvidence

client = TestClient(app)
HEADERS = {"Authorization": "Bearer valid_token"}


def evidence_card() -> ApplicationEvidence:
    return ApplicationEvidence(
        id="ev-1",
        title="Operational review",
        task="I was responsible for assessing the available options and making a recommendation.",
        actions=[
            "I checked the available information and compared the operational risks.",
            "I consulted colleagues affected by the proposed change before making my recommendation.",
        ],
        outcome="The recommendation was accepted and the work was completed safely.",
        authority_context="I made the recommendation; final approval remained with the senior manager.",
    )


def test_application_builder_requires_authentication():
    response = client.post("/application-builder", json={"job": {"title": "Officer"}})
    assert response.status_code == 401


def test_grounding_rejects_invented_numeric_claim():
    card = evidence_card()
    raw = {
        "text": "I reduced processing time by 40% after assessing the options.",
        "requirement_indices": [0],
        "evidence_ids": [card.id],
        "supporting_facts": [
            {
                "evidence_id": card.id,
                "field": "actions",
                "text": "I checked the available information and compared the operational risks.",
            }
        ],
    }
    assert validate_ai_paragraph(raw, {card.id: card}, 1) is None


def test_grounding_rejects_authority_upgrade():
    card = evidence_card()
    raw = {
        "text": "I approved the final course of action after assessing the available options.",
        "requirement_indices": [0],
        "evidence_ids": [card.id],
        "supporting_facts": [
            {
                "evidence_id": card.id,
                "field": "authority_context",
                "text": "I made the recommendation; final approval remained with the senior manager.",
            }
        ],
    }
    assert validate_ai_paragraph(raw, {card.id: card}, 1) is None


def test_deterministic_builder_uses_supported_evidence_and_reports_gap(monkeypatch):
    monkeypatch.setattr("routes.application_builder.semantic_application_draft", lambda *args, **kwargs: None)
    card = evidence_card()
    payload = {
        "job": {"title": "Operations Officer", "organisation": "Public Service Team"},
        "application_type": "statement_of_suitability",
        "word_limit": 500,
        "requirements": [
            {
                "text": "Make evidence-based recommendations",
                "category": "essential",
                "match_strength": "strong",
                "evidence_ids": [card.id],
            },
            {
                "text": "Hold a specialist qualification",
                "category": "essential",
                "match_strength": "missing",
                "evidence_ids": [],
            },
        ],
        "evidence_cards": [card.model_dump()],
    }
    response = client.post("/application-builder", headers=HEADERS, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["can_generate"] is True
    assert data["provider"] == "deterministic-grounded-v1"
    assert card.actions[0] in data["draft"]
    assert data["coverage"][0]["status"] == "covered"
    assert data["coverage"][1]["status"] == "evidence-gap"
    assert any("specialist qualification" in warning for warning in data["warnings"])


def test_builder_does_not_generate_when_no_supported_evidence(monkeypatch):
    monkeypatch.setattr("routes.application_builder.semantic_application_draft", lambda *args, **kwargs: None)
    payload = {
        "job": {"title": "Operations Officer"},
        "requirements": [
            {
                "text": "Advanced stakeholder negotiation",
                "category": "essential",
                "match_strength": "missing",
                "evidence_ids": [],
            }
        ],
        "evidence_cards": [],
    }
    data = client.post("/application-builder", headers=HEADERS, json=payload).json()
    assert data["can_generate"] is False
    assert data["draft"] == ""
    assert data["coverage"][0]["status"] == "evidence-gap"
