"""FastAPI application entry point for JobSleuth AI backend.

This file sets up the FastAPI app with CORS and includes routes for
billing, authentication, jobs, saved jobs, and user management.
A simple health check endpoint is provided for monitoring deployments.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import stripe_routes, stripe_portal, stripe_webhook
from routes import jobs, saved_jobs, users

app = FastAPI()

# Allow all origins for simplicity; adjust for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include subrouters
app.include_router(stripe_routes.router)
app.include_router(stripe_portal.router)
app.include_router(stripe_webhook.router)
app.include_router(jobs.router)
app.include_router(saved_jobs.router)
app.include_router(users.router)

@app.get("/health")
async def health() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}
