#!/usr/bin/env python3
"""
Test script for the webhook client
"""
import asyncio
import time
from .webhook_client import WebhookClient, EventEmitter, DeliveryStatus

async def test_basic_webhook():
    """Test basic webhook sending"""
    print("🧪 Testing basic webhook sending...")
    
    client = WebhookClient(secret_key="your-secret-key-here")
    
    payload = {
        "event_type": "test.basic",
        "timestamp": int(time.time()),
        "data": {"message": "Basic webhook test"}
    }
    
    delivery = await client.send_webhook(
        url="http://localhost:8000/webhook",
        payload=payload
    )
    
    print(f"✅ Delivery ID: {delivery.id}")
    print(f"✅ Status: {delivery.status.value}")
    print(f"✅ Attempts: {delivery.attempts}")
    print(f"✅ Response Status: {delivery.response_status}")
    print()

async def test_webhook_with_retry():
    """Test webhook with retry on failure"""
    print("🧪 Testing webhook with retry (using invalid URL)...")
    
    client = WebhookClient(
        secret_key="your-secret-key-here",
        max_retries=2,
        timeout=5
    )
    
    # Add callback to monitor delivery attempts
    def on_delivery_change(delivery):
        print(f"📊 Delivery {delivery.id}: {delivery.status.value} (attempt {delivery.attempts})")
    
    client.add_delivery_callback(on_delivery_change)
    
    payload = {
        "event_type": "test.retry",
        "data": {"message": "Retry test"}
    }
    
    # Test with invalid URL to trigger retries
    delivery = await client.send_webhook(
        url="http://invalid-webhook-url:9999/webhook",
        payload=payload
    )
    
    print(f"✅ Final Status: {delivery.status.value}")
    print(f"✅ Total Attempts: {delivery.attempts}")
    print(f"✅ Error: {delivery.error_message}")
    print()

async def test_multiple_webhooks():
    """Test sending multiple webhooks concurrently"""
    print("🧪 Testing multiple webhook sending...")
    
    client = WebhookClient(secret_key="your-secret-key-here")
    
    webhooks = [
        {
            "url": "http://localhost:8000/webhook",
            "payload": {
                "event_type": "test.multi",
                "data": {"id": i, "message": f"Multi webhook test {i}"}
            },
            "delivery_id": f"multi_test_{i}"
        }
        for i in range(5)
    ]
    
    start_time = time.time()
    results = await client.send_multiple(webhooks, max_concurrent=3)
    end_time = time.time()
    
    print(f"✅ Sent {len(webhooks)} webhooks in {end_time - start_time:.2f} seconds")
    
    success_count = sum(1 for r in results if hasattr(r, 'status') and r.status == DeliveryStatus.SUCCESS)
    print(f"✅ Successful deliveries: {success_count}/{len(webhooks)}")
    
    # Show delivery stats
    stats = client.get_delivery_stats()
    print(f"✅ Delivery stats: {stats}")
    print()

async def test_event_emitter():
    """Test the EventEmitter class"""
    print("🧪 Testing EventEmitter...")
    
    client = WebhookClient(secret_key="your-secret-key-here")
    
    # Multiple webhook URLs (including one invalid for demonstration)
    webhook_urls = [
        "http://localhost:8000/webhook",
        # "http://localhost:8001/webhook"  # Uncomment to test multiple endpoints
    ]
    
    emitter = EventEmitter(client, webhook_urls)
    
    # Emit user created event
    await emitter.emit_user_created({
        "id": "user_12345",
        "email": "newuser@example.com",
        "name": "New User",
        "created_at": time.time()
    })
    
    # Emit order completed event
    await emitter.emit_order_completed({
        "id": "order_67890",
        "user_id": "user_12345",
        "amount": 99.99,
        "status": "completed"
    })
    
    print("✅ Events emitted successfully")
    
    # Show final stats
    stats = client.get_delivery_stats()
    print(f"✅ Final delivery stats: {stats}")
    print()

async def test_delivery_tracking():
    """Test delivery tracking and monitoring"""
    print("🧪 Testing delivery tracking...")
    
    client = WebhookClient(secret_key="your-secret-key-here")
    
    # Send a webhook
    delivery = await client.send_webhook(
        url="http://localhost:8000/webhook",
        payload={"event_type": "test.tracking", "data": {"test": True}},
        delivery_id="tracking_test_001"
    )
    
    # Retrieve delivery by ID
    retrieved_delivery = client.get_delivery("tracking_test_001")
    print(f"✅ Retrieved delivery: {retrieved_delivery.id}")
    print(f"✅ Status: {retrieved_delivery.status.value}")
    print(f"✅ Created at: {time.ctime(retrieved_delivery.created_at)}")
    print(f"✅ Last attempt: {time.ctime(retrieved_delivery.last_attempt_at) if retrieved_delivery.last_attempt_at else 'Never'}")
    
    # Get all deliveries
    all_deliveries = client.get_all_deliveries()
    print(f"✅ Total deliveries tracked: {len(all_deliveries)}")
    
    # Get deliveries by status
    successful_deliveries = client.get_deliveries_by_status(DeliveryStatus.SUCCESS)
    print(f"✅ Successful deliveries: {len(successful_deliveries)}")
    print()

async def main():
    """Run all tests"""
    print("🚀 Webhook Client Test Suite")
    print("=" * 50)
    
    try:
        # Check if webhook server is running
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Webhook server is running")
                print()
                
                await test_basic_webhook()
                await test_multiple_webhooks()
                await test_event_emitter()
                await test_delivery_tracking()
                await test_webhook_with_retry()  # Run retry test last
                
                print("🎉 All tests completed!")
                
            else:
                print("❌ Webhook server is not responding properly")
                
    except Exception as e:
        print(f"❌ Cannot connect to webhook server: {e}")
        print("Make sure the server is running: python webhook_server.py")
        print("You can still run the retry test to see failure handling:")
        await test_webhook_with_retry()

if __name__ == "__main__":
    asyncio.run(main())