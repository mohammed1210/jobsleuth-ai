"""
Supabase client utilities for JobSleuth AI backend.

Provides functions to interact with Supabase database and auth.
"""

from typing import Any, Dict, List, Optional
from supabase import create_client, Client
from postgrest import APIError

from backend.lib.settings import settings


def get_supabase_client() -> Client:
    """
    Create and return a Supabase client instance.
    
    Returns:
        Client: Supabase client with service role key for admin operations
    """
    return create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SERVICE_KEY
    )


def get_user_supabase_client(user_token: str) -> Client:
    """
    Create a Supabase client with user authentication.
    
    Args:
        user_token: JWT token from Supabase auth
        
    Returns:
        Client: Supabase client authenticated as the user
    """
    client = create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_KEY
    )
    # Set the auth token for this client
    client.auth.set_session(user_token, None)
    return client


async def execute_query(
    table: str,
    operation: str = "select",
    filters: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Execute a database query with common parameters.
    
    Args:
        table: Table name to query
        operation: Operation type (select, insert, update, delete)
        filters: Dictionary of column:value filters
        data: Data to insert/update
        order_by: Column to order by (prefix with - for desc)
        limit: Maximum number of results
        offset: Number of results to skip
        
    Returns:
        List of dictionaries representing rows
    """
    client = get_supabase_client()
    query = client.table(table)
    
    if operation == "select":
        query = query.select("*")
    elif operation == "insert" and data:
        return query.insert(data).execute().data
    elif operation == "update" and data:
        query = query.update(data)
    elif operation == "delete":
        pass  # Will be filtered below
    
    # Apply filters
    if filters:
        for key, value in filters.items():
            if isinstance(value, dict) and "op" in value:
                # Complex filter like {"op": "gte", "value": 50000}
                op = value["op"]
                val = value["value"]
                if op == "gte":
                    query = query.gte(key, val)
                elif op == "lte":
                    query = query.lte(key, val)
                elif op == "gt":
                    query = query.gt(key, val)
                elif op == "lt":
                    query = query.lt(key, val)
                elif op == "like":
                    query = query.like(key, val)
                elif op == "ilike":
                    query = query.ilike(key, val)
            else:
                # Simple equality filter
                query = query.eq(key, value)
    
    # Apply ordering
    if order_by:
        if order_by.startswith("-"):
            query = query.order(order_by[1:], desc=True)
        else:
            query = query.order(order_by)
    
    # Apply pagination
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    
    # Execute and return
    if operation == "delete":
        return query.delete().execute().data
    else:
        return query.execute().data


async def upsert_job(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upsert a job (insert or update on conflict).
    
    Args:
        job_data: Job data dictionary
        
    Returns:
        The upserted job record
    """
    client = get_supabase_client()
    try:
        result = client.table("jobs").upsert(
            job_data,
            on_conflict="url"
        ).execute()
        return result.data[0] if result.data else {}
    except APIError as e:
        raise Exception(f"Failed to upsert job: {str(e)}")


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Get user record by email.
    
    Args:
        email: User email address
        
    Returns:
        User record or None if not found
    """
    client = get_supabase_client()
    result = client.table("users").select("*").eq("email", email).execute()
    return result.data[0] if result.data else None


async def update_user_plan(user_id: str, plan: str, stripe_customer_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Update user's subscription plan.
    
    Args:
        user_id: User UUID
        plan: Plan name (free, pro, investor)
        stripe_customer_id: Optional Stripe customer ID
        
    Returns:
        Updated user record
    """
    client = get_supabase_client()
    update_data = {"plan": plan}
    if stripe_customer_id:
        update_data["stripe_customer_id"] = stripe_customer_id
    
    result = client.table("users").update(update_data).eq("id", user_id).execute()
    return result.data[0] if result.data else {}
