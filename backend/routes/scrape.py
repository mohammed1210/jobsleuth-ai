"""Scraping routes for JobSleuth AI."""


from fastapi import APIRouter, HTTPException, Query
from lib.supabase import supabase_admin
from scrapers.normalize import normalize_job_data, upsert_job
from scrapers.playwright_driver import scrape_jobs_with_playwright
from scrapers.provider_driver import scrape_jobs_from_provider

router = APIRouter(prefix="/scrape", tags=["scraping"])


@router.post("/jobs")
async def scrape_and_store_jobs(
    query: str = Query(..., description="Search query"),
    location: str | None = Query(None, description="Location"),
    source: str = Query("provider", description="Source type: provider or internal"),
):
    """Scrape jobs and store them in the database.

    This is an admin endpoint that should be protected in production.
    """
    jobs_scraped = []

    try:
        if source == "provider":
            # Use provider API
            raw_jobs = await scrape_jobs_from_provider(query, location)
            source_name = "provider_api"
        else:
            # Use internal Playwright scraper
            # In production, you'd pass a specific URL
            url = f"https://example.com/jobs?q={query}"
            raw_jobs = await scrape_jobs_with_playwright(url)
            source_name = "playwright"

        # Normalize and upsert each job
        for raw_job in raw_jobs:
            normalized = normalize_job_data(raw_job, source_name)
            stored_job = await upsert_job(normalized, supabase_admin)
            jobs_scraped.append(stored_job)

        return {
            "ok": True,
            "count": len(jobs_scraped),
            "jobs": jobs_scraped,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")
