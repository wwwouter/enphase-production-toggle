"""Simple integration tests that don't require full Home Assistant setup."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from custom_components.enphase_production_toggle.const import (
    DOMAIN,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    DEFAULT_NAME,
)


def test_constants():
    """Test that constants are defined correctly."""
    assert DOMAIN == "enphase_production_toggle"
    assert CONF_HOST == "host"
    assert CONF_USERNAME == "username"
    assert CONF_PASSWORD == "password"
    assert DEFAULT_NAME == "Enphase Production"


@pytest.mark.asyncio
async def test_coordinator_initialization():
    """Test coordinator can be initialized."""
    from custom_components.enphase_production_toggle.coordinator import (
        EnphaseDataUpdateCoordinator,
    )

    # Mock config entry
    mock_entry = MagicMock()
    mock_entry.data = {
        CONF_HOST: "192.168.1.100",
        CONF_USERNAME: "test@example.com",
        CONF_PASSWORD: "testpassword",
    }

    # Mock hass
    mock_hass = MagicMock()

    with patch(
        "custom_components.enphase_production_toggle.coordinator.EnvoyClient"
    ) as mock_client_class:
        coordinator = EnphaseDataUpdateCoordinator(mock_hass, mock_entry)

        # Verify client was created with correct parameters
        mock_client_class.assert_called_once_with(
            "192.168.1.100", "test@example.com", "testpassword"
        )

        # Verify coordinator properties
        assert coordinator.name == DOMAIN


@pytest.mark.asyncio
async def test_switch_entity_creation():
    """Test switch entity can be created."""
    from custom_components.enphase_production_toggle.switch import (
        EnphaseProductionSwitch,
    )
    from custom_components.enphase_production_toggle.coordinator import (
        EnphaseDataUpdateCoordinator,
    )

    # Mock coordinator
    mock_coordinator = MagicMock()
    mock_coordinator.data = {
        "is_producing": True,
        "current_power": 5000,
        "production_enabled": True,
    }
    mock_coordinator.last_update_success = True

    # Mock config entry
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry_id"

    switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

    # Test basic properties
    assert switch.name == DEFAULT_NAME
    assert switch.unique_id == "test_entry_id_production_switch"
    assert switch.is_on is True
    assert switch.available is True

    # Test device info
    device_info = switch.device_info
    assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
    assert device_info["manufacturer"] == "Enphase"


@pytest.mark.asyncio
async def test_switch_turn_on():
    """Test switch turn on functionality."""
    from custom_components.enphase_production_toggle.switch import (
        EnphaseProductionSwitch,
    )

    # Mock coordinator with client
    mock_coordinator = MagicMock()
    mock_coordinator.client.set_production_power = AsyncMock()
    mock_coordinator.async_request_refresh = AsyncMock()

    # Mock config entry
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry_id"

    switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

    await switch.async_turn_on()

    # Verify client method was called
    mock_coordinator.client.set_production_power.assert_called_once_with(True)
    mock_coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_switch_turn_off():
    """Test switch turn off functionality."""
    from custom_components.enphase_production_toggle.switch import (
        EnphaseProductionSwitch,
    )

    # Mock coordinator with client
    mock_coordinator = MagicMock()
    mock_coordinator.client.set_production_power = AsyncMock()
    mock_coordinator.async_request_refresh = AsyncMock()

    # Mock config entry
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry_id"

    switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

    await switch.async_turn_off()

    # Verify client method was called
    mock_coordinator.client.set_production_power.assert_called_once_with(False)
    mock_coordinator.async_request_refresh.assert_called_once()
