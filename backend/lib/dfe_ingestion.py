"""UK DfE Teaching Vacancies OGL v3.0 JSON feed.

Source contract verified against DFE-Digital/teaching-vacancies:
  app/controllers/api/vacancies_controller.rb
  app/views/api/vacancies/index.json.jbuilder
  app/views/api/vacancies/_show.json.jbuilder
No production job writes or scheduling are enabled by default.
"""
from __future__ import annotations

import os
import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit, urlunsplit

import httpx

from lib.greenhouse_ingestion import excerpt, FeedError

SOURCE = "dfe_teaching_vacancies"
BOARD = "england"
HOST = "teaching-vacancies.service.gov.uk"
PATH = "/api/v1/jobs.json"
PUBLIC_URL = "https://jobsleuth-ai.vercel.app/"
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,159}$", re.I)
MAX_PAGES = 200
MAX_PAGE_BYTES = 1_500_000
MAX_TOTAL = 20_000
GRACE_HOURS = 72


def official_job_url(value: object) -> tuple[str, str] | None:
    if not isinstance(value, str):
        return None
    try:
        u = urlsplit(value)
    except ValueError:
        return None
    if (u.scheme != "https" or u.hostname != HOST or u.username or u.password
            or u.port not in (None, 443)):
        return None
    parts = u.path.rstrip("/").split("/")
    if len(parts) != 3 or parts[1] != "jobs" or not SLUG_RE.fullmatch(parts[2]):
        return None
    return parts[2], urlunsplit(("https", HOST, u.path.rstrip("/"), "", ""))


def read_date(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise FeedError(f"Missing {field} in DfE vacancy")
    # DfE's live JobPosting response can use date-only ISO 8601 for
    # datePosted. Do not pretend it specifies an exact publication time.
    # For date-only expiry, remain active until the END of the UK calendar
    # day rather than incorrectly closing at midnight UTC.
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            day = date.fromisoformat(value)
        except ValueError as e:
            raise FeedError(f"Invalid {field} date") from e
        if field == "validThrough":
            return datetime.combine(
                day, time.max, tzinfo=ZoneInfo("Europe/London")
            ).astimezone(timezone.utc)
        return datetime.combine(day, time.min, tzinfo=timezone.utc)
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as e:
        raise FeedError(f"Invalid {field} timestamp") from e
    if result.tzinfo is None:
        raise FeedError(f"{field} timestamp is missing timezone")
    return result.astimezone(timezone.utc)


def annual_salary(value: object) -> tuple[int | None, str | None]:
    if not isinstance(value, dict) or value.get("currency") != "GBP":
        return None, None
    raw = value.get("value")
    if not isinstance(raw, dict) or raw.get("unitText") != "YEAR":
        return None, None
    number = raw.get("value")
    if isinstance(number, bool) or not isinstance(number, (int, float, str)):
        return None, None
    try:
        amount = Decimal(str(number))
    except InvalidOperation:
        return None, None
    if not amount.is_finite() or amount <= 0 or amount > 500_000:
        return None, None
    return int(amount), f"£{amount:,.0f} per year"


def record(raw: object, seen_at: datetime) -> dict:
    if not isinstance(raw, dict) or raw.get("@type") != "JobPosting":
        raise FeedError("Malformed DfE JobPosting record")
    link = official_job_url(raw.get("url"))
    title = raw.get("title")
    employer = raw.get("hiringOrganization")
    address = (raw.get("jobLocation") or {}).get("address") if isinstance(raw.get("jobLocation"), dict) else None
    if not link or not isinstance(title, str) or not 0 < len(title.strip()) <= 300:
        raise FeedError("DfE record missing stable official URL/title")
    if not isinstance(employer, dict) or not isinstance(employer.get("name"), str) or not employer["name"].strip():
        raise FeedError("DfE record missing employer name")
    if not isinstance(address, dict) or address.get("addressCountry") != "GB":
        raise FeedError("DfE record is missing GB location")
    place = [address.get("addressLocality"), address.get("addressRegion")]
    pieces = [str(x).strip() for x in place if isinstance(x, str) and x.strip()]
    if not pieces:
        raise FeedError("DfE record missing location details")
    published = read_date(raw.get("datePosted"), "datePosted")
    closes = read_date(raw.get("validThrough"), "validThrough")
    # Source expiration is authoritative: show closed immediately even if the
    # DfE endpoint returns it briefly during indexing.
    is_active = closes > seen_at
    salary_min, salary = annual_salary(raw.get("baseSalary"))
    job_type = raw.get("employmentType")
    if isinstance(job_type, list):
        kinds = [x for x in job_type if x in ("FULL_TIME", "PART_TIME", "CONTRACTOR")]
        role_type = " / ".join(x.replace("_", " ").title() for x in kinds) or None
    else:
        role_type = None
    return {
        "source": SOURCE, "source_board": BOARD, "external_id": link[0],
        "title": title.strip(), "company": employer["name"].strip()[:200],
        "location": ", ".join(pieces)[:250], "url": link[1],
        "description": excerpt(raw.get("description")),
        "salary": salary, "salary_min": salary_min, "salary_max": salary_min,
        "role_type": role_type, "is_active": is_active,
        "last_seen_at": seen_at.isoformat(),
        "source_updated_at": None,  # DfE datePosted is NOT last-edited timestamp.
        "expires_at": closes.isoformat(),
    }


def _page(client: httpx.Client, number: int, now: datetime) -> tuple[list[dict], int, int]:
    response = client.get(
        f"https://{HOST}{PATH}", params={"page": number}, timeout=20,
        headers={"Accept": "application/json", "Referer": PUBLIC_URL},
    )
    response.raise_for_status()
    if len(response.content) > MAX_PAGE_BYTES:
        raise FeedError("DfE page exceeds safe size limit")
    data = response.json()
    if not isinstance(data, dict) or data.get("openapi") != "3.0.0" or not isinstance(data.get("data"), list):
        raise FeedError("Unexpected DfE API format")
    meta = data.get("meta")
    if (not isinstance(meta, dict) or type(meta.get("totalPages")) is not int
            or type(meta.get("count")) is not int):
        raise FeedError("DfE pagination metadata missing")
    pages, count = meta["totalPages"], meta["count"]
    if not 1 <= pages <= MAX_PAGES or count <= 0 or count > MAX_TOTAL:
        raise FeedError("DfE vacancy count/page limit outside safe bounds")
    items = data["data"]
    if not 1 <= len(items) <= 100:
        raise FeedError("DfE page empty or exceeds 100 jobs")
    records = [record(row, now) for row in items]
    return records, pages, count


def fetch_all(client: httpx.Client, now: datetime) -> list[dict]:
    if now.tzinfo is None:
        raise FeedError("Source scan requires timezone-aware UTC clock")
    first, pages, expected = _page(client, 1, now)
    by_id = {}
    for page in range(1, pages + 1):
        items, total_pages, count = (first, pages, expected) if page == 1 else _page(client, page, now)
        if total_pages != pages or count != expected:
            raise FeedError("DfE source changed mid-scan: refuse partial import")
        for row in items:
            key = row["external_id"]
            if key in by_id and by_id[key] != row:
                raise FeedError("Conflicting DfE posting IDs across pages")
            by_id[key] = row
    if len(by_id) != expected:
        raise FeedError("Incomplete, shifting or duplicate DfE pages: refuse import/expiry")
    return list(by_id.values())


def persist(storage, records: list[dict], now: datetime) -> dict:
    if not records:
        raise FeedError("Cannot apply an empty DfE feed")
    for offset in range(0, len(records), 100):
        batch = records[offset:offset + 100]
        result = storage.table("jobs").upsert(
            batch, on_conflict="source,source_board,external_id"
        ).execute()
        if result.data is None:
            raise FeedError("DfE job upsert did not confirm persistence")
    # Verify all expected source IDs before inactivating missing old postings.
    for offset in range(0, len(records), 100):
        ids = [r["external_id"] for r in records[offset:offset + 100]]
        result = (storage.table("jobs").select("external_id")
                  .eq("source", SOURCE).eq("source_board", BOARD)
                  .in_("external_id", ids).execute())
        if {r["external_id"] for r in (result.data or [])} != set(ids):
            raise FeedError("DfE import verification failed; no expiry")
    cutoff = (now - timedelta(hours=GRACE_HOURS)).isoformat()
    old = (storage.table("jobs").update({"is_active": False})
           .eq("source", SOURCE).eq("source_board", BOARD)
           .eq("is_active", True).lt("last_seen_at", cutoff).execute())
    return {"upserted": len(records), "deactivated": len(old.data or [])}


def run(*, client: httpx.Client, apply: bool, storage=None, now: datetime | None = None) -> dict:
    if apply and os.environ.get("JOBSLEUTH_INGEST_ENABLED") != "true":
        raise FeedError("Global vacancy ingestion is disabled")
    if apply and os.environ.get("JOBSLEUTH_DFE_OGL_TERMS_ACK") != "true":
        raise FeedError("DfE API reuse terms must be reviewed/acknowledged")
    if apply and os.environ.get("JOBSLEUTH_DFE_INGEST_ENABLED") != "true":
        raise FeedError("DfE feed is disabled")
    if apply and storage is None:
        raise FeedError("Backend-only database connection required")
    at = now or datetime.now(timezone.utc)
    jobs = fetch_all(client, at)
    result = {"source": SOURCE, "records": len(jobs), "applied": apply}
    if apply:
        result.update(persist(storage, jobs, at))
    return result
