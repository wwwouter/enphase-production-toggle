"""Enphase Envoy client for production control."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import secrets
import string
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class EnvoyClient:
    """Client for communicating with Enphase Envoy."""

    def __init__(self, host: str, username: str, password: str, serial_number: str = None) -> None:
        """Initialize the client."""
        _LOGGER.debug(
            "Initializing EnvoyClient for host: %s, username: %s", host, username
        )
        self.host = host
        self.username = username
        self.password = password
        self.serial_number = serial_number
        self.session_id = None
        self.jwt_token = None
        self._session = None
        self._debug_mode = False
        _LOGGER.debug("EnvoyClient initialized successfully")

    async def authenticate(self) -> None:
        """Authenticate with the Enphase Envoy."""
        _LOGGER.debug("Starting authentication process")

        try:
            if self._session is None:
                _LOGGER.debug("Creating new aiohttp session")
                # Create session with SSL verification disabled for local Envoy
                ssl_context = aiohttp.TCPConnector(ssl=False)
                self._session = aiohttp.ClientSession(connector=ssl_context)

            # Get serial number if not provided
            if not self.serial_number:
                _LOGGER.debug("Serial number not provided, fetching from Envoy")
                self.serial_number = await self._get_serial_number()
                _LOGGER.debug("Retrieved serial number: %s", self.serial_number)

            # Generate OAuth parameters (40 character code_verifier)
            code_verifier = self._generate_code_verifier(40)
            code_challenge = self._generate_challenge(code_verifier)
            _LOGGER.debug(
                "Generated OAuth parameters: verifier length=%d, challenge length=%d",
                len(code_verifier),
                len(code_challenge),
            )

            # Step 1: Get authorization code from Enphase using OAuth flow
            auth_url = "https://entrez.enphaseenergy.com/login"
            redirect_uri = f"https://{self.host}/auth/callback"
            auth_data = {
                "username": self.username,
                "password": self.password,
                "codeChallenge": code_challenge,
                "redirectUri": redirect_uri,
                "client": "envoy-ui",
                "clientId": "envoy-ui-client",
                "authFlow": "oauth",
                "serialNum": self.serial_number or "",
                "granttype": "authorize",
                "state": "",
                "invalidSerialNum": ""
            }
            _LOGGER.debug("Authenticating with Enphase cloud service at %s", auth_url)
            _LOGGER.debug("Redirect URI: %s", redirect_uri)

            timeout = aiohttp.ClientTimeout(total=30)
            async with self._session.post(
                auth_url, data=auth_data, timeout=timeout, allow_redirects=False
            ) as response:
                _LOGGER.debug(
                    "Enphase authentication response status: %d", response.status
                )
                
                # Expect a 302 redirect with authorization code
                if response.status == 302:
                    location = response.headers.get('Location', '')
                    _LOGGER.debug("Redirect location: %s", location)
                    
                    # Extract authorization code from redirect URL
                    from urllib.parse import urlparse, parse_qs
                    parsed_url = urlparse(location)
                    query_params = parse_qs(parsed_url.query)
                    
                    if 'code' in query_params:
                        auth_code = query_params['code'][0]
                        _LOGGER.info("Successfully extracted authorization code")
                        _LOGGER.debug("Authorization code: %s...", auth_code[:8])
                        
                        # Step 2: Get JWT token from local Envoy using auth code
                        await self._get_jwt_token(code_verifier, auth_code, redirect_uri)
                        return
                    else:
                        _LOGGER.error("No authorization code found in redirect URL")
                        raise Exception("Authorization code not found in redirect")
                        
                elif response.status != 200:
                    _LOGGER.error(
                        "Enphase authentication failed with status: %d", response.status
                    )
                    raise Exception(f"Authentication failed: {response.status}")

                # Handle non-redirect response (fallback for debugging)
                response_text = await response.text()
                _LOGGER.debug(
                    "Received response text length: %d characters", len(response_text)
                )
                
                if self._debug_mode:
                    print(f"\n=== AUTHENTICATION RESPONSE DEBUG ===")
                    print(f"Status: {response.status}")
                    print(f"Headers: {dict(response.headers)}")
                    print(f"Response text (first 500 chars):\n{response_text[:500]}")
                    print(f"=== END DEBUG ===\n")
                
                _LOGGER.warning("Expected redirect but got %d response", response.status)
                raise Exception(f"Unexpected response: {response.status}")

        except aiohttp.ClientConnectorError as err:
            _LOGGER.error("Network connection error: %s", err)
            raise Exception(f"Cannot connect to Enphase servers: {err}") from err
        except asyncio.TimeoutError as err:
            _LOGGER.error("Request timeout: %s", err)
            raise Exception(f"Request timed out: {err}") from err
        except Exception as err:
            _LOGGER.error("Authentication failed with error: %s", err)
            _LOGGER.error("Error type: %s", type(err).__name__)
            raise

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

    async def _get_jwt_token(self, code_verifier: str, auth_code: str, redirect_uri: str) -> None:
        """Get JWT token from Entrez cloud service and validate with Envoy."""
        # Step 1: Exchange authorization code for JWT token via Entrez
        entrez_url = "https://entrez.enphaseenergy.com/oauth/token"
        _LOGGER.debug("Getting JWT token from Entrez at %s", entrez_url)

        jwt_data = {
            "client_id": "envoy-ui-client",
            "code": auth_code,
            "code_verifier": code_verifier,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "serial_number": self.serial_number,
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "Home Assistant Enphase Integration"
        }
        
        _LOGGER.debug("JWT request prepared with authorization code")
        _LOGGER.debug("JWT request data: %s", jwt_data)

        if self._session is None:
            _LOGGER.error("Session is None, cannot make JWT request")
            return

        # Step 1: Get JWT token from Entrez cloud service
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout like working implementations
        async with self._session.post(entrez_url, data=jwt_data, headers=headers, ssl=True, timeout=timeout) as response:
            _LOGGER.debug("Entrez token response status: %d", response.status)
            if response.status == 200:
                try:
                    data = await response.json()
                    _LOGGER.debug("Entrez response JSON data: %s", data)
                    # Get the access token from Entrez response
                    token = data.get("access_token") or data.get("token")
                    if token:
                        _LOGGER.info("Successfully obtained JWT token from Entrez")
                        _LOGGER.debug("JWT token: %s...", str(token)[:8])
                        
                        # Step 2: Validate token with Envoy's /auth/check_jwt endpoint
                        await self._validate_jwt_token(token)
                        return
                    else:
                        _LOGGER.error("No access token found in Entrez response")
                        _LOGGER.debug("Entrez response data: %s", data)
                except Exception as e:
                    _LOGGER.error("Failed to parse Entrez JSON response: %s", e)
                    response_text = await response.text()
                    _LOGGER.debug("Raw Entrez response: %s", response_text[:500])
            else:
                _LOGGER.warning("Failed to get JWT token, status: %d", response.status)
                response_text = await response.text()
                _LOGGER.debug("JWT error response: %s", response_text[:200])
                _LOGGER.debug("Response headers: %s", dict(response.headers))
                
                # Common error messages to help with debugging
                if response.status == 400:
                    if "Failed to obtain access_code" in response_text:
                        _LOGGER.error("Authorization code may be expired or invalid")
                    elif "invalid_client" in response_text:
                        _LOGGER.error("Client ID may be incorrect")
                    elif "invalid_grant" in response_text:
                        _LOGGER.error("Grant type or code verifier may be incorrect")
                    else:
                        _LOGGER.error("Bad request - check all JWT parameters")
                elif response.status == 401:
                    _LOGGER.error("Unauthorized - authentication failed")
                elif response.status == 404:
                    _LOGGER.error("Endpoint not found - check URL path")
                
                raise Exception(f"JWT token exchange failed: {response.status} - {response_text[:100]}")

    async def _validate_jwt_token(self, token: str) -> None:
        """Validate JWT token with Envoy's /auth/check_jwt endpoint."""
        validation_url = f"https://{self.host}/auth/check_jwt"
        _LOGGER.debug("Validating JWT token with Envoy at %s", validation_url)
        
        # Headers based on working implementations
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "*/*"
            # Note: User-Agent is intentionally omitted as per working implementations
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        try:
            async with self._session.post(validation_url, headers=headers, ssl=False, timeout=timeout) as response:
                _LOGGER.debug("JWT validation response status: %d", response.status)
                if response.status == 200:
                    response_text = await response.text()
                    _LOGGER.debug("JWT validation response: %s", response_text[:100])
                    
                    # Check for the expected validation response
                    if "Valid token" in response_text or "<!DOCTYPE html>" in response_text:
                        self.jwt_token = token
                        _LOGGER.info("JWT token validated successfully with Envoy")
                        return
                    else:
                        _LOGGER.warning("Unexpected validation response: %s", response_text[:200])
                else:
                    response_text = await response.text()
                    _LOGGER.error("JWT token validation failed: %d - %s", response.status, response_text[:200])
                    raise Exception(f"JWT token validation failed: {response.status}")
        except Exception as e:
            _LOGGER.error("Error during JWT token validation: %s", e)
            raise

    async def get_production_status(self) -> dict[str, Any]:
        """Get current production status."""
        _LOGGER.debug("Getting production status")

        url = f"https://{self.host}/production.json"
        _LOGGER.debug("Making production status request to %s", url)
        
        # Use JWT token with proper header format
        headers = {}
        if self.jwt_token:
            # Try different authorization header formats
            headers["Authorization"] = f"Bearer {self.jwt_token}"
            # Some Envoy versions might need this cookie format
            headers["Cookie"] = f"sessionId={self.jwt_token}"
            _LOGGER.debug("Using JWT token for authentication with both Bearer and Cookie headers")

        if self._session is None:
            _LOGGER.error("Session not initialized for production status request")
            raise Exception("Session not initialized")

        async with self._session.get(url, headers=headers, ssl=False) as response:
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

        # The production control endpoint - uses EMU device ID from /ivp/mod endpoint
        # Note: 603980032 is the dev_eid for EMU device type - this may need to be 
        # dynamically detected for different Envoy models in future versions
        url = f"https://{self.host}/ivp/mod/603980032/mode/power"
        
        # Authentication headers - use ONLY Authorization header initially
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
        }

        # Data format exactly matching HACS integration
        power_forced_off = 0 if enabled else 1  # 0 = on, 1 = off (opposite of enabled)
        data = {
            "length": 1,
            "arr": [power_forced_off]
        }

        _LOGGER.debug("Making production control request to %s", url)
        _LOGGER.debug("Request data: %s", data)
        _LOGGER.debug("Power forced off value: %d", power_forced_off)

        if self._session is None:
            _LOGGER.error("Session not initialized for production control request")
            raise Exception("Session not initialized")

        async with self._session.put(url, headers=headers, json=data, ssl=False) as response:
            _LOGGER.debug("Production control response status: %d", response.status)
            if response.status not in [200, 201, 204]:
                _LOGGER.error(
                    "Failed to set production power, status: %d", response.status
                )
                response_text = await response.text()
                _LOGGER.debug(
                    "Production control error response: %s", response_text[:200]
                )
                _LOGGER.error(
                    "Production control failed with exact HACS payload format. "
                    "This may indicate insufficient permissions or Envoy firmware differences."
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
    
    def _generate_code_verifier(self, length: int = 40) -> str:
        """Generate a random code verifier for OAuth PKCE."""
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    def _generate_challenge(self, code_verifier: str) -> str:
        """Generate code challenge from verifier using SHA256 and base64url encoding."""
        sha_code = hashlib.sha256()
        sha_code.update(code_verifier.encode("utf-8"))
        
        return (
            base64.b64encode(sha_code.digest())
            .decode("utf-8")
            .replace("+", "-")  # + will be -
            .replace("/", "_")  # / will be _
            .replace("=", "")  # remove = chars
        )

    async def _get_serial_number(self) -> str:
        """Get the Envoy serial number from info endpoint."""
        _LOGGER.debug("Fetching serial number from Envoy")
        
        if self._session is None:
            _LOGGER.error("Session not initialized for serial number request")
            raise Exception("Session not initialized")
        
        url = f"http://{self.host}/info.xml"
        
        try:
            async with self._session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    # Extract serial number from XML
                    import re
                    match = re.search(r'<sn>(\d+)</sn>', text)
                    if match:
                        serial = match.group(1)
                        _LOGGER.debug("Found serial number: %s", serial)
                        return serial
                    else:
                        _LOGGER.error("Serial number not found in info.xml response")
                        raise Exception("Serial number not found")
                else:
                    _LOGGER.error("Failed to get info.xml, status: %d", response.status)
                    raise Exception(f"Failed to get serial number: {response.status}")
        except Exception as err:
            _LOGGER.error("Error getting serial number: %s", err)
            raise
