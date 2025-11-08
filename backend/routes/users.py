"""
User API routes.

Endpoints for user profile and plan management.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, Header

from backend.lib.supabase import get_user_by_email, get_supabase_client
from backend.lib.auth import get_user_from_token_or_none


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/plan")
async def get_user_plan(
    email: Optional[str] = Query(None, description="User email (fallback if no Bearer token)"),
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Get user's subscription plan.
    
    Prioritizes Bearer token authentication, falls back to email parameter.
    Returns plan='free' if user not found.
    
    Args:
        email: Optional user email (query parameter fallback)
        authorization: Optional Authorization header with Bearer token
        
    Returns:
        Dictionary with plan and stripe_customer_id
    """
    user_id = None
    user_email = None
    
    # First, try to get user from Bearer token
    if authorization:
        user_id = get_user_from_token_or_none(authorization)
    
    # If we have user_id from token, look up by ID
    if user_id:
        client = get_supabase_client()
        result = client.table("users").select("*").eq("id", user_id).execute()
        
        if result.data:
            user = result.data[0]
            return {
                "plan": user.get("plan", "free"),
                "stripe_customer_id": user.get("stripe_customer_id")
            }
    
    # Fallback to email parameter
    if email:
        user = await get_user_by_email(email)
        if user:
            return {
                "plan": user.get("plan", "free"),
                "stripe_customer_id": user.get("stripe_customer_id")
            }
    
    # Default response if no user found
    return {
        "plan": "free",
        "stripe_customer_id": None
    }
