#!/usr/bin/env python3
"""Test production control with form data instead of JSON."""

import asyncio

from custom_components.enphase_production_toggle.envoy_client import EnvoyClient


async def test_form_data():
    """Test production control with form data."""
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

        url = f"https://{host}/ivp/mod/603980032/mode/power"

        # Test with form data instead of JSON
        headers = {
            "Authorization": f"Bearer {client.jwt_token}",
            "Cookie": f"sessionId={client.jwt_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Test turning off production (powerForcedOff=true)
        print("\n=== Test: Form data to turn OFF production ===")
        form_data = {"powerForcedOff": "true"}

        try:
            async with client._session.put(
                url, headers=headers, data=form_data, ssl=False
            ) as response:
                print(f"PUT {url}")
                print(f"Form data: {form_data}")
                print(f"Status: {response.status}")
                text = await response.text()
                print(f"Response: {text}")

                if response.status in [200, 201, 204]:
                    print("✅ Production control request successful!")

                    # Wait 3 seconds and check the mode
                    print("\nWaiting 3 seconds...")
                    await asyncio.sleep(3)

                    # Check current mode
                    get_headers = {
                        "Authorization": f"Bearer {client.jwt_token}",
                        "Cookie": f"sessionId={client.jwt_token}",
                    }
                    async with client._session.get(
                        url, headers=get_headers, ssl=False
                    ) as check_response:
                        print(f"Checking mode status: {check_response.status}")
                        if check_response.status == 200:
                            check_data = await check_response.json()
                            print(f"Current mode: {check_data}")

                    # Turn it back on
                    print("\n=== Turning production back ON ===")
                    form_data_on = {"powerForcedOff": "false"}
                    async with client._session.put(
                        url, headers=headers, data=form_data_on, ssl=False
                    ) as response2:
                        print(f"PUT {url}")
                        print(f"Form data: {form_data_on}")
                        print(f"Status: {response2.status}")
                        text2 = await response2.text()
                        print(f"Response: {text2}")

        except Exception as e:
            print(f"Error: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_form_data())
