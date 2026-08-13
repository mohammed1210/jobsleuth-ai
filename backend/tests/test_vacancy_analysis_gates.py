from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)
HEADERS = {"Authorization": "Bearer valid_token"}


def base_payload():
    return {
        "job": {"title": "Operations Officer"},
        "requirements": [
            {"text": "confident decision making", "category": "essential"},
        ],
        "evidence_cards": [
            {"id": "ev-1", "title": "Decision example", "skills": ["confident decision making"]}
        ],
    }


def test_practical_issue_changes_apply_to_consider():
    payload = base_payload()
    payload["practical_issues"] = ["Working pattern needs checking"]
    data = client.post("/vacancy-analysis", headers=HEADERS, json=payload).json()
    assert data["decision"] == "CONSIDER"
    assert data["practical_fit"]["status"] == "concern"


def test_missing_hard_requirement_returns_skip():
    payload = base_payload()
    payload["requirements"].append(
        {"text": "mandatory professional licence", "category": "essential", "blocker": True}
    )
    data = client.post("/vacancy-analysis", headers=HEADERS, json=payload).json()
    assert data["decision"] == "SKIP"
    assert data["requirements"][-1]["status"] == "gap"
