"""Provider-based job scraper (SerpAPI, Zyte, etc)."""

from typing import Any, Dict, List, Optional

from lib.settings import settings


async def scrape_jobs_from_provider(
    query: str,
    location: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Scrape jobs using external provider API (SerpAPI, Zyte, etc).
    
    This is a stub implementation. In production, you'd integrate with:
    - SerpAPI for Google Jobs
    - Zyte for general web scraping
    - Other job board APIs
    """
    if settings.SCRAPE_PROVIDER == "off" or not settings.PROVIDER_API_KEY:
        return []
    
    # Stub implementation - return empty list
    # In production, make actual API calls:
    # if settings.SCRAPE_PROVIDER == "serpapi":
    #     response = requests.get(
    #         "https://serpapi.com/search",
    #         params={
    #             "api_key": settings.PROVIDER_API_KEY,
    #             "engine": "google_jobs",
    #             "q": query,
    #             "location": location,
    #         }
    #     )
    #     return response.json().get("jobs_results", [])
    
    return []
