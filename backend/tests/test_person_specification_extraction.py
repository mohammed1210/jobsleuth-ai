from lib.vacancy_extraction import deterministic_extract
from routes.vacancy_intelligence import _reconcile_items


def test_person_specification_bullets_default_to_essential_until_new_section():
    advert = """
Person specification
We are looking for a candidate who is:
- Motivated and able to take responsibility for your personal performance and delivering your work objectives.
- A team player who can contribute to the success of the team and to IPCO's wider goals and objectives. You should be adaptable and willing to consider a diverse range of views, working collaboratively to resolve challenging issues.
- Well organised and efficient, able to prioritise different pieces of work with different deadlines.
Security Clearance
You must hold DV Clearance to be eligible to apply for this EOI.
"""

    items = deterministic_extract(advert)
    essential_texts = [item["text"] for item in items if item["category"] == "essential"]
    eligibility_texts = [item["text"] for item in items if item["category"] == "eligibility"]

    assert "Motivated and able to take responsibility for your personal performance and delivering your work objectives." in essential_texts
    assert any(text.startswith("A team player who can contribute") for text in essential_texts)
    assert "Well organised and efficient, able to prioritise different pieces of work with different deadlines." in essential_texts
    assert "We are looking for a candidate who is:" not in essential_texts
    assert "You must hold DV Clearance to be eligible to apply for this EOI." in eligibility_texts


def test_deterministic_section_classification_wins_same_text_category_conflict():
    text = "You should be adaptable and willing to consider a diverse range of views, working collaboratively to resolve challenging issues."
    semantic = [{
        "text": text,
        "category": "desirable",
        "source_text": text,
        "confidence": 1.0,
        "explicit_blocker": False,
    }]
    deterministic = [{
        "text": text,
        "category": "essential",
        "source_text": text,
        "confidence": 0.9,
        "explicit_blocker": False,
    }]

    merged, provider = _reconcile_items(semantic, deterministic)

    assert len(merged) == 1
    assert merged[0]["category"] == "essential"
    assert provider == "hybrid-grounded-v4"
