"""FastAPI application entry point for JobSleuth AI backend.

This file sets up the FastAPI app with CORS and includes routes for
billing and authentication. A simple health check endpoint is provided
for monitoring deployments.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import stripe_routes, stripe_portal, stripe_webhook

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

@app.get("/health")
async def health() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}
