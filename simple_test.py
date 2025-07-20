#!/usr/bin/env python3
"""Simple test to check Envoy endpoints without complex authentication."""

import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.DEBUG)

async def test_simple_access():
    """Test simple access to Envoy endpoints."""
    host = "192.168.1.xxx"  # Replace with your Envoy IP
    
    # Create session without SSL verification
    connector = aiohttp.TCPConnector(ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        
        # Test 1: Try production.json without auth
        print("Test 1: Trying production.json without authentication...")
        try:
            async with session.get(f"http://{host}/production.json") as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Success! Data: {data}")
                    return
                else:
                    text = await response.text()
                    print(f"Failed: {text[:200]}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 2: Try with digest auth (some Envoy versions use this)
        print("\nTest 2: Trying with digest authentication...")
        try:
            auth = aiohttp.BasicAuth("envoy", "envoy")  # Common default
            async with session.get(f"http://{host}/production.json", auth=auth) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Success! Data: {data}")
                    return
                else:
                    text = await response.text()
                    print(f"Failed: {text[:200]}")
        except Exception as e:
            print(f"Error: {e}")
            
        # Test 3: Try HTTPS endpoints
        print("\nTest 3: Trying HTTPS endpoints...")
        try:
            async with session.get(f"https://{host}/production.json", ssl=False) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Success! Data: {data}")
                    return
                else:
                    text = await response.text()
                    print(f"Failed: {text[:200]}")
        except Exception as e:
            print(f"Error: {e}")
            
        print("\nAll simple access methods failed. Need full OAuth flow.")

if __name__ == "__main__":
    asyncio.run(test_simple_access())