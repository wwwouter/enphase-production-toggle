#!/usr/bin/env python3
"""Decode JWT token to see permissions."""

import asyncio
import base64
import json

from custom_components.enphase_production_toggle.envoy_client import EnvoyClient


def decode_jwt_payload(token):
    """Decode JWT payload (not verifying signature, just reading contents)."""
    try:
        # JWT has 3 parts: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            return "Invalid JWT format"

        # Decode the payload (middle part)
        payload = parts[1]

        # Add padding if needed (JWT base64 might be missing padding)
        missing_padding = len(payload) % 4
        if missing_padding:
            payload += "=" * (4 - missing_padding)

        # Decode base64
        decoded = base64.b64decode(payload)

        # Parse JSON
        payload_json = json.loads(decoded)
        return payload_json

    except Exception as e:
        return f"Error decoding JWT: {e}"


async def main():
    """Get JWT and decode it."""
    host = "192.168.1.xxx"  # Replace with your Envoy IP
    username = "your-email@example.com"  # Replace with your Enphase installer email

    import os

    password = os.environ.get("ENPHASE_PASSWORD")
    if not password:
        print("Please set ENPHASE_PASSWORD environment variable")
        return

    client = EnvoyClient(host, username, password)

    try:
        print("Authenticating...")
        await client.authenticate()
        print("✅ Authentication successful!")

        print(f"\nJWT Token: {client.jwt_token}")

        print("\n=== JWT Token Payload ===")
        payload = decode_jwt_payload(client.jwt_token)
        print(json.dumps(payload, indent=2))

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
