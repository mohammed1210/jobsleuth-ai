"""Issue #106: role-specific evidence must precede a tailored application draft."""
from fastapi.testclient import TestClient

from backend.main import app
from backend.lib.application_readiness import missing_direct_school_experience
from backend.routes.application_builder import ApplicationEvidence, ApplicationRequirement

client = TestClient(app)
HEADERS = {"Authorization": "Bearer valid_token"}
DIRECT = "Significant and successful leadership experience within a primary school setting."


def operations_card():
    return ApplicationEvidence(
        id="freight",
        title="High-risk freight operation",
        task="I assessed how an examination could continue safely.",
        actions=["I reviewed risks and recommended a course of action to a manager."],
        outcome="The inspection progressed.",
    )


def school_card():
    return ApplicationEvidence(
        id="school",
        title="Deputy Head at Grove Primary School",
        situation="I worked as deputy head within a primary school.",
        actions=["I led colleagues through a school improvement programme."],
        outcome="The school's improvement plan was delivered.",
    )


def test_no_full_draft_for_generic_operations_evidence_in_school_head_role(monkeypatch):
    def no_model_call(*_args, **_kwargs):
        raise AssertionError("Must stop before contacting AI provider")

    monkeypatch.setattr("routes.application_builder.semantic_application_draft", no_model_call)
    card = operations_card()
    response = client.post("/application-builder", headers=HEADERS, json={
        "job": {"title": "Head of School", "organisation": "Grove Primary School"},
        "word_limit": 500,
        "application_type": "statement_of_suitability",
        "requirements": [
            {"text": DIRECT, "category": "essential", "match_strength": "partial", "evidence_ids": [card.id]},
            {"text": "Assess operational risks", "category": "essential", "match_strength": "partial", "evidence_ids": [card.id]},
        ],
        "evidence_cards": [card.model_dump()],
    })
    assert response.status_code == 200
    result = response.json()
    assert result["provider"] == "role-readiness-guard-v1"
    assert result["fallback_reason"] == "missing_direct_school_experience"
    assert result["can_generate"] is False
    assert result["draft"] == ""
    assert result["paragraphs"] == []
    assert any(DIRECT in message for message in result["warnings"])


def test_genuine_school_evidence_passes_direct_experience_gate(monkeypatch):
    monkeypatch.setattr("routes.application_builder.semantic_application_draft", lambda *_args, **_kwargs: (None, "no_api_key"))
    card = school_card()
    response = client.post("/application-builder", headers=HEADERS, json={
        "job": {"title": "Head of School", "organisation": "Grove Primary School"},
        "requirements": [{"text": DIRECT, "category": "essential", "match_strength": "strong", "evidence_ids": [card.id]}],
        "evidence_cards": [card.model_dump()],
    })
    assert response.status_code == 200
    result = response.json()
    assert result["can_generate"] is True
    assert result["provider"] == "deterministic-grounded-v2"
    assert "school improvement" in result["draft"]


def test_generic_school_knowledge_does_not_trigger_workplace_gate():
    card = operations_card()
    criterion = ApplicationRequirement(
        text="Understanding of teaching and leadership practices in a primary school",
        category="essential", match_strength="partial", evidence_ids=[card.id],
    )
    assert missing_direct_school_experience([criterion], {card.id: card}) == []


def test_role_specific_gate_uses_only_linked_genuine_evidence():
    freight = operations_card()
    school = school_card()
    criterion = ApplicationRequirement(
        text=DIRECT, category="essential", match_strength="strong", evidence_ids=[freight.id],
    )
    assert missing_direct_school_experience([criterion], {freight.id: freight, school.id: school}) == [DIRECT]
    assert missing_direct_school_experience(
        [criterion.model_copy(update={"evidence_ids": [school.id]})],
        {freight.id: freight, school.id: school},
    ) == []
