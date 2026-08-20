from routes.application_builder import _clean_meta_commentary, _normalise_paragraphs


def test_removes_parenthetical_assessor_commentary():
    text = (
        "I compared the available options and assessed the operational risks. "
        "(This paragraph underpins my ability to make evidence-based decisions.)"
    )
    cleaned = _clean_meta_commentary(text)
    assert cleaned == "I compared the available options and assessed the operational risks."


def test_removes_standalone_meta_sentence_but_keeps_evidence():
    text = (
        "I briefed colleagues and invited challenge before recommending the revised plan. "
        "This evidence demonstrates effective stakeholder management. "
        "The Senior Officer retained final decision-making authority."
    )
    cleaned = _clean_meta_commentary(text)
    assert "This evidence demonstrates" not in cleaned
    assert "I briefed colleagues" in cleaned
    assert "Senior Officer retained final decision-making authority" in cleaned


def test_normalise_preserves_grounding_metadata():
    paragraph = {
        "text": "I reassessed the risks. This example shows my adaptability.",
        "requirement_indices": [1, 2],
        "evidence_ids": ["card-1"],
        "supporting_facts": [{"field": "actions", "text": "I reassessed the risks."}],
        "grounding_status": "grounded",
    }
    result = _normalise_paragraphs([paragraph])
    assert result[0]["text"] == "I reassessed the risks."
    assert result[0]["requirement_indices"] == [1, 2]
    assert result[0]["evidence_ids"] == ["card-1"]
    assert result[0]["grounding_status"] == "grounded"


def test_does_not_strip_normal_candidate_language():
    text = "This example involved coordinating with three operational teams before I made my recommendation."
    assert _clean_meta_commentary(text) == text
