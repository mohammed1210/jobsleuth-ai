"""One-page, read-only Himalayas GB search contract probe.

No persistence, AI calls, source activation or scheduling. Only aggregate
counts leave the process. See ops/VACANCY_SOURCE_PREFLIGHT.md.
"""
from __future__ import annotations

import json
import time
from urllib.parse import urlsplit

import httpx

URL = "https://himalayas.app/jobs/api/search"
MAX_BYTES = 1_500_000


def safe_apply_url(value: object) -> bool:
    if not isinstance(value, str) or len(value) > 4096:
        return False
    if any(ord(c) < 33 or ord(c) == 127 or c == "\\" for c in value):
        return False
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and parsed.port in (None, 443)
        )
    except ValueError:
        return False


def summarize(payload: object, now: int) -> dict:
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise ValueError("Unexpected Himalayas response")
    jobs = payload["jobs"]
    if len(jobs) > 20:
        raise ValueError("Himalayas page exceeds documented limit")
    seen: set[str] = set()
    active = expired = 0
    for job in jobs:
        if not isinstance(job, dict):
            raise ValueError("Invalid job")
        for field in ("guid", "title", "companyName"):
            value = job.get(field)
            if not isinstance(value, str) or not value.strip() or len(value) > 4096:
                raise ValueError("Missing job identity")
        guid = job["guid"]
        if guid in seen:
            raise ValueError("Duplicate GUID on probe page")
        seen.add(guid)
        expiry = job.get("expiryDate")
        if type(expiry) is not int or expiry <= 0:
            raise ValueError("Invalid expiry")
        if not safe_apply_url(job.get("applicationLink")):
            raise ValueError("Unsafe or unsupported application URL")
        if expiry > now:
            active += 1
        else:
            expired += 1
    return {
        "source": "himalayas",
        "country_filter": "GB",
        "scope": "one_page_only",
        "records": len(jobs),
        "unexpired_on_page": active,
        "expired_on_page": expired,
        "applied": False,
        "missing_job_expiry": False,
    }


def probe(client: httpx.Client, now: int) -> dict:
    with client.stream(
        "GET", URL, params={"country": "GB", "page": 1},
        headers={"Accept": "application/json"}, timeout=20,
        follow_redirects=False,
    ) as response:
        response.raise_for_status()
        body = bytearray()
        for chunk in response.iter_bytes():
            if len(body) + len(chunk) > MAX_BYTES:
                raise ValueError("Himalayas response exceeds byte limit")
            body.extend(chunk)
    return summarize(json.loads(body), now)


def main():
    try:
        with httpx.Client(trust_env=False, follow_redirects=False) as client:
            summary = probe(client, int(time.time()))
        print(json.dumps(summary, sort_keys=True))
    except (httpx.HTTPError, ValueError):
        print("Himalayas preflight failed; no vacancy data changed.")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
