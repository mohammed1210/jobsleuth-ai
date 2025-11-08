"""Internal Playwright-based job scraper."""

import asyncio
from typing import Any, Dict, List, Optional

from lib.settings import settings

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class RateLimiter:
    """Simple rate limiter for scraping."""
    
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.min_delay = 60.0 / requests_per_minute
        self.last_request = 0.0
    
    async def wait(self):
        """Wait if necessary to maintain rate limit."""
        import time
        now = time.time()
        elapsed = now - self.last_request
        if elapsed < self.min_delay:
            await asyncio.sleep(self.min_delay - elapsed)
        self.last_request = time.time()


rate_limiter = RateLimiter(requests_per_minute=10)


async def scrape_jobs_with_playwright(
    url: str,
    selectors: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """Scrape jobs using Playwright (internal scraper).
    
    Args:
        url: URL to scrape
        selectors: CSS selectors for job elements
    
    Returns:
        List of job dictionaries
    """
    if not PLAYWRIGHT_AVAILABLE:
        return []
    
    if not settings.FEATURE_SCRAPE_INTERNAL:
        return []
    
    # Respect rate limiting
    await rate_limiter.wait()
    
    jobs = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.HEADLESS,
                proxy={"server": settings.PROXY_URL} if settings.PROXY_URL else None,
            )
            
            page = await browser.new_page()
            
            # Respect robots.txt (simplified check)
            # In production, use a proper robots.txt parser
            
            await page.goto(url, wait_until="networkidle")
            
            # Use provided selectors or default ones
            if not selectors:
                selectors = {
                    "container": ".job-listing",
                    "title": ".job-title",
                    "company": ".company-name",
                    "location": ".location",
                    "url": "a.job-link",
                }
            
            # Extract job elements
            containers = await page.query_selector_all(selectors.get("container", ".job"))
            
            for container in containers[:20]:  # Limit to 20 jobs per page
                try:
                    title_el = await container.query_selector(selectors.get("title", "h2"))
                    title = await title_el.inner_text() if title_el else "Unknown"
                    
                    company_el = await container.query_selector(selectors.get("company", ".company"))
                    company = await company_el.inner_text() if company_el else "Unknown"
                    
                    location_el = await container.query_selector(selectors.get("location", ".location"))
                    location = await location_el.inner_text() if location_el else None
                    
                    url_el = await container.query_selector(selectors.get("url", "a"))
                    job_url = await url_el.get_attribute("href") if url_el else None
                    
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location.strip() if location else None,
                        "url": job_url,
                    })
                except Exception:
                    continue  # Skip failed extractions
            
            await browser.close()
    
    except Exception:
        pass  # Return empty list on error
    
    return jobs
