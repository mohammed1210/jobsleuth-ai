"""Prevent cross-sector false positives in vacancy matching and qualification checks."""
from fastapi.testclient import TestClient

from backend.lib.evidence_matching import (
    deterministic_match,
    has_school_setting_experience,
    requires_school_setting_experience,
)
from backend.main import app
from backend.routes.vacancy_analysis import Evidence

client = TestClient(app)
HEADERS = {"Authorization": "Bearer valid_token"}
SCHOOL_REQUIREMENT = "Significant and successful leadership experience within a primary school setting."


def freight_card() -> Evidence:
    return Evidence(
        id="freight",
        title="Border operations review",
        task="I assessed options and presented a recommendation to a senior manager.",
        actions=["I coordinated with colleagues and managed operational risks."],
        outcome="The operation was completed safely.",
        skills=["leadership", "operational decision making", "stakeholder coordination"],
    )


def school_card() -> Evidence:
    return Evidence(
        id="school",
        title="Assistant Head at Meadow Primary School",
        task="I was responsible for leading the curriculum team.",
        actions=["I led primary school staff through a school improvement programme."],
        outcome="School improvement targets were achieved.",
    )


def test_primary_school_leadership_requires_explicit_primary_school_experience():
    assert requires_school_setting_experience(SCHOOL_REQUIREMENT)
    assert not requires_school_setting_experience("An understanding of the primary school curriculum")
    assert not requires_school_setting_experience("Understanding of teaching and leadership practices in a primary school")
    assert requires_school_setting_experience("Successful teaching experience in primary schools")
    assert not has_school_setting_experience(freight_card())
    match = deterministic_match(SCHOOL_REQUIREMENT, freight_card())
    assert match["strength"] in {"weak", "missing"}
    assert match["score"] < 48
    assert any("school setting" in gap for gap in match["gaps"])
    assert has_school_setting_experience(school_card())
    school_match = deterministic_match(SCHOOL_REQUIREMENT, school_card())
    assert not any("school setting" in gap for gap in school_match["gaps"])


def test_semantic_score_cannot_restore_cross_sector_school_match(monkeypatch):
    card = freight_card()

    def fake_batch(entries):
        return {
            entries[0][0]: {
                card.id: {
                    "strength": "strong",
                    "score": 91,
                    "confidence": 0.95,
                    "why": "Generic leadership sounds relevant.",
                    "gaps": [],
                    "supporting_facts": [],
                    "signals": {"concepts": ["leadership"], "matched_terms": ["leadership"], "evidence_quality": 1},
                }
            }
        }

    monkeypatch.setattr("routes.vacancy_analysis.semantic_assess_batch", fake_batch)
    response = client.post("/vacancy-analysis", headers=HEADERS, json={
        "job": {"title": "Head of School"},
        "requirements": [{"text": SCHOOL_REQUIREMENT, "category": "essential"}],
        "evidence_cards": [card.model_dump()],
    })
    assert response.status_code == 200
    result = response.json()
    assert result["requirements"][0]["match_strength"] == "weak"
    assert result["requirements"][0]["evidence"][0]["score"] <= 39
    assert result["decision"] == "CONSIDER"


def test_explicit_qts_no_is_skip_and_unknown_requires_confirmation(monkeypatch):
    monkeypatch.setattr("routes.vacancy_analysis.semantic_assess_batch", lambda _entries: None)
    for answer, decision, status in [
        ("no", "SKIP", "not-met"),
        ("unsure", "CONSIDER", "unconfirmed"),
        ("yes", "APPLY", "met"),
    ]:
        response = client.post("/vacancy-analysis", headers=HEADERS, json={
            "job": {"title": "Head of School"},
            "requirements": [{
                "text": "Qualified Teacher Status.",
                "category": "eligibility",
                "blocker": True,
                "eligibility_answer": answer,
            }],
            "evidence_cards": [freight_card().model_dump()],
        })
        assert response.status_code == 200
        result = response.json()
        assert result["decision"] == decision
        assert result["requirements"][0]["status"] == status


def test_explicit_school_role_in_situation_satisfies_context_gate():
    card = Evidence(
        id="school-situation",
        title="Leading a small team",
        situation="I was Assistant Head at Meadow Primary School.",
        actions=["I led colleagues through a curriculum improvement project."],
        outcome="Standards improved.",
    )
    assert has_school_setting_experience(card)
    match = deterministic_match(SCHOOL_REQUIREMENT, card)
    assert not any("school setting" in gap for gap in match["gaps"])


def test_knowledge_of_school_practices_is_not_direct_experience():
    card = Evidence(
        id="research",
        title="Public policy researcher",
        task="I researched education policy.",
        actions=["I analysed teaching and leadership practices in a primary school."],
        outcome="The review informed policy guidance.",
    )
    requirement = "Understanding of teaching and leadership practices in a primary school"
    assert not requires_school_setting_experience(requirement)
    # The workplace-specific guard must not artificially cap this knowledge criterion.
    assert not any("school setting" in gap for gap in deterministic_match(requirement, card)["gaps"])
