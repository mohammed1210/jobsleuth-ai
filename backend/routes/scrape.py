"""
Scraping API routes.

Endpoints for triggering job scraping and importing jobs.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query, Depends

from backend.lib.auth import verify_scraper_key
from backend.lib.supabase import upsert_job
from backend.scrapers.provider_driver import scrape_jobs as scrape_with_provider
from backend.scrapers.normalize import normalize_job


router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.post("/")
async def scrape_and_import(
    query: str = Query(..., description="Search query"),
    location: str = Query("", description="Location"),
    provider: str = Query("serpapi", description="Scraping provider"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    _verified: bool = Depends(verify_scraper_key)
) -> Dict[str, Any]:
    """
    Scrape jobs from external providers and import to database.
    
    Requires AUTH_SCRAPER_KEY for authentication.
    
    Args:
        query: Job search query
        location: Location string
        provider: Provider to use (serpapi, etc.)
        limit: Maximum number of jobs to scrape
        
    Returns:
        Dictionary with scraping results and imported job count
    """
    try:
        # Scrape jobs
        raw_jobs = await scrape_with_provider(query, location, provider, limit)
        
        if not raw_jobs:
            return {
                "message": "No jobs found",
                "scraped": 0,
                "imported": 0,
                "jobs": []
            }
        
        # Normalize and import jobs
        imported = []
        errors = []
        
        for raw_job in raw_jobs:
            try:
                # Normalize job data
                normalized = normalize_job(raw_job, provider)
                
                # Upsert to database
                result = await upsert_job(normalized)
                imported.append(result)
                
            except Exception as e:
                errors.append({
                    "job": raw_job.get("title", "Unknown"),
                    "error": str(e)
                })
        
        return {
            "message": f"Scraped {len(raw_jobs)} jobs, imported {len(imported)}",
            "scraped": len(raw_jobs),
            "imported": len(imported),
            "errors": errors,
            "jobs": imported[:10]  # Return first 10 for preview
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")
