"""Conservative one-time enrichment of *existing* DfE listings only.

This is deliberately separate from page-one pilot ingestion: per-slug publisher
records are checked, no new rows are inserted and no missing-job expiry is run.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone

import httpx

from lib.dfe_ingestion import (
    BOARD, HOST, MAX_PAGE_BYTES, PUBLIC_URL, SLUG_RE, SOURCE, FeedError, record,
)


def fetch_one(client: httpx.Client, slug: str, at: datetime) -> dict | None:
    if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
        raise FeedError("Invalid publisher identity in existing database")
    response = client.get(
        f"https://{HOST}/api/v1/jobs/{slug}.json",
        headers={"Accept": "application/json", "Referer": PUBLIC_URL},
        timeout=20,
    )
    if response.status_code in (404, 410):
        return None  # Cannot enrich; never deactivate from this path.
    response.raise_for_status()
    if len(response.content) > MAX_PAGE_BYTES:
        raise FeedError("DfE vacancy response is too large")
    payload = response.json()
    if not isinstance(payload, dict):
        raise FeedError("Malformed individual DfE response")
    parsed = record(payload, at)
    if parsed["external_id"] != slug:
        raise FeedError("Publisher identity mismatch; refuse enrichment")
    return parsed


def enrich_existing(*, client: httpx.Client, storage, apply: bool = False,
                    max_records: int = 100, pause_seconds: float = 0.2) -> dict:
    if not 1 <= max_records <= 100:
        raise FeedError("Use an explicitly bounded batch of at most 100")
    if apply and any(os.environ.get(key) != "true" for key in (
        "JOBSLEUTH_INGEST_ENABLED",
        "JOBSLEUTH_DFE_INGEST_ENABLED",
        "JOBSLEUTH_DFE_OGL_TERMS_ACK",
        "JOBSLEUTH_DFE_BACKFILL_ENABLED",
    )):
        raise FeedError("Existing-job backfill is disabled")
    now = datetime.now(timezone.utc)
    existing_result = (
        storage.table("jobs")
        .select("id,external_id,source,source_board,url,salary,description")
        .eq("source", SOURCE).eq("source_board", BOARD)
        .order("id")
        .limit(max_records).execute()
    )
    existing = existing_result.data
    if existing is None:
        raise FeedError("Could not read existing DfE job identities")
    staged: list[tuple[dict, dict]] = []
    unavailable = 0
    salary_available = 0
    descriptions_extended = 0
    for idx, stored in enumerate(existing):
        slug = stored.get("external_id")
        parsed = fetch_one(client, slug, now)
        if parsed is None:
            unavailable += 1
            continue
        # Explicitly forbid changing an existing record's identity or link.
        if parsed["url"] != stored.get("url"):
            raise FeedError("Publisher link changed: manual review required")
        patch = {}
        if parsed.get("salary"):
            patch.update({
                "salary": parsed["salary"], "salary_min": parsed["salary_min"],
                "salary_max": parsed["salary_max"],
            })
            salary_available += 1
        if parsed.get("description") and len(parsed["description"]) > len(stored.get("description") or ""):
            patch["description"] = parsed["description"]
            descriptions_extended += 1
        if patch:
            staged.append((stored, patch))
        if idx < len(existing) - 1 and pause_seconds:
            time.sleep(pause_seconds)

    # No database writes occur until the entire bounded source-check succeeded.
    if apply:
        for stored, patch in staged:
            result = (
                storage.table("jobs").update(patch)
                .eq("id", stored["id"]).eq("source", SOURCE)
                .eq("source_board", BOARD).eq("external_id", stored["external_id"])
                .execute()
            )
            if result.data is None or len(result.data) != 1:
                raise FeedError("Backfill update could not confirm existing row")
    return {
        "scanned_existing": len(existing),
        "publisher_unavailable": unavailable,
        "salary_available": salary_available,
        "descriptions_extended": descriptions_extended,
        "updated_existing": len(staged) if apply else 0,
        "would_update": len(staged),
        "applied": apply,
        "new_jobs": 0,
        "deactivated": 0,
    }
