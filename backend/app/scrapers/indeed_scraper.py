
import requests
from bs4 import BeautifulSoup

def scrape_indeed(query, location):
    jobs = []
    query = query.replace(" ", "+")
    location = location.replace(" ", "+")
    url = f"https://www.indeed.co.uk/jobs?q={query}&l={location}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    for div in soup.find_all("a", attrs={"class": "tapItem"}):
        title_elem = div.find("h2", {"class": "jobTitle"})
        company_elem = div.find("span", {"class": "companyName"})
        location_elem = div.find("div", {"class": "companyLocation"})

        title = title_elem.get_text(strip=True) if title_elem else None
        company = company_elem.get_text(strip=True) if company_elem else None
        location = location_elem.get_text(strip=True) if location_elem else None

        job_link = "https://www.indeed.co.uk" + div.get("href") if div.get("href") else None

        if title and company and job_link:
            jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "salary": None,
                "link": job_link,
                "source": "Indeed",
                "date_posted": None
            })

    return jobs
