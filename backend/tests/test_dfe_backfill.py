"""Offline contract checks for conservative existing-job DfE enrichment."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest

from lib.dfe_backfill import enrich_existing, fetch_one
from lib.dfe_ingestion import FeedError

NOW = datetime(2026, 11, 23, tzinfo=timezone.utc)
SLUG = "fictional-support-vacancy"
LINK = f"https://teaching-vacancies.service.gov.uk/jobs/{SLUG}"


def publisher_job(slug=SLUG):
    return {
        "@type": "JobPosting",
        "title": "Support assistant",
        "datePosted": "2026-11-20",
        "validThrough": "2026-12-03T09:00:00Z",
        "description": "<p>" + ("Support students safely. " * 70) + "</p>",
        "url": f"https://teaching-vacancies.service.gov.uk/jobs/{slug}",
        "hiringOrganization": {"name": "Synthetic School"},
        "jobLocation": {"address": {"addressCountry": "GB", "addressLocality": "London"}},
        "baseSalary": {
            "currency": "GBP", "value": {"unitText": "YEAR", "value": "£23,000 - £25,500"}
        },
        "employmentType": ["FULL_TIME"],
    }


def mock_http(payload=None, status=200):
    def responder(request):
        assert request.url.host == "teaching-vacancies.service.gov.uk"
        assert request.url.path == f"/api/v1/jobs/{SLUG}.json"
        assert request.headers["referer"] == "https://jobsleuth-ai.vercel.app/"
        return httpx.Response(status, json=payload or publisher_job())
    return httpx.Client(transport=httpx.MockTransport(responder), follow_redirects=False)


class Store:
    def __init__(self):
        self.rows = [{
            "id": 77,
            "external_id": SLUG,
            "source": "dfe_teaching_vacancies",
            "source_board": "england",
            "url": LINK,
            "salary": None,
            "description": "Old 600-character excerpt." * 20,
        }]
        self.updates = []
        self.action = "read"
        self.patch = None

    def table(self, name):
        assert name == "jobs"
        return self

    def select(self, *args):
        self.action = "read"
        return self

    def eq(self, field, value):
        return self

    def order(self, *args):
        return self

    def limit(self, number):
        return self

    def update(self, patch):
        self.action = "update"
        self.patch = patch
        return self

    def execute(self):
        if self.action == "read":
            return SimpleNamespace(data=self.rows)
        self.updates.append(self.patch)
        return SimpleNamespace(data=[{"id": 77}])


def test_existing_job_dry_run_reports_changes_without_writes():
    store = Store()
    with mock_http() as client:
        summary = enrich_existing(client=client, storage=store, pause_seconds=0)
    assert summary["scanned_existing"] == 1
    assert summary["salary_available"] == 1
    assert summary["descriptions_extended"] == 1
    assert summary["updated_existing"] == 0
    assert not store.updates


def test_backfill_apply_requires_all_four_private_flags():
    store = Store()
    with mock_http() as client, patch.dict("os.environ", {}, clear=True):
        with pytest.raises(FeedError, match="disabled"):
            enrich_existing(client=client, storage=store, apply=True, pause_seconds=0)
    assert not store.updates


def test_backfill_only_updates_existing_records_and_keeps_ids():
    flags = {
        "JOBSLEUTH_INGEST_ENABLED": "true",
        "JOBSLEUTH_DFE_INGEST_ENABLED": "true",
        "JOBSLEUTH_DFE_OGL_TERMS_ACK": "true",
        "JOBSLEUTH_DFE_BACKFILL_ENABLED": "true",
    }
    store = Store()
    with mock_http() as client, patch.dict("os.environ", flags, clear=True):
        summary = enrich_existing(client=client, storage=store, apply=True, pause_seconds=0)
    assert summary["updated_existing"] == 1
    assert summary["new_jobs"] == 0 and summary["deactivated"] == 0
    assert store.updates[0]["salary_min"] == 23000
    assert store.updates[0]["salary_max"] == 25500
    assert len(store.updates[0]["description"]) > 600
    assert "id" not in store.updates[0]
    assert "is_active" not in store.updates[0]


def test_mismatched_publisher_id_cannot_modify_existing_job():
    store = Store()
    with mock_http(payload=publisher_job("mismatch")) as client:
        with pytest.raises(FeedError, match="identity mismatch"):
            enrich_existing(client=client, storage=store, pause_seconds=0)
    assert not store.updates


def test_source_404_never_marks_job_inactive():
    store = Store()
    with mock_http(status=404) as client:
        summary = enrich_existing(client=client, storage=store, pause_seconds=0)
    assert summary["publisher_unavailable"] == 1
    assert not store.updates
