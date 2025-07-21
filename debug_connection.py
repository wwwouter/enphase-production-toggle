#!/usr/bin/env python3
"""Debug script to test Enphase connection without Home Assistant."""

import asyncio
import logging

from custom_components.enphase_production_toggle.envoy_client import EnvoyClient

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def test_connection():
    """Test connection to Enphase."""
    # Use your actual credentials from previous test
    host = "XXX"
    username = "XXX"

    print(f"\nTesting connection to {host} with username {username}")

    import os

    password = os.environ.get("ENPHASE_PASSWORD")
    if not password:
        try:
            import getpass

            password = getpass.getpass("Enter your Enphase password: ")
        except Exception:
            print("Please set ENPHASE_PASSWORD environment variable or run in terminal")
            return

    client = EnvoyClient(host, username, password)

    try:
        print("Step 1: Authenticating...")

        # Enable debug mode to see response content
        client._debug_mode = True

        await client.authenticate()
        print("✅ Authentication successful!")

        print("Step 2: Getting initial production status...")
        status = await client.get_production_status()
        print(f"✅ Production status: {status}")

        current_power = status.get("current_power", 0)
        is_producing = status.get("is_producing", False)
        production_enabled = status.get("production_enabled", True)

        print("📊 Current state:")
        print(f"   Power: {current_power}W")
        print(f"   Producing: {is_producing}")
        print(f"   Production enabled: {production_enabled}")

        print("\nStep 3: Testing production control...")

        # Turn production OFF
        print("🔴 Turning production OFF...")
        await client.set_production_power(False)
        print("✅ Production OFF command sent")

        # Wait 5 seconds and check status
        print("⏳ Waiting 5 seconds...")
        import asyncio

        await asyncio.sleep(5)

        status_off = await client.get_production_status()
        print(f"📊 Status after turning OFF: {status_off}")

        # Wait another 5 seconds (total 10 seconds off)
        print("⏳ Waiting another 5 seconds (total 10s off)...")
        await asyncio.sleep(5)

        # Turn production ON
        print("🟢 Turning production ON...")
        await client.set_production_power(True)
        print("✅ Production ON command sent")

        # Wait 5 seconds and check final status
        print("⏳ Waiting 5 seconds...")
        await asyncio.sleep(5)

        status_on = await client.get_production_status()
        print(f"📊 Final status after turning ON: {status_on}")

        print("\n🎉 Production control test completed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")

    finally:
        await client.close()
        print("Connection closed.")


if __name__ == "__main__":
    asyncio.run(test_connection())
