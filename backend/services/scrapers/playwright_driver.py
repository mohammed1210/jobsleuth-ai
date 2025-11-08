"""Playwright-based scraping driver with rate limiting and robots.txt support.

This module provides an internal scraping option using Playwright.
Supports HEADLESS mode and optional PROXY_URL.
"""

import os
import asyncio
from typing import Any, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, Browser, Page


class RateLimiter:
    """Simple rate limiter for web scraping."""
    
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests: list[datetime] = []
    
    async def wait_if_needed(self):
        """Wait if rate limit is reached."""
        now = datetime.now()
        # Remove requests older than 1 minute
        self.requests = [req for req in self.requests if now - req < timedelta(minutes=1)]
        
        if len(self.requests) >= self.requests_per_minute:
            # Wait until the oldest request is more than 1 minute old
            oldest = self.requests[0]
            wait_time = 60 - (now - oldest).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.requests = self.requests[1:]
        
        self.requests.append(now)


class PlaywrightDriver:
    """Playwright-based web scraping driver with rate limiting and robots.txt support."""
    
    def __init__(self):
        self.headless = os.getenv("HEADLESS", "true").lower() == "true"
        self.proxy_url = os.getenv("PROXY_URL")
        self.respect_robots = os.getenv("RESPECT_ROBOTS_TXT", "true").lower() == "true"
        self.rate_limiter = RateLimiter(
            requests_per_minute=int(os.getenv("SCRAPE_RATE_LIMIT", "10"))
        )
        self.robots_cache: dict[str, RobotFileParser] = {}
    
    def _get_robots_parser(self, url: str) -> Optional[RobotFileParser]:
        """Get robots.txt parser for a URL."""
        if not self.respect_robots:
            return None
        
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        if base_url not in self.robots_cache:
            robots_url = f"{base_url}/robots.txt"
            parser = RobotFileParser()
            parser.set_url(robots_url)
            try:
                parser.read()
                self.robots_cache[base_url] = parser
            except Exception as e:
                print(f"Failed to read robots.txt from {robots_url}: {e}")
                # If we can't read robots.txt, allow scraping
                self.robots_cache[base_url] = None
        
        return self.robots_cache[base_url]
    
    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Check if URL can be fetched according to robots.txt."""
        if not self.respect_robots:
            return True
        
        parser = self._get_robots_parser(url)
        if parser is None:
            return True
        
        return parser.can_fetch(user_agent, url)
    
    async def scrape_page(
        self,
        url: str,
        wait_selector: Optional[str] = None,
        timeout: int = 30000
    ) -> Optional[str]:
        """Scrape a single page.
        
        Args:
            url: URL to scrape
            wait_selector: Optional CSS selector to wait for
            timeout: Page load timeout in milliseconds
            
        Returns:
            HTML content of the page or None if failed
        """
        if not self.can_fetch(url):
            print(f"Scraping not allowed by robots.txt: {url}")
            return None
        
        await self.rate_limiter.wait_if_needed()
        
        async with async_playwright() as p:
            browser_args = {"headless": self.headless}
            
            if self.proxy_url:
                browser_args["proxy"] = {"server": self.proxy_url}
            
            browser = await p.chromium.launch(**browser_args)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(url, timeout=timeout)
                
                if wait_selector:
                    await page.wait_for_selector(wait_selector, timeout=timeout)
                
                content = await page.content()
                await browser.close()
                return content
            except Exception as e:
                print(f"Failed to scrape {url}: {e}")
                await browser.close()
                return None
    
    async def scrape_jobs_indeed(
        self,
        query: str,
        location: str = "",
        max_results: int = 10
    ) -> list[dict[str, Any]]:
        """Scrape jobs from Indeed using Playwright.
        
        Args:
            query: Job search query
            location: Location filter
            max_results: Maximum number of results
            
        Returns:
            List of raw job data
        """
        jobs = []
        query_str = query.replace(" ", "+")
        location_str = location.replace(" ", "+")
        url = f"https://www.indeed.com/jobs?q={query_str}&l={location_str}"
        
        if not self.can_fetch(url):
            print(f"Scraping not allowed by robots.txt: {url}")
            return []
        
        await self.rate_limiter.wait_if_needed()
        
        async with async_playwright() as p:
            browser_args = {"headless": self.headless}
            
            if self.proxy_url:
                browser_args["proxy"] = {"server": self.proxy_url}
            
            browser = await p.chromium.launch(**browser_args)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(url, timeout=30000)
                
                # Wait for job listings
                await page.wait_for_selector(".job_seen_beacon", timeout=30000)
                
                # Extract job data
                job_cards = await page.query_selector_all(".job_seen_beacon")
                
                for i, card in enumerate(job_cards):
                    if i >= max_results:
                        break
                    
                    try:
                        title_elem = await card.query_selector("h2.jobTitle")
                        title = await title_elem.inner_text() if title_elem else "N/A"
                        
                        company_elem = await card.query_selector(".companyName")
                        company = await company_elem.inner_text() if company_elem else "N/A"
                        
                        location_elem = await card.query_selector(".companyLocation")
                        loc = await location_elem.inner_text() if location_elem else "N/A"
                        
                        salary_elem = await card.query_selector(".salary-snippet")
                        salary = await salary_elem.inner_text() if salary_elem else None
                        
                        link_elem = await card.query_selector("h2.jobTitle a")
                        href = await link_elem.get_attribute("href") if link_elem else None
                        job_link = f"https://www.indeed.com{href}" if href else None
                        
                        jobs.append({
                            "title": title,
                            "company": company,
                            "location": loc,
                            "salary": salary,
                            "link": job_link,
                            "source": "Indeed",
                            "date_posted": None,
                        })
                    except Exception as e:
                        print(f"Error extracting job {i}: {e}")
                
                await browser.close()
            except Exception as e:
                print(f"Failed to scrape Indeed: {e}")
                await browser.close()
        
        return jobs
