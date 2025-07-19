"""Enphase Envoy client for production control."""
from __future__ import annotations

import hashlib
import logging
import secrets
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class EnvoyClient:
    """Client for communicating with Enphase Envoy."""

    def __init__(self, host: str, username: str, password: str) -> None:
        """Initialize the client."""
        self.host = host
        self.username = username
        self.password = password
        self.session_id = None
        self.jwt_token = None
        self._session = None

    async def authenticate(self) -> None:
        """Authenticate with the Enphase Envoy."""
        if self._session is None:
            self._session = aiohttp.ClientSession()

        # Generate OAuth-like parameters
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = hashlib.sha256(code_verifier.encode()).hexdigest()

        # Step 1: Get session ID from Enphase
        auth_url = "https://entrez.enphaseenergy.com/login"
        auth_data = {
            "username": self.username,
            "password": self.password,
        }

        async with self._session.post(auth_url, data=auth_data) as response:
            if response.status != 200:
                raise Exception(f"Authentication failed: {response.status}")

            # Extract session ID from response
            response_text = await response.text()
            if "session_id" in response_text:
                # Parse session ID from HTML/JSON response
                self.session_id = self._extract_session_id(response_text)

        # Step 2: Get JWT token from local Envoy
        if self.session_id:
            await self._get_jwt_token(code_verifier, code_challenge)

    def _extract_session_id(self, response_text: str) -> str:
        """Extract session ID from authentication response."""
        # Simplified extraction - in real implementation, parse JSON/HTML properly
        import re
        match = re.search(r'"session_id":"([^"]+)"', response_text)
        if match:
            return match.group(1)
        return None

    async def _get_jwt_token(self, code_verifier: str, code_challenge: str) -> None:
        """Get JWT token from Envoy using session ID."""
        token_url = f"http://{self.host}/auth/check_jwt"

        headers = {
            "Authorization": f"Bearer {self.session_id}",
            "Content-Type": "application/json",
        }

        async with self._session.get(token_url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                self.jwt_token = data.get("generation_time")

    async def get_production_status(self) -> dict[str, Any]:
        """Get current production status."""
        if not self.jwt_token:
            await self.authenticate()

        url = f"http://{self.host}/production.json"
        headers = {"Authorization": f"Bearer {self.jwt_token}"}

        async with self._session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                # Extract production status from response
                production = data.get("production", [{}])[0]
                return {
                    "is_producing": production.get("wNow", 0) > 0,
                    "current_power": production.get("wNow", 0),
                    "production_enabled": True,  # Default assumption
                }
            else:
                raise Exception(f"Failed to get production status: {response.status}")

    async def set_production_power(self, enabled: bool) -> None:
        """Enable or disable production power."""
        if not self.jwt_token:
            await self.authenticate()

        # The production control endpoint - may need adjustment based on Envoy model
        url = f"http://{self.host}/ivp/mod/603980032/mode/power"
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
        }

        # Data format based on the HACS integration analysis
        data = {
            "length": 1,
            "arr": [not enabled]  # False = production on, True = production off
        }

        async with self._session.put(url, headers=headers, json=data) as response:
            if response.status not in [200, 201, 204]:
                raise Exception(f"Failed to set production power: {response.status}")

    async def close(self) -> None:
        """Close the client session."""
        if self._session:
            await self._session.close()
            self._session = None
