"""UK DfE Teaching Vacancies OGL v3.0 JSON feed.

Source contract verified against DFE-Digital/teaching-vacancies:
  app/controllers/api/vacancies_controller.rb
  app/views/api/vacancies/index.json.jbuilder
  app/views/api/vacancies/_show.json.jbuilder
No production job writes or scheduling are enabled by default.
"""
from __future__ import annotations

import html
import os
import re
from html.parser import HTMLParser
import time as sleeper
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit, urlunsplit

import httpx

from lib.greenhouse_ingestion import FeedError

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
MAX_DFE_DESCRIPTION_CHARS = 40_000

class _PublisherTextParser(HTMLParser):
    """Preserve readable paragraph breaks without retaining publisher HTML."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs):
        if tag in ("script", "style", "noscript"):
            self.hidden += 1
        elif not self.hidden and tag in ("p", "div", "br", "li", "h1", "h2", "h3", "h4", "ul", "ol"):
            self.parts.append("\n" if tag == "br" else "\n\n")
            if tag == "li":
                self.parts.append("• ")

    def handle_endtag(self, tag: str):
        if tag in ("script", "style", "noscript"):
            self.hidden = max(0, self.hidden - 1)
        elif not self.hidden and tag in ("p", "div", "li", "h1", "h2", "h3", "h4", "ul", "ol"):
            self.parts.append("\n")

    def handle_data(self, data: str):
        if not self.hidden:
            self.parts.append(data)


def publisher_description(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    # DfE's JobPosting.description is the source-provided advert content,
    # which may omit parts of the publisher's rendered vacancy page.
    # Never silently truncate to Greenhouse's 600-character preview length.
    parser = _PublisherTextParser()
    parser.feed(html.unescape(html.unescape(value[:80_000])))
    text = "".join(parser.parts).replace("\r", "").strip()
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text)
    if len(text) > MAX_DFE_DESCRIPTION_CHARS:
        return text[:MAX_DFE_DESCRIPTION_CHARS].rstrip() + (
            "\n\n[Description shortened for display; see the original vacancy for full details.]"
        )
    return text or None


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


def annual_salary(value: object) -> tuple[int | None, int | None, str | None]:
    """Keep the publisher's GBP annual salary text; infer bounds only if explicit.

    Teaching Vacancies provides a salary field as either a number or a
    publisher-authored string such as "£68,691 - £77,676 Annually (Actual)".
    Reject unsupported currencies/units; never invent a pay band.
    """
    if not isinstance(value, dict) or value.get("currency") != "GBP":
        return None, None, None
    raw = value.get("value")
    if not isinstance(raw, dict) or raw.get("unitText") != "YEAR":
        return None, None, None
    number = raw.get("value")
    if isinstance(number, bool) or not isinstance(number, (int, float, str)):
        return None, None, None

    if isinstance(number, (int, float)):
        text = str(number)
    else:
        text = " ".join(number.split())
    if not text or len(text) > 200 or "<" in text or ">" in text:
        return None, None, None
    try:
        amount = Decimal(text)
    except InvalidOperation:
        amount = None
    if amount is not None:
        if not amount.is_finite() or not 0 < amount <= 500_000:
            return None, None, None
        return int(amount), int(amount), f"£{amount:,.0f} per year"

    # For free-form salary text, preserve the advertised wording and extract
    # only explicit £ amounts, not misleading grade numbers such as SCP 11-16.
    # No implied lower bound or amount is created for grade-only adverts.
    pounds = re.findall(
        r"£\s*(\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?(?![\d,.])", text
    )
    try:
        values = [int(x.replace(",", "")) for x in pounds]
    except ValueError:
        return None, None, None
    if any(not 0 < x <= 500_000 for x in values):
        return None, None, None
    if len(values) == 1:
        return values[0], values[0], text
    if len(values) == 2 and values[0] <= values[1]:
        return values[0], values[1], text
    return None, None, text


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
        postcode = address.get("postalCode")
        if isinstance(postcode, str) and postcode.strip():
            pieces = [postcode.strip()]
        else:
            # DfE publishes only GB/England vacancies, and the verified
            # country is GB. Label missing locality honestly; never guess it.
            pieces = ["England (specific location not provided)"]
    published = read_date(raw.get("datePosted"), "datePosted")
    closes = read_date(raw.get("validThrough"), "validThrough")
    # Source expiration is authoritative: show closed immediately even if the
    # DfE endpoint returns it briefly during indexing.
    is_active = closes > seen_at
    salary_min, salary_max, salary = annual_salary(raw.get("baseSalary"))
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
        "description": publisher_description(raw.get("description")),
        "salary": salary, "salary_min": salary_min, "salary_max": salary_max,
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
        if page > 1:
            # Polite, sequential requests; no parallel load on the public
            # government endpoint and no burst traffic between pages.
            sleeper.sleep(0.2)
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


def fetch_pilot(client: httpx.Client, now: datetime) -> tuple[list[dict], int, int]:
    """Read only page one for a bounded pilot, never treating it as a full feed.

    DfE sorts solely by publish_on, so tied publication dates may straddle
    paginated pages without stable ordering. A pilot cannot determine which
    old records disappeared; callers MUST disable missing-job deactivation.
    """
    if now.tzinfo is None:
        raise FeedError("Source scan requires timezone-aware UTC clock")
    first, pages, expected = _page(client, 1, now)
    by_id = {}
    for row in first:
        key = row["external_id"]
        if key in by_id and by_id[key] != row:
            raise FeedError("Conflicting DfE posting IDs within pilot page")
        by_id[key] = row
    return list(by_id.values()), pages, expected


def persist(storage, records: list[dict], now: datetime, *,
            deactivate_missing: bool = True) -> dict:
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
    # A partial page is never evidence that another vacancy disappeared.
    # Source-advertised expires_at is separately enforced by live_jobs.
    if not deactivate_missing:
        return {"upserted": len(records), "deactivated": 0}
    cutoff = (now - timedelta(hours=GRACE_HOURS)).isoformat()
    old = (storage.table("jobs").update({"is_active": False})
           .eq("source", SOURCE).eq("source_board", BOARD)
           .eq("is_active", True).lt("last_seen_at", cutoff).execute())
    return {"upserted": len(records), "deactivated": len(old.data or [])}


def run(*, client: httpx.Client, apply: bool, storage=None,
        now: datetime | None = None, pilot: bool = False) -> dict:
    if apply and os.environ.get("JOBSLEUTH_INGEST_ENABLED") != "true":
        raise FeedError("Global vacancy ingestion is disabled")
    if apply and os.environ.get("JOBSLEUTH_DFE_OGL_TERMS_ACK") != "true":
        raise FeedError("DfE API reuse terms must be reviewed/acknowledged")
    if apply and os.environ.get("JOBSLEUTH_DFE_INGEST_ENABLED") != "true":
        raise FeedError("DfE feed is disabled")
    if apply and pilot and os.environ.get("JOBSLEUTH_DFE_PILOT_ENABLED") != "true":
        raise FeedError("One-page pilot import requires a separate explicit gate")
    if apply and storage is None:
        raise FeedError("Backend-only database connection required")
    at = now or datetime.now(timezone.utc)
    if pilot:
        jobs, pages, advertised = fetch_pilot(client, at)
        result = {"source": SOURCE, "records": len(jobs), "applied": apply,
                  "scope": "first_page_only", "source_total": advertised,
                  "source_pages": pages, "missing_job_expiry": False}
    else:
        jobs = fetch_all(client, at)
        result = {"source": SOURCE, "records": len(jobs), "applied": apply}
    if apply:
        result.update(persist(storage, jobs, at, deactivate_missing=not pilot))
    return result
