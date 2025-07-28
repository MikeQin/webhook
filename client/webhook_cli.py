#!/usr/bin/env python3
"""
Command-line interface for the webhook client
"""
import asyncio
import json
import sys
import argparse
from typing import Dict, Any
from .webhook_client import WebhookClient, DeliveryStatus

async def send_single_webhook(args):
    """Send a single webhook"""
    client = WebhookClient(
        secret_key=args.secret,
        max_retries=args.retries,
        timeout=args.timeout
    )
    
    # Parse payload
    try:
        if args.payload_file:
            with open(args.payload_file, 'r') as f:
                payload = json.load(f)
        else:
            payload = json.loads(args.payload)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error parsing payload: {e}")
        return 1
    
    # Parse headers
    headers = {}
    if args.headers:
        for header in args.headers:
            key, value = header.split(':', 1)
            headers[key.strip()] = value.strip()
    
    print(f"Sending webhook to: {args.url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    if headers:
        print(f"Headers: {json.dumps(headers, indent=2)}")
    
    # Send webhook
    delivery = await client.send_webhook(
        url=args.url,
        payload=payload,
        headers=headers if headers else None
    )
    
    # Print results
    print(f"\nDelivery Results:")
    print(f"ID: {delivery.id}")
    print(f"Status: {delivery.status.value}")
    print(f"Attempts: {delivery.attempts}")
    print(f"Response Status: {delivery.response_status}")
    
    if delivery.status == DeliveryStatus.FAILED:
        print(f"Error: {delivery.error_message}")
        return 1
    
    return 0

async def send_batch_webhooks(args):
    """Send batch webhooks from a file"""
    client = WebhookClient(
        secret_key=args.secret,
        max_retries=args.retries,
        timeout=args.timeout
    )
    
    try:
        with open(args.batch_file, 'r') as f:
            batch_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading batch file: {e}")
        return 1
    
    if not isinstance(batch_data, list):
        print("Batch file must contain a JSON array of webhook configurations")
        return 1
    
    print(f"Sending {len(batch_data)} webhooks...")
    
    # Add progress callback
    completed = 0
    def on_delivery_change(delivery):
        nonlocal completed
        if delivery.status in [DeliveryStatus.SUCCESS, DeliveryStatus.FAILED]:
            completed += 1
            print(f"Progress: {completed}/{len(batch_data)} - {delivery.id}: {delivery.status.value}")
    
    client.add_delivery_callback(on_delivery_change)
    
    # Send webhooks
    results = await client.send_multiple(batch_data, max_concurrent=args.concurrent)
    
    # Print summary
    stats = client.get_delivery_stats()
    print(f"\nBatch Results:")
    print(f"Total: {len(batch_data)}")
    print(f"Success: {stats.get('success', 0)}")
    print(f"Failed: {stats.get('failed', 0)}")
    
    return 0 if stats.get('failed', 0) == 0 else 1

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Webhook Client CLI")
    parser.add_argument("--secret", help="Webhook secret key for signature")
    parser.add_argument("--retries", type=int, default=3, help="Maximum retry attempts")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Single webhook command
    single_parser = subparsers.add_parser("send", help="Send a single webhook")
    single_parser.add_argument("url", help="Webhook URL")
    single_parser.add_argument("--payload", help="JSON payload string")
    single_parser.add_argument("--payload-file", help="File containing JSON payload")
    single_parser.add_argument("--headers", action="append", help="Headers in format 'Key: Value'")
    
    # Batch webhook command
    batch_parser = subparsers.add_parser("batch", help="Send multiple webhooks from file")
    batch_parser.add_argument("batch_file", help="JSON file containing webhook configurations")
    batch_parser.add_argument("--concurrent", type=int, default=5, help="Maximum concurrent requests")
    
    # Generate example files command
    example_parser = subparsers.add_parser("examples", help="Generate example configuration files")
    
    args = parser.parse_args()
    
    if args.command == "send":
        if not args.payload and not args.payload_file:
            print("Error: Either --payload or --payload-file is required")
            return 1
        return asyncio.run(send_single_webhook(args))
    
    elif args.command == "batch":
        return asyncio.run(send_batch_webhooks(args))
    
    elif args.command == "examples":
        generate_examples()
        return 0
    
    else:
        parser.print_help()
        return 1

def generate_examples():
    """Generate example configuration files"""
    # Single webhook payload example
    single_example = {
        "event_type": "user.created",
        "timestamp": 1234567890,
        "data": {
            "id": "user_123",
            "email": "user@example.com",
            "name": "John Doe"
        }
    }
    
    with open("example_payload.json", "w") as f:
        json.dump(single_example, f, indent=2)
    
    # Batch webhooks example
    batch_example = [
        {
            "url": "https://webhook1.example.com/hook",
            "payload": {
                "event_type": "order.created",
                "data": {"order_id": "123", "amount": 99.99}
            },
            "headers": {"X-Custom-Header": "value1"}
        },
        {
            "url": "https://webhook2.example.com/hook",
            "payload": {
                "event_type": "user.updated",
                "data": {"user_id": "456", "changes": ["email"]}
            }
        }
    ]
    
    with open("example_batch.json", "w") as f:
        json.dump(batch_example, f, indent=2)
    
    print("Generated example files:")
    print("- example_payload.json (single webhook payload)")
    print("- example_batch.json (batch webhook configuration)")

if __name__ == "__main__":
    sys.exit(main())