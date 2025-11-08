"""Digest routes for JobSleuth AI."""

from fastapi import APIRouter, HTTPException, Query, Header

from lib.auth import get_user_id_from_token
from lib.settings import settings
from lib.supabase import supabase_admin
from services.emailer import send_digest_email

router = APIRouter(prefix="/digests", tags=["digests"])


@router.post("/run")
async def run_digest(
    user_id: str = Query(..., description="User ID to send digest to"),
    authorization: str = Header(...),
):
    """Run digest for a specific user (admin only via AUTH_SCRAPER_KEY)."""
    # Verify admin token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.replace("Bearer ", "")
    if token != settings.AUTH_SCRAPER_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        # Get user
        user_response = supabase_admin.table("users").select("*").eq("id", user_id).execute()
        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = user_response.data[0]
        user_email = user.get("email")
        if not user_email:
            raise HTTPException(status_code=400, detail="User has no email")
        
        # Get user's digest preferences
        digest_response = supabase_admin.table("digests").select("*").eq("user_id", user_id).execute()
        
        # Get recent jobs (for now, just get recent 10)
        jobs_response = supabase_admin.table("jobs")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(10)\
            .execute()
        
        jobs = jobs_response.data or []
        
        # Send email
        success = await send_digest_email(user_email, jobs)
        
        if success:
            # Update last_sent timestamp
            if digest_response.data:
                supabase_admin.table("digests")\
                    .update({"last_sent": "now()"})\
                    .eq("user_id", user_id)\
                    .execute()
            
            return {"ok": True, "message": f"Digest sent to {user_email}"}
        else:
            return {"ok": False, "message": "Failed to send email (no email service configured)"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run digest: {str(e)}")
