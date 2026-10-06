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
            {
                "id": "ev-1",
                "title": "Decision example",
                "skills": ["confident decision making"],
                "actions": ["I reviewed the evidence and made a confident decision."],
                "outcome": "The decision resolved the issue safely.",
            }
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
    assert data["requirements"][-1]["match_strength"] in {"weak", "missing"}


def test_unconfirmed_mandatory_eligibility_returns_consider():
    payload = base_payload()
    payload["requirements"].insert(
        0,
        {
            "text": "Valid SIA licence",
            "category": "eligibility",
            "blocker": True,
            "eligibility_answer": "unsure",
        },
    )
    data = client.post("/vacancy-analysis", headers=HEADERS, json=payload).json()
    assert data["decision"] == "CONSIDER"
    eligibility = data["requirements"][0]
    assert eligibility["status"] == "unconfirmed"
    assert "needs to be confirmed" in data["decision_reasons"][0].lower()


def test_failed_mandatory_eligibility_returns_skip():
    payload = base_payload()
    payload["requirements"].insert(
        0,
        {
            "text": "Valid UK driving licence",
            "category": "eligibility",
            "blocker": True,
            "eligibility_answer": "no",
        },
    )
    data = client.post("/vacancy-analysis", headers=HEADERS, json=payload).json()
    assert data["decision"] == "SKIP"
    assert data["requirements"][0]["status"] == "not-met"


def test_confirmed_eligibility_does_not_block_apply():
    payload = base_payload()
    payload["requirements"].insert(
        0,
        {
            "text": "Valid UK driving licence",
            "category": "eligibility",
            "blocker": True,
            "eligibility_answer": "yes",
        },
    )
    data = client.post("/vacancy-analysis", headers=HEADERS, json=payload).json()
    assert data["requirements"][0]["status"] == "met"
    assert data["decision"] == "APPLY"
