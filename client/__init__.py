"""
Webhook Client Package

A comprehensive webhook client library with retry logic, delivery tracking,
and signature verification for Python applications.
"""

from .webhook_client import WebhookClient, EventEmitter, DeliveryStatus, WebhookDelivery

__version__ = "1.0.0"
__all__ = ["WebhookClient", "EventEmitter", "DeliveryStatus", "WebhookDelivery"]