from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.scrapers.indeed_scraper_playwright import scrape_indeed_playwright

app = FastAPI()

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
async def scrape_indeed_endpoint(query: str, location: str):
    results = await scrape_indeed_playwright(query, location)
    return {"results": results}
