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
    with patch("custom_components.enphase_production_toggle.envoy_client.EnvoyClient") as mock:
        client = mock.return_value
        client.authenticate = AsyncMock()
        client.get_production_status = AsyncMock(return_value={
            "is_producing": True,
            "current_power": 5000,
            "production_enabled": True,
        })
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
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "production": [{"wNow": 5000}]
        })
        mock_response.text = AsyncMock(return_value='{"session_id":"test_session"}')
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        session.get.return_value = mock_response
        session.post.return_value = mock_response
        session.put.return_value = mock_response
        
        yield session