import asyncio
from playwright.async_api import async_playwright

async def scrape_indeed_playwright(query: str, location: str, max_results: int = 10):
    jobs = []
    query_str = query.replace(" ", "+")
    location_str = location.replace(" ", "+")
    url = f"https://www.indeed.co.uk/jobs?q={query_str}&l={location_str}"

    async with async_playwright() as p:
        # Headless False for debugging if running locally
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"Navigating to: {url}")
        await page.goto(url)

        # Accept cookies if present
        try:
            await page.get_by_text("Accept all cookies").click(timeout=3000)
            print("✅ Accepted cookies.")
        except:
            print("No cookie popup or already accepted.")

        # Take screenshot before waiting for selector
        print("Taking debug screenshot...")
        await page.screenshot(path="page_debug.png", full_page=True)
        print("✅ Screenshot saved as page_debug.png")

        # Wait for job cards to load (extended timeout)
        try:
            await page.wait_for_selector("a.tapItem", timeout=30000)
        except Exception as e:
            print(f"❌ Selector wait failed: {e}")
            await browser.close()
            return []

        job_cards = await page.query_selector_all("a.tapItem")
        for i, card in enumerate(job_cards):
            if i >= max_results:
                break
            try:
                title_elem = await card.query_selector("h2.jobTitle span")
                title = await title_elem.inner_text() if title_elem else "N/A"

                company_elem = await card.query_selector("span.companyName")
                company = await company_elem.inner_text() if company_elem else "N/A"

                location_elem = await card.query_selector("div.companyLocation")
                location_text = await location_elem.inner_text() if location_elem else "N/A"

                href = await card.get_attribute("href")
                job_link = "https://www.indeed.co.uk" + href if href else "#"

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location_text,
                    "salary": None,
                    "link": job_link,
                    "source": "Indeed",
                    "date_posted": None
                })
                print(f"✅ {title} | {company} | {location_text}")

            except Exception as e:
                print(f"❌ Error extracting job {i}: {e}")

        await browser.close()
    return jobs
