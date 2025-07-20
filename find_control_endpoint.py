#!/usr/bin/env python3
"""Find the correct production control endpoint for this Envoy."""

import asyncio
import aiohttp
from custom_components.enphase_production_toggle.envoy_client import EnvoyClient

async def find_control_endpoint():
    """Find the production control endpoint."""
    host = "192.168.1.xxx"  # Replace with your Envoy IP
    username = "your-email@example.com"  # Replace with your Enphase installer email
    
    import os
    password = os.environ.get('ENPHASE_PASSWORD')
    if not password:
        print("Please set ENPHASE_PASSWORD environment variable")
        return
    
    client = EnvoyClient(host, username, password)
    
    try:
        print("Authenticating...")
        await client.authenticate()
        print("✅ Authentication successful!")
        
        # Try to find inventory or devices endpoint
        test_endpoints = [
            f"https://{host}/inventory.json",
            f"https://{host}/api/v1/inventory",
            f"https://{host}/devices.json", 
            f"https://{host}/api/v1/devices",
            f"https://{host}/ivp/ensemble/inventory",
            f"https://{host}/ivp/ensemble/secctrl",
            f"https://{host}/ivp/meters",
            f"https://{host}/ivp/mod",
            f"https://{host}/ivp",
        ]
        
        headers = {
            "Authorization": f"Bearer {client.jwt_token}",
            "Cookie": f"sessionId={client.jwt_token}",
        }
        
        for endpoint in test_endpoints:
            print(f"\nTrying: {endpoint}")
            try:
                async with client._session.get(endpoint, headers=headers, ssl=False, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    print(f"Status: {response.status}")
                    if response.status == 200:
                        try:
                            data = await response.json()
                            print(f"JSON Response: {data}")
                        except:
                            text = await response.text()
                            print(f"Text Response (first 500 chars): {text[:500]}")
                    else:
                        text = await response.text()
                        print(f"Error: {text[:200]}")
            except Exception as e:
                print(f"Error: {e}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(find_control_endpoint())