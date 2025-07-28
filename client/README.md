# Webhook Client

A comprehensive Python webhook client with retry logic, delivery tracking, and signature verification.

## Features

- ✅ Async/await support with httpx
- ✅ Automatic retry with exponential backoff
- ✅ HMAC-SHA256 signature generation
- ✅ Delivery tracking and monitoring
- ✅ Concurrent webhook sending
- ✅ Callback system for delivery status
- ✅ Command-line interface
- ✅ Comprehensive test suite

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Programmatic Usage

```python
import asyncio
from webhook_client import WebhookClient

async def main():
    # Create client
    client = WebhookClient(
        secret_key="your-secret-key-here",
        max_retries=3,
        timeout=30
    )
    
    # Send a webhook
    delivery = await client.send_webhook(
        url="http://localhost:8000/webhook",
        payload={"event_type": "test", "data": {"key": "value"}}
    )
    
    print(f"Status: {delivery.status.value}")
    print(f"Attempts: {delivery.attempts}")
    print(f"Response Status: {delivery.response_status}")

asyncio.run(main())
```

### CLI Usage

The client includes a command-line interface for easy webhook sending:

#### Send Single Webhook
```bash
python webhook_cli.py send http://localhost:8000/webhook \
  --payload '{"event_type": "test", "data": {"message": "hello"}}' \
  --secret "your-secret-key-here"
```

#### Send from File
```bash
python webhook_cli.py send http://localhost:8000/webhook \
  --payload-file payload.json \
  --secret "your-secret-key-here"
```

#### Send Batch Webhooks
```bash
python webhook_cli.py batch batch_config.json \
  --secret "your-secret-key-here" \
  --concurrent 10
```

#### Generate Example Files
```bash
python webhook_cli.py examples
```

### Event Emitter Pattern

Use the EventEmitter class for structured event handling:

```python
from webhook_client import WebhookClient, EventEmitter

client = WebhookClient(secret_key="your-secret")
emitter = EventEmitter(client, ["http://localhost:8000/webhook"])

# Emit events
await emitter.emit_user_created({
    "id": "user_123",
    "email": "user@example.com"
})

await emitter.emit_order_completed({
    "id": "order_456",
    "amount": 99.99
})
```

## Testing

Run the comprehensive test suite:

```bash
python test_webhook_client.py
```

The tests include:
- Basic webhook sending
- Retry mechanism testing
- Multiple webhook sending
- Event emitter functionality
- Delivery tracking

## Configuration

The WebhookClient accepts the following parameters:

- `secret_key`: HMAC secret for signature generation
- `timeout`: Request timeout in seconds (default: 30)
- `max_retries`: Maximum retry attempts (default: 3)
- `retry_wait_min`: Minimum wait time between retries (default: 1)
- `retry_wait_max`: Maximum wait time between retries (default: 60)

## Delivery Tracking

Track webhook deliveries with detailed status information:

```python
# Get delivery by ID
delivery = client.get_delivery("webhook_123")

# Get all deliveries
all_deliveries = client.get_all_deliveries()

# Get deliveries by status
successful = client.get_deliveries_by_status(DeliveryStatus.SUCCESS)

# Get delivery statistics
stats = client.get_delivery_stats()
print(stats)  # {'success': 5, 'failed': 1, 'pending': 0, 'retrying': 0}
```

## Callbacks

Monitor delivery status changes with callbacks:

```python
def on_delivery_change(delivery):
    print(f"Delivery {delivery.id}: {delivery.status.value}")

client.add_delivery_callback(on_delivery_change)
```

## Error Handling

The client handles various error scenarios:
- Network timeouts and connection errors
- HTTP 4xx/5xx responses
- JSON parsing errors
- Invalid signatures

All errors are logged and tracked in the delivery status.