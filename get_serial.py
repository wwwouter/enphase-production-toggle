#!/usr/bin/env python3
"""Get Envoy serial number from info endpoint."""

import asyncio

import aiohttp


async def get_envoy_serial():
    """Get the Envoy serial number."""
    host = "192.168.1.xxx"  # Replace with your Envoy IP

    # Try various endpoints that might contain serial number
    endpoints_to_try = [
        f"http://{host}/info.xml",
        f"http://{host}/info",
        f"http://{host}/api/v1/info",
        f"http://{host}/inventory.json",
        f"http://{host}/api/v1/inventory",
        f"https://{host}/info.xml",
        f"https://{host}/info",
        f"https://{host}/api/v1/info",
    ]

    connector = aiohttp.TCPConnector(ssl=False)

    async with aiohttp.ClientSession(connector=connector) as session:
        for endpoint in endpoints_to_try:
            print(f"\nTrying: {endpoint}")
            try:
                async with session.get(
                    endpoint, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    print(f"Status: {response.status}")
                    if response.status == 200:
                        if endpoint.endswith(".xml"):
                            text = await response.text()
                            print(f"XML Response:\n{text}")
                        else:
                            try:
                                data = await response.json()
                                print(f"JSON Response:\n{data}")
                            except Exception:
                                text = await response.text()
                                print(f"Text Response:\n{text}")
                    else:
                        text = await response.text()
                        print(f"Error response: {text[:200]}")
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(get_envoy_serial())
