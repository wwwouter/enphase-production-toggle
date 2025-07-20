"""Test configuration for Enphase Production Toggle."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.enphase_production_toggle.const import (
    DOMAIN,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
)


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    return ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Enphase Envoy (192.168.1.100)",
        data={
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "testpassword",
        },
        source="user",
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_envoy_client():
    """Mock Enphase Envoy client."""
    with patch(
        "custom_components.enphase_production_toggle.envoy_client.EnvoyClient"
    ) as mock:
        client = mock.return_value
        client.authenticate = AsyncMock()
        client.get_production_status = AsyncMock(
            return_value={
                "is_producing": True,
                "current_power": 5000,
                "production_enabled": True,
            }
        )
        client.set_production_power = AsyncMock()
        client.close = AsyncMock()
        yield client


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session."""
    with patch("aiohttp.ClientSession") as mock_session:
        session = mock_session.return_value
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=None)
        session.close = AsyncMock()

        # Mock serial number response (info.xml)
        serial_response = MagicMock()
        serial_response.status = 200
        serial_response.text = AsyncMock(return_value='<?xml version="1.0"?><envoy_info><device><sn>123456789012</sn></device></envoy_info>')
        serial_response.__aenter__ = AsyncMock(return_value=serial_response)
        serial_response.__aexit__ = AsyncMock(return_value=None)

        # Mock OAuth response (302 redirect)
        oauth_response = MagicMock()
        oauth_response.status = 302
        oauth_response.headers = {'Location': 'https://192.168.1.100/auth/callback?code=test_auth_code'}
        oauth_response.__aenter__ = AsyncMock(return_value=oauth_response)
        oauth_response.__aexit__ = AsyncMock(return_value=None)

        # Mock JWT token response
        jwt_response = MagicMock()
        jwt_response.status = 200
        jwt_response.json = AsyncMock(return_value={'access_token': 'test_jwt_token'})
        jwt_response.__aenter__ = AsyncMock(return_value=jwt_response)
        jwt_response.__aexit__ = AsyncMock(return_value=None)

        # Mock JWT validation response
        jwt_check_response = MagicMock()
        jwt_check_response.status = 200
        jwt_check_response.text = AsyncMock(return_value='<h2>Valid token.</h2>')
        jwt_check_response.__aenter__ = AsyncMock(return_value=jwt_check_response)
        jwt_check_response.__aexit__ = AsyncMock(return_value=None)

        # Mock production status response
        production_response = MagicMock()
        production_response.status = 200
        production_response.json = AsyncMock(return_value={"production": [{"wNow": 5000, "type": "inverters"}]})
        production_response.__aenter__ = AsyncMock(return_value=production_response)
        production_response.__aexit__ = AsyncMock(return_value=None)

        # Mock production control response
        control_response = MagicMock()
        control_response.status = 204
        control_response.text = AsyncMock(return_value='')
        control_response.__aenter__ = AsyncMock(return_value=control_response)
        control_response.__aexit__ = AsyncMock(return_value=None)

        # Configure session to return appropriate responses based on URL
        def get_side_effect(url, *args, **kwargs):
            if 'info.xml' in str(url):
                return serial_response
            elif 'production.json' in str(url):
                return production_response
            elif 'check_jwt' in str(url):
                return jwt_check_response
            return production_response

        def post_side_effect(url, *args, **kwargs):
            if 'entrez.enphaseenergy.com/login' in str(url):
                return oauth_response
            elif 'oauth/token' in str(url):
                return jwt_response
            return oauth_response

        session.get.side_effect = get_side_effect
        session.post.side_effect = post_side_effect
        session.put.return_value = control_response

        yield session
