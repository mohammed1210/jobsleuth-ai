from routes.vacancy_intelligence import _reconcile_items


def test_question_style_admin_heading_is_not_returned_as_requirement():
    heading = {
        "text": "Who is eligible to apply for roles advertised Across Government?",
        "category": "eligibility",
        "source_text": "Who is eligible to apply for roles advertised Across Government?",
        "confidence": 0.9,
        "explicit_blocker": False,
    }
    actual_rule = {
        "text": "Existing Civil Servants are eligible to apply on a loan basis.",
        "category": "eligibility",
        "source_text": "Existing Civil Servants are eligible to apply on a loan basis.",
        "confidence": 1.0,
        "explicit_blocker": True,
    }

    merged, _ = _reconcile_items([heading, actual_rule], [])

    assert [item["text"] for item in merged] == [actual_rule["text"]]
