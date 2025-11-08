"""
Internal Playwright-based web scraping driver.

Optional fallback scraper using Playwright for direct site scraping.
Includes rate limiting and robots.txt respect.
"""

import asyncio
from typing import Any, Dict, List, Optional
from urllib.robotparser import RobotFileParser
import time

from backend.lib.settings import settings

# Try to import Playwright, but don't fail if not available
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# Simple rate limiter
class RateLimiter:
    """Rate limiter to avoid overwhelming target sites."""
    
    def __init__(self, calls_per_minute: int = 10):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self.last_call = 0.0
    
    async def acquire(self):
        """Wait if necessary to respect rate limit."""
        now = time.time()
        elapsed = now - self.last_call
        
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            await asyncio.sleep(wait_time)
        
        self.last_call = time.time()


# Global rate limiter instance
rate_limiter = RateLimiter(calls_per_minute=6)  # Conservative rate


def check_robots_txt(url: str, user_agent: str = "JobSleuthBot") -> bool:
    """
    Check if scraping is allowed by robots.txt.
    
    Args:
        url: URL to check
        user_agent: User agent string
        
    Returns:
        True if scraping is allowed
    """
    try:
        # Extract base URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        
        return rp.can_fetch(user_agent, url)
    except Exception:
        # If we can't read robots.txt, assume it's okay
        return True


async def scrape_with_playwright(
    url: str,
    selectors: Dict[str, str],
    respect_robots: bool = True
) -> List[Dict[str, Any]]:
    """
    Scrape a webpage using Playwright.
    
    Args:
        url: URL to scrape
        selectors: Dictionary of CSS selectors for extracting data
        respect_robots: Whether to respect robots.txt
        
    Returns:
        List of extracted job data
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise Exception("Playwright not available. Install with: playwright install")
    
    if not settings.FEATURE_SCRAPE_INTERNAL:
        raise Exception("Internal scraping is disabled via feature flag")
    
    # Check robots.txt
    if respect_robots and not check_robots_txt(url):
        raise Exception(f"Scraping not allowed by robots.txt: {url}")
    
    # Rate limiting
    await rate_limiter.acquire()
    
    results = []
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=settings.HEADLESS,
            proxy={"server": settings.PROXY_URL} if settings.PROXY_URL else None
        )
        
        try:
            # Create page with realistic user agent
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            
            # Navigate to URL
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for job listings to load
            job_list_selector = selectors.get("job_list", ".job-card")
            await page.wait_for_selector(job_list_selector, timeout=10000)
            
            # Extract job cards
            job_elements = await page.query_selector_all(job_list_selector)
            
            for element in job_elements[:20]:  # Limit to 20 per page
                try:
                    job_data = {}
                    
                    # Extract each field using provided selectors
                    for field, selector in selectors.items():
                        if field == "job_list":
                            continue
                        
                        try:
                            field_element = await element.query_selector(selector)
                            if field_element:
                                if field == "url":
                                    job_data[field] = await field_element.get_attribute("href")
                                else:
                                    job_data[field] = await field_element.inner_text()
                        except Exception:
                            pass
                    
                    if job_data:
                        results.append(job_data)
                        
                except Exception as e:
                    print(f"Error extracting job: {e}")
                    continue
                    
        finally:
            await browser.close()
    
    return results


async def scrape_indeed_internal(query: str, location: str) -> List[Dict[str, Any]]:
    """
    Scrape Indeed using Playwright (internal method).
    
    Args:
        query: Job search query
        location: Location string
        
    Returns:
        List of job dictionaries
    """
    # Build Indeed search URL
    base_url = "https://www.indeed.com/jobs"
    params = f"?q={query.replace(' ', '+')}&l={location.replace(' ', '+')}"
    url = base_url + params
    
    # Define selectors for Indeed (these may need updates as site changes)
    selectors = {
        "job_list": ".job_seen_beacon",
        "title": ".jobTitle",
        "company": ".companyName",
        "location": ".companyLocation",
        "salary": ".salary-snippet",
        "url": "h2.jobTitle a"
    }
    
    return await scrape_with_playwright(url, selectors)
