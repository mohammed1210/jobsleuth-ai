from fastapi.testclient import TestClient

from backend.lib.application_draft import deterministic_draft
from backend.lib.application_grounding import validate_ai_paragraph
from backend.main import app
from backend.routes.application_builder import ApplicationEvidence, ApplicationRequirement

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
        "supporting_facts": [{"evidence_id": card.id, "field": "actions", "text": card.actions[0]}],
    }
    assert validate_ai_paragraph(raw, {card.id: card}, 1) is None


def test_grounding_rejects_authority_upgrade():
    card = evidence_card()
    raw = {
        "text": "I approved the final course of action after assessing the available options.",
        "requirement_indices": [0],
        "evidence_ids": [card.id],
        "supporting_facts": [{"evidence_id": card.id, "field": "authority_context", "text": card.authority_context}],
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
            {"text": "Make evidence-based recommendations", "category": "essential", "match_strength": "strong", "evidence_ids": [card.id]},
            {"text": "Hold a specialist qualification", "category": "essential", "match_strength": "missing", "evidence_ids": []},
        ],
        "evidence_cards": [card.model_dump()],
    }
    response = client.post("/application-builder", headers=HEADERS, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["can_generate"] is True
    assert data["provider"] == "deterministic-grounded-v2"
    assert card.actions[0] in data["draft"]
    assert data["coverage"][0]["status"] == "covered"
    assert data["coverage"][1]["status"] == "evidence-gap"
    assert any("specialist qualification" in warning for warning in data["warnings"])


def test_fallback_adds_sentence_boundaries_to_evidence_fragments():
    card = evidence_card().model_copy(update={"actions": ["I contacted senior colleagues", "I checked the policy"]})
    requirement = ApplicationRequirement(text="Work within appropriate authority", match_strength="strong", evidence_ids=[card.id])
    paragraphs = deterministic_draft([requirement], {card.id: card}, "Officer", 200)
    text = paragraphs[0]["text"]
    assert "I contacted senior colleagues. I checked the policy." in text


def test_same_evidence_is_composed_once_for_multiple_requirements(monkeypatch):
    monkeypatch.setattr("routes.application_builder.semantic_application_draft", lambda *args, **kwargs: None)
    card = evidence_card()
    requirements = [
        {"text": text, "category": "essential", "match_strength": "strong", "evidence_ids": [card.id]}
        for text in [
            "Analyse complex information",
            "Assess operational risk",
            "Work with stakeholders",
            "Adapt to changing circumstances",
            "Explain recommendations clearly",
            "Work within appropriate authority",
        ]
    ]
    payload = {"job": {"title": "Operations Officer"}, "application_type": "statement_of_suitability", "word_limit": 500, "requirements": requirements, "evidence_cards": [card.model_dump()]}
    data = client.post("/application-builder", headers=HEADERS, json=payload).json()
    assert data["provider"] == "deterministic-grounded-v2"
    assert len(data["paragraphs"]) == 1
    assert data["paragraphs"][0]["requirement_indices"] == list(range(6))
    assert data["word_count"] <= 500
    assert all(item["status"] == "covered" for item in data["coverage"])


def test_oversized_semantic_draft_falls_back_to_budgeted_grounded_version(monkeypatch):
    card = evidence_card()
    oversized = {"text": " ".join(["grounded"] * 700), "requirement_indices": [0], "evidence_ids": [card.id], "supporting_facts": [], "grounding_status": "grounded"}
    monkeypatch.setattr("routes.application_builder.semantic_application_draft", lambda *args, **kwargs: [oversized])
    payload = {
        "job": {"title": "Operations Officer"},
        "word_limit": 500,
        "requirements": [{"text": "Make evidence-based recommendations", "category": "essential", "match_strength": "strong", "evidence_ids": [card.id]}],
        "evidence_cards": [card.model_dump()],
    }
    data = client.post("/application-builder", headers=HEADERS, json=payload).json()
    assert data["provider"] == "deterministic-grounded-v2"
    assert data["word_count"] <= 500
    assert not any("above the requested" in warning for warning in data["warnings"])


def test_builder_does_not_generate_when_no_supported_evidence(monkeypatch):
    monkeypatch.setattr("routes.application_builder.semantic_application_draft", lambda *args, **kwargs: None)
    payload = {
        "job": {"title": "Operations Officer"},
        "requirements": [{"text": "Advanced stakeholder negotiation", "category": "essential", "match_strength": "missing", "evidence_ids": []}],
        "evidence_cards": [],
    }
    data = client.post("/application-builder", headers=HEADERS, json=payload).json()
    assert data["can_generate"] is False
    assert data["draft"] == ""
    assert data["coverage"][0]["status"] == "evidence-gap"
