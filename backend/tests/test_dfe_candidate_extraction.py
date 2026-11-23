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
    assert len(essentials) >= 4
    assert any("Qualified Teacher Status" in x["text"] for x in essentials)
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
