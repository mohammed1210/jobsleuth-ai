"""FastAPI application entry point for JobSleuth AI."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from lib.settings import settings  # noqa: E402
from routes import ai_scoring, digests, jobs, resume_tools, saved_jobs, stripe_portal, stripe_routes, stripe_webhook, users  # noqa: E402

app = FastAPI(title="JobSleuth AI API")


def _allowed_origins() -> list[str]:
    origins = [settings.FRONTEND_URL]
    if settings.ALLOWED_ORIGINS:
        origins.extend(settings.ALLOWED_ORIGINS.split(","))
    return sorted({origin.strip().rstrip("/") for origin in origins if origin.strip()})


app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_origin_regex=r"^https:\/\/.*(\.vercel\.app|\.app\.github\.dev|\.github\.dev)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(saved_jobs.router)
app.include_router(saved_jobs.legacy_router)
app.include_router(ai_scoring.router)
app.include_router(resume_tools.router)
app.include_router(digests.router)
app.include_router(stripe_routes.router)
app.include_router(stripe_portal.router)
app.include_router(stripe_webhook.router)
app.include_router(users.router)


@app.get("/")
def root() -> dict[str, str | bool]:
    return {"ok": True, "service": "jobsleuth-backend"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config")
def config_status() -> dict:
    return {
        "status": "ok",
        "service": "jobsleuth-backend",
        "supabase": {
            "configured": bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY),
            "url_present": bool(settings.SUPABASE_URL),
            "service_role_present": bool(settings.SUPABASE_SERVICE_ROLE_KEY),
        },
        "stripe": {"configured": bool(settings.STRIPE_SECRET_KEY)},
        "openai": {"configured": bool(settings.OPENAI_API_KEY)},
        "email": {
            "configured": bool(settings.EMAIL_SERVER and settings.EMAIL_USER and settings.EMAIL_PASSWORD)
        },
    }


def _require_debug_enabled() -> None:
    if not settings.ENABLE_DEBUG_ROUTES:
        raise HTTPException(status_code=404, detail="Not found")


@app.get("/debug/routes")
def debug_routes() -> dict:
    _require_debug_enabled()
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append(
                {
                    "path": route.path,
                    "methods": sorted(route.methods or []),
                    "name": route.name,
                }
            )
    return {"count": len(routes), "routes": sorted(routes, key=lambda item: item["path"])}
