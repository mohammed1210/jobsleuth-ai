from fastapi.testclient import TestClient

from backend.main import app
from lib.vacancy_ai import _validate_item
from lib.vacancy_extraction import deterministic_extract
from routes.vacancy_intelligence import _reconcile_items

client = TestClient(app)
HEADERS = {"Authorization": "Bearer valid_token"}

VACANCY = """
Eligibility:
- Applicants must have the right to work in the UK.

Essential criteria:
- Experience analysing complex information and making recommendations.
- You must demonstrate effective stakeholder management.

Desirable:
- Fraud investigation experience is desirable.

Training:
- Successful candidates will receive training in the internal casework system.
- Role-specific legislation and procedures will be taught during training.

Working pattern:
- The role requires a minimum of 30 hours per week across 4 days.
"""


def test_deterministic_extraction_groups_grounded_requirements():
    items = deterministic_extract(VACANCY)
    categories = {item["category"] for item in items}

    assert {"eligibility", "essential", "desirable", "practical", "trainable"}.issubset(categories)
    eligibility = next(item for item in items if item["category"] == "eligibility")
    assert eligibility["explicit_blocker"] is True
    assert eligibility["source_text"] in VACANCY
    assert all(item["source_text"] in VACANCY for item in items)


def test_normal_essential_must_language_is_not_a_hard_blocker():
    items = deterministic_extract(VACANCY)
    stakeholder = next(item for item in items if "stakeholder management" in item["text"].lower())

    assert stakeholder["category"] == "essential"
    assert stakeholder["explicit_blocker"] is False


def test_training_language_including_will_be_taught_is_captured():
    items = deterministic_extract(VACANCY)
    trainable = [item for item in items if item["category"] == "trainable"]

    assert len(trainable) == 2
    assert any("will receive training" in item["text"].lower() for item in trainable)
    assert any("will be taught" in item["text"].lower() for item in trainable)


def test_ai_validation_rejects_ungrounded_source_text():
    raw = {
        "text": "Five years of management experience",
        "category": "essential",
        "source_text": "Five years of management experience is required.",
        "confidence": 0.9,
        "explicit_blocker": True,
    }
    assert _validate_item(raw, VACANCY) is None


def test_ai_validation_does_not_promote_normal_essential_to_hard_blocker():
    source = "You must demonstrate effective stakeholder management."
    raw = {
        "text": source,
        "category": "essential",
        "source_text": source,
        "confidence": 0.9,
        "explicit_blocker": True,
    }

    item = _validate_item(raw, VACANCY)
    assert item is not None
    assert item["explicit_blocker"] is False


def test_reconcile_supplements_semantic_omissions_without_duplicates():
    deterministic = deterministic_extract(VACANCY)
    semantic = [
        {
            "text": "Applicants must have the right to work in the UK.",
            "category": "eligibility",
            "source_text": "Applicants must have the right to work in the UK.",
            "confidence": 1.0,
            "explicit_blocker": True,
        },
        {
            "text": "Experience analysing complex information and making recommendations.",
            "category": "essential",
            "source_text": "Experience analysing complex information and making recommendations.",
            "confidence": 1.0,
            "explicit_blocker": False,
        },
    ]

    merged, provider = _reconcile_items(semantic, deterministic)

    assert provider == "hybrid-grounded-v3"
    assert len(merged) == len(deterministic)
    assert sum(1 for item in merged if "right to work" in item["text"].lower()) == 1
    assert any("stakeholder management" in item["text"].lower() for item in merged)
    assert len([item for item in merged if item["category"] == "trainable"]) == 2


def test_reconcile_uses_deterministic_when_semantic_unavailable():
    deterministic = deterministic_extract(VACANCY)
    merged, provider = _reconcile_items(None, deterministic)

    assert provider == "deterministic-v2"
    assert merged == deterministic


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


def test_route_supplements_under_extracted_semantic_result(monkeypatch):
    monkeypatch.setattr(
        "routes.vacancy_intelligence.semantic_extract",
        lambda _text: [
            {
                "text": "Applicants must have the right to work in the UK.",
                "category": "eligibility",
                "source_text": "Applicants must have the right to work in the UK.",
                "confidence": 1.0,
                "explicit_blocker": True,
            }
        ],
    )

    response = client.post(
        "/vacancy-intelligence",
        headers=HEADERS,
        json={"vacancy_text": VACANCY},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "hybrid-grounded-v3"
    assert data["summary"]["items"] >= 7
    assert len([item for item in data["requirements"] if item["category"] == "trainable"]) == 2