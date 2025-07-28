# Webhook Tutorial: Complete FastAPI Implementation

A comprehensive webhook implementation tutorial with both server and client components, including detailed explanations of webhook architecture and best practices.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the webhook server
python webhook_server.py

# Test with the client (in another terminal)
python run_client_tests.py
```

## 📋 Table of Contents

- [Why Webhooks vs REST APIs?](#why-use-webhooks-instead-of-rest-api-calls)
- [Project Structure](#project-structure)
- [Server Implementation](#server-implementation)
- [Client Implementation](#client-implementation)
- [Architecture Documentation](#architecture-documentation)
- [Getting Started](#getting-started)
- [Examples](#examples)

## Why Use Webhooks Instead of REST API Calls?

### **Event-Driven Architecture vs Request-Response**

| **Webhooks** | **REST API Calls** |
|--------------|-------------------|
| **Push-based**: Server sends data when events occur | **Pull-based**: Client requests data periodically |
| **Real-time**: Immediate notification of events | **Delayed**: Data freshness depends on polling frequency |
| **Efficient**: No unnecessary API calls | **Resource-intensive**: Constant polling even when no changes |

### **⚠️ Critical: Responsibility & Data Ownership**

**REST API Polling:**
```
Service A: Data Owner + Data Provider + "Here's data when you ask"
Service B: Data Consumer + "I'll check when I need updates" ← CONTROLS timing, retries, failures
```

**Webhooks:**
```
Service A: Data Owner + Data Provider + "I'll push data to YOUR endpoint when events happen" ← CONTROLS delivery, retries, failures
Service B: Endpoint Provider + Data Recipient + "Here's MY endpoint, send data here" + "I'll process whatever you send"
```

**Key Roles:**
- **Data Owner**: Producer (owns the original data - orders, users, payments)
- **Data Provider**: Producer (decides what/when/how to send data)
- **Endpoint Provider**: Consumer (provides webhook URL, maintains server infrastructure)
- **Data Recipient**: Consumer (receives and processes the data)

**Key Implications:**
- **Data Control**: Producer controls what data is shared and when
- **Operational Complexity**: Shifts from consumer to producer
- **Reliability Ownership**: Producer must ensure webhook delivery
- **Dependency**: Consumer depends on producer for both data and delivery

### **Key Advantages of Webhooks**

#### 🚀 **Real-Time Communication**
```
Event occurs → Immediate webhook → Instant processing
vs
Event occurs → Wait for next poll → Process (delay: seconds to minutes)
```

#### 💰 **Cost & Resource Efficiency**
- **Webhooks**: Send only when something happens
- **REST Polling**: Waste resources checking for updates that may not exist
- **Example**: 1 webhook vs 1,440 daily API calls (polling every minute)

#### 🔄 **Reduced Complexity**
```python
# Webhook: Event-driven (simple)
@app.post("/webhook")
async def handle_order_complete(order_data):
    send_confirmation_email(order_data)
    update_inventory(order_data)

# REST Polling: Complex state management needed
while True:
    new_orders = api.get_orders(last_check_time)
    for order in new_orders:
        if order.status == "completed" and not_processed(order):
            process_order(order)
    time.sleep(60)  # Check every minute
```

#### 📊 **Better User Experience**
- **Immediate updates**: Users see changes instantly
- **No refresh needed**: Real-time notifications
- **Lower latency**: Sub-second response times

### **When to Use Webhooks vs REST APIs**

#### ✅ **Use Webhooks When:**
- **Event notifications**: Order completed, user registered, payment processed
- **Real-time updates**: Chat messages, live scores, status changes  
- **Integration workflows**: Connecting different services automatically
- **Producer service is reliable**: Can handle delivery responsibility
- **Third-party integrations**: GitHub commits, Stripe payments, Slack notifications

#### ✅ **Use REST APIs When:**
- **Data retrieval**: Getting user profiles, product lists, reports
- **Direct user actions**: Creating/updating/deleting resources
- **Consumer controls timing**: Needs to decide when to fetch data
- **Complex queries**: Filtering, searching, pagination
- **Consumer service more reliable**: Better suited to handle retry logic

#### ⚖️ **Responsibility Trade-offs:**

**Choose Webhooks IF:**
- Producer service has robust infrastructure
- Producer team can own delivery guarantees
- Events are infrequent enough to justify complexity

**Choose REST APIs IF:**
- Consumer needs control over timing
- Producer service should stay simple
- Consumer has better error handling capabilities

### **Real-World Example: E-commerce Order Processing**

#### **With Webhooks (Recommended):**
```
1. Order placed → Webhook sent immediately
2. Payment service → Processes payment → Sends webhook
3. Inventory service → Receives webhook → Updates stock
4. Email service → Receives webhook → Sends confirmation
5. Analytics → Receives webhook → Updates dashboard
Total time: < 1 second
```

#### **With REST Polling:**
```
1. Order placed
2. Payment service polls every 30 seconds for new orders
3. Inventory service polls every minute for order updates  
4. Email service polls every 2 minutes for completed orders
5. Analytics polls every 5 minutes for new data
Total delay: 30 seconds to 5 minutes
```

### **Common Webhook Use Cases**

- **Payment Processing**: Stripe, PayPal payment confirmations
- **CI/CD Pipelines**: GitHub push triggers deployment
- **Communication**: Slack bot notifications
- **Monitoring**: Server alerts, uptime notifications
- **Content Management**: Blog post published, content updated
- **IoT**: Sensor readings, device status changes

### **Important: Company vs Service Boundaries**

**Ownership boundaries ≠ Company boundaries**

The same company can operate multiple services with clear producer/consumer relationships:

#### **GitHub's Dual Role Example:**
```
Scenario 1: GitHub → External CI/CD
┌─────────────┐    webhook     ┌─────────────┐
│   GitHub    │ ──────────────►│  Jenkins    │
│ (Producer)  │                │ (Consumer)  │
│ Repo data   │                │ Provides    │
│ owner       │                │ endpoint    │
└─────────────┘                └─────────────┘

Scenario 2: GitHub → GitHub Actions (Same Company)
┌─────────────┐    internal    ┌─────────────┐
│   GitHub    │    events      │   GitHub    │
│ Repo Service│ ──────────────►│  Actions    │
│ (Producer)  │                │ (Consumer)  │
│ Data owner  │                │ Different   │
│             │                │ service     │
└─────────────┘                └─────────────┘
```

#### **Other Platform Examples:**
- **AWS**: S3 → Lambda (internal) + S3 → External apps (webhooks)
- **Stripe**: Payment engine → Internal fraud detection + External merchant webhooks  
- **Shopify**: Store data → Internal analytics + External app webhooks

**Key Insight**: Even within the same company, services maintain clear data ownership and webhook patterns for good microservices architecture.

## 📁 Project Structure

```
webhook/
├── 🌐 Server Components
│   ├── webhook_server.py          # FastAPI webhook server
│   ├── test_webhook.py           # Server tests
│   ├── requirements.txt          # Server dependencies
│   └── .env.example             # Environment template
│
├── 📦 Client Package
│   ├── client/
│   │   ├── __init__.py          # Package initialization
│   │   ├── webhook_client.py    # Core client implementation
│   │   ├── webhook_cli.py       # Command-line interface
│   │   ├── test_webhook_client.py # Client test suite
│   │   ├── requirements.txt     # Client dependencies
│   │   └── README.md           # Client documentation
│   │
│   ├── run_client_cli.py        # CLI wrapper
│   └── run_client_tests.py      # Test wrapper
│
├── 📚 Documentation
│   ├── README.md                # This file
│   ├── webhook_comparison.md    # Webhooks vs REST APIs
│   ├── data_ownership_examples.md # Data ownership patterns
│   └── webhook_endpoint_setup.md # Endpoint setup guide
│
└── 🔧 Repository Files
    ├── .gitignore              # Git ignore rules
    └── LICENSE                 # MIT License
```

### Server Features

- ✅ FastAPI-based webhook endpoint
- ✅ JSON payload handling
- ✅ HMAC-SHA256 signature verification
- ✅ Structured logging
- ✅ Error handling
- ✅ Health check endpoint
- ✅ Event-based processing

### Server Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /webhook` - Main webhook endpoint

### Built-in Event Types

- `user.created` - User creation events
- `order.completed` - Order completion events
- Custom event types (easily extensible)

### Client Features

- ✅ Async/await support with httpx
- ✅ Automatic retry with exponential backoff
- ✅ HMAC-SHA256 signature generation
- ✅ Delivery tracking and monitoring
- ✅ Concurrent webhook sending
- ✅ Callback system for delivery status
- ✅ Command-line interface
- ✅ Comprehensive test suite

### Client Usage Examples

**Programmatic Usage:**
```python
from client import WebhookClient

client = WebhookClient(secret_key="your-secret", max_retries=3)
delivery = await client.send_webhook(url, payload)
print(f"Status: {delivery.status.value}")
```

**CLI Usage:**
```bash
# Send single webhook
python run_client_cli.py send http://localhost:8000/webhook \
  --payload '{"event_type": "test", "data": {"message": "hello"}}'

# Send batch webhooks  
python run_client_cli.py batch config.json

# Generate examples
python run_client_cli.py examples
```

## 📚 Architecture Documentation

This project includes comprehensive documentation about webhook architecture:

- **[webhook_comparison.md](webhook_comparison.md)** - Detailed comparison of webhooks vs REST APIs
- **[data_ownership_examples.md](data_ownership_examples.md)** - Data ownership patterns and examples
- **[webhook_endpoint_setup.md](webhook_endpoint_setup.md)** - Complete guide to webhook endpoint setup

## 🚀 Getting Started

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd webhook

# Install server dependencies
pip install -r requirements.txt

# Install client dependencies (optional)
pip install -r client/requirements.txt
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env and set your webhook secret
echo "WEBHOOK_SECRET=your-super-secret-key" > .env
```

### 3. Run the Server

```bash
# Start webhook server
python webhook_server.py

# Server runs on http://localhost:8000
```

### 4. Test Everything

```bash
# Test server functionality
python test_webhook.py

# Test client functionality  
python run_client_tests.py
```

## 📖 Examples

### Server Example

```python
# webhook_server.py handles events like this:
@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()
    
    if payload["event_type"] == "user.created":
        await handle_user_created(payload["data"])
    elif payload["event_type"] == "order.completed":
        await handle_order_completed(payload["data"])
    
    return {"status": "processed"}
```

### Client Example

```python
# Send webhooks with the client:
from client import WebhookClient

client = WebhookClient(secret_key="secret")

# Single webhook
delivery = await client.send_webhook(
    url="http://localhost:8000/webhook",
    payload={
        "event_type": "order.completed",
        "data": {"order_id": "12345", "amount": 99.99}
    }
)

# Batch webhooks
webhooks = [
    {"url": "http://app1.com/webhook", "payload": {...}},
    {"url": "http://app2.com/webhook", "payload": {...}}
]
results = await client.send_multiple(webhooks)
```

## 🔒 Security Features

- **HMAC-SHA256 signature verification** - Ensure webhook authenticity
- **Secure string comparison** - Prevent timing attacks  
- **Environment-based secrets** - Keep credentials secure
- **Request logging** - Monitor webhook activity
- **Error handling** - Don't expose internal details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for the server
- Uses [httpx](https://www.python-httpx.org/) for async HTTP requests
- Implements industry-standard webhook patterns and security practices

---

*Happy webhook building! 🎣*