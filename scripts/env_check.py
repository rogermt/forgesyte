#!/usr/bin/env python3
"""Phase 14 Environment Sanity Check Script.

This script verifies:
- REST connectivity
- WS connectivity
- CORS headers
- API prefix correctness
- Plugin listing endpoint

Usage:
    python scripts/env_check.py
"""

import asyncio
import json
import os
import sys

try:
    import requests
    import websockets
except ImportError as e:
    print(f"❌ Missing required dependency: {e}")
    print("Install with: pip install requests websockets")
    sys.exit(1)

# Default URLs - can be overridden with environment variables
API_URL = os.getenv("FORGESYTE_API_URL", "https://forgetunnel.loca.lt/v1")
WS_URL = os.getenv("FORGESYTE_WS_URL", "wss://forgetunnel.loca.lt/v1/stream")


def check_rest():
    """Check REST API connectivity and CORS headers."""
    print("🔍 Checking REST API:", API_URL)

    try:
        # Check CORS headers with OPTIONS request
        r = requests.options(f"{API_URL}/plugins", timeout=10)
        print("  OPTIONS /plugins:", r.status_code)
        cors_origin = r.headers.get("Access-Control-Allow-Origin")
        print("  CORS headers:", cors_origin or "❌ Not set")

        # Check plugin listing endpoint
        r = requests.get(f"{API_URL}/plugins", timeout=10)
        print("  GET /plugins:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print(f"  Response: {len(data.get('plugins', []))} plugins found")
        else:
            print(f"  ❌ Error: {r.text[:100]}")

        # Check CORS diagnostic endpoint
        r = requests.get(f"{API_URL}/debug/cors", timeout=10)
        print("  GET /debug/cors:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print(f"  Allowed origins: {data.get('allowed_origins', [])}")
        else:
            print(f"  ⚠️  CORS diagnostic endpoint not available")

    except requests.exceptions.RequestException as e:
        print(f"  ❌ REST check failed: {e}")


async def check_ws():
    """Check WebSocket connectivity."""
    print("\n🔍 Checking WebSocket:", WS_URL)

    try:
        async with websockets.connect(WS_URL, timeout=10) as ws:
            # Send ping message
            await ws.send(json.dumps({"type": "ping"}))
            msg = await ws.recv()
            print(f"  WS response: {msg[:100] if len(msg) > 100 else msg}")
    except (websockets.exceptions.WebSocketException, asyncio.TimeoutError) as e:
        print(f"  ❌ WS check failed: {e}")


if __name__ == "__main__":
    check_rest()
    asyncio.run(check_ws())
    print("\n✅ Environment check complete")