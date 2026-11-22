"""Offline tests using only synthetic employer API payloads and fake storage."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest

from lib.greenhouse_ingestion import (
    Board, FeedError, employer_apply_link, excerpt, fetch_board, is_uk_location,
    parse_boards, persist_board, record, run,
)

NOW = datetime(2026, 11, 22, 12, tzinfo=timezone.utc)
BOARD = Board("sampleemployer", "Synthetic Employer")


def job(jid=1234, location="London, United Kingdom", title="Investigator"):
    return {
        "id": jid, "title": title, "updated_at": "2026-11-21T14:00:00Z",
        "location": {"name": location},
        "absolute_url": f"https://job-boards.greenhouse.io/sampleemployer/jobs/{jid}?gh_src=tracker",
        "content": "&lt;p&gt;Help investigate fraud cases.&lt;/p&gt;",
    }


def mock_client(posts):
    def handler(request):
        assert request.url.host == "boards-api.greenhouse.io"
        assert request.url.path == "/v1/boards/sampleemployer/jobs"
        assert request.url.params.get("content") == "true"
        return httpx.Response(200, json={"jobs": posts, "meta": {"total": len(posts)}})
    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)


class Storage:
    def __init__(self):
        self.rows = {}
        self.operation = None
        self.batch = None
        self.filters = []
        self.fail = False

    def table(self, name):
        assert name == "jobs"
        self.filters = []
        return self

    def upsert(self, batch, on_conflict):
        assert on_conflict == "source,source_board,external_id"
        self.operation = "upsert"
        self.batch = batch
        return self

    def select(self, *_args):
        self.operation = "select"
        return self

    def eq(self, field, value):
        self.filters.append(("eq", field, value))
        return self

    def in_(self, field, values):
        self.filters.append(("in", field, values))
        return self

    def lt(self, field, value):
        self.filters.append(("lt", field, value))
        return self

    def update(self, values):
        self.operation = "update"
        self.batch = values
        return self

    def execute(self):
        if self.fail:
            raise RuntimeError("Synthetic Supabase write outage")
        if self.operation == "upsert":
            for row in self.batch:
                k = (row["source"], row["source_board"], row["external_id"])
                self.rows[k] = dict(row)
            return SimpleNamespace(data=list(self.batch))
        found = list(self.rows.values())
        for t, field, value in self.filters:
            if t == "eq":
                found = [x for x in found if x.get(field) == value]
            elif t == "in":
                found = [x for x in found if x.get(field) in value]
            elif t == "lt":
                found = [x for x in found if x.get(field) and x[field] < value]
        if self.operation == "update":
            for x in found:
                x.update(self.batch)
        return SimpleNamespace(data=[dict(x) for x in found])


def test_empty_configuration_is_safe():
    assert parse_boards("") == []
    assert parse_boards("sampleemployer=Synthetic Employer") == [BOARD]
    for invalid in ("../evil=X", "sampleemployer", "foo=X,foo=X", "bad host=Bad"):
        with pytest.raises(FeedError):
            parse_boards(invalid)


def test_uk_only_and_no_invented_salary():
    assert is_uk_location("Remote - United Kingdom")
    assert is_uk_location("London, United Kingdom")
    assert not is_uk_location("London, Ontario, Canada")
    assert not is_uk_location("New York")
    r = record(job(), BOARD, NOW)
    assert r["company"] == "Synthetic Employer"
    assert r["source"] == "greenhouse"
    assert r["description"] == "Help investigate fraud cases."
    assert r["salary"] is None and r["salary_min"] is None
    assert r["url"] == "https://job-boards.greenhouse.io/sampleemployer/jobs/1234"
    assert r["last_seen_at"] == NOW.isoformat()


def test_url_rejects_unsafe_external_redirect():
    assert employer_apply_link("http://job-boards.greenhouse.io/sampleemployer/jobs/1234") is None
    assert employer_apply_link("https://evil.example/jobs/1234") is None
    assert employer_apply_link("https://job-boards.greenhouse.io@evil.example/sampleemployer/jobs/1234") is None


def test_markup_stripped_and_truncated():
    assert excerpt("&lt;p&gt;HELLO&lt;/p&gt;<script>steal()</script>") == "HELLO"
    assert len(excerpt("Z" * 5000)) <= 600


def test_one_uk_post_imported_non_uk_skipped():
    with mock_client([job(), job(998, "New York")]) as client:
        listings, count = fetch_board(BOARD, client, NOW)
    assert count == 2
    assert len(listings) == 1
    assert listings[0]["external_id"] == "1234"


def test_malformed_uk_post_fails_entire_board():
    value = job()
    value["absolute_url"] = "https://not-our-board.example/x"
    with mock_client([value]) as client, pytest.raises(FeedError):
        fetch_board(BOARD, client, NOW)


def test_zero_results_fails_closed():
    with mock_client([]) as client, pytest.raises(FeedError):
        fetch_board(BOARD, client, NOW)


def test_apply_requires_both_explicit_gates():
    with mock_client([job()]) as client, patch.dict("os.environ", {}, clear=True):
        with pytest.raises(FeedError):
            run([BOARD], apply=True, client=client, storage=Storage(), now=NOW)
    with mock_client([job()]) as client, patch.dict("os.environ", {
        "JOBSLEUTH_FEED_RIGHTS_CONFIRMED": "true",
    }, clear=True):
        with pytest.raises(FeedError):
            run([BOARD], apply=True, client=client, storage=Storage(), now=NOW)


def test_dry_run_never_writes():
    store = Storage()
    with mock_client([job()]) as client:
        out = run([BOARD], apply=False, client=client, storage=store, now=NOW)
    assert out[0]["uk_jobs"] == 1
    assert out[0]["applied"] is False
    assert not store.rows


def test_idempotent_upsert_and_expiry_without_deletion():
    store = Storage()
    approved = {"JOBSLEUTH_FEED_RIGHTS_CONFIRMED": "true", "JOBSLEUTH_INGEST_ENABLED": "true"}
    with patch.dict("os.environ", approved, clear=True):
        with mock_client([job(), job(4567, title="Fraud Analyst")]) as client:
            assert run([BOARD], apply=True, client=client, storage=store, now=NOW)[0]["upserted"] == 2
        with mock_client([job(), job(4567, title="Fraud Analyst")]) as client:
            run([BOARD], apply=True, client=client, storage=store, now=NOW + timedelta(hours=24))
        assert len(store.rows) == 2
        # Exactly 72h since last seen must NOT expire; only strictly older
        # listings become inactive after a complete successful source scan.
        with mock_client([job()]) as client:
            run([BOARD], apply=True, client=client, storage=store, now=NOW + timedelta(hours=96))
        assert store.rows[("greenhouse", "sampleemployer", "4567")]["is_active"] is True
        with mock_client([job()]) as client:
            run([BOARD], apply=True, client=client, storage=store, now=NOW + timedelta(hours=97))
    removed = store.rows[("greenhouse", "sampleemployer", "4567")]
    assert removed["is_active"] is False
    assert store.rows[("greenhouse", "sampleemployer", "1234")]["is_active"] is True


def test_failed_upsert_never_deactivates():
    store = Storage()
    store.fail = True
    approved = {"JOBSLEUTH_FEED_RIGHTS_CONFIRMED": "true", "JOBSLEUTH_INGEST_ENABLED": "true"}
    with patch.dict("os.environ", approved, clear=True), mock_client([job()]) as client:
        with pytest.raises(RuntimeError):
            run([BOARD], apply=True, client=client, storage=store, now=NOW)
