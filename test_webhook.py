#!/usr/bin/env python3
"""
Test script for the webhook server
"""
import requests
import json
import hmac
import hashlib
import time

WEBHOOK_URL = "http://localhost:8000/webhook"
SECRET = "test-secret-for-verification"

def create_signature(payload: str, secret: str) -> str:
    """Create HMAC-SHA256 signature for the payload"""
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def test_webhook_without_signature():
    """Test webhook without signature verification
    Expected: 401 - Signature required (when WEBHOOK_SECRET is configured)
    """
    print("Testing webhook without signature...")
    
    payload = {
        "event_type": "user.created",
        "timestamp": int(time.time()),
        "data": {
            "id": "user_123",
            "email": "test@example.com",
            "name": "Test User"
        }
    }
    
    response = requests.post(WEBHOOK_URL, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_webhook_with_signature():
    """Test webhook with signature verification
    Expected: 200 - Success (webhook processed successfully)
    """
    print("Testing webhook with signature...")
    
    payload = {
        "event_type": "order.completed",
        "timestamp": int(time.time()),
        "data": {
            "id": "order_456",
            "amount": 99.99,
            "customer_id": "user_123"
        }
    }
    
    payload_str = json.dumps(payload, separators=(',', ':'))
    signature = create_signature(payload_str, SECRET)
    
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": signature
    }
    
    response = requests.post(WEBHOOK_URL, data=payload_str, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_invalid_signature():
    """Test webhook with invalid signature
    Expected: 401 - Invalid signature
    """
    print("Testing webhook with invalid signature...")
    
    payload = {
        "event_type": "test.event",
        "data": {"test": "data"}
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": "sha256=invalid_signature"
    }
    
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_invalid_json():
    """Test webhook with invalid JSON
    Expected: 400 - Invalid JSON payload
    """
    print("Testing webhook with invalid JSON...")
    
    headers = {"Content-Type": "application/json"}
    invalid_json = '{"invalid": json}'
    
    response = requests.post(WEBHOOK_URL, data=invalid_json, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

if __name__ == "__main__":
    print("Webhook Test Suite")
    print("=" * 50)
    
    try:
        # Check if server is running
        health_response = requests.get("http://localhost:8000/health")
        if health_response.status_code == 200:
            print("✅ Webhook server is running")
            print()
            
            test_webhook_without_signature()
            test_webhook_with_signature()
            test_invalid_signature()
            test_invalid_json()
            
        else:
            print("❌ Webhook server is not responding")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to webhook server")
        print("Make sure the server is running: python webhook_server.py")