"""Stripe webhook receiver for JobSleuth AI backend.

This endpoint handles events from Stripe and updates user subscription plans.
Implements deterministic responses with proper plan mapping.
"""

import stripe
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.lib.settings import settings
from backend.lib.supabase import get_supabase_client, update_user_plan

router = APIRouter(prefix="/stripe")

stripe.api_key = settings.STRIPE_SECRET_KEY


def map_price_to_plan(price_id: str) -> str:
    """
    Map Stripe price ID to plan name.
    
    Args:
        price_id: Stripe price ID
        
    Returns:
        Plan name (free, pro, investor)
    """
    if price_id == settings.PRICE_ID_PRO:
        return "pro"
    elif price_id == settings.PRICE_ID_INVESTOR:
        return "investor"
    else:
        return "free"


@router.post("/webhook")
async def stripe_webhook(request: Request) -> JSONResponse:
    """
    Handle Stripe webhook events.
    
    Processes checkout completion and subscription updates.
    Returns deterministic JSON responses.
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, 
            sig_header, 
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "Invalid payload"}
        )
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "Invalid signature"}
        )

    # Handle checkout.session.completed
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Extract customer and subscription details
        customer_id = session.get('customer')
        customer_email = session.get('customer_email') or session.get('customer_details', {}).get('email')
        
        # Get subscription to find price ID
        subscription_id = session.get('subscription')
        if subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
                price_id = subscription['items']['data'][0]['price']['id']
                plan = map_price_to_plan(price_id)
                
                # Find user by email and update plan
                if customer_email:
                    client = get_supabase_client()
                    user_result = client.table("users").select("id").eq("email", customer_email).execute()
                    
                    if user_result.data:
                        user_id = user_result.data[0]['id']
                        await update_user_plan(user_id, plan, customer_id)
                        
                        return JSONResponse(
                            status_code=200,
                            content={"ok": True}
                        )
            except Exception as e:
                return JSONResponse(
                    status_code=200,
                    content={"ok": False, "error": f"Failed to process checkout: {str(e)}"}
                )
    
    # Handle invoice.paid (subscription renewal)
    elif event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        
        customer_id = invoice.get('customer')
        subscription_id = invoice.get('subscription')
        
        if subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
                price_id = subscription['items']['data'][0]['price']['id']
                plan = map_price_to_plan(price_id)
                
                # Find user by stripe_customer_id
                client = get_supabase_client()
                user_result = client.table("users").select("id").eq("stripe_customer_id", customer_id).execute()
                
                if user_result.data:
                    user_id = user_result.data[0]['id']
                    await update_user_plan(user_id, plan, customer_id)
                    
                    return JSONResponse(
                        status_code=200,
                        content={"ok": True}
                    )
            except Exception as e:
                return JSONResponse(
                    status_code=200,
                    content={"ok": False, "error": f"Failed to process invoice: {str(e)}"}
                )
    
    # Handle customer.subscription.deleted (cancellation)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        
        try:
            # Find user and downgrade to free
            client = get_supabase_client()
            user_result = client.table("users").select("id").eq("stripe_customer_id", customer_id).execute()
            
            if user_result.data:
                user_id = user_result.data[0]['id']
                await update_user_plan(user_id, "free", customer_id)
                
                return JSONResponse(
                    status_code=200,
                    content={"ok": True}
                )
        except Exception as e:
            return JSONResponse(
                status_code=200,
                content={"ok": False, "error": f"Failed to process cancellation: {str(e)}"}
            )
    
    # Default response for unhandled events
    return JSONResponse(
        status_code=200,
        content={"ok": True}
    )
