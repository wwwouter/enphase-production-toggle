"""Test the Enphase Production Toggle coordinator."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.enphase_production_toggle.coordinator import (
    EnphaseDataUpdateCoordinator,
)
from custom_components.enphase_production_toggle.const import DEFAULT_SCAN_INTERVAL


async def test_coordinator_init(hass: HomeAssistant, mock_config_entry):
    """Test coordinator initialization."""
    with patch(
        "custom_components.enphase_production_toggle.coordinator.EnvoyClient"
    ) as mock_client_class:
        coordinator = EnphaseDataUpdateCoordinator(hass, mock_config_entry)

        # Verify client was created with correct parameters
        mock_client_class.assert_called_once_with(
            "192.168.1.100", "test@example.com", "testpassword"
        )

        # Verify coordinator properties
        assert coordinator.name == "enphase_production_toggle"
        assert coordinator.update_interval == timedelta(seconds=DEFAULT_SCAN_INTERVAL)


async def test_coordinator_update_data_success(
    hass: HomeAssistant, mock_config_entry, mock_envoy_client
):
    """Test successful data update."""
    with patch(
        "custom_components.enphase_production_toggle.coordinator.EnvoyClient",
        return_value=mock_envoy_client,
    ):
        coordinator = EnphaseDataUpdateCoordinator(hass, mock_config_entry)

        # Mock successful responses
        mock_envoy_client.authenticate = AsyncMock()
        mock_envoy_client.get_production_status = AsyncMock(
            return_value={
                "is_producing": True,
                "current_power": 5000,
                "production_enabled": True,
            }
        )

        result = await coordinator._async_update_data()

        # Verify authentication and data retrieval
        mock_envoy_client.authenticate.assert_called_once()
        mock_envoy_client.get_production_status.assert_called_once()

        # Verify returned data
        expected = {
            "is_producing": True,
            "current_power": 5000,
            "production_enabled": True,
        }
        assert result == expected


async def test_coordinator_update_data_auth_failure(
    hass: HomeAssistant, mock_config_entry, mock_envoy_client
):
    """Test data update with authentication failure."""
    with patch(
        "custom_components.enphase_production_toggle.coordinator.EnvoyClient",
        return_value=mock_envoy_client,
    ):
        coordinator = EnphaseDataUpdateCoordinator(hass, mock_config_entry)

        # Mock authentication failure
        mock_envoy_client.authenticate = AsyncMock(side_effect=Exception("Auth failed"))

        with pytest.raises(
            UpdateFailed, match="Error communicating with API: Auth failed"
        ):
            await coordinator._async_update_data()


async def test_coordinator_update_data_get_status_failure(
    hass: HomeAssistant, mock_config_entry, mock_envoy_client
):
    """Test data update with get_production_status failure."""
    with patch(
        "custom_components.enphase_production_toggle.coordinator.EnvoyClient",
        return_value=mock_envoy_client,
    ):
        coordinator = EnphaseDataUpdateCoordinator(hass, mock_config_entry)

        # Mock successful auth but failed status retrieval
        mock_envoy_client.authenticate = AsyncMock()
        mock_envoy_client.get_production_status = AsyncMock(
            side_effect=Exception("Status failed")
        )

        with pytest.raises(
            UpdateFailed, match="Error communicating with API: Status failed"
        ):
            await coordinator._async_update_data()


async def test_coordinator_client_property(
    hass: HomeAssistant, mock_config_entry, mock_envoy_client
):
    """Test coordinator client property access."""
    with patch(
        "custom_components.enphase_production_toggle.coordinator.EnvoyClient",
        return_value=mock_envoy_client,
    ):
        coordinator = EnphaseDataUpdateCoordinator(hass, mock_config_entry)

        # Verify client is accessible
        assert coordinator.client == mock_envoy_client
