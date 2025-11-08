"""
Job data normalization utilities.

Converts raw job data from various sources into standardized schema.
"""

import re
from typing import Any, Dict, Optional
from datetime import datetime, timedelta


def extract_salary(salary_str: Optional[str]) -> Dict[str, Optional[int]]:
    """
    Extract salary min/max from salary string.
    
    Args:
        salary_str: Salary string like "$100k - $150k" or "$120,000/year"
        
    Returns:
        Dictionary with salary_min, salary_max, salary_text
    """
    if not salary_str:
        return {"salary_min": None, "salary_max": None, "salary_text": None}
    
    # Remove common prefixes/suffixes
    clean = salary_str.strip()
    
    # Try to find salary numbers (handle k/K for thousands)
    numbers = re.findall(r'\$?([\d,]+)k?', clean, re.IGNORECASE)
    
    if not numbers:
        return {"salary_min": None, "salary_max": None, "salary_text": clean}
    
    # Parse numbers
    parsed = []
    for num_str in numbers:
        num_str = num_str.replace(',', '')
        try:
            num = int(num_str)
            # If ends with 'k' or number < 1000, multiply by 1000
            if 'k' in clean.lower() or num < 1000:
                num *= 1000
            parsed.append(num)
        except ValueError:
            continue
    
    if len(parsed) == 0:
        return {"salary_min": None, "salary_max": None, "salary_text": clean}
    elif len(parsed) == 1:
        # Single number - use as both min and max
        return {"salary_min": parsed[0], "salary_max": parsed[0], "salary_text": clean}
    else:
        # Range - use first as min, last as max
        return {"salary_min": min(parsed), "salary_max": max(parsed), "salary_text": clean}


def parse_relative_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse relative date strings like "2 days ago" or "1 week ago".
    
    Args:
        date_str: Relative date string
        
    Returns:
        datetime object or None
    """
    if not date_str:
        return None
    
    date_str_lower = date_str.lower()
    now = datetime.utcnow()
    
    # Match patterns like "X days ago", "X hours ago", etc.
    match = re.search(r'(\d+)\s*(hour|day|week|month)s?\s*ago', date_str_lower)
    
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'hour':
            return now - timedelta(hours=amount)
        elif unit == 'day':
            return now - timedelta(days=amount)
        elif unit == 'week':
            return now - timedelta(weeks=amount)
        elif unit == 'month':
            return now - timedelta(days=amount * 30)
    
    # If "today" or "just now"
    if 'today' in date_str_lower or 'just now' in date_str_lower:
        return now
    
    # If "yesterday"
    if 'yesterday' in date_str_lower:
        return now - timedelta(days=1)
    
    return None


def normalize_serpapi_job(raw_job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a job from SerpAPI format.
    
    Args:
        raw_job: Raw job dictionary from SerpAPI
        
    Returns:
        Normalized job dictionary matching our schema
    """
    salary_info = extract_salary(raw_job.get('detected_extensions', {}).get('salary'))
    
    return {
        "source": "serpapi",
        "external_id": raw_job.get("job_id"),
        "title": raw_job.get("title", ""),
        "company": raw_job.get("company_name", ""),
        "location": raw_job.get("location", ""),
        "salary_min": salary_info["salary_min"],
        "salary_max": salary_info["salary_max"],
        "salary_text": salary_info["salary_text"],
        "type": raw_job.get("detected_extensions", {}).get("schedule_type"),
        "url": raw_job.get("share_link") or raw_job.get("link") or f"https://google.com/search?q={raw_job.get('title', '')}",
        "posted_at": parse_relative_date(raw_job.get("detected_extensions", {}).get("posted_at")),
        "raw": raw_job
    }


def normalize_playwright_job(raw_job: Dict[str, Any], source: str = "internal") -> Dict[str, Any]:
    """
    Normalize a job scraped with Playwright.
    
    Args:
        raw_job: Raw job dictionary from Playwright scraper
        source: Source identifier
        
    Returns:
        Normalized job dictionary
    """
    salary_info = extract_salary(raw_job.get("salary"))
    
    # Generate external_id from URL if available
    external_id = None
    if raw_job.get("url"):
        # Try to extract ID from URL
        id_match = re.search(r'/([\w-]+)/?$', raw_job["url"])
        if id_match:
            external_id = id_match.group(1)
    
    return {
        "source": source,
        "external_id": external_id,
        "title": raw_job.get("title", "").strip(),
        "company": raw_job.get("company", "").strip(),
        "location": raw_job.get("location", "").strip(),
        "salary_min": salary_info["salary_min"],
        "salary_max": salary_info["salary_max"],
        "salary_text": salary_info["salary_text"],
        "type": raw_job.get("type"),
        "url": raw_job.get("url", ""),
        "posted_at": parse_relative_date(raw_job.get("posted")),
        "raw": raw_job
    }


def normalize_job(raw_job: Dict[str, Any], source_type: str) -> Dict[str, Any]:
    """
    Normalize a job from any source to our standard schema.
    
    Args:
        raw_job: Raw job data
        source_type: Type of source (serpapi, playwright, manual, etc.)
        
    Returns:
        Normalized job dictionary ready for database insertion
    """
    if source_type == "serpapi":
        return normalize_serpapi_job(raw_job)
    elif source_type == "playwright":
        return normalize_playwright_job(raw_job)
    else:
        # Assume it's already normalized or close to it
        return raw_job
