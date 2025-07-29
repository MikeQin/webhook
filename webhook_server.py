from fastapi import FastAPI, Request, HTTPException
from typing import Dict, Any, Optional
import json
import logging
import hmac
import hashlib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get webhook secret from environment
# To run test_webhook.py, set the environment variable:
#   export WEBHOOK_SECRET="test-secret-for-verification"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your-secret-key-here")
logger.info(f"Webhook secret configured: {'YES' if WEBHOOK_SECRET != 'your-secret-key-here' else 'NO (using default)'}")

app = FastAPI(title="Simple Webhook Server", version="1.0.0")

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify webhook signature using HMAC-SHA256
    """
    if not signature:
        return False
    
    try:
        # Remove 'sha256=' prefix if present (GitHub style)
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        # Create expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Use secure comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying signature: {str(e)}")
        return False

@app.get("/")
async def root():
    return {"message": "Webhook server is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/webhook")
async def receive_webhook(request: Request):
    """
    Main webhook endpoint that receives and processes webhook payloads
    """
    try:
        # Get raw body for signature verification if needed
        raw_body = await request.body()
        logger.info(f"Raw body received: {raw_body[:100]}...")  # Log first 100 chars
        
        # Get headers
        headers = dict(request.headers)
        logger.info(f"Headers received: {list(headers.keys())}")
        
        # Verify signature if secret is configured
        if WEBHOOK_SECRET and WEBHOOK_SECRET != "your-secret-key-here":
            signature = headers.get("x-hub-signature-256") or headers.get("x-signature-256") or headers.get("signature")
            if signature and not verify_signature(raw_body, signature, WEBHOOK_SECRET):
                logger.warning("Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
            elif not signature:
                logger.warning("No signature provided but signature verification is enabled")
                raise HTTPException(status_code=401, detail="Signature required")
        
        # Parse JSON payload
        try:
            payload = json.loads(raw_body.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload received")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Log the webhook event
        logger.info(f"Webhook received: {payload}")
        logger.info(f"Headers: {headers}")
        
        # Process the webhook payload
        result = await process_webhook_payload(payload, headers)
        
        return {"status": "success", "message": "Webhook processed", "result": result}
        
    except HTTPException:
        # Re-raise HTTPException without modification (401, 400, etc.)
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error processing webhook: {str(e)}")
        logger.error(f"Full traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def process_webhook_payload(payload: Dict[Any, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Process the webhook payload based on your business logic
    """
    # Example processing - customize this based on your needs
    event_type = payload.get("event_type", "unknown")
    
    if event_type == "user.created":
        return await handle_user_created(payload)
    elif event_type == "order.completed":
        return await handle_order_completed(payload)
    else:
        logger.info(f"Unhandled event type: {event_type}")
        return {"processed": True, "event_type": event_type}

async def handle_user_created(payload: Dict[Any, Any]) -> Dict[str, Any]:
    """Handle user creation events"""
    user_data = payload.get("data", {})
    user_id = user_data.get("id")
    user_email = user_data.get("email")
    
    logger.info(f"Processing user creation: ID={user_id}, Email={user_email}")
    
    # Add your business logic here
    # For example: send welcome email, create user profile, etc.
    
    return {"action": "user_created", "user_id": user_id}

async def handle_order_completed(payload: Dict[Any, Any]) -> Dict[str, Any]:
    """Handle order completion events"""
    order_data = payload.get("data", {})
    order_id = order_data.get("id")
    amount = order_data.get("amount")
    
    logger.info(f"Processing order completion: ID={order_id}, Amount={amount}")
    
    # Add your business logic here
    # For example: send confirmation email, update inventory, etc.
    
    return {"action": "order_completed", "order_id": order_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)