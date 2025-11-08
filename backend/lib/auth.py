"""Authentication utilities for JobSleuth AI backend."""

from typing import Optional

from fastapi import Header, HTTPException


def get_user_id_from_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract user ID from Supabase JWT token.
    
    This is a simplified version. In production, you'd verify the JWT signature.
    For now, we rely on Supabase RLS to enforce security.
    """
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    # In a real implementation, decode and verify the JWT
    # For now, return None to indicate token exists but needs verification
    # The actual user_id will be obtained from Supabase client
    return authorization.replace("Bearer ", "")


def require_auth(authorization: Optional[str] = Header(None)) -> str:
    """Require authentication and return token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    return authorization.replace("Bearer ", "")
