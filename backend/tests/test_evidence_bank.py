"""Tests for the private Evidence Bank API."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.main import app
from backend.routes import evidence_bank

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

    def order(self, *args, **kwargs):
        return self

    def _matches(self, row):
        return all(row.get(field) == value for field, value in self.filters)

    def execute(self):
        now = datetime.now(timezone.utc).isoformat()
        if self.operation == "insert":
            row = {
                "id": "ev-1",
                "created_at": now,
                "updated_at": now,
                **self.payload,
            }
            self.rows.append(row)
            return FakeResult([row])

        if self.operation == "update":
            updated = []
            for row in self.rows:
                if self._matches(row):
                    row.update(self.payload)
                    row["updated_at"] = now
                    updated.append(dict(row))
            return FakeResult(updated)

        if self.operation == "delete":
            deleted = [dict(row) for row in self.rows if self._matches(row)]
            self.rows = [row for row in self.rows if not self._matches(row)]
            return FakeResult(deleted)

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
            "confidence": 90,
        },
    )
    assert create.status_code == 201
    created = create.json()
    assert created["id"] == "ev-1"
    assert created["user_id"] == "user_123"
    assert created["confidence"] == 90

    listed = client.get("/evidence", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["title"] == "Major freight examination"

    updated = client.patch(
        "/evidence/ev-1",
        headers=headers,
        json={"confidence": 95, "reflection": "Improved contingency planning"},
    )
    assert updated.status_code == 200
    assert updated.json()["confidence"] == 95

    deleted = client.delete("/evidence/ev-1", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json() == {"ok": True}

    empty = client.get("/evidence", headers=headers)
    assert empty.status_code == 200
    assert empty.json() == []
