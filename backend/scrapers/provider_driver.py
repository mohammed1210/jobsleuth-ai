"""
Provider-based job scraping driver.

Uses external APIs (SerpAPI, Zyte, etc.) to scrape job listings.
"""

from typing import Any, Dict, List, Optional
import httpx

from backend.lib.settings import settings


async def scrape_with_serpapi(
    query: str,
    location: str,
    num_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Scrape job listings using SerpAPI.
    
    Args:
        query: Search query (job title, keywords)
        location: Location string
        num_results: Number of results to fetch
        
    Returns:
        List of raw job dictionaries from API
    """
    if not settings.PROVIDER_API_KEY:
        raise Exception("PROVIDER_API_KEY not configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://serpapi.com/search",
            params={
                "engine": "google_jobs",
                "q": query,
                "location": location,
                "api_key": settings.PROVIDER_API_KEY,
                "num": num_results
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise Exception(f"SerpAPI request failed: {response.text}")
        
        data = response.json()
        return data.get("jobs_results", [])


async def scrape_jobs(
    query: str,
    location: str = "",
    provider: str = "serpapi",
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Scrape jobs using configured provider.
    
    Args:
        query: Search query
        location: Location string
        provider: Provider name (serpapi, zyte, etc.)
        limit: Max number of results
        
    Returns:
        List of raw job data from provider
    """
    if settings.SCRAPE_PROVIDER == "off":
        return []
    
    if provider == "serpapi":
        return await scrape_with_serpapi(query, location, limit)
    else:
        raise Exception(f"Unsupported provider: {provider}")
