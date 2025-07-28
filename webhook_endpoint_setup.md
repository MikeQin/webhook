# Webhook Endpoint Setup: Consumer's Responsibility

## Who Provides What?

```
┌─────────────────┐                    ┌─────────────────┐
│    Producer     │    HTTP POST       │    Consumer     │
│   (Service A)   │ ──────────────────►│   (Service B)   │
│                 │                    │                 │
│ • Owns data     │                    │ • Provides URL  │
│ • Sends webhook │                    │ • Runs server   │
│ • Handles retry │                    │ • Processes data│
└─────────────────┘                    └─────────────────┘
     │                                           │
     └─── Calls endpoint provided by ───────────┘
```

## Consumer's Endpoint Responsibilities

### 1. **Provide Webhook URL**
```
Consumer tells Producer: "Send webhooks to https://myapp.com/webhooks/orders"
```

### 2. **Run Web Server**
```python
# Consumer must run this server
@app.post("/webhooks/orders")
async def handle_order_webhook(request: Request):
    payload = await request.json()
    # Process the webhook data
    return {"status": "success"}
```

### 3. **Maintain Infrastructure**
- Keep server running 24/7
- Handle high availability
- Manage SSL certificates
- Monitor endpoint health

### 4. **Handle HTTP Responses**
- Return 2xx status codes for success
- Return appropriate error codes for failures
- Respond quickly (typically < 30 seconds)

## Real-World Setup Examples

### Example 1: E-commerce App Receiving Payment Webhooks

**Setup Process:**
1. **Consumer (E-commerce App)** creates webhook endpoint:
   ```python
   @app.post("/webhooks/stripe")
   async def stripe_webhook(request: Request):
       # Process payment data
       return {"received": True}
   ```

2. **Consumer** tells **Producer (Stripe)**: 
   ```
   "Send payment webhooks to https://mystore.com/webhooks/stripe"
   ```

3. **Producer (Stripe)** stores the URL and sends webhooks there when payments occur

### Example 2: CI/CD Pipeline Receiving GitHub Webhooks

**Setup Process:**
1. **Consumer (Jenkins)** creates webhook endpoint:
   ```python
   @app.post("/github-webhook")
   async def github_push(request: Request):
       # Trigger build pipeline
       return {"build_triggered": True}
   ```

2. **Consumer** configures **Producer (GitHub)** via GitHub settings:
   ```
   Repository Settings → Webhooks → Add webhook
   URL: https://jenkins.company.com/github-webhook
   ```

3. **Producer (GitHub)** sends webhooks to that URL on code pushes

## Consumer's Server Requirements

### Infrastructure Needs:
```yaml
Consumer must provide:
  - Public webhook URL (HTTPS required)
  - Web server (FastAPI, Flask, Express, etc.)
  - Server hosting (AWS, GCP, Azure, etc.)
  - SSL certificate
  - Load balancing (for high traffic)
  - Monitoring and alerting
```

### Endpoint Implementation:
```python
# Consumer's webhook server implementation
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib

app = FastAPI()

@app.post("/webhook")
async def receive_webhook(request: Request):
    # 1. Verify signature (security)
    signature = request.headers.get("x-hub-signature-256")
    body = await request.body()
    if not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # 2. Parse payload
    payload = await request.json()
    
    # 3. Process the webhook data
    await process_webhook_event(payload)
    
    # 4. Return success response
    return {"status": "processed"}

def verify_signature(body: bytes, signature: str) -> bool:
    # Consumer verifies producer's signature
    expected = hmac.new(SECRET_KEY.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## Configuration Flow

### Typical Webhook Setup:
1. **Consumer** creates webhook endpoint server
2. **Consumer** registers webhook URL with **Producer**
3. **Producer** validates the endpoint (usually with a test webhook)
4. **Producer** starts sending real webhooks
5. **Consumer** processes incoming webhooks

### Configuration Examples:

**Stripe Dashboard:**
```
Developers → Webhooks → Add endpoint
Endpoint URL: https://yourapp.com/webhooks/stripe
Events: payment_intent.succeeded, payment_intent.payment_failed
```

**GitHub Repository:**
```
Settings → Webhooks → Add webhook  
Payload URL: https://yourci.com/github-webhook
Content type: application/json
Events: Just the push event
```

**Slack App:**
```
App Settings → Event Subscriptions
Request URL: https://yourbot.com/slack/events
Subscribe to bot events: message.channels, app_mention
```

## Consumer's Operational Burden

Since consumer provides the endpoint, they must handle:

### Security:
- Verify webhook signatures
- Validate incoming data
- Rate limiting to prevent abuse
- IP whitelisting (if supported)

### Reliability:
- Keep endpoint available 24/7
- Handle server restarts gracefully
- Implement proper error handling
- Monitor endpoint performance

### Scalability:
- Handle webhook traffic spikes
- Implement queuing for heavy processing
- Auto-scale server resources
- Load balance across multiple instances

## Best Practices for Consumers

### 1. **Quick Response**
```python
@app.post("/webhook")
async def webhook_handler(request: Request):
    payload = await request.json()
    
    # Respond quickly
    background_tasks.add_task(process_webhook_async, payload)
    return {"status": "received"}  # Return immediately

async def process_webhook_async(payload):
    # Do heavy processing in background
    await heavy_processing(payload)
```

### 2. **Idempotency**
```python
@app.post("/webhook")
async def webhook_handler(request: Request):
    webhook_id = request.headers.get("x-webhook-id")
    
    # Check if already processed
    if await already_processed(webhook_id):
        return {"status": "already_processed"}
    
    # Process and mark as processed
    await process_webhook(payload)
    await mark_processed(webhook_id)
    return {"status": "processed"}
```

### 3. **Error Handling**
```python
@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        payload = await request.json()
        await process_webhook(payload)
        return {"status": "success"}
    except ValidationError:
        # Return 4xx for client errors (don't retry)
        raise HTTPException(status_code=400, detail="Invalid payload")
    except ProcessingError:
        # Return 5xx for server errors (producer should retry)
        raise HTTPException(status_code=500, detail="Processing failed")
```

The key insight is that **both sides provide infrastructure**:
- **Producer** provides data and delivery logic
- **Consumer** provides endpoint and processing infrastructure