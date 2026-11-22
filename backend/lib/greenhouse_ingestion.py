"""Carefully gated Greenhouse employer-board vacancy ingestion for JobSleuth.

Reads only documented public JSON list endpoints with a fixed hostname.
NO feeds are enabled by default. Operators must confirm source reuse rights.
Store only public metadata, a short plain-text excerpt, and employer apply URL.
"""
from __future__ import annotations

import html
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import urlsplit, urlunsplit

import httpx

SOURCE = "greenhouse"
API_HOST = "boards-api.greenhouse.io"
ALLOWED_JOB_HOSTS = {"job-boards.greenhouse.io", "boards.greenhouse.io"}
BOARD_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,79}$")
# Only explicit country/UK constituent nation evidence qualifies a post.
# City-only labels (e.g. Cambridge, Birmingham) exist outside Britain too.
UK_LOCATION_RE = re.compile(
    r"\\b(?:united kingdom|u\\.?k\\.?|england|scotland|wales|northern ireland)\\b",
    flags=re.I,
)
FOREIGN_LOCATION_RE = re.compile(
    r"\\b(?:ontario|canada|united states|u\\.?s\\.?a\\.?|australia|"
    r"new south wales|nsw|united arab emirates)\\b",
    flags=re.I,
)
MAX_JOBS_PER_BOARD = 1000
MAX_CONTENT_BYTES = 2_000_000
MAX_DESCRIPTION_CHARS = 600
MISSING_GRACE_HOURS = 72


class FeedError(ValueError):
    pass


@dataclass(frozen=True)
class Board:
    slug: str
    employer: str


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs):
        if tag in ("script", "style", "noscript"):
            self.hidden_depth += 1

    def handle_endtag(self, tag: str):
        if tag in ("script", "style", "noscript") and self.hidden_depth > 0:
            self.hidden_depth -= 1

    def handle_data(self, data: str):
        if not self.hidden_depth:
            self.parts.append(data)


def excerpt(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    # Greenhouse encodes HTML elements as entities. Decode twice, then strip
    # markup and never store or render scripts, style tags or raw HTML.
    cleaned = html.unescape(html.unescape(value))
    parser = TextExtractor()
    parser.feed(cleaned[:40_000])
    text = " ".join(" ".join(parser.parts).split())
    return text[:MAX_DESCRIPTION_CHARS].rstrip() or None


def parse_boards(config: str) -> list[Board]:
    if not config.strip():
        return []
    out = []
    for entry in config.split(","):
        if "=" not in entry:
            raise FeedError("Each approved board needs the format board_slug=Employer Name")
        slug, employer = (part.strip() for part in entry.split("=", 1))
        if not BOARD_RE.fullmatch(slug) or not employer or len(employer) > 120:
            raise FeedError("Invalid approved board slug or employer name")
        out.append(Board(slug, employer))
    if len(out) > 12 or len(set(b.slug for b in out)) != len(out):
        raise FeedError("Duplicate or excessive board configuration")
    return out


def is_uk_location(location: str) -> bool:
    return bool(UK_LOCATION_RE.search(location)) and not bool(FOREIGN_LOCATION_RE.search(location))


def employer_apply_link(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    try:
        url = urlsplit(raw)
    except ValueError:
        return None
    if url.scheme != "https" or url.username or url.password or url.port not in (None, 443):
        return None
    if (url.hostname or "").lower() not in ALLOWED_JOB_HOSTS:
        return None
    if not re.fullmatch(r"/[a-z0-9_-]{2,80}/jobs/[0-9]+/?", url.path, flags=re.I):
        return None
    # Drop tracking parameters and fragments, but keep the official apply link.
    return urlunsplit(("https", url.hostname.lower(), url.path, "", ""))


def record(job: object, board: Board, seen_at: datetime) -> dict | None:
    if not isinstance(job, dict):
        return None
    location = job.get("location")
    place = location.get("name", "") if isinstance(location, dict) else ""
    title = job.get("title")
    external_id = job.get("id")
    link = employer_apply_link(job.get("absolute_url"))
    if not isinstance(place, str) or not is_uk_location(place):
        return None
    if not isinstance(title, str) or not title.strip() or len(title) > 300:
        return None
    if isinstance(external_id, bool) or not isinstance(external_id, int) or external_id <= 0:
        return None
    if not link:
        return None
    # Compare the complete canonical path; substring matching would turn
    # upstream ID 1234 into another job's /jobs/12345 link.
    if urlsplit(link).path.rstrip("/").casefold() != f"/{board.slug}/jobs/{external_id}":
        return None

    updated_at = job.get("updated_at")
    source_updated = None
    if isinstance(updated_at, str):
        try:
            date = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            if date.tzinfo is not None:
                source_updated = date.astimezone(timezone.utc).isoformat()
        except ValueError:
            pass
    remote = "remote" in place.casefold()
    hybrid = "hybrid" in place.casefold()
    return {
        "source": SOURCE,
        "source_board": board.slug,
        "external_id": str(external_id),
        "title": title.strip(),
        "company": board.employer,
        "location": place.strip()[:250],
        "url": link,
        "description": excerpt(job.get("content")),
        "salary": None,
        "salary_min": None,
        "salary_max": None,
        "role_type": "Remote" if remote else "Hybrid" if hybrid else None,
        "is_active": True,
        "last_seen_at": seen_at.isoformat(),
        "source_updated_at": source_updated,
    }


def fetch_board(board: Board, client: httpx.Client, seen_at: datetime) -> tuple[list[dict], int]:
    url = f"https://{API_HOST}/v1/boards/{board.slug}/jobs"
    response = client.get(url, params={"content": "true"}, timeout=15)
    response.raise_for_status()
    if len(response.content) > MAX_CONTENT_BYTES:
        raise FeedError("Board response exceeds safe size limit")
    payload = response.json()
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise FeedError("Unexpected employer board response")
    posts = payload["jobs"]
    if len(posts) == 0 or len(posts) > MAX_JOBS_PER_BOARD:
        raise FeedError("Empty or unexpectedly large board; do not expire existing jobs")
    meta = payload.get("meta")
    if isinstance(meta, dict) and isinstance(meta.get("total"), int) and meta["total"] != len(posts):
        raise FeedError("Incomplete source feed; do not expire jobs")
    results: dict[str, dict] = {}
    for post in posts:
        # Fail a whole scan if a row lacks the location field. Otherwise a
        # UK posting could remain live upstream but be wrongly expired when
        # its latest location is malformed or missing.
        if not isinstance(post, dict):
            raise FeedError("Malformed job row in employer feed")
        loc = post.get("location")
        if not isinstance(loc, dict) or not isinstance(loc.get("name"), str) or not loc["name"].strip():
            raise FeedError("Missing location in employer feed; no expiry")
        if not is_uk_location(loc["name"]):
            continue
        item = record(post, board, seen_at)
        if item is None:
            raise FeedError("Malformed UK vacancy row; no expiry")
        if item["external_id"] in results and results[item["external_id"]] != item:
            raise FeedError("Conflicting duplicate external posting in source feed")
        results[item["external_id"]] = item
    # Identical duplicate rows are harmless; unique source ID is the canonical
    # identity. Never compare raw UK row count against deduplicated identities.
    return list(results.values()), len(posts)


def _verify_persisted(storage, board: Board, ids: list[str]) -> None:
    for offset in range(0, len(ids), 100):
        selected = ids[offset:offset + 100]
        response = (
            storage.table("jobs").select("external_id")
            .eq("source", SOURCE).eq("source_board", board.slug)
            .in_("external_id", selected).execute()
        )
        observed = {str(x["external_id"]) for x in (response.data or [])}
        if observed != set(selected):
            raise FeedError("Upsert verification failed; no expiry performed")


def persist_board(storage, board: Board, records: list[dict], seen_at: datetime) -> dict:
    if not records:
        # Legitimate zero-UK boards can occur. Do NOT mark existing records closed
        # because this could also be an upstream board/location metadata outage.
        return {"upserted": 0, "deactivated": 0}
    for offset in range(0, len(records), 100):
        batch = records[offset:offset + 100]
        storage.table("jobs").upsert(
            batch, on_conflict="source,source_board,external_id"
        ).execute()
    _verify_persisted(storage, board, [x["external_id"] for x in records])
    # Only after successful full scan and idempotent upsert, transition postings
    # missing for >72 hours to inactive; never delete saved_jobs references.
    cutoff = (seen_at - timedelta(hours=MISSING_GRACE_HOURS)).isoformat()
    response = (
        storage.table("jobs").update({"is_active": False})
        .eq("source", SOURCE).eq("source_board", board.slug)
        .eq("is_active", True).lt("last_seen_at", cutoff).execute()
    )
    return {"upserted": len(records), "deactivated": len(response.data or [])}


def run(boards: list[Board], *, apply: bool, client: httpx.Client, storage=None,
        now: datetime | None = None) -> list[dict]:
    if not boards:
        raise FeedError("No approved employer boards configured")
    if apply and os.environ.get("JOBSLEUTH_FEED_RIGHTS_CONFIRMED") != "true":
        raise FeedError("Approved employer feed usage/attribution must be confirmed")
    if apply and os.environ.get("JOBSLEUTH_INGEST_ENABLED") != "true":
        raise FeedError("Ingestion is disabled until deliberately enabled")
    at = now or datetime.now(timezone.utc)
    if at.tzinfo is None:
        raise FeedError("Ingestion run timestamp must include timezone")
    if apply and storage is None:
        raise FeedError("Private service-role database client required")
    summaries = []
    for board in boards:
        listings, count = fetch_board(board, client, at)
        result = {"board": board.slug, "feed_posts": count, "uk_jobs": len(listings),
                  "applied": apply}
        if apply:
            result.update(persist_board(storage, board, listings, at))
        summaries.append(result)
    return summaries
