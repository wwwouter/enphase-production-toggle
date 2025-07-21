#!/usr/bin/env python3
"""
Test script to verify the JWT authentication fix.
This tests the corrected two-step JWT process:
1. Exchange authorization code for JWT token via Entrez cloud service
2. Validate JWT token with Envoy's /auth/check_jwt endpoint
"""

import logging
import os
import sys

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from custom_components.enphase_production_toggle.envoy_client import EnvoyClient

# Set up logging to see detailed output
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def test_jwt_authentication():
    """Test the JWT authentication process."""

    # Replace with your actual Envoy details
    host = "192.168.1.xxx"  # Replace with your Envoy IP
    username = (
        "your_enphase_email@example.com"  # Replace with your Enphase account email
    )
    password = "your_enphase_password"  # Replace with your Enphase account password

    print("=" * 60)
    print("Testing JWT Authentication Fix")
    print("=" * 60)

    # Create client
    client = EnvoyClient(host, username, password)
    client._debug_mode = True  # Enable debug mode for more output

    try:
        print("\n1. Starting authentication process...")
        await client.authenticate()

        if client.jwt_token:
            print("\n✓ SUCCESS: JWT token obtained and validated!")
            print(f"  Token preview: {client.jwt_token[:20]}...")

            print("\n2. Testing production status with JWT token...")
            status = await client.get_production_status()
            print(f"✓ Production status retrieved: {status}")

        else:
            print("\n✗ FAILED: No JWT token obtained")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await client.close()


if __name__ == "__main__":
    print("Make sure to replace the username and password in this script!")
    print("with your actual Enphase account credentials.\n")

    # Uncomment the line below to run the test (after updating credentials)
    # asyncio.run(test_jwt_authentication())

    print(
        "Please update the credentials in test_jwt_fix.py and uncomment the test line."
    )
