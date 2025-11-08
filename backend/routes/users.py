"""User routes for JobSleuth AI."""

from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query

from lib.auth import get_user_id_from_token
from lib.supabase import supabase, supabase_admin

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/plan")
async def get_user_plan(
    authorization: Optional[str] = Header(None),
    email: Optional[str] = Query(None, description="Email fallback for plan lookup"),
):
    """Get user plan. Prefers Authorization header, falls back to email query parameter."""
    try:
        user_data = None
        
        # Try to get user from Bearer token first
        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
            try:
                # Get user from token - in production this would verify JWT
                auth_response = supabase.auth.get_user(token)
                if auth_response and hasattr(auth_response, 'user') and auth_response.user:
                    user_email = auth_response.user.email
                    if user_email:
                        response = supabase_admin.table("users").select("*").eq("email", user_email).execute()
                        if response.data:
                            user_data = response.data[0]
            except Exception:
                pass  # Fall back to email parameter
        
        # Fallback to email parameter
        if not user_data and email:
            response = supabase_admin.table("users").select("*").eq("email", email).execute()
            if response.data:
                user_data = response.data[0]
        
        # Return default if user not found
        if not user_data:
            return {
                "plan": "free",
                "stripe_customer_id": None,
            }
        
        return {
            "plan": user_data.get("plan", "free"),
            "stripe_customer_id": user_data.get("stripe_customer_id"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user plan: {str(e)}")
