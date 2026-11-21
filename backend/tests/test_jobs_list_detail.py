"""Job listing API: real-table semantics; never return fictional fallback data."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from routes import jobs

client = TestClient(app)


class PublicJobs:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.fail = False

    def table(self, name):
        assert name == "jobs"
        return JobQuery(self)


class JobQuery:
    def __init__(self, database):
        self.database = database
        self.filters = []
        self.window = None
        self.count_requested = False
        self.sort_columns = []

    def select(self, _columns, count=None):
        self.count_requested = count == "exact"
        return self

    def or_(self, expression):
        self.filters.append(("search", expression))
        return self

    def ilike(self, field, value):
        self.filters.append(("ilike", field, value))
        return self

    def gte(self, field, value):
        self.filters.append(("gte", field, value))
        return self

    def eq(self, field, value):
        self.filters.append(("eq", field, value))
        return self

    def order(self, field, desc=False):
        assert field in ("created_at", "id") and desc
        self.sort_columns.append(field)
        return self

    def range(self, start, end):
        self.window = (start, end)
        return self

    def limit(self, value):
        self.window = (0, value - 1)
        return self

    def execute(self):
        if self.database.fail:
            raise RuntimeError("synthetic database outage")
        rows = list(self.database.rows)
        for filt in self.filters:
            kind = filt[0]
            if kind == "eq":
                rows = [r for r in rows if r.get(filt[1]) == filt[2]]
            elif kind == "gte":
                rows = [r for r in rows if r.get(filt[1]) is not None and r[filt[1]] >= filt[2]]
            elif kind == "ilike":
                query = filt[2].replace("%", "").casefold()
                rows = [r for r in rows if r.get(filt[1]) and query in r[filt[1]].casefold()]
            elif kind == "search":
                # Fixed structure asserted, not an arbitrary remote expression.
                expression = filt[1]
                assert expression.startswith("title.ilike.%")
                assert ",company.ilike.%" in expression
                query = expression.split("title.ilike.%", 1)[1].split("%,company.ilike.", 1)[0]
                rows = [r for r in rows if query.casefold() in r["title"].casefold() or query.casefold() in r["company"].casefold()]
        assert self.sort_columns in ([], ["created_at", "id"])
        rows.sort(key=lambda r: (r["created_at"], r["id"]), reverse=True)
        count = len(rows)
        if self.window:
            start, end = self.window
            rows = rows[start:end + 1]
        from types import SimpleNamespace
        return SimpleNamespace(data=rows, count=count if self.count_requested else None)


@pytest.fixture
def db(monkeypatch):
    database = PublicJobs()
    monkeypatch.setattr(jobs, "get_supabase_anon_client", lambda: database)
    return database


def row(job_id=9, title="Public sector investigator", company="Example Agency", salary_max=60000):
    return {"id": job_id, "title": title, "company": company, "location": "London",
            "salary": None, "salary_min": 40000, "salary_max": salary_max,
            "role_type": "Hybrid", "source": "synthetic", "url": "https://example.org/vacancy",
            "description": "Synthetic data only", "created_at": "2026-11-21T00:00:00Z"}


def test_empty_database_returns_no_jobs(db):
    resp = client.get("/jobs")
    assert resp.status_code == 200
    assert resp.json() == {"jobs": [], "total": 0, "page": 1, "per_page": 10}
    assert client.get("/jobs/1").status_code == 404


def test_list_and_get_real_rows(db):
    db.rows = [row()]
    res = client.get("/jobs")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["jobs"][0]["id"] == 9
    assert data["jobs"][0]["ai_score"] is None
    assert data["jobs"][0]["date_posted"] is None
    assert client.get("/jobs/9").json()["title"] == "Public sector investigator"


def test_company_title_location_and_salary_filters(db):
    db.rows = [row(1, title="Project manager", company="Council A"),
               row(2, title="Operations specialist", company="Agency B", salary_max=30000)]
    assert client.get("/jobs?q=project").json()["total"] == 1
    assert client.get("/jobs?q=Agency").json()["jobs"][0]["id"] == 2
    assert client.get("/jobs?location=london").json()["total"] == 2
    assert client.get("/jobs?role_type=hybrid").json()["total"] == 2
    assert client.get("/jobs?salary_min=50000").json()["jobs"][0]["id"] == 1
    assert client.get("/jobs?q=project&salary_min=50000").json()["total"] == 1


def test_pagination_uses_exact_db_total(db):
    db.rows = [row(1), row(2), row(3)]
    res = client.get("/jobs?page=2&per_page=2")
    assert res.status_code == 200
    assert res.json()["total"] == 3
    assert len(res.json()["jobs"]) == 1
    page_one = client.get("/jobs?page=1&per_page=2").json()["jobs"]
    page_two = res.json()["jobs"]
    # Same created_at batch timestamp: ID is a unique and stable tie-breaker.
    assert [job["id"] for job in page_one] == [3, 2]
    assert [job["id"] for job in page_two] == [1]
    assert set(job["id"] for job in page_one).isdisjoint(
        job["id"] for job in page_two
    )


@pytest.mark.parametrize("search", ["Lead,role", "test)or(title.eq.x)", "100%", "Developer.name", "foo_bar", "foo\nbar"])
def test_postgrest_filter_injection_rejected(db, search):
    res = client.get("/jobs", params={"q": search})
    assert res.status_code == 422


def test_unavailable_db_does_not_show_mock_jobs(db):
    db.fail = True
    assert client.get("/jobs").status_code == 503
    assert client.get("/jobs/1").status_code == 503


def test_no_credentials_provided_is_unavailable(monkeypatch):
    from lib.settings import settings
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    monkeypatch.setattr(jobs, "get_supabase_anon_client", __import__("lib.supabase", fromlist=["get_supabase_anon_client"]).get_supabase_anon_client)
    assert client.get("/jobs").status_code == 503
