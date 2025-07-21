#!/usr/bin/env python3
"""Test different production control endpoints."""

import asyncio

from custom_components.enphase_production_toggle.envoy_client import EnvoyClient


async def test_production_control():
    """Test various production control methods."""
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

        headers = {
            "Authorization": f"Bearer {client.jwt_token}",
            "Cookie": f"sessionId={client.jwt_token}",
            "Content-Type": "application/json",
        }

        # Test 1: Try the ensemble/secctrl endpoint to set shutdown=true
        print("\n=== Test 1: Ensemble SecCtrl (shutdown) ===")
        url1 = f"https://{host}/ivp/ensemble/secctrl"
        data1 = {"shutdown": True}

        try:
            async with client._session.put(
                url1, headers=headers, json=data1, ssl=False
            ) as response:
                print(f"PUT {url1}")
                print(f"Data: {data1}")
                print(f"Status: {response.status}")
                text = await response.text()
                print(f"Response: {text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

        # Test 2: Try different data format for the original endpoint
        print("\n=== Test 2: Different data format for ivp/mod endpoint ===")
        url2 = f"https://{host}/ivp/mod/603980032/mode/power"
        data2 = {"enable": False}  # Try simpler format

        try:
            async with client._session.put(
                url2, headers=headers, json=data2, ssl=False
            ) as response:
                print(f"PUT {url2}")
                print(f"Data: {data2}")
                print(f"Status: {response.status}")
                text = await response.text()
                print(f"Response: {text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

        # Test 3: Try correct HACS format with PUT
        print("\n=== Test 3: HACS format with PUT ===")
        data3 = {"length": 1, "arr": [1]}  # Correct format: 1 = off, 0 = on

        try:
            async with client._session.put(
                url2, headers=headers, json=data3, ssl=False
            ) as response:
                print(f"PUT {url2}")
                print(f"Data: {data3}")
                print(f"Status: {response.status}")
                text = await response.text()
                print(f"Response: {text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

        # Test 4: Try GET to see current mode first
        print("\n=== Test 4: GET current mode ===")
        try:
            async with client._session.get(
                url2, headers=headers, ssl=False
            ) as response:
                print(f"GET {url2}")
                print(f"Status: {response.status}")
                text = await response.text()
                print(f"Response: {text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_production_control())
