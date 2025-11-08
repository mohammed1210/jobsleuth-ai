"""Job data normalization for JobSleuth AI scrapers."""

import re
from datetime import datetime
from typing import Any
from uuid import uuid4


def extract_salary_range(
    salary_text: str | None,
) -> tuple[int | None, int | None, str | None]:
    """Extract min, max salary from text like '$100k-$150k' or '100000-150000'."""
    if not salary_text:
        return None, None, None

    # Remove common formatting
    clean = re.sub(r"[,$]", "", salary_text.lower())

    # Look for patterns like "100k-150k" or "100000-150000"
    range_match = re.search(r"(\d+)k?\s*[-–to]\s*(\d+)k?", clean)
    if range_match:
        min_val = int(range_match.group(1))
        max_val = int(range_match.group(2))

        # If values are < 1000, assume they're in thousands
        if min_val < 1000:
            min_val *= 1000
        if max_val < 1000:
            max_val *= 1000

        return min_val, max_val, salary_text

    # Single value like "120k" or "120000"
    single_match = re.search(r"(\d+)k?", clean)
    if single_match:
        val = int(single_match.group(1))
        if val < 1000:
            val *= 1000
        return val, val, salary_text

    return None, None, salary_text


def normalize_job_data(raw_data: dict[str, Any], source: str) -> dict[str, Any]:
    """Normalize job data from various sources into our schema.

    Args:
        raw_data: Raw job data from provider or scraper
        source: Source identifier (e.g., 'serpapi', 'manual', 'playwright')

    Returns:
        Normalized job data ready for database insertion
    """
    # Extract basic fields
    title = raw_data.get("title") or raw_data.get("job_title") or "Unknown"
    company = raw_data.get("company") or raw_data.get("company_name") or "Unknown"
    location = raw_data.get("location") or raw_data.get("job_location")
    url = raw_data.get("url") or raw_data.get("job_url") or f"https://example.com/job/{uuid4()}"

    # External ID (if provided by source)
    external_id = raw_data.get("id") or raw_data.get("job_id")

    # Salary extraction
    salary_text = raw_data.get("salary") or raw_data.get("salary_range")
    salary_min, salary_max, salary_text = extract_salary_range(salary_text)

    # Job type
    job_type = raw_data.get("type") or raw_data.get("job_type") or raw_data.get("employment_type")

    # Posted date
    posted_at = None
    if raw_data.get("posted_at"):
        try:
            if isinstance(raw_data["posted_at"], str):
                posted_at = datetime.fromisoformat(raw_data["posted_at"].replace("Z", "+00:00"))
            else:
                posted_at = raw_data["posted_at"]
        except Exception:
            pass

    return {
        "source": source,
        "external_id": external_id,
        "title": title,
        "company": company,
        "location": location,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_text": salary_text,
        "type": job_type,
        "url": url,
        "posted_at": posted_at.isoformat() if posted_at else None,
        "raw": raw_data,
    }


async def upsert_job(job_data: dict[str, Any], supabase_client) -> dict[str, Any]:
    """Upsert a job into the database.

    Uses url as primary unique key, with (source, external_id) as secondary.
    """
    try:
        # Try to upsert by url
        response = supabase_client.table("jobs").upsert(job_data, on_conflict="url").execute()

        return response.data[0] if response.data else job_data
    except Exception as e:
        # If upsert fails, try regular insert
        try:
            response = supabase_client.table("jobs").insert(job_data).execute()
            return response.data[0] if response.data else job_data
        except Exception:
            # Job might already exist, fetch it
            response = (
                supabase_client.table("jobs").select("*").eq("url", job_data["url"]).execute()
            )
            if response.data:
                return response.data[0]
            raise e
