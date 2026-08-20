from backend.lib.application_grounding import validate_ai_paragraph
from backend.routes.application_builder import ApplicationEvidence


def evidence_with_duration() -> ApplicationEvidence:
    return ApplicationEvidence(
        id="ev-duration",
        title="Operational examination",
        task="I assessed the available options and made a recommendation.",
        actions=["I compared the operational risks and consulted affected colleagues."],
        outcome="Access was achieved and the extraction operation continued for approximately 18 hours.",
        authority_context="I made a recommendation; final approval remained with the senior manager.",
    )


def test_validator_repairs_omitted_numeric_fact_from_same_evidence_card():
    card = evidence_with_duration()
    raw = {
        "text": "I compared the operational risks, and the extraction operation then continued for approximately 18 hours.",
        "requirement_indices": [0],
        "evidence_ids": [card.id],
        "supporting_facts": [
            {"evidence_id": card.id, "field": "actions", "text": card.actions[0]},
        ],
    }

    paragraph = validate_ai_paragraph(raw, {card.id: card}, 1)

    assert paragraph is not None
    assert any(fact["field"] == "outcome" and "18 hours" in fact["text"] for fact in paragraph["supporting_facts"])


def test_validator_does_not_repair_same_number_with_wrong_unit():
    card = evidence_with_duration()
    raw = {
        "text": "I compared the operational risks and the operation resulted in 18 arrests.",
        "requirement_indices": [0],
        "evidence_ids": [card.id],
        "supporting_facts": [
            {"evidence_id": card.id, "field": "actions", "text": card.actions[0]},
        ],
    }

    assert validate_ai_paragraph(raw, {card.id: card}, 1) is None
