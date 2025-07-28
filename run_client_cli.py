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