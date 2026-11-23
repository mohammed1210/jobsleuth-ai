"""Source-grounded school leadership vacancy extraction regression checks."""
from lib.vacancy_extraction import deterministic_extract


def test_dfe_about_you_bullets_are_requirements_without_intro_heading():
    advert = """Job title
Head of School
Employer
Synthetic Academy
Working pattern: Full Time

About You
You will be a highly effective primary leader with experience in school improvement.
You will have:
• Qualified Teacher Status.
• Significant and successful leadership experience within a primary school setting.
• Experience of leading and developing high-performing teams.
• A strong understanding of curriculum development, school improvement and safeguarding.
Benefits
We provide a supportive workplace and professional development.
"""
    items = deterministic_extract(advert)
    essentials = [x for x in items if x["category"] == "essential"]
    assert len(essentials) >= 3
    qualifications = [x for x in items if x["category"] == "eligibility"]
    assert len(qualifications) == 1
    assert qualifications[0]["text"] == "Qualified Teacher Status."
    assert qualifications[0]["explicit_blocker"] is True
    assert any("leadership experience" in x["text"] for x in essentials)
    assert not any(x["text"].strip(":").lower() == "you will have" for x in items)
    assert not any("supportive workplace" in x["text"] for x in items)
    assert all(x["source_text"] == x["text"] for x in items)


def test_metadata_without_person_spec_cannot_fake_fit_criteria():
    excerpt = """Job title
Head of School
Employer
Synthetic Academy
Location
Leeds
Working pattern: Full Time
About the school
We are proud of our history and the many opportunities available to pupils.
"""
    items = deterministic_extract(excerpt)
    assert not [x for x in items if x["category"] in ("essential", "desirable", "eligibility")]


def test_qts_is_only_a_prerequisite_when_stated_as_required():
    required = deterministic_extract("About You\nYou will have:\n• Qualified Teacher Status (QTS).")
    assert [(x["category"], x["explicit_blocker"]) for x in required] == [("eligibility", True)]

    desirable = deterministic_extract("Desirable criteria:\n• Qualified Teacher Status.")
    assert all(x["category"] != "eligibility" for x in desirable)

    optional = deterministic_extract("About You\n• Qualified Teacher Status is desirable.")
    assert [x["category"] for x in optional] == ["desirable"]

    negated = deterministic_extract("About You\n• Qualified Teacher Status is not required.")
    assert not any("Teacher Status" in x["text"] for x in negated)

    context_only = deterministic_extract(
        "About the school\nWe provide training for colleagues seeking Qualified Teacher Status."
    )
    assert not any(x["category"] == "eligibility" for x in context_only)


def test_negated_qts_does_not_hide_other_mandatory_criteria_on_same_line():
    examples = [
        "Qualified Teacher Status is not required, but experience supporting children is essential",
        "Experience supporting children is essential, but QTS is not required",
    ]
    for sentence in examples:
        items = deterministic_extract("About You\n• " + sentence)
        assert not any(x["category"] == "eligibility" for x in items)
        assert any(
            x["category"] == "essential"
            and "experience supporting children is essential" in x["text"].lower()
            for x in items
        )
        assert all("not required" not in x["text"].lower() for x in items)
