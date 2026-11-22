"""Stage 3 Saved Jobs requires real Auth and persistence, not sample success."""
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.main import app
from lib.settings import settings
from routes import saved_jobs

client = TestClient(app)
UID = "00000000-0000-4000-8000-000000000123"


class Query:
    def __init__(self, storage, name):
        self.storage, self.name, self.operation = storage, name, "select"
        self.filters = []
        self.payload = None

    def select(self, *_args):
        self.operation = "select"
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def limit(self, _limit):
        return self

    def upsert(self, payload, **_kwargs):
        self.operation = "upsert"
        self.payload = payload
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def execute(self):
        if self.storage.fail:
            raise RuntimeError("synthetic storage outage")
        if self.name == "live_jobs":
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            match = next((j for j in self.storage.jobs
                          if all(j.get(k)==v for k,v in self.filters)
                          and j.get("is_active", True)
                          and (not j.get("expires_at") or
                               datetime.fromisoformat(j["expires_at"].replace("Z", "+00:00")) > now)), None)
            return SimpleNamespace(data=[{"id": match["id"]}] if match else [])
        rows = self.storage.saved
        if self.operation == "upsert":
            existing = next((x for x in rows if x["user_id"] == self.payload["user_id"] and x["job_id"] == self.payload["job_id"]), None)
            if existing is None:
                existing = {"id": len(rows)+1, "saved_at": "2026-11-21T00:00:00Z", **self.payload}
                rows.append(existing)
            return SimpleNamespace(data=[existing])
        if self.operation == "delete":
            self.storage.saved = [x for x in rows if not all(x.get(k)==v for k,v in self.filters)]
            return SimpleNamespace(data=[])
        matching = [x for x in rows if all(x.get(k)==v for k,v in self.filters)]
        return SimpleNamespace(data=[{**x, "jobs": next((j for j in self.storage.jobs if j["id"]==x["job_id"]), None)} for x in matching])


class Storage:
    def __init__(self):
        self.saved = []
        self.jobs = [{"id": 4, "title": "Synthetic job", "company": "Example", "location": "Remote", "is_active": True}]
        self.fail = False

    def table(self, name):
        assert name in {"live_jobs", "saved_jobs"}
        return Query(self, name)


@pytest.fixture
def storage(monkeypatch):
    db = Storage()

    async def verified(header):
        if header != "Bearer valid_token":
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": UID, "email": "test@example.org"}

    monkeypatch.setattr(saved_jobs, "verify_supabase_user", verified)
    monkeypatch.setattr(saved_jobs, "get_supabase_client", lambda: db)
    return db


def test_unauthenticated_cannot_save_jobs():
    assert client.post("/saved", json={"job_id": 4}).status_code == 401
    assert client.get("/saved-jobs").status_code == 401


def test_invalid_token_rejected():
    assert client.get("/saved", headers={"Authorization": "Bearer invalid"}).status_code == 401
    assert client.get("/saved", headers={"Authorization": "valid_token"}).status_code == 401


def test_unconfigured_auth_fails_closed(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    assert client.get("/saved", headers={"Authorization": "Bearer valid_token"}).status_code == 503


def test_empty_saved_jobs_are_empty_not_sample(storage):
    response = client.get("/saved", headers={"Authorization": "Bearer valid_token"})
    assert response.status_code == 200
    assert response.json() == []


def test_authenticated_save_list_delete_real_persistence(storage):
    h = {"Authorization": "Bearer valid_token"}
    saved = client.post("/saved", json={"job_id": 4}, headers=h)
    assert saved.status_code == 200
    assert saved.json()["job_id"] == 4
    assert len(storage.saved) == 1
    listed = client.get("/saved-jobs", headers=h)
    assert listed.status_code == 200
    assert listed.json()[0]["job"]["title"] == "Synthetic job"
    removed = client.delete("/saved/4", headers=h)
    assert removed.status_code == 200
    assert storage.saved == []
    assert client.get("/saved-jobs", headers=h).json() == []


def test_unknown_job_does_not_report_saved(storage):
    response = client.post("/saved-jobs", json={"job_id": 9999},
                           headers={"Authorization": "Bearer valid_token"})
    assert response.status_code == 404
    assert storage.saved == []


def test_closed_job_cannot_be_newly_saved(storage):
    storage.jobs[0]["is_active"] = False
    response = client.post("/saved-jobs", json={"job_id": 4},
                           headers={"Authorization": "Bearer valid_token"})
    assert response.status_code == 404
    assert storage.saved == []


def test_expired_advert_cannot_be_saved_even_if_active_flag_stale(storage):
    storage.jobs[0]["expires_at"] = "2026-01-01T00:00:00Z"
    response = client.post("/saved-jobs", json={"job_id": 4},
                           headers={"Authorization": "Bearer valid_token"})
    assert response.status_code == 404
    assert storage.saved == []


def test_expired_saved_history_is_still_visible(storage):
    storage.saved.append({"id": 99, "user_id": UID, "job_id": 4,
                          "saved_at": "2026-11-20T00:00:00Z"})
    storage.jobs[0]["expires_at"] = "2026-01-01T00:00:00Z"
    response = client.get("/saved-jobs", headers={"Authorization": "Bearer valid_token"})
    assert response.status_code == 200
    assert response.json()[0]["job"]["expires_at"] == "2026-01-01T00:00:00Z"


def test_storage_failures_return_503_without_sample(storage):
    storage.fail = True
    h = {"Authorization": "Bearer valid_token"}
    assert client.get("/saved", headers=h).status_code == 503
    assert client.post("/saved", json={"job_id": 4}, headers=h).status_code == 503
    assert client.delete("/saved/4", headers=h).status_code == 503


def test_verified_auth_provider_rejects_error_or_missing_configuration(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    with pytest.raises(HTTPException) as exc:
        import asyncio
        asyncio.run(saved_jobs.verify_supabase_user("Bearer arbitrary"))
    assert exc.value.status_code == 503
