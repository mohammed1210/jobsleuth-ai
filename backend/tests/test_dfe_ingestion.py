"""DfE public Open Government Licence feed: mock HTTP, no network or private data."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import httpx
import pytest

from lib.dfe_ingestion import (
    BOARD, HOST, SOURCE, FeedError, annual_salary, fetch_all, official_job_url,
    record, run,
)

NOW = datetime(2026, 11, 22, 12, tzinfo=timezone.utc)


def item(slug="school-support-worker-567", date="2026-12-12T16:00:00+00:00"):
    return {
        "@type": "JobPosting", "title": "School support worker",
        "datePosted": "2026-11-20T09:00:00Z", "validThrough": date,
        "jobLocation": {"address": {"addressCountry": "GB",
                                    "addressLocality": "West Drayton", "addressRegion": "London"}},
        "url": f"https://teaching-vacancies.service.gov.uk/jobs/{slug}",
        "hiringOrganization": {"name": "Synthetic School"},
        "employmentType": ["PART_TIME"],
        "description": "<p>Help children learn.</p>",
        "baseSalary": {"currency": "GBP",
                       "value": {"unitText": "YEAR", "value": 34000}},
    }


def client_with_pages(pages, override_meta=None):
    all_count = sum(len(x) for x in pages)
    def handler(req):
        assert req.url.host == HOST
        assert req.url.path == "/api/v1/jobs.json"
        assert req.headers["referer"] == "https://jobsleuth-ai.vercel.app/"
        assert req.headers["accept"] == "application/json"
        page = int(req.url.params["page"])
        payload = {"openapi": "3.0.0", "data": pages[page-1],
                   "meta": override_meta or {"totalPages": len(pages), "count": all_count}}
        return httpx.Response(200, json=payload)
    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)


def test_official_source_and_salary():
    r = record(item(), NOW)
    assert r["source"] == SOURCE and r["source_board"] == BOARD
    assert r["external_id"] == "school-support-worker-567"
    assert r["location"] == "West Drayton, London"
    assert r["salary_min"] == 34000 and r["salary_max"] == 34000
    assert r["role_type"] == "Part Time"
    assert r["description"] == "Help children learn."
    assert r["is_active"] is True
    assert r["source_updated_at"] is None


def test_date_only_fields_from_real_dfe_api_are_supported():
    from lib.dfe_ingestion import read_date
    post = item()
    post["datePosted"] = "2026-11-20"
    post["validThrough"] = "2026-11-22"
    assert record(post, datetime(2026, 11, 22, 18, tzinfo=timezone.utc))["is_active"]
    assert not record(post, datetime(2026, 11, 23, 0, tzinfo=timezone.utc))["is_active"]
    assert read_date("2026-07-02", "validThrough").isoformat() == "2026-07-02T22:59:59.999999+00:00"
    with pytest.raises(FeedError):
        read_date("2026-02-30", "validThrough")
    with pytest.raises(FeedError):
        read_date("2026-11-22T09:30:00", "validThrough")


def test_closed_source_job_is_immediately_inactive():
    assert record(item(date="2026-11-20T16:00:00Z"), NOW)["is_active"] is False


def test_malformed_countries_urls_and_nonfinite_salary():
    for u in ("http://teaching-vacancies.service.gov.uk/jobs/x",
              "https://evil.example/jobs/x", "https://teaching-vacancies.service.gov.uk@evil.example/jobs/x"):
        assert official_job_url(u) is None
    bad = item()
    bad["jobLocation"]["address"]["addressCountry"] = "US"
    with pytest.raises(FeedError):
        record(bad, NOW)
    assert annual_salary({"currency": "GBP",
                          "value": {"unitText": "YEAR", "value": "NaN"}}) == (None, None)


def test_page_scan_complete_before_any_write():
    with client_with_pages([[item("one-posting")],
                            [item("another-posting")]]) as client:
        jobs = fetch_all(client, NOW)
    assert len(jobs) == 2
    assert {j["external_id"] for j in jobs} == {"one-posting", "another-posting"}


def test_duplicate_pages_fail_closed():
    with client_with_pages([[item("same")], [item("same")]]) as client:
        with pytest.raises(FeedError):
            fetch_all(client, NOW)


def test_changed_source_meta_or_malformed_row_fails_closed():
    with client_with_pages([[item()]], override_meta={"totalPages": 1000, "count": 1}) as client:
        with pytest.raises(FeedError):
            fetch_all(client, NOW)
    bad = item()
    bad.pop("hiringOrganization")
    with client_with_pages([[bad]]) as client:
        with pytest.raises(FeedError):
            fetch_all(client, NOW)


def test_unapproved_apply_rejected_before_network_call():
    with client_with_pages([[item()]]) as client, patch.dict("os.environ", {}, clear=True):
        with pytest.raises(FeedError):
            run(client=client, apply=True, storage=object(), now=NOW)
    with client_with_pages([[item()]]) as client, patch.dict("os.environ", {
        "JOBSLEUTH_INGEST_ENABLED": "true",
        "JOBSLEUTH_DFE_INGEST_ENABLED": "true",
    }, clear=True):
        with pytest.raises(FeedError):
            run(client=client, apply=True, storage=object(), now=NOW)


def test_read_only_preview_does_not_write():
    with client_with_pages([[item()]]) as client:
        out = run(client=client, apply=False, now=NOW)
    assert out == {"source": SOURCE, "records": 1, "applied": False}
