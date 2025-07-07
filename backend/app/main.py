from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scrapers.indeed_scraper import scrape_indeed

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/scrape/indeed")
def scrape_indeed_endpoint(query: str, location: str):
    results = scrape_indeed(query, location)
    return results
