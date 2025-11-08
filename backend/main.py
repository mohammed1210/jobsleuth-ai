"""FastAPI application entry point for JobSleuth AI backend.

This file sets up the FastAPI app with CORS and includes routes for
billing, authentication, jobs, scoring, and more.
A simple health check endpoint is provided for monitoring deployments.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import (
    digests,
    jobs,
    resumes,
    saved,
    scoring,
    scrape,
    stripe_portal,
    stripe_routes,
    stripe_webhook,
    users,
)

app = FastAPI(title="JobSleuth AI API", version="1.0.0")

# Allow all origins for simplicity; adjust for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(stripe_routes.router)
app.include_router(stripe_portal.router)
app.include_router(stripe_webhook.router)
app.include_router(jobs.router)
app.include_router(users.router)
app.include_router(saved.router)
app.include_router(scoring.router)
app.include_router(resumes.router)
app.include_router(digests.router)
app.include_router(scrape.router)


@app.get("/health")
async def health() -> dict[str, bool]:
    """Simple health check endpoint."""
    return {"ok": True}
