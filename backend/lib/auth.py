"""
Authentication utilities for JobSleuth AI backend.

Handles JWT token validation and user extraction from Supabase auth.
"""

from typing import Optional
from fastapi import HTTPException, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import PyJWTError

from backend.lib.settings import settings


security = HTTPBearer(auto_error=False)


def decode_jwt(token: str) -> dict:
    """
    Decode and validate a Supabase JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Supabase uses the SUPABASE_SERVICE_KEY as the JWT secret
        # For development, we'll skip verification if service key is not set
        if not settings.SUPABASE_SERVICE_KEY or len(settings.SUPABASE_SERVICE_KEY) < 10:
            # In development, do minimal validation
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        
        # In production, properly verify the signature
        payload = jwt.decode(
            token,
            settings.SUPABASE_SERVICE_KEY,
            algorithms=["HS256"],
            options={"verify_exp": True}
        )
        return payload
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[str]:
    """
    Extract user ID from JWT token in Authorization header.
    
    Args:
        credentials: HTTP Authorization credentials from FastAPI
        
    Returns:
        User ID (UUID) or None if not authenticated
    """
    if not credentials:
        return None
    
    try:
        payload = decode_jwt(credentials.credentials)
        user_id = payload.get("sub")
        return user_id
    except HTTPException:
        return None


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> str:
    """
    Require authentication and return user ID.
    
    Args:
        credentials: HTTP Authorization credentials from FastAPI
        
    Returns:
        User ID (UUID)
        
    Raises:
        HTTPException: If not authenticated
    """
    user_id = get_current_user_id(credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id


def verify_scraper_key(authorization: Optional[str] = Header(None)) -> bool:
    """
    Verify the scraper/admin API key.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        True if key is valid
        
    Raises:
        HTTPException: If key is invalid or missing
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Support both "Bearer <key>" and direct key
    key = authorization
    if authorization.startswith("Bearer "):
        key = authorization[7:]
    
    if key != settings.AUTH_SCRAPER_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return True


def get_user_from_token_or_none(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Get user ID from Authorization header, return None if invalid/missing.
    
    Useful for optional authentication endpoints.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        User ID or None
    """
    if not authorization:
        return None
    
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    
    try:
        payload = decode_jwt(token)
        return payload.get("sub")
    except Exception:
        return None
