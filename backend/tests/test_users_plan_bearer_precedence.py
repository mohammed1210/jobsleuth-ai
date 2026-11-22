"""User profile endpoints cannot accept arbitrary bearer strings or fake writes."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.main import app
from routes import users

client = TestClient(app)
UID = "00000000-0000-4000-8000-000000000123"


class Storage:
    def __init__(self):
        self.rows = []
        self.operation = "select"
        self.payload = None
        self.fail = False

    def table(self, name):
        assert name == "user_profiles"
        return self

    def select(self, *_args):
        self.operation = "select"
        return self

    def eq(self, *_args):
        return self

    def limit(self, *_args):
        return self

    def upsert(self, payload, **_kwargs):
        self.operation = "upsert"
        self.payload = payload
        return self

    def execute(self):
        if self.fail:
            raise RuntimeError("synthetic storage outage")
        if self.operation == "upsert":
            self.rows = [{**self.payload, "created_at": "2026-11-21T00:00:00Z"}]
            return SimpleNamespace(data=self.rows)
        return SimpleNamespace(data=list(self.rows))


@pytest.fixture
def db(monkeypatch):
    storage = Storage()

    async def verified(header):
        if header != "Bearer valid_token":
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return {"id": UID, "email": "test@example.org"}

    monkeypatch.setattr(users, "verify_supabase_user", verified)
    monkeypatch.setattr(users, "get_supabase_client", lambda: storage)
    return storage


def test_plan_rejects_unverified_bearer():
    res = client.get("/users/me/plan", headers={"Authorization": "Bearer valid_token"})
    assert res.status_code in (401, 503)
    assert res.json().get("plan") != "pro"


def test_plan_missing_token_rejected():
    assert client.get("/users/me/plan").status_code == 401


def test_user_routes_missing_token_rejected():
    assert client.get("/users/me").status_code == 401
    assert client.put("/users/me", json={"name":"Synthetic"}).status_code == 401


def test_get_real_profile_no_mock_person(db):
    res = client.get("/users/me", headers={"Authorization": "Bearer valid_token"})
    assert res.status_code == 200
    assert res.json() == {"user_id": UID, "email": "test@example.org",
                          "name": None, "desired_title": None,
                          "location": None, "created_at": None}


def test_update_is_persisted_before_reporting_success(db):
    h = {"Authorization": "Bearer valid_token"}
    res = client.put("/users/me", json={"name":"Synthetic Test"}, headers=h)
    assert res.status_code == 200
    assert res.json()["updated_fields"] == ["full_name"]
    assert db.rows[0]["full_name"] == "Synthetic Test"
    assert client.get("/users/me", headers=h).json()["name"] == "Synthetic Test"


def test_profile_storage_failure_fails_closed(db):
    db.fail = True
    h = {"Authorization": "Bearer valid_token"}
    assert client.get("/users/me", headers=h).status_code == 503
    assert client.put("/users/me", json={"name":"Synthetic"}, headers=h).status_code == 503


def test_unknown_profile_field_rejected(db):
    response = client.put("/users/me", json={"subscription_status":"pro"},
                          headers={"Authorization": "Bearer valid_token"})
    assert response.status_code in (422, 503)
