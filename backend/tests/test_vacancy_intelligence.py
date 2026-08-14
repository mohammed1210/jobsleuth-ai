from fastapi.testclient import TestClient

from backend.lib.vacancy_ai import _validate_item
from backend.lib.vacancy_extraction import deterministic_extract
from backend.main import app

client = TestClient(app)
HEADERS = {"Authorization": "Bearer valid_token"}

VACANCY = """
Eligibility:
- Applicants must have the right to work in the UK.

Essential criteria:
- Experience analysing complex information and making recommendations.
- Ability to work with multiple stakeholders.

Desirable:
- Fraud investigation experience is desirable.

Working pattern:
- The role requires a minimum of 30 hours per week across 4 days.
- Full training will be provided on the internal casework system.
"""


def test_deterministic_extraction_groups_grounded_requirements():
    items = deterministic_extract(VACANCY)
    categories = {item["category"] for item in items}

    assert {"eligibility", "essential", "desirable", "practical", "trainable"}.issubset(categories)
    eligibility = next(item for item in items if item["category"] == "eligibility")
    assert eligibility["explicit_blocker"] is True
    assert eligibility["source_text"] in VACANCY
    assert all(item["source_text"] in VACANCY for item in items)


def test_ai_validation_rejects_ungrounded_source_text():
    raw = {
        "text": "Five years of management experience",
        "category": "essential",
        "source_text": "Five years of management experience is required.",
        "confidence": 0.9,
        "explicit_blocker": True,
    }
    assert _validate_item(raw, VACANCY) is None


def test_route_requires_authentication():
    response = client.post("/vacancy-intelligence", json={"vacancy_text": VACANCY})
    assert response.status_code == 401


def test_route_returns_structured_fallback(monkeypatch):
    monkeypatch.setattr("routes.vacancy_intelligence.semantic_extract", lambda _text: None)

    response = client.post(
        "/vacancy-intelligence",
        headers=HEADERS,
        json={"vacancy_text": VACANCY},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "deterministic-v2"
    assert data["eligibility"]
    assert data["requirements"]
    assert data["practical"]
    assert data["summary"]["items"] == len(data["eligibility"]) + len(data["requirements"]) + len(data["practical"])
    assert all("source_text" in item and "confidence" in item for item in data["requirements"])
