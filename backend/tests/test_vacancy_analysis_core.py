from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)
HEADERS = {"Authorization": "Bearer valid_token"}


def payload():
    return {
        "job": {"title": "Operations Officer"},
        "requirements": [
            {"text": "confident decision making", "category": "essential"},
            {"text": "role specific training", "category": "trainable"},
        ],
        "evidence_cards": [
            {
                "id": "ev-1",
                "title": "Operational decision",
                "skills": ["confident decision making"],
                "actions": ["I reviewed the available information and made a confident decision."],
                "outcome": "The decision resolved the operational issue safely.",
            }
        ],
    }


def test_requires_authentication():
    assert client.post("/vacancy-analysis", json=payload()).status_code == 401


def test_apply_with_supported_essential_requirement():
    response = client.post("/vacancy-analysis", headers=HEADERS, json=payload())
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "APPLY"
    assert data["requirements"][0]["status"] == "met"
    assert data["requirements"][0]["match_strength"] == "strong"
    assert data["requirements"][1]["status"] == "trainable"
