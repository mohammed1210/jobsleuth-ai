"""User and plan management routes with bearer token precedence."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from enum import Enum

router = APIRouter(prefix="/users", tags=["users"])


class PlanType(str, Enum):
    """User plan types."""
    FREE = "free"
    PRO = "pro"
    INVESTOR = "investor"


class UserPlanResponse(BaseModel):
    """User plan response."""
    user_id: str
    email: str
    plan: PlanType
    features: dict[str, bool]


def verify_bearer_token(authorization: Optional[str]) -> str:
    """Verify bearer token with precedence and return user ID.
    
    Bearer token takes precedence over other auth methods.
    
    Args:
        authorization: Authorization header
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(
            status_code=401, 
            detail="Authorization required. Please provide a Bearer token."
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Invalid authorization format. Expected: Bearer <token>"
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    # Mock validation - in production, validate with Supabase JWT
    if not token or token == "invalid":
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Return mock user ID - in production, decode JWT and get user ID
    # The JWT validation takes precedence over any other auth method
    return "user_123"


@router.get("/me/plan", response_model=UserPlanResponse)
async def get_user_plan(
    authorization: Optional[str] = Header(None)
) -> UserPlanResponse:
    """Get the authenticated user's plan (bearer token precedence).
    
    Args:
        authorization: Bearer token (takes precedence)
        
    Returns:
        User plan details
        
    Raises:
        HTTPException: If unauthorized
    """
    # Bearer token verification takes precedence
    user_id = verify_bearer_token(authorization)
    
    # Mock implementation - in production, query database
    mock_plan = UserPlanResponse(
        user_id=user_id,
        email="user@example.com",
        plan=PlanType.PRO,
        features={
            "unlimited_saved_jobs": True,
            "ai_scores": True,
            "advanced_filters": True,
            "email_alerts": True,
        },
    )
    
    return mock_plan


@router.get("/me", response_model=dict)
async def get_user_profile(
    authorization: Optional[str] = Header(None)
) -> dict:
    """Get the authenticated user's profile (bearer token precedence).
    
    Args:
        authorization: Bearer token (takes precedence)
        
    Returns:
        User profile
        
    Raises:
        HTTPException: If unauthorized
    """
    # Bearer token verification takes precedence
    user_id = verify_bearer_token(authorization)
    
    # Mock implementation
    return {
        "user_id": user_id,
        "email": "user@example.com",
        "name": "John Doe",
        "created_at": "2024-01-01T00:00:00Z",
    }


@router.put("/me", response_model=dict)
async def update_user_profile(
    profile_data: dict,
    authorization: Optional[str] = Header(None)
) -> dict:
    """Update the authenticated user's profile (bearer token precedence).
    
    Args:
        profile_data: Profile update data
        authorization: Bearer token (takes precedence)
        
    Returns:
        Updated profile
        
    Raises:
        HTTPException: If unauthorized
    """
    # Bearer token verification takes precedence
    user_id = verify_bearer_token(authorization)
    
    # Mock implementation - in production, update database
    return {
        "status": "success",
        "user_id": user_id,
        "updated_fields": list(profile_data.keys()),
    }
