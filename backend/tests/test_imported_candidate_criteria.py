"""Regression fixtures model the two reported DfE handoff failures, without user data."""
import pytest

from lib.vacancy_extraction import deterministic_extract
from routes.vacancy_intelligence import _reconcile_items


HANDOFF = """Job title
Teaching Assistant
Employer
Example Primary School
Location
England
Working pattern: Part Time
Publisher-supplied job description (review original for full criteria and application instructions):
"""


@pytest.mark.parametrize("apostrophe", ["'", "’"])
def test_short_publisher_candidate_list_is_extracted_without_ai(apostrophe):
    criteria = [
        "Has a patient approach and remains calm in challenging situations.",
        "Demonstrates communication and partnership skills.",
        "Has GCSE English and Maths (or equivalent).",
        "Shares our commitment to supporting children.",
    ]
    advert = HANDOFF + f"We{apostrophe}d love to hear from someone who:\n\n"
    advert += "\n\n".join("• " + criterion for criterion in criteria)
    advert += "\n\nWe offer excellent professional development.\n• Staff pension scheme."
    items, provider = _reconcile_items(None, deterministic_extract(advert))
    assert provider == "deterministic-v2"
    assert [i["text"] for i in items if i["category"] == "essential"] == criteria
    assert any(i["category"] == "practical" for i in items)
    assert all(i["source_text"] in advert for i in items)
    assert not any(i["explicit_blocker"] for i in items)


def test_prose_candidate_preference_is_desirable_not_mandatory():
    preference = "The successful candidate will ideally have experience of working as a Level 2 Teaching Assistant in a primary school."
    advert = HANDOFF + "\nWe are a thriving school.\n" + preference + "\nWe welcome visits."
    items, _ = _reconcile_items(None, deterministic_extract(advert))
    requirements = [i for i in items if i["category"] != "practical"]
    assert len(requirements) == 1
    assert requirements[0]["text"] == preference
    assert requirements[0]["category"] == "desirable"
    assert not requirements[0]["explicit_blocker"]


def test_metadata_and_marketing_do_not_create_candidate_criteria():
    advert = HANDOFF + "\nWe are a friendly school.\nWe would ideally have more staff."
    assert not any(i["category"] != "practical" for i in deterministic_extract(advert))


def test_candidate_list_preserves_explicit_qts_blocker():
    advert = HANDOFF + "\nWe'd love to hear from someone who:\n• Qualified Teacher Status.\n• Demonstrates strong leadership."
    items = deterministic_extract(advert)
    assert any(i["category"] == "eligibility" and i["explicit_blocker"] for i in items)
    assert any(i["category"] == "essential" for i in items)


def test_negated_preference_does_not_create_requirement():
    advert = HANDOFF + "\nThe successful candidate will ideally have no experience in the role."
    assert not any(i["category"] != "practical" for i in deterministic_extract(advert))


def test_unbulleted_qts_does_not_end_candidate_list():
    advert = HANDOFF + "\nAbout You\nWe'd love to hear from someone who:\nQualified Teacher Status.\nExperience leading a primary school team."
    items = deterministic_extract(advert)
    assert any(i["category"] == "eligibility" and i["explicit_blocker"] and "Qualified Teacher Status" in i["text"] for i in items)
    assert any(i["category"] == "essential" and "Experience leading" in i["text"] for i in items)


def test_informal_intro_inherits_desirable_scope():
    advert = HANDOFF + "\nDesirable criteria:\nWe'd love to hear from someone who:\n• Qualified Teacher Status."
    items = deterministic_extract(advert)
    qts = [i for i in items if "Qualified Teacher Status" in i["text"]]
    assert len(qts) == 1
    assert qts[0]["category"] == "desirable"
    assert not qts[0]["explicit_blocker"]


def test_inline_preference_does_not_swallow_mandatory_experience():
    advert = HANDOFF + "\nThe successful candidate will ideally have experience in a primary school, but experience working with children is essential."
    items = deterministic_extract(advert)
    assert any(i["category"] == "desirable" and "primary school" in i["text"] for i in items)
    assert any(i["category"] == "essential" and "experience working with children" in i["text"] for i in items)
    assert all(i["source_text"] in advert for i in items)


@pytest.mark.parametrize("heading,expected", [("About You", "essential"), ("Desirable criteria:", "desirable")])
@pytest.mark.parametrize("lead_in", ["You will have:", "You should have:", "The successful candidate will have:"])
def test_recognised_lead_in_does_not_end_informal_scope(heading, expected, lead_in):
    advert = HANDOFF + "\n" + heading + "\nWe'd love to hear from someone who:\n" + lead_in + "\n• Qualified Teacher Status.\n• Experience leading a primary school team."
    items = deterministic_extract(advert)
    qts = [i for i in items if "Qualified Teacher Status" in i["text"]]
    assert len(qts) == 1
    assert qts[0]["category"] == ("eligibility" if expected == "essential" else "desirable")
    assert qts[0]["explicit_blocker"] == (expected == "essential")
    assert any(i["category"] == expected and "Experience leading" in i["text"] for i in items)
    assert not any(i["text"] == lead_in for i in items)
