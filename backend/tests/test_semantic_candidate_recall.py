"""Regression tests for bounded recall beyond lexical top-three matches."""
from backend.lib.evidence_matching import rank_evidence
from backend.routes.vacancy_analysis import Evidence, _semantic_candidates
from backend.lib.evidence_semantic_batch import _compact_card


def _card(identifier: str, title: str, actions: list[str], outcome: str = "") -> Evidence:
    return Evidence(
        id=identifier,
        title=title,
        situation="A team handled operational activity.",
        task="I had to support the team's work.",
        actions=actions,
        outcome=outcome,
    )


def test_action_rich_card_outside_lexical_top_three_is_included():
    requirement = "Excellent organisational skills"
    # Repeated exact labels in poor-quality cards are plausible lexical decoys.
    decoys = [
        Evidence(id=f"label-{i}", title="Excellent organisational skills",
                 skills=["excellent organisational skills"])
        for i in range(3)
    ]
    grounded = _card(
        "grounded", "Managing daily duties",
        ["I reassigned officers between priorities.", "I arranged cover for unplanned absences."],
        "The duty rota was updated and cover was maintained.",
    )
    ranked = rank_evidence(requirement, decoys + [grounded])
    # Test the selection directly to avoid relying on the scoring order changing.
    assert [card.id for card in _semantic_candidates(ranked)] == [
        card.id for card, _ in ranked[:3]
    ] + [card.id for card, _ in ranked[3:]]
    assert "grounded" in [card.id for card in _semantic_candidates(ranked)]


def test_recall_is_capped_and_prefers_grounded_personal_actions():
    ranked = [
        (Evidence(id=f"thin-{i}", title="Organising"), {"score": 60.0 - i})
        for i in range(3)
    ]
    ranked += [
        (_card(f"weak-{i}", "Shadowing", ["The manager planned the rota."]), {"score": 39.0 - i})
        for i in range(4)
    ]
    ranked += [
        (_card(f"real-{i}", "Operational cover",
               ["I checked shift gaps.", "I rearranged duty cover."],
               "Coverage was maintained."), {"score": 15.0 - i})
        for i in range(4)
    ]
    selected = _semantic_candidates(ranked)
    assert len(selected) == 6
    assert [c.id for c in selected[:3]] == ["thin-0", "thin-1", "thin-2"]
    assert all(c.id.startswith("real-") for c in selected[3:])
    assert all(_compact_card(c) is not None for c in selected)


def test_small_evidence_banks_keep_existing_order():
    cards = [(_card(f"card-{i}", "Audit", ["I verified reports."], "Records were corrected."),
              {"score": 55.0-i}) for i in range(3)]
    assert [c.id for c in _semantic_candidates(cards)] == ["card-0", "card-1", "card-2"]


def test_route_passes_broader_candidates_to_semantic_without_promoting_unsupported_scope(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import app

    calls = []

    def observe(entries):
        calls.extend(entries)
        return None

    monkeypatch.setattr("routes.vacancy_analysis.semantic_assess_batch", observe)
    cards = [
        Evidence(id=f"keyword-{i}", title="Previous experience at management level within security operations",
                 skills=["security operations management"])
        for i in range(3)
    ]
    cards.append(_card("risk-only", "Operational risk",
                      ["I assessed security risks and implemented controls."],
                      "The security risk was reduced."))
    response = TestClient(app).post(
        "/vacancy-analysis",
        headers={"Authorization": "Bearer valid_token"},
        json={
            "job": {"title": "Security Manager"},
            "requirements": [{"text": "Previous experience at management level within security operations",
                              "category": "essential"}],
            "evidence_cards": [card.model_dump() for card in cards],
        },
    )
    assert response.status_code == 200
    assert len(calls) == 1
    assert "risk-only" in [card.id for card in calls[0][2]]
    assert response.json()["requirements"][0]["match_strength"] != "strong"
