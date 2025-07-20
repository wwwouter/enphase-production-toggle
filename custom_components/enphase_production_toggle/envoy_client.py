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
        _LOGGER.debug(
            "Initializing EnvoyClient for host: %s, username: %s", host, username
        )
        self.host = host
        self.username = username
        self.password = password
        self.session_id = None
        self.jwt_token = None
        self._session = None
        _LOGGER.debug("EnvoyClient initialized successfully")

    async def authenticate(self) -> None:
        """Authenticate with the Enphase Envoy."""
        _LOGGER.debug("Starting authentication process")

        if self._session is None:
            _LOGGER.debug("Creating new aiohttp session")
            self._session = aiohttp.ClientSession()

        # Generate OAuth-like parameters
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = hashlib.sha256(code_verifier.encode()).hexdigest()
        _LOGGER.debug(
            "Generated OAuth parameters: verifier length=%d, challenge length=%d",
            len(code_verifier),
            len(code_challenge),
        )

        # Step 1: Get session ID from Enphase
        auth_url = "https://entrez.enphaseenergy.com/login"
        auth_data = {
            "username": self.username,
            "password": self.password,
        }
        _LOGGER.debug("Authenticating with Enphase cloud service at %s", auth_url)

        async with self._session.post(auth_url, data=auth_data) as response:
            _LOGGER.debug("Enphase authentication response status: %d", response.status)
            if response.status != 200:
                _LOGGER.error(
                    "Enphase authentication failed with status: %d", response.status
                )
                raise Exception(f"Authentication failed: {response.status}")

            # Extract session ID from response
            response_text = await response.text()
            _LOGGER.debug(
                "Received response text length: %d characters", len(response_text)
            )
            if "session_id" in response_text:
                # Parse session ID from HTML/JSON response
                self.session_id = self._extract_session_id(response_text)
                if self.session_id:
                    _LOGGER.info("Successfully extracted session ID")
                    _LOGGER.debug(
                        "Session ID: %s...",
                        self.session_id[:8] if self.session_id else "None",
                    )
                else:
                    _LOGGER.warning(
                        "Session ID found in response but extraction failed"
                    )
            else:
                _LOGGER.warning("No session_id found in authentication response")

        # Step 2: Get JWT token from local Envoy
        if self.session_id:
            _LOGGER.debug("Proceeding to get JWT token from local Envoy")
            await self._get_jwt_token(code_verifier, code_challenge)
        else:
            _LOGGER.error("Cannot proceed without session ID")
            raise Exception("Failed to obtain session ID from Enphase")

    def _extract_session_id(self, response_text: str) -> str | None:
        """Extract session ID from authentication response."""
        # Simplified extraction - in real implementation, parse JSON/HTML properly
        import re

        _LOGGER.debug("Extracting session ID from response text")
        match = re.search(r'"session_id":"([^"]+)"', response_text)
        if match:
            session_id = match.group(1)
            _LOGGER.debug("Found session ID with length: %d", len(session_id))
            return session_id
        else:
            _LOGGER.debug("No session ID pattern found in response")
            return None

    async def _get_jwt_token(self, code_verifier: str, code_challenge: str) -> None:
        """Get JWT token from Envoy using session ID."""
        token_url = f"http://{self.host}/auth/check_jwt"
        _LOGGER.debug("Getting JWT token from Envoy at %s", token_url)

        headers = {
            "Authorization": f"Bearer {self.session_id}",
            "Content-Type": "application/json",
        }
        _LOGGER.debug("Request headers prepared with session ID")

        if self._session is None:
            _LOGGER.error("Session is None, cannot make JWT request")
            return

        async with self._session.get(token_url, headers=headers) as response:
            _LOGGER.debug("JWT token response status: %d", response.status)
            if response.status == 200:
                data = await response.json()
                self.jwt_token = data.get("generation_time")
                if self.jwt_token:
                    _LOGGER.info("Successfully obtained JWT token")
                    _LOGGER.debug("JWT token: %s...", str(self.jwt_token)[:8])
                else:
                    _LOGGER.warning("JWT token response did not contain expected data")
                    _LOGGER.debug("JWT response data: %s", data)
            else:
                _LOGGER.warning("Failed to get JWT token, status: %d", response.status)
                response_text = await response.text()
                _LOGGER.debug("JWT error response: %s", response_text[:200])

    async def get_production_status(self) -> dict[str, Any]:
        """Get current production status."""
        _LOGGER.debug("Getting production status")

        if not self.jwt_token:
            _LOGGER.debug("No JWT token available, authenticating first")
            await self.authenticate()

        url = f"http://{self.host}/production.json"
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        _LOGGER.debug("Making production status request to %s", url)

        if self._session is None:
            _LOGGER.error("Session not initialized for production status request")
            raise Exception("Session not initialized")

        async with self._session.get(url, headers=headers) as response:
            _LOGGER.debug("Production status response status: %d", response.status)
            if response.status == 200:
                data = await response.json()
                _LOGGER.debug("Received production data: %s", data)

                # Extract production status from response
                production_array = data.get("production", [{}])
                production = production_array[0] if production_array else {}
                current_power = production.get("wNow", 0)
                is_producing = current_power > 0

                result = {
                    "is_producing": is_producing,
                    "current_power": current_power,
                    "production_enabled": True,  # Default assumption
                }

                _LOGGER.info(
                    "Production status: %d W, producing: %s",
                    current_power,
                    is_producing,
                )
                _LOGGER.debug("Full production result: %s", result)
                return result
            else:
                _LOGGER.error(
                    "Failed to get production status, status: %d", response.status
                )
                response_text = await response.text()
                _LOGGER.debug(
                    "Production status error response: %s", response_text[:200]
                )
                raise Exception(f"Failed to get production status: {response.status}")

    async def set_production_power(self, enabled: bool) -> None:
        """Enable or disable production power."""
        _LOGGER.info(
            "Setting production power to: %s", "enabled" if enabled else "disabled"
        )

        if not self.jwt_token:
            _LOGGER.debug("No JWT token available, authenticating first")
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
            "arr": [not enabled],  # False = production on, True = production off
        }

        _LOGGER.debug("Making production control request to %s", url)
        _LOGGER.debug("Request data: %s", data)

        if self._session is None:
            _LOGGER.error("Session not initialized for production control request")
            raise Exception("Session not initialized")

        async with self._session.put(url, headers=headers, json=data) as response:
            _LOGGER.debug("Production control response status: %d", response.status)
            if response.status not in [200, 201, 204]:
                _LOGGER.error(
                    "Failed to set production power, status: %d", response.status
                )
                response_text = await response.text()
                _LOGGER.debug(
                    "Production control error response: %s", response_text[:200]
                )
                raise Exception(f"Failed to set production power: {response.status}")
            else:
                _LOGGER.info(
                    "Successfully set production power to %s",
                    "enabled" if enabled else "disabled",
                )

    async def close(self) -> None:
        """Close the client session."""
        _LOGGER.debug("Closing EnvoyClient session")
        if self._session:
            await self._session.close()
            self._session = None
            _LOGGER.debug("Session closed successfully")
        else:
            _LOGGER.debug("No session to close")
