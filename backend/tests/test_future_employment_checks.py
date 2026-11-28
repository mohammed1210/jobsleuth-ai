"""Offer screening is not a credential already held by a candidate."""
import pytest

from lib.vacancy_extraction import deterministic_extract, is_future_employment_check
from routes.vacancy_intelligence import _reconcile_items


CHECK = ("Our trust promotes safeguarding. An offer of employment will be subject to "
         "pre-employment checks including ID, right to work, satisfactory written references, "
         "occupational health check and a successful Enhanced DBS check.")


def test_receptionist_offer_checks_are_not_present_eligibility():
    advert = "Eligibility:\nYou must have the right to work in the UK.\n" + CHECK
    items = deterministic_extract(advert)
    assert [i["text"] for i in items if i["category"] == "eligibility"] == [
        "You must have the right to work in the UK."]
    assert any(i["text"] == CHECK and i["category"] == "practical"
               and not i["explicit_blocker"] for i in items)


def test_hybrid_corrects_semantic_misclassification_without_inventing_checks():
    deterministic = deterministic_extract(CHECK)
    semantic = [{"text": "Must have an Enhanced DBS check", "source_text": CHECK,
                 "category": "eligibility", "explicit_blocker": True, "confidence": 0.95}]
    merged, _ = _reconcile_items(semantic, deterministic)
    assert len(merged) == 1
    assert merged[0]["text"] == CHECK
    assert merged[0]["category"] == "practical"
    assert merged[0]["explicit_blocker"] is False


@pytest.mark.parametrize("text", [
    "You must hold a current Enhanced DBS certificate.",
    "A valid security clearance is required.",
    "Experience preparing employment references for candidates.",
    "You must have the right to work in the UK.",
    "You must already hold a driving licence and appointment is subject to DBS checks.",
    "A full UK driving licence is essential and appointment is subject to Enhanced DBS checks.",
    "All successful candidates will be required to undergo Full Police Vetting",
])
def test_current_or_mixed_requirements_are_not_demoted(text):
    assert not is_future_employment_check(text)


@pytest.mark.parametrize("text", [
    "Job offers are subject to Enhanced DBS clearance.",
    "The successful candidate must undergo occupational health checks.",
    "Appointment is conditional on satisfactory employment references.",
])
def test_explicit_future_screening_is_not_current_eligibility(text):
    assert is_future_employment_check(text)
    items = deterministic_extract("Eligibility:\n" + text)
    assert len(items) == 1
    assert items[0]["category"] == "practical"
    assert not items[0]["explicit_blocker"]


@pytest.mark.parametrize("criterion", [
    "Experience carrying out pre-employment checks.",
    "Experience administering pe-employment checks.",
    "You will be required to conduct pre-employment checks.",
])
def test_screening_work_is_not_applicant_screening(criterion):
    assert not is_future_employment_check(criterion)
    items = deterministic_extract("Essential criteria:\n" + criterion)
    assert any(i["category"] == "essential" and i["text"] == criterion for i in items)
    semantic = [{"text": criterion, "source_text": criterion, "category": "essential",
                 "explicit_blocker": False, "confidence": 0.95}]
    merged, _ = _reconcile_items(semantic, items)
    assert any(i["category"] == "essential" and i["text"] == criterion for i in merged)


def test_mixed_mandatory_licence_remains_blocker():
    text = "A full UK driving licence is essential and appointment is subject to Enhanced DBS checks."
    items = deterministic_extract("Eligibility:\n" + text)
    assert any(i["category"] == "eligibility" and i["explicit_blocker"] for i in items)
