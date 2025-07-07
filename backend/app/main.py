from fastapi import FastAPI, Query
from .scrapers.indeed_scraper import scrape_indeed
from .models import Job
from .schemas import JobResponse
from typing import List

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/scrape/indeed", response_model=List[JobResponse])
def get_indeed_jobs(query: str = "Software Engineer", location: str = "London"):
    jobs_data = scrape_indeed(query, location)
    return jobs_data

@app.get("/api/jobs", response_model=List[JobResponse])
def get_jobs_stub():
    # Placeholder, DB connection needed
    return []