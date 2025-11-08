"""FastAPI application entry point for JobSleuth AI backend.

This file sets up the FastAPI app with CORS and includes routes for
jobs, users, saved jobs, scoring, resumes, digests, scraping, and billing.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import (
    stripe_routes,
    stripe_portal,
    stripe_webhook,
    jobs,
    saved,
    scoring,
    resumes,
    digests,
    users,
    scrape,
)

app = FastAPI(
    title="JobSleuth AI API",
    description="Backend API for JobSleuth AI job sourcing platform",
    version="1.0.0"
)

# Allow all origins for simplicity; adjust for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router)
app.include_router(saved.router)
app.include_router(scoring.router)
app.include_router(resumes.router)
app.include_router(digests.router)
app.include_router(users.router)
app.include_router(scrape.router)
app.include_router(stripe_routes.router)
app.include_router(stripe_portal.router)
app.include_router(stripe_webhook.router)


@app.get("/health")
async def health() -> dict:
    """Health check endpoint for monitoring."""
    return {"ok": True}


@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": "JobSleuth AI API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }
