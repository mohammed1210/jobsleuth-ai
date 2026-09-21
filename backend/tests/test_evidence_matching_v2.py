from fastapi.testclient import TestClient

from backend.lib.evidence_matching import deterministic_match, requires_personal_management_scope
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


def test_authority_context_can_support_accountability_requirement():
    card = strong_card()
    match = deterministic_match(
        "Demonstrate personal accountability while working within appropriate levels of authority and escalation",
        card,
    )
    assert match["strength"] in {"partial", "strong"}
    assert match["score"] >= 48
    assert "authority" in match["signals"]["concepts"]
    assert "authority and escalation context" in match["why"]


def test_public_service_operational_context_is_not_treated_as_wording_only():
    card = Evidence(
        id="ev-public",
        title="Operational compliance activity",
        situation="I worked in a Border Force operational environment on a high-risk compliance activity.",
        task="I supported an operational examination with colleagues and external partners.",
        actions=["I coordinated with operational teams and law-enforcement partners."],
        outcome="The operation was completed safely and the examination progressed.",
        tags=["law enforcement", "public sector", "operations"],
    )
    match = deterministic_match(
        "Experience working within a government, regulatory or operational environment",
        card,
    )
    assert match["strength"] in {"partial", "strong"}
    assert match["score"] >= 48
    assert "public_service" in match["signals"]["concepts"]


def test_management_level_requirement_needs_personal_management_scope():
    card = Evidence(
        id="ev-security-risk",
        title="High-risk freight examination",
        situation="A secure operational examination involved significant security risks.",
        task="I assessed options and contributed a recommendation to senior management.",
        actions=[
            "I assessed security and transport risks.",
            "I consulted colleagues and recommended a revised operational plan.",
        ],
        outcome="The operation progressed safely.",
        skills=["risk assessment", "operational decision making"],
    )
    match = deterministic_match(
        "Previous experience at management level within security operations",
        card,
    )
    assert match["strength"] in {"weak", "missing"}
    assert match["score"] < 48
    assert any("management or supervisory responsibility" in gap for gap in match["gaps"])


def test_management_verb_without_people_scope_does_not_satisfy_requirement():
    card = Evidence(
        id="ev-managed-risk",
        title="Security risk management",
        task="I managed security risks in operations.",
        actions=["I reviewed controls and mitigated operational risks."],
        outcome="The operation progressed safely.",
    )
    match = deterministic_match(
        "Previous experience at management level within security operations",
        card,
    )
    assert match["strength"] in {"weak", "missing"}
    assert any("management or supervisory responsibility" in gap for gap in match["gaps"])


def test_line_manager_reference_is_not_a_management_requirement():
    assert not requires_personal_management_scope("Work effectively with your line manager and colleagues")
    assert requires_personal_management_scope("Previous experience at management level within security operations")


def test_management_scope_accepts_common_first_person_constructions():
    variants = [
        Evidence(
            id="ev-managed",
            title="Team management",
            task="I have managed a team across several sites.",
            actions=["I set priorities and reviewed performance."],
            outcome="Service levels improved.",
        ),
        Evidence(
            id="ev-supervised",
            title="Team supervision",
            task="I was responsible for supervising officers on shift.",
            actions=["I allocated work and supported staff."],
            outcome="Coverage was maintained.",
        ),
        Evidence(
            id="ev-fragment",
            title="Team leadership",
            actions=["Managed a team of officers across multiple locations."],
            outcome="Standards were maintained.",
        ),
    ]

    for card in variants:
        match = deterministic_match("Previous experience at management level within security operations", card)
        assert "management or supervisory responsibility" not in " ".join(match["gaps"])


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


def test_semantic_reassessment_cannot_restore_false_management_match(monkeypatch):
    card = Evidence(
        id="ev-security-risk",
        title="High-risk freight examination",
        situation="A secure operational examination involved significant security risks.",
        task="I assessed options and contributed a recommendation to senior management.",
        actions=["I assessed risks and recommended a revised operational plan."],
        outcome="The operation progressed safely.",
    )

    def fake_batch(entries):
        return {
            entries[0][0]: {
                card.id: {
                    "strength": "strong",
                    "score": 88,
                    "confidence": 0.9,
                    "why": "Operational security experience appears related.",
                    "gaps": [],
                    "supporting_facts": [],
                    "signals": {"concepts": ["risk"], "matched_terms": ["security"], "evidence_quality": 1},
                }
            }
        }

    monkeypatch.setattr("routes.vacancy_analysis.semantic_assess_batch", fake_batch)
    payload = {
        "job": {"title": "Security Operations Manager"},
        "requirements": [
            {"text": "Previous experience at management level within security operations", "category": "essential"}
        ],
        "evidence_cards": [card.model_dump()],
    }

    data = client.post("/vacancy-analysis", headers=HEADERS, json=payload).json()
    item = data["requirements"][0]
    assert item["match_strength"] == "weak"
    assert item["evidence"][0]["score"] <= 39
    assert any("management or supervisory responsibility" in gap for gap in item["gaps"])
