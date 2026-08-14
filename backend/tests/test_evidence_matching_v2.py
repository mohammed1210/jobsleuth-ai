from fastapi.testclient import TestClient

from backend.lib.evidence_matching import deterministic_match
from backend.lib.evidence_semantic import _validated_match
from backend.main import app
from backend.routes.vacancy_analysis import Evidence

client = TestClient(app)
HEADERS = {"Authorization": "Bearer valid_token"}


def strong_card() -> Evidence:
    return Evidence(
        id="ev-strong",
        title="Operational decision",
        situation="A time-critical operational issue required a decision with incomplete information.",
        task="I was responsible for assessing the options and making a recommendation.",
        actions=[
            "I assessed several options, checked the available evidence and evaluated the risks.",
            "I consulted affected stakeholders and recommended the safest proportionate course.",
        ],
        outcome="The recommendation was accepted and the operation was completed safely.",
        reflection="I learned to verify assumptions before making a recommendation.",
        authority_context="I made the recommendation; the senior manager retained final approval.",
        skills=["decision making", "risk assessment"],
    )


def test_structured_synonym_evidence_is_partial_without_exact_wording():
    match = deterministic_match("Make sound decisions using incomplete information", strong_card())
    assert match["strength"] in {"partial", "strong"}
    assert "decision" in match["signals"]["concepts"]
    assert match["score"] >= 48


def test_shared_generic_word_does_not_create_false_match():
    card = Evidence(id="ev-thin", title="Management meeting", tags=["management"])
    match = deterministic_match("Build stakeholder relationships and influence senior partners", card)
    assert match["strength"] in {"weak", "missing"}
    assert match["score"] < 48


def test_exact_labels_without_actions_or_outcome_are_not_strong():
    card = Evidence(id="ev-label", title="Decision example", skills=["confident decision making"])
    match = deterministic_match("confident decision making", card)
    assert match["strength"] == "partial"
    assert "Personal actions" in " ".join(match["gaps"])


def test_semantic_match_requires_grounded_supporting_facts():
    card = strong_card()
    cards = {card.id: card}
    raw = {
        "evidence_id": card.id,
        "strength": "strong",
        "score": 88,
        "confidence": 0.9,
        "why": "The example shows option analysis and recommendation.",
        "gaps": [],
        "supporting_facts": [
            {"field": "actions", "text": "I assessed several options, checked the available evidence and evaluated the risks."}
        ],
    }
    validated = _validated_match(raw, cards)
    assert validated is not None
    assert validated["strength"] == "strong"
    assert validated["supporting_facts"][0]["field"] == "actions"


def test_semantic_match_rejects_invented_supporting_fact():
    card = strong_card()
    raw = {
        "evidence_id": card.id,
        "strength": "strong",
        "score": 90,
        "confidence": 0.9,
        "why": "Invented claim.",
        "supporting_facts": [{"field": "outcome", "text": "Saved the organisation one million pounds."}],
    }
    assert _validated_match(raw, {card.id: card}) is None


def test_route_returns_explainable_match_contract(monkeypatch):
    monkeypatch.setattr("routes.vacancy_analysis.semantic_assess_batch", lambda _entries: None)
    payload = {
        "job": {"title": "Operations Officer"},
        "requirements": [{"text": "confident decision making", "category": "essential"}],
        "evidence_cards": [strong_card().model_dump()],
    }
    response = client.post("/vacancy-analysis", headers=HEADERS, json=payload)
    assert response.status_code == 200
    data = response.json()
    item = data["requirements"][0]
    assert item["match_strength"] in {"strong", "partial"}
    assert "confidence" in item
    assert "why" in item
    assert "gaps" in item
    assert data["analysis_provider"] == "structured-evidence-v2"


def test_partial_essential_match_returns_consider(monkeypatch):
    monkeypatch.setattr("routes.vacancy_analysis.semantic_assess_batch", lambda _entries: None)
    thin_card = Evidence(id="ev-label", title="Decision example", skills=["confident decision making"])
    payload = {
        "job": {"title": "Operations Officer"},
        "requirements": [{"text": "confident decision making", "category": "essential"}],
        "evidence_cards": [thin_card.model_dump()],
    }
    data = client.post("/vacancy-analysis", headers=HEADERS, json=payload).json()
    assert data["requirements"][0]["match_strength"] == "partial"
    assert data["requirements"][0]["status"] == "partial"
    assert data["decision"] == "CONSIDER"


def test_route_batches_ambiguous_semantic_work_once(monkeypatch):
    calls = []

    def fake_batch(entries):
        calls.append(entries)
        return None

    monkeypatch.setattr("routes.vacancy_analysis.semantic_assess_batch", fake_batch)
    card = Evidence(id="ev-thin", title="General example", tags=["communication"])
    payload = {
        "job": {"title": "Officer"},
        "requirements": [
            {"text": "stakeholder engagement", "category": "essential"},
            {"text": "written communication", "category": "essential"},
            {"text": "planning and prioritisation", "category": "desirable"},
        ],
        "evidence_cards": [card.model_dump()],
    }
    client.post("/vacancy-analysis", headers=HEADERS, json=payload)
    assert len(calls) == 1
    assert len(calls[0]) >= 1
