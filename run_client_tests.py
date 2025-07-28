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