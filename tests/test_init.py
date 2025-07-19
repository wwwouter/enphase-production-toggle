"""Test the Enphase Production Toggle integration initialization."""

import pytest
from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from custom_components.enphase_production_toggle import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.enphase_production_toggle.const import DOMAIN


async def test_setup_entry(hass: HomeAssistant, mock_config_entry, mock_envoy_client):
    """Test successful setup of config entry."""
    # Mock coordinator
    with patch(
        "custom_components.enphase_production_toggle.coordinator.EnphaseDataUpdateCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()

        # Mock platform setup
        with patch.object(
            hass.config_entries, "async_forward_entry_setups", return_value=True
        ) as mock_forward:
            result = await async_setup_entry(hass, mock_config_entry)

            assert result is True

            # Verify coordinator was created and initialized
            mock_coordinator_class.assert_called_once_with(hass, mock_config_entry)
            mock_coordinator.async_config_entry_first_refresh.assert_called_once()

            # Verify platform setup
            mock_forward.assert_called_once_with(mock_config_entry, [Platform.SWITCH])

            # Verify data storage
            assert DOMAIN in hass.data
            assert mock_config_entry.entry_id in hass.data[DOMAIN]
            assert hass.data[DOMAIN][mock_config_entry.entry_id] == mock_coordinator


async def test_setup_entry_coordinator_error(hass: HomeAssistant, mock_config_entry):
    """Test setup entry when coordinator fails to refresh."""
    with patch(
        "custom_components.enphase_production_toggle.coordinator.EnphaseDataUpdateCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_config_entry_first_refresh = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        with pytest.raises(Exception, match="Connection failed"):
            await async_setup_entry(hass, mock_config_entry)


async def test_unload_entry(hass: HomeAssistant, mock_config_entry):
    """Test successful unload of config entry."""
    # Setup initial data
    hass.data.setdefault(DOMAIN, {})
    mock_coordinator = AsyncMock()
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    # Mock platform unload
    with patch.object(
        hass.config_entries, "async_unload_platforms", return_value=True
    ) as mock_unload:
        result = await async_unload_entry(hass, mock_config_entry)

        assert result is True

        # Verify platform unload
        mock_unload.assert_called_once_with(mock_config_entry, [Platform.SWITCH])

        # Verify data cleanup
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]


async def test_unload_entry_platform_fail(hass: HomeAssistant, mock_config_entry):
    """Test unload entry when platform unload fails."""
    # Setup initial data
    hass.data.setdefault(DOMAIN, {})
    mock_coordinator = AsyncMock()
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    # Mock platform unload failure
    with patch.object(
        hass.config_entries, "async_unload_platforms", return_value=False
    ) as mock_unload:
        result = await async_unload_entry(hass, mock_config_entry)

        assert result is False

        # Verify platform unload was attempted
        mock_unload.assert_called_once_with(mock_config_entry, [Platform.SWITCH])

        # Verify data was NOT cleaned up due to failure
        assert mock_config_entry.entry_id in hass.data[DOMAIN]


async def test_unload_entry_no_data(hass: HomeAssistant, mock_config_entry):
    """Test unload entry when no data exists."""
    # Mock platform unload
    with patch.object(
        hass.config_entries, "async_unload_platforms", return_value=True
    ) as mock_unload:
        result = await async_unload_entry(hass, mock_config_entry)

        assert result is True

        # Verify platform unload
        mock_unload.assert_called_once_with(mock_config_entry, [Platform.SWITCH])
