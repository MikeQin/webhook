# Webhook Tutorial: Complete FastAPI Implementation

A comprehensive webhook implementation tutorial with both server and client components, including detailed explanations of webhook architecture and best practices.

## 🚀 Quick Start

### For Git Bash on Windows:

```bash
# Create virtual environment (use python or python3, whichever you have)
python -m venv .venv --copies

# Activate virtual environment
source .venv/Scripts/activate

# Verify setup (should show venv path)
which python
python --version

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
python -m pip install -r requirements.txt

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

### Understanding Webhook Security & Secret Exchange

#### **WEBHOOK_SECRET vs API Key:**

| **Aspect** | **API Key** | **Webhook Secret** |
|------------|-------------|-------------------|
| **Direction** | Client → Server | Server → Client |
| **Purpose** | Authenticate API requests | Authenticate webhook deliveries |
| **Who generates** | Server provides to client | Client provides to server |
| **Usage** | "I'm authorized to call your API" | "This webhook is really from me" |

#### **How Secret Exchange Works:**

**Method 1: Platform Dashboard (Most Common)**
```bash
# Example: GitHub Webhook Setup
1. Go to: Repository → Settings → Webhooks → Add webhook
2. Enter URL: https://yourapp.com/webhook
3. Set Secret: your-super-secret-123
4. GitHub uses this secret to sign all webhooks to you
```

**Method 2: Service-Generated Secrets**
```bash
# Example: Stripe auto-generates secrets
# Copy from Stripe Dashboard: whsec_1234567890abcdef...
export WEBHOOK_SECRET="whsec_1234567890abcdef..."
```

#### **Complete Setup Flow:**

**1. Generate Strong Secret:**
```bash
# Generate cryptographically secure secret
openssl rand -hex 32
# Output: a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

**2. Configure Your Server:**
```bash
# Set environment variable
export WEBHOOK_SECRET="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
```

**3. Configure Webhook Provider:**
```bash
# In GitHub/Stripe/etc. dashboard:
# - Webhook URL: https://yourapp.com/webhook
# - Secret: a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

**4. Webhook Signature Verification:**
```python
# How the server code works:
if WEBHOOK_SECRET and WEBHOOK_SECRET != "your-secret-key-here":
    # Try multiple header formats (GitHub, Stripe, etc.)
    signature = headers.get("x-hub-signature-256") or headers.get("x-signature-256") or headers.get("signature")
    if not verify_signature(raw_body, signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
```

#### **How HMAC Verification Works:**

**Sender Side (GitHub/Stripe):**
1. Takes raw webhook payload: `{"event": "push", "data": "..."}`
2. Creates HMAC-SHA256: `hmac_sha256(payload, secret)`
3. Sends: `X-Hub-Signature-256: sha256=calculated_hash`

**Receiver Side (Your Server):**
1. Receives same payload and signature
2. Calculates: `hmac_sha256(received_payload, same_secret)`
3. Compares hashes using secure comparison
4. ✅ Match = Authentic, ❌ No match = Reject

#### **Security Best Practices:**

**Environment Variables (Never Hardcode):**
```bash
# ✅ Good - Environment variables
export WEBHOOK_SECRET="$(openssl rand -hex 32)"

# ❌ Bad - Hardcoded in code
WEBHOOK_SECRET = "my-secret"  # Never do this!
```

**Multiple Secrets for Different Services:**
```bash
export GITHUB_WEBHOOK_SECRET="secret_for_github"
export STRIPE_WEBHOOK_SECRET="secret_for_stripe"  
export SLACK_WEBHOOK_SECRET="secret_for_slack"
```

**Secret Rotation Support:**
```python
# Support multiple secrets during rotation
WEBHOOK_SECRETS = [
    os.getenv("WEBHOOK_SECRET_NEW"),  # Try new secret first
    os.getenv("WEBHOOK_SECRET_OLD")   # Fallback during transition
]

def verify_any_signature(payload, signature):
    for secret in WEBHOOK_SECRETS:
        if secret and verify_signature(payload, signature, secret):
            return True
    return False
```

#### **Common Signature Headers:**
- **`X-Hub-Signature-256`** - GitHub, GitLab
- **`X-Signature-256`** - Some custom services  
- **`Stripe-Signature`** - Stripe (different format)
- **`X-Slack-Signature`** - Slack
- **`signature`** - Generic implementations

The webhook secret creates **mutual authentication** - both parties prove they know the same secret without ever transmitting it over the network! 🔐

### Understanding Python Imports in Package Structure

#### **Package Structure Overview:**
```
client/
├── __init__.py               # Package initialization & exports
├── webhook_client.py         # Core classes (WebhookClient, DeliveryStatus)
├── webhook_cli.py           # CLI interface 
└── test_webhook_client.py   # Test suite
```

#### **Relative vs Absolute Imports:**

**Relative Imports (Within Package):**
```python
# In client/webhook_cli.py and client/test_webhook_client.py
from .webhook_client import WebhookClient, DeliveryStatus
#    ^
#    The dot (.) means "from current package"
```

**Absolute Imports (From Outside Package):**
```python
# From root directory files (run_client_cli.py, run_client_tests.py)
from client.webhook_client import WebhookClient, DeliveryStatus
```

**Package-Level Imports:**
```python
# From anywhere, using package exports
from client import WebhookClient, DeliveryStatus
```

#### **How Package Imports Work:**

**1. Package Initialization (`client/__init__.py`):**
```python
# Exposes main classes for easy importing
from .webhook_client import WebhookClient, EventEmitter, DeliveryStatus, WebhookDelivery

__version__ = "1.0.0"
__all__ = ["WebhookClient", "EventEmitter", "DeliveryStatus", "WebhookDelivery"]
```

**2. Internal Module Imports:**
```python
# client/webhook_cli.py uses relative imports
from .webhook_client import WebhookClient, DeliveryStatus

# This works because both files are in the same package
```

**3. External Access Patterns:**
```python
# Method 1: Direct module import
from client.webhook_client import WebhookClient

# Method 2: Package-level import (uses __init__.py exports)
from client import WebhookClient

# Method 3: Import entire package
import client
client = client.WebhookClient()
```

#### **Why Use Relative Imports:**

| **Aspect** | **Relative Imports** | **Absolute Imports** |
|------------|---------------------|---------------------|
| **Syntax** | `from .module import Class` | `from package.module import Class` |
| **Portability** | ✅ Works if package is renamed | ❌ Hardcoded package name |
| **Clarity** | ✅ Shows same-package relationship | ❌ Looks like external dependency |
| **Refactoring** | ✅ Easy to move packages | ❌ Need to update all imports |
| **Performance** | ✅ Slightly faster lookup | ❌ Longer module path resolution |

#### **Import Examples in This Project:**

**Package Export (`client/__init__.py`):**
```python
"""
Makes these classes available at package level:
>>> from client import WebhookClient
>>> client = WebhookClient()
"""
from .webhook_client import WebhookClient, EventEmitter, DeliveryStatus, WebhookDelivery
```

**Internal Usage (`client/webhook_cli.py`):**
```python
"""
Relative import within same package - clean and portable
"""
from .webhook_client import WebhookClient, DeliveryStatus
```

**External Usage (`run_client_cli.py`):**
```python
"""
Wrapper script imports from package root
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'client'))

from client.webhook_cli import main  # Absolute import
```

**User Code Examples:**
```python
# Option 1: Package-level import (recommended for users)
from client import WebhookClient
client = WebhookClient(secret_key="test")

# Option 2: Direct module import
from client.webhook_client import WebhookClient
client = WebhookClient(secret_key="test")

# Option 3: Full package import
import client
webhook_client = client.WebhookClient(secret_key="test")
```

#### **Python Import Resolution Order:**

1. **Built-in modules** (os, sys, json)
2. **Site-packages** (pip-installed packages)
3. **Current working directory**
4. **PYTHONPATH directories**
5. **Relative to current package** (for relative imports)

#### **Common Import Patterns:**

**Package Development:**
```python
# Inside package modules - use relative imports
from .core import SomeClass        # Same package
from ..utils import helper_func    # Parent package
from ...config import settings     # Great-grandparent package
```

**Application Code:**
```python
# External code - use absolute imports
from mypackage.core import SomeClass
from mypackage.utils import helper_func
```

**Testing:**
```python
# Test files - often use absolute imports for clarity
from client.webhook_client import WebhookClient
from client.webhook_client import DeliveryStatus
```

Understanding Python's import system helps you organize code better and avoid common pitfalls like circular imports and namespace conflicts! 🐍📦

### Understanding Client Package Components

The webhook client package consists of three main components, each serving a distinct purpose:

#### **File Overview:**

| **File** | **Purpose** | **Target User** | **Usage Pattern** |
|----------|-------------|-----------------|-------------------|
| **`webhook_client.py`** | Core library & classes | Developers (programmatic) | Import & use in code |
| **`webhook_cli.py`** | Command-line interface | End users/operators | Terminal commands |
| **`test_webhook_client.py`** | Automated testing suite | Developers/CI systems | Verification & testing |

#### **`webhook_client.py` - Core Library**

**What it contains:**
- **`WebhookClient`** - Main class for sending webhooks
- **`EventEmitter`** - High-level event publishing class
- **`DeliveryStatus`** - Enum for delivery states (SUCCESS, FAILED, etc.)
- **`WebhookDelivery`** - Data class for tracking delivery details

**Key Features:**
```python
class WebhookClient:
    """Core webhook sending functionality"""
    
    async def send_webhook(url, payload):        # Send single webhook
    async def send_multiple(webhooks):           # Send batch webhooks
    def get_delivery(delivery_id):               # Track specific delivery
    def get_delivery_stats():                    # Overall statistics
    def add_delivery_callback(callback):         # Monitor delivery status
```

**Usage Example:**
```python
from client.webhook_client import WebhookClient, DeliveryStatus

# Create client instance
client = WebhookClient(
    secret_key="your-secret",
    max_retries=3,
    timeout=30
)

# Send webhook programmatically
delivery = await client.send_webhook(
    url="https://api.example.com/webhook",
    payload={"event": "user.created", "data": {"id": 123}}
)

# Check delivery status
if delivery.status == DeliveryStatus.SUCCESS:
    print(f"Webhook delivered successfully!")
```

**When to use:**
- Building applications that send webhooks
- Integrating webhook functionality into existing code
- Need programmatic control and customization
- Building higher-level abstractions

#### **`webhook_cli.py` - Command Line Interface**

**What it does:**
- **Production tool** for sending webhooks from terminal
- **Batch processing** capabilities
- **File-based configuration** support
- **User-friendly error messages**

**Key Commands:**
```python
# CLI command structure
async def send_single_webhook(args):     # Handle 'send' command
async def send_batch_webhooks(args):     # Handle 'batch' command  
def generate_examples():                 # Handle 'examples' command
def main():                             # Parse CLI arguments
```

**Usage Examples:**
```bash
# Send single webhook
python run_client_cli.py send https://api.example.com/webhook \
  --payload '{"event": "deployment", "version": "1.2.3"}' \
  --secret "production-secret"

# Send batch webhooks from file
python run_client_cli.py batch production_webhooks.json \
  --concurrent 10

# Generate example configuration files
python run_client_cli.py examples
```

**When to use:**
- Operations and deployment scripts
- Manual webhook testing
- Bulk webhook operations
- Integration with shell scripts/cron jobs
- Quick debugging of webhook endpoints

#### **`test_webhook_client.py` - Testing Suite**

**What it tests:**
- **Basic functionality** - Simple webhook sending
- **Error handling** - Network failures, invalid responses
- **Retry logic** - Exponential backoff behavior
- **Concurrent operations** - Multiple webhook handling
- **Delivery tracking** - Status monitoring and callbacks

**Key Test Functions:**
```python
async def test_basic_webhook():          # Test simple webhook sending
async def test_webhook_with_retry():     # Test retry mechanism
async def test_multiple_webhooks():      # Test concurrent sending
async def test_event_emitter():          # Test EventEmitter class
async def test_delivery_tracking():      # Test monitoring features
```

**Sample Output:**
```
🧪 Testing basic webhook sending...
✅ Delivery ID: webhook_1234567890
✅ Status: success
✅ Attempts: 1
✅ Response Status: 200

🧪 Testing multiple webhook sending...
✅ Sent 5 webhooks in 1.23 seconds
✅ Successful deliveries: 5/5

🎉 All tests completed!
```

**When to run:**
- During development (before commits)
- In CI/CD pipelines
- When debugging webhook issues
- After making changes to client code
- Before releasing new versions

#### **Component Interaction Flow:**

```
┌─────────────────────┐    imports    ┌─────────────────────┐
│  webhook_cli.py     │──────────────►│  webhook_client.py  │
│  (User Interface)   │               │  (Core Library)     │
└─────────────────────┘               └─────────────────────┘
          │                                     ▲
          │                                     │ imports
          ▼                                     │
┌─────────────────────┐               ┌─────────────────────┐
│  User Commands      │               │ test_webhook_client │
│  (Terminal)         │               │ (Automated Tests)   │
└─────────────────────┘               └─────────────────────┘
```

#### **Development Workflow:**

**1. Core Development:**
```python
# Modify webhook_client.py - add new features
class WebhookClient:
    async def new_feature(self):
        # Implementation
        pass
```

**2. Testing:**
```python
# Add tests in test_webhook_client.py
async def test_new_feature():
    client = WebhookClient()
    result = await client.new_feature()
    assert result.status == DeliveryStatus.SUCCESS
```

**3. CLI Integration:**
```python
# Add CLI command in webhook_cli.py
async def handle_new_feature(args):
    client = WebhookClient()
    result = await client.new_feature()
    print(f"Feature result: {result}")
```

#### **Usage Scenarios:**

**Scenario 1: Application Integration**
```python
# Use webhook_client.py directly in your app
from client import WebhookClient

class OrderService:
    def __init__(self):
        self.webhook_client = WebhookClient(secret_key=os.getenv("WEBHOOK_SECRET"))
    
    async def process_order(self, order):
        # Process order logic...
        await self.webhook_client.send_webhook(
            url="https://inventory.example.com/webhook",
            payload={"event": "order.completed", "order_id": order.id}
        )
```

**Scenario 2: DevOps Automation**
```bash
# Use webhook_cli.py in deployment scripts
#!/bin/bash
# Deploy application
kubectl apply -f deployment.yaml

# Notify via webhook
python run_client_cli.py send https://slack.example.com/webhook \
  --payload '{"text": "Deployment completed successfully"}' \
  --secret "$SLACK_WEBHOOK_SECRET"
```

**Scenario 3: Quality Assurance**
```bash
# Use test_webhook_client.py in CI/CD
#!/bin/bash
# Run all tests
python run_client_tests.py

# Exit with error code if tests fail
if [ $? -ne 0 ]; then
    echo "Webhook client tests failed!"
    exit 1
fi
```

Each component serves a specific role in the webhook ecosystem, from core functionality to user interfaces to quality assurance! 🔧📋🧪

### Understanding Root Directory Helper Files

The main project directory contains several important files that serve as bridges and interfaces between different components:

#### **File Overview:**

| **File** | **Purpose** | **Connects** | **Usage** |
|----------|-------------|--------------|-----------|
| **`test_webhook.py`** | Server testing | Tests webhook server directly | `python test_webhook.py` |
| **`run_client_cli.py`** | CLI wrapper | Root directory ↔ client CLI | `python run_client_cli.py send ...` |
| **`run_client_tests.py`** | Test wrapper | Root directory ↔ client tests | `python run_client_tests.py` |

#### **`test_webhook.py` - Server Testing**

**What it does:**
- **Tests the webhook SERVER** (not the client)
- **Validates server functionality** - endpoints, signature verification, event processing
- **Direct HTTP requests** to test server responses
- **Integration testing** of the FastAPI webhook server

**Key Functions:**
```python
def test_webhook_without_signature():    # Test server without auth
def test_webhook_with_signature():       # Test server with HMAC auth
def test_invalid_signature():           # Test server security
def test_invalid_json():                # Test server error handling
```

**Sample Usage:**
```bash
# Start server in one terminal
python webhook_server.py

# Test server in another terminal
python test_webhook.py
```

**Sample Output:**
```
Webhook Test Suite
==================================================
✅ Webhook server is running

Testing webhook without signature...
Status: 200
Response: {'status': 'success', 'message': 'Webhook processed'}

Testing webhook with signature...
Status: 200
Response: {'status': 'success', 'message': 'Webhook processed'}
```

**When to use:**
- Testing the webhook SERVER functionality
- Validating server endpoints work correctly
- Debugging server-side issues
- Integration testing of server components

#### **`run_client_cli.py` - CLI Wrapper**

**What it does:**
- **Wrapper script** to run the client CLI from the root directory
- **Path management** - adds client directory to Python path
- **User convenience** - allows running CLI without cd into client/
- **Maintains project structure** while providing easy access

**Code Structure:**
```python
#!/usr/bin/env python3
"""
Wrapper script to run client CLI from the root directory
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'client'))

from client.webhook_cli import main

if __name__ == "__main__":
    sys.exit(main())
```

**Usage Examples:**
```bash
# Instead of this (requires cd):
cd client
python webhook_cli.py send http://localhost:8000/webhook --payload '{...}'

# You can do this (from root):
python run_client_cli.py send http://localhost:8000/webhook --payload '{...}'
```

**Why it exists:**
- **User convenience** - work from project root
- **Script integration** - easier to use in automation
- **Path isolation** - keeps client as separate package
- **Consistent interface** - all commands from root directory

#### **`run_client_tests.py` - Test Wrapper**

**What it does:**
- **Wrapper script** to run client tests from root directory
- **Path management** for client package
- **Test execution** without changing directories
- **CI/CD integration** - single command to test client

**Code Structure:**
```python
#!/usr/bin/env python3
"""
Wrapper script to run client tests from the root directory
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'client'))

from client.test_webhook_client import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
```

**Usage Examples:**
```bash
# Instead of this (requires cd):
cd client
python test_webhook_client.py

# You can do this (from root):
python run_client_tests.py
```

**When to use:**
- Testing client functionality from root directory
- CI/CD pipeline integration
- Development workflow without directory changes
- Automated testing scripts

#### **Project Architecture & File Relationships:**

```
webhook/                          # Root directory
├── 🌐 Server Components
│   ├── webhook_server.py         # FastAPI server
│   └── test_webhook.py          # ← Tests SERVER directly
│
├── 📦 Client Package
│   ├── client/
│   │   ├── webhook_client.py     # Core client library
│   │   ├── webhook_cli.py        # CLI implementation  
│   │   └── test_webhook_client.py # Client tests
│   │
│   ├── run_client_cli.py        # ← CLI wrapper (ROOT → CLIENT)
│   └── run_client_tests.py      # ← Test wrapper (ROOT → CLIENT)
│
└── 📚 Documentation & Config
    ├── README.md
    └── requirements.txt
```

#### **Why We Need These Wrapper Files:**

**1. Package Isolation:**
```python
# Without wrappers - user must navigate directories
cd client
python webhook_cli.py send ...

# With wrappers - work from root
python run_client_cli.py send ...
```

**2. Path Management:**
```python
# Wrappers handle Python path automatically
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'client'))
# User doesn't need to worry about import paths
```

**3. Consistent Interface:**
```bash
# All commands work from root directory
python webhook_server.py          # Start server
python test_webhook.py            # Test server
python run_client_cli.py send ... # Use client CLI
python run_client_tests.py        # Test client
```

**4. CI/CD Integration:**
```yaml
# GitHub Actions can use simple commands
- name: Test Server
  run: python test_webhook.py

- name: Test Client  
  run: python run_client_tests.py
```

#### **Development Workflow:**

**Server Development:**
```bash
# Start server
python webhook_server.py

# Test server (different terminal)
python test_webhook.py
```

**Client Development:**
```bash
# Test client functionality
python run_client_tests.py

# Use client CLI for manual testing
python run_client_cli.py send http://localhost:8000/webhook \
  --payload '{"event": "test"}' --secret "test-key"
```

**Full Integration Testing:**
```bash
# 1. Start server
python webhook_server.py &

# 2. Test server
python test_webhook.py

# 3. Test client
python run_client_tests.py

# 4. Manual client testing
python run_client_cli.py examples
python run_client_cli.py send http://localhost:8000/webhook \
  --payload-file example_payload.json
```

#### **Benefits of This Architecture:**

| **Benefit** | **Description** |
|-------------|-----------------|
| **User Convenience** | All commands from root directory |
| **Package Isolation** | Client remains separate package |
| **Path Management** | Automatic Python path handling |
| **CI/CD Friendly** | Simple command structure for automation |
| **Development Flow** | Easy testing and development workflow |
| **Consistent Interface** | Predictable command patterns |

**Summary:**
- **`test_webhook.py`** = "Test the SERVER"
- **`run_client_cli.py`** = "Use CLIENT CLI from root"  
- **`run_client_tests.py`** = "Test CLIENT from root"

These files create a seamless user experience while maintaining clean package architecture! 🌉🔧

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