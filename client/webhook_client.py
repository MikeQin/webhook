#!/usr/bin/env python3
"""
Webhook Client - Send webhooks with retry logic and delivery tracking
"""
import asyncio
import json
import logging
import hmac
import hashlib
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeliveryStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class WebhookDelivery:
    """Represents a webhook delivery attempt"""
    id: str
    url: str
    payload: Dict[Any, Any]
    headers: Dict[str, str] = field(default_factory=dict)
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    created_at: float = field(default_factory=time.time)
    last_attempt_at: Optional[float] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None

class WebhookClient:
    """
    Async webhook client with retry logic and delivery tracking
    """
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_wait_min: int = 1,
        retry_wait_max: int = 60
    ):
        self.secret_key = secret_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_wait_min = retry_wait_min
        self.retry_wait_max = retry_wait_max
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.delivery_callbacks: List[Callable[[WebhookDelivery], None]] = []
        
    def add_delivery_callback(self, callback: Callable[[WebhookDelivery], None]):
        """Add a callback to be called when delivery status changes"""
        self.delivery_callbacks.append(callback)
    
    def _create_signature(self, payload: str) -> str:
        """Create HMAC-SHA256 signature for the payload"""
        if not self.secret_key:
            return ""
        
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def _notify_callbacks(self, delivery: WebhookDelivery):
        """Notify all registered callbacks about delivery status change"""
        for callback in self.delivery_callbacks:
            try:
                callback(delivery)
            except Exception as e:
                logger.error(f"Error in delivery callback: {e}")
    
    async def send_webhook(
        self,
        url: str,
        payload: Dict[Any, Any],
        delivery_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        max_attempts: Optional[int] = None
    ) -> WebhookDelivery:
        """
        Send a webhook with automatic retry logic
        """
        if delivery_id is None:
            delivery_id = f"webhook_{int(time.time() * 1000)}"
        
        if headers is None:
            headers = {}
        
        if max_attempts is None:
            max_attempts = self.max_retries
        
        # Create delivery record
        delivery = WebhookDelivery(
            id=delivery_id,
            url=url,
            payload=payload,
            headers=headers.copy(),
            max_attempts=max_attempts
        )
        
        # Store delivery
        self.deliveries[delivery_id] = delivery
        
        # Add default headers
        payload_str = json.dumps(payload, separators=(',', ':'))
        delivery.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "WebhookClient/1.0",
            "X-Webhook-ID": delivery_id,
            "X-Webhook-Timestamp": str(int(time.time()))
        })
        
        # Add signature if secret key is provided
        if self.secret_key:
            signature = self._create_signature(payload_str)
            delivery.headers["X-Hub-Signature-256"] = signature
        
        # Attempt delivery with retry logic
        try:
            await self._deliver_with_retry(delivery, payload_str)
        except Exception as e:
            delivery.status = DeliveryStatus.FAILED
            delivery.error_message = str(e)
            logger.error(f"Failed to deliver webhook {delivery_id}: {e}")
        
        self._notify_callbacks(delivery)
        return delivery
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError))
    )
    async def _deliver_with_retry(self, delivery: WebhookDelivery, payload_str: str):
        """Deliver webhook with automatic retry logic"""
        delivery.attempts += 1
        delivery.last_attempt_at = time.time()
        delivery.status = DeliveryStatus.RETRYING if delivery.attempts > 1 else DeliveryStatus.PENDING
        
        logger.info(f"Attempting webhook delivery {delivery.id} (attempt {delivery.attempts}/{delivery.max_attempts})")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    delivery.url,
                    data=payload_str,
                    headers=delivery.headers
                )
                
                delivery.response_status = response.status_code
                delivery.response_body = response.text[:1000]  # Limit response body size
                
                # Check if delivery was successful
                if 200 <= response.status_code < 300:
                    delivery.status = DeliveryStatus.SUCCESS
                    logger.info(f"Webhook {delivery.id} delivered successfully (status: {response.status_code})")
                else:
                    # Raise exception to trigger retry for 4xx/5xx errors
                    response.raise_for_status()
                    
            except httpx.HTTPStatusError as e:
                delivery.error_message = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                if delivery.attempts >= delivery.max_attempts:
                    delivery.status = DeliveryStatus.FAILED
                    raise
                else:
                    logger.warning(f"Webhook {delivery.id} failed (attempt {delivery.attempts}): {delivery.error_message}")
                    raise
                    
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                delivery.error_message = f"Network error: {str(e)}"
                if delivery.attempts >= delivery.max_attempts:
                    delivery.status = DeliveryStatus.FAILED
                    raise
                else:
                    logger.warning(f"Webhook {delivery.id} network error (attempt {delivery.attempts}): {delivery.error_message}")
                    raise
    
    async def send_multiple(
        self,
        webhooks: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[WebhookDelivery]:
        """
        Send multiple webhooks concurrently
        
        Args:
            webhooks: List of webhook configs with 'url', 'payload', and optional 'headers'
            max_concurrent: Maximum number of concurrent requests
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def send_single(webhook_config):
            async with semaphore:
                return await self.send_webhook(
                    url=webhook_config['url'],
                    payload=webhook_config['payload'],
                    headers=webhook_config.get('headers'),
                    delivery_id=webhook_config.get('delivery_id')
                )
        
        tasks = [send_single(webhook) for webhook in webhooks]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_delivery(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get delivery by ID"""
        return self.deliveries.get(delivery_id)
    
    def get_all_deliveries(self) -> List[WebhookDelivery]:
        """Get all deliveries"""
        return list(self.deliveries.values())
    
    def get_deliveries_by_status(self, status: DeliveryStatus) -> List[WebhookDelivery]:
        """Get deliveries by status"""
        return [d for d in self.deliveries.values() if d.status == status]
    
    def get_delivery_stats(self) -> Dict[str, int]:
        """Get delivery statistics"""
        stats = {status.value: 0 for status in DeliveryStatus}
        for delivery in self.deliveries.values():
            stats[delivery.status.value] += 1
        return stats

# Example event emitter class
class EventEmitter:
    """
    Example class that emits webhooks for various events
    """
    
    def __init__(self, webhook_client: WebhookClient, webhook_urls: List[str]):
        self.webhook_client = webhook_client
        self.webhook_urls = webhook_urls
    
    async def emit_user_created(self, user_data: Dict[str, Any]):
        """Emit user created event"""
        payload = {
            "event_type": "user.created",
            "timestamp": int(time.time()),
            "data": user_data
        }
        
        await self._emit_to_all_urls(payload)
    
    async def emit_order_completed(self, order_data: Dict[str, Any]):
        """Emit order completed event"""
        payload = {
            "event_type": "order.completed",
            "timestamp": int(time.time()),
            "data": order_data
        }
        
        await self._emit_to_all_urls(payload)
    
    async def _emit_to_all_urls(self, payload: Dict[str, Any]):
        """Send webhook to all configured URLs"""
        webhooks = [
            {"url": url, "payload": payload}
            for url in self.webhook_urls
        ]
        
        results = await self.webhook_client.send_multiple(webhooks)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to send webhook to {self.webhook_urls[i]}: {result}")
            else:
                logger.info(f"Webhook sent to {self.webhook_urls[i]}: {result.status.value}")

if __name__ == "__main__":
    async def main():
        # Example usage
        client = WebhookClient(
            secret_key="your-secret-key-here",
            max_retries=3
        )
        
        # Add delivery callback for monitoring
        def on_delivery_change(delivery: WebhookDelivery):
            print(f"Delivery {delivery.id}: {delivery.status.value}")
        
        client.add_delivery_callback(on_delivery_change)
        
        # Send a test webhook
        test_payload = {
            "event_type": "test.event",
            "data": {"message": "Hello from webhook client!"}
        }
        
        delivery = await client.send_webhook(
            url="http://localhost:8000/webhook",
            payload=test_payload
        )
        
        print(f"Delivery result: {delivery.status.value}")
        print(f"Response status: {delivery.response_status}")
        
        # Print delivery stats
        stats = client.get_delivery_stats()
        print(f"Delivery stats: {stats}")
    
    asyncio.run(main())