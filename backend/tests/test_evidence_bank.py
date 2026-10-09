"""Tests for the private Evidence Bank API."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.main import app
from routes import evidence_bank

client = TestClient(app)


class FakeResult:
    def __init__(self, data):
        self.data = data


class FakeTable:
    def __init__(self):
        self.rows = []
        self.operation = "select"
        self.payload = None
        self.filters = []

    def select(self, *args, **kwargs):
        self.operation = "select"
        self.filters = []
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = payload
        self.filters = []
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = payload
        self.filters = []
        return self

    def delete(self):
        self.operation = "delete"
        self.filters = []
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def _matches(self, row):
        return all(row.get(field) == value for field, value in self.filters)

    def execute(self):
        now = datetime.now(timezone.utc).isoformat()
        if self.operation == "insert":
            row = {"id": "ev-1", "created_at": now, "updated_at": now, **self.payload}
            self.rows.append(row)
            return FakeResult([row])

        if self.operation == "update":
            updated = []
            for row in self.rows:
                if self._matches(row):
                    row.update(self.payload)
                    updated.append(dict(row))
            return FakeResult(updated)

        if self.operation == "delete":
            removed = [dict(row) for row in self.rows if self._matches(row)]
            self.rows = [row for row in self.rows if not self._matches(row)]
            return FakeResult(removed)

        return FakeResult([dict(row) for row in self.rows if self._matches(row)])


class FakeClient:
    def __init__(self):
        self.evidence = FakeTable()

    def table(self, name):
        assert name == "evidence_cards"
        return self.evidence


def test_evidence_requires_authentication():
    response = client.get("/evidence")
    assert response.status_code == 401


def test_evidence_crud_is_scoped_to_authenticated_user(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(evidence_bank, "get_supabase_client", lambda: fake)
    headers = {"Authorization": "Bearer valid_token"}

    create = client.post(
        "/evidence",
        headers=headers,
        json={
            "title": "Major freight examination",
            "situation": "Complex operational examination",
            "task": "Assess options and recommend a safe course of action",
            "actions": ["Verified constraints", "Compared alternatives", "Recommended relocation"],
            "outcome": "Examination completed successfully",
            "reflection": "Use a named liaison earlier next time",
            "tags": ["investigation", "risk"],
            "behaviours": ["Making Effective Decisions"],
            "skills": ["decision making", "stakeholder management"],
            "authority_context": "Joint recommendation; senior officer retained final authority",
            "confidence": 90
        }
    )
    assert create.status_code == 201
    assert create.json()["user_id"] == "user_123"

    listed = client.get("/evidence", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.patch("/evidence/ev-1", headers=headers, json={"confidence": 95})
    assert updated.status_code == 200
    assert updated.json()["confidence"] == 95

    removed = client.delete("/evidence/ev-1", headers=headers)
    assert removed.status_code == 200
    assert removed.json() == {"ok": True}


def test_internal_cv_profile_is_hidden_from_evidence_bank(monkeypatch):
    fake = FakeClient()
    now = datetime.now(timezone.utc).isoformat()
    base = {
        "situation": "",
        "task": "",
        "actions": [],
        "outcome": "",
        "reflection": "",
        "tags": [],
        "behaviours": [],
        "skills": [],
        "authority_context": None,
        "confidence": 70,
        "user_id": "user_123",
        "created_at": now,
        "updated_at": now,
    }
    fake.evidence.rows = [
        {"id": "manual-1", "title": "Real example", "source": "manual", **base},
        {"id": "cv-1", "title": "CV profile", "source": "cv_profile", **base},
    ]
    monkeypatch.setattr(evidence_bank, "get_supabase_client", lambda: fake)

    response = client.get("/evidence", headers={"Authorization": "Bearer valid_token"})
    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == ["manual-1"]



def test_statement_import_returns_review_drafts_without_persisting(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(evidence_bank, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(
        evidence_bank,
        "_openai_evidence_import",
        lambda _text, _filename: [
            evidence_bank.EvidenceImportDraft(
                title="Multi-agency operational response",
                situation="An operational incident required coordination with partner agencies.",
                task="I was responsible for maintaining communication and recording updates.",
                actions=["I briefed police and operational colleagues as circumstances changed."],
                outcome="The incident was managed safely.",
                skills=["communication", "teamwork"],
                confidence=55,
                source_excerpt="I briefed police and operational colleagues as circumstances changed.",
            )
        ],
    )

    response = client.post(
        "/evidence/import",
        headers={"Authorization": "Bearer valid_token"},
        files={
            "file": (
                "old-statement.txt",
                (
                    b"During an operational incident I briefed police and operational colleagues "
                    b"as circumstances changed. I maintained accurate records and the incident was "
                    b"managed safely. This example demonstrates communication and teamwork."
                ),
                "text/plain",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_filename"] == "old-statement.txt"
    assert body["extraction_provider"] == "openai"
    assert len(body["drafts"]) == 1
    assert body["drafts"][0]["title"] == "Multi-agency operational response"
    assert body["drafts"][0]["confidence"] == 55
    assert fake.evidence.rows == []


def test_statement_import_star_fallback_is_conservative(monkeypatch):
    monkeypatch.setattr(evidence_bank, "_openai_evidence_import", lambda _text, _filename: None)
    text = b"""
Situation: A time-sensitive operational issue needed a safe response.
Task: I was responsible for checking the available information and escalating within my authority.
Action: I checked the records, contacted the relevant colleagues and documented the decision.
Result: The issue was resolved safely and the required record was completed.
Reflection: I would establish the named liaison earlier next time.
"""

    response = client.post(
        "/evidence/import",
        headers={"Authorization": "Bearer valid_token"},
        files={"file": ("star-example.txt", text, "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["extraction_provider"] == "star-fallback"
    draft = body["drafts"][0]
    assert "time-sensitive operational issue" in draft["situation"]
    assert "checking the available information" in draft["task"]
    assert "contacted the relevant colleagues" in draft["actions"][0]
    assert "resolved safely" in draft["outcome"]


def test_statement_import_rejects_unstructured_text_when_no_ai(monkeypatch):
    monkeypatch.setattr(evidence_bank, "_openai_evidence_import", lambda _text, _filename: None)
    response = client.post(
        "/evidence/import",
        headers={"Authorization": "Bearer valid_token"},
        files={
            "file": (
                "generic.txt",
                b"I am a motivated professional with excellent communication skills. " * 4,
                "text/plain",
            )
        },
    )

    assert response.status_code == 422
    assert "could not reliably identify" in response.json()["detail"].lower()
