"""
Email digest API routes.

Endpoints for managing and sending job email digests.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from backend.lib.auth import verify_scraper_key
from backend.lib.supabase import get_supabase_client, get_user_by_email
from backend.services.emailer import send_job_digest


router = APIRouter(prefix="/digests", tags=["digests"])


@router.post("/run")
async def run_digest(
    user_id: Optional[str] = Query(None, description="User ID to send digest to"),
    _verified: bool = Depends(verify_scraper_key)
) -> Dict[str, Any]:
    """
    Run email digest for a specific user (admin endpoint).
    
    Requires AUTH_SCRAPER_KEY for authentication.
    
    Args:
        user_id: User UUID to send digest to
        
    Returns:
        Success message and email status
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id parameter required")
    
    client = get_supabase_client()
    
    # Get user info
    user_result = client.table("users").select("*").eq("id", user_id).execute()
    if not user_result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = user_result.data[0]
    
    # Get digest settings
    digest_result = client.table("digests").select("*").eq("user_id", user_id).eq("active", True).execute()
    if not digest_result.data:
        raise HTTPException(status_code=404, detail="No active digest found for user")
    
    digest = digest_result.data[0]
    filters = digest.get("filters", {})
    
    # Query for matching jobs
    jobs_query = client.table("jobs").select("*").limit(20)
    
    # Apply filters from digest settings
    if filters.get("location"):
        jobs_query = jobs_query.ilike("location", f"%{filters['location']}%")
    
    if filters.get("minSalary"):
        min_sal = filters["minSalary"]
        jobs_query = jobs_query.or_(f"salary_min.gte.{min_sal},salary_max.gte.{min_sal}")
    
    if filters.get("type"):
        jobs_query = jobs_query.eq("type", filters["type"])
    
    jobs_result = jobs_query.order("posted_at", desc=True).execute()
    jobs = jobs_result.data
    
    if not jobs:
        return {
            "message": "No jobs found matching filters",
            "user_id": user_id,
            "jobs_count": 0
        }
    
    # Send digest email
    try:
        email_result = await send_job_digest(
            user_email=user["email"],
            jobs=jobs,
            cadence=digest.get("cadence", "weekly")
        )
        
        # Update last_sent timestamp
        client.table("digests").update({
            "last_sent": "now()"
        }).eq("id", digest["id"]).execute()
        
        return {
            "message": "Digest sent successfully",
            "user_id": user_id,
            "email": user["email"],
            "jobs_count": len(jobs),
            "email_id": email_result.get("id")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send digest: {str(e)}")
