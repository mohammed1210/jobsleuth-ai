import requests
from bs4 import BeautifulSoup

def scrape_indeed(query: str, location: str, limit: int = 10):
    url = f"https://uk.indeed.com/jobs?q={query}&l={location}&limit={limit}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    jobs = []

    for card in soup.select("a.tapItem"):
        title = card.select_one("h2 span")
        company = card.select_one(".companyName")
        loc = card.select_one(".companyLocation")
        link = "https://uk.indeed.com" + card.get("href")
        job = {
            "title": title.text.strip() if title else "N/A",
            "company": company.text.strip() if company else "N/A",
            "location": loc.text.strip() if loc else "N/A",
            "salary": None,
            "link": link,
            "source": "Indeed",
            "date_posted": None
        }
        jobs.append(job)
    return jobs