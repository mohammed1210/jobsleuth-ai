"""Data normalization for job scraping results.

Converts raw provider or HTML data into standardized job schema.
Handles upsert by URL or (source, external_id).
"""

from typing import Any, Optional
from datetime import datetime


def normalize_serpapi_job(raw_job: dict[str, Any]) -> dict[str, Any]:
    """Normalize a job from SerpAPI format.
    
    Args:
        raw_job: Raw job data from SerpAPI
        
    Returns:
        Normalized job data
    """
    return {
        "title": raw_job.get("title", ""),
        "company": raw_job.get("company_name", ""),
        "location": raw_job.get("location", ""),
        "salary": raw_job.get("detected_extensions", {}).get("salary"),
        "description": raw_job.get("description", ""),
        "url": raw_job.get("share_url") or raw_job.get("related_links", [{}])[0].get("link"),
        "source": "Google Jobs (SerpAPI)",
        "external_id": raw_job.get("job_id"),
        "date_posted": raw_job.get("detected_extensions", {}).get("posted_at"),
        "job_type": raw_job.get("detected_extensions", {}).get("schedule_type"),
    }


def normalize_indeed_job(raw_job: dict[str, Any]) -> dict[str, Any]:
    """Normalize a job from Indeed scraping.
    
    Args:
        raw_job: Raw job data from Indeed
        
    Returns:
        Normalized job data
    """
    return {
        "title": raw_job.get("title", ""),
        "company": raw_job.get("company", ""),
        "location": raw_job.get("location", ""),
        "salary": raw_job.get("salary"),
        "description": raw_job.get("description", ""),
        "url": raw_job.get("link", ""),
        "source": "Indeed",
        "external_id": _extract_indeed_job_id(raw_job.get("link", "")),
        "date_posted": raw_job.get("date_posted"),
        "job_type": None,
    }


def normalize_zyte_job(raw_job: dict[str, Any]) -> dict[str, Any]:
    """Normalize a job from Zyte format.
    
    Args:
        raw_job: Raw job data from Zyte
        
    Returns:
        Normalized job data
    """
    return {
        "title": raw_job.get("title", ""),
        "company": raw_job.get("company", ""),
        "location": raw_job.get("location", ""),
        "salary": raw_job.get("salary"),
        "description": raw_job.get("description", ""),
        "url": raw_job.get("url", ""),
        "source": "Zyte",
        "external_id": raw_job.get("id"),
        "date_posted": raw_job.get("posted_date"),
        "job_type": raw_job.get("employment_type"),
    }


def normalize_job(raw_job: dict[str, Any], source: str) -> dict[str, Any]:
    """Normalize a job from any source.
    
    Args:
        raw_job: Raw job data
        source: Source identifier (serpapi, indeed, zyte, etc.)
        
    Returns:
        Normalized job data
    """
    source_lower = source.lower()
    
    if source_lower == "serpapi":
        return normalize_serpapi_job(raw_job)
    elif source_lower == "indeed":
        return normalize_indeed_job(raw_job)
    elif source_lower == "zyte":
        return normalize_zyte_job(raw_job)
    else:
        # Generic normalization for unknown sources
        return {
            "title": raw_job.get("title", ""),
            "company": raw_job.get("company", ""),
            "location": raw_job.get("location", ""),
            "salary": raw_job.get("salary"),
            "description": raw_job.get("description", ""),
            "url": raw_job.get("link") or raw_job.get("url", ""),
            "source": source,
            "external_id": raw_job.get("id") or raw_job.get("external_id"),
            "date_posted": raw_job.get("date_posted") or raw_job.get("posted_at"),
            "job_type": raw_job.get("job_type") or raw_job.get("employment_type"),
        }


def _extract_indeed_job_id(url: str) -> Optional[str]:
    """Extract job ID from Indeed URL.
    
    Args:
        url: Indeed job URL
        
    Returns:
        Job ID or None
    """
    if not url:
        return None
    
    # Indeed job URLs typically contain jk parameter
    # Example: https://www.indeed.com/viewjob?jk=abc123
    try:
        if "jk=" in url:
            return url.split("jk=")[1].split("&")[0]
    except Exception:
        pass
    
    return None


def get_upsert_key(job: dict[str, Any]) -> tuple[str, Any]:
    """Get the key for upserting a job (avoiding duplicates).
    
    Args:
        job: Normalized job data
        
    Returns:
        Tuple of (key_type, key_value)
    """
    # Prefer URL as unique identifier
    if job.get("url"):
        return ("url", job["url"])
    
    # Fall back to (source, external_id)
    if job.get("external_id"):
        return ("source_external_id", (job.get("source"), job["external_id"]))
    
    # If neither is available, generate a hash from key fields
    # This is a last resort
    key_fields = (
        job.get("title", ""),
        job.get("company", ""),
        job.get("location", ""),
    )
    return ("hash", hash(key_fields))


def deduplicate_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate jobs from a list.
    
    Args:
        jobs: List of normalized jobs
        
    Returns:
        Deduplicated list of jobs
    """
    seen = set()
    unique_jobs = []
    
    for job in jobs:
        key_type, key_value = get_upsert_key(job)
        
        # Convert to hashable type
        if isinstance(key_value, tuple):
            key = (key_type, *key_value)
        else:
            key = (key_type, key_value)
        
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    
    return unique_jobs
