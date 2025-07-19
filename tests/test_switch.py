"""Test the Enphase Production Toggle switch."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.const import STATE_ON, STATE_OFF

from custom_components.enphase_production_toggle.const import DOMAIN
from custom_components.enphase_production_toggle.switch import EnphaseProductionSwitch


async def test_switch_setup(hass: HomeAssistant, mock_config_entry, mock_envoy_client):
    """Test switch setup."""
    from custom_components.enphase_production_toggle.coordinator import EnphaseDataUpdateCoordinator
    from custom_components.enphase_production_toggle.switch import async_setup_entry
    
    # Setup coordinator
    coordinator = EnphaseDataUpdateCoordinator(hass, mock_config_entry)
    coordinator.client = mock_envoy_client
    coordinator.data = {
        "is_producing": True,
        "current_power": 5000,
        "production_enabled": True,
    }
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = coordinator
    
    # Setup switch
    async_add_entities = MagicMock()
    await async_setup_entry(hass, mock_config_entry, async_add_entities)
    
    # Verify switch was added
    async_add_entities.assert_called_once()
    switch = async_add_entities.call_args[0][0][0]
    assert isinstance(switch, EnphaseProductionSwitch)


async def test_switch_properties(hass: HomeAssistant, mock_config_entry, mock_envoy_client):
    """Test switch properties."""
    from custom_components.enphase_production_toggle.coordinator import EnphaseDataUpdateCoordinator
    
    coordinator = EnphaseDataUpdateCoordinator(hass, mock_config_entry)
    coordinator.client = mock_envoy_client
    coordinator.data = {
        "is_producing": True,
        "current_power": 5000,
        "production_enabled": True,
    }
    coordinator.last_update_success = True
    
    switch = EnphaseProductionSwitch(coordinator, mock_config_entry)
    
    # Test properties
    assert switch.name == "Enphase Production"
    assert switch.unique_id == "test_entry_id_production_switch"
    assert switch.is_on is True
    assert switch.available is True
    
    # Test device info
    device_info = switch.device_info
    assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
    assert device_info["name"] == "Enphase Envoy"
    assert device_info["manufacturer"] == "Enphase"
    
    # Test extra state attributes
    attrs = switch.extra_state_attributes
    assert attrs["current_power"] == 5000
    assert attrs["is_producing"] is True


async def test_switch_is_on_no_data(hass: HomeAssistant, mock_config_entry, mock_envoy_client):
    """Test switch is_on property when no data available."""
    from custom_components.enphase_production_toggle.coordinator import EnphaseDataUpdateCoordinator
    
    coordinator = EnphaseDataUpdateCoordinator(hass, mock_config_entry)
    coordinator.client = mock_envoy_client
    coordinator.data = None
    
    switch = EnphaseProductionSwitch(coordinator, mock_config_entry)
    
    assert switch.is_on is False
    assert switch.extra_state_attributes == {}


async def test_switch_turn_on(hass: HomeAssistant, mock_config_entry, mock_envoy_client):
    """Test turning the switch on."""
    from custom_components.enphase_production_toggle.coordinator import EnphaseDataUpdateCoordinator
    
    coordinator = EnphaseDataUpdateCoordinator(hass, mock_config_entry)
    coordinator.client = mock_envoy_client
    coordinator.data = {
        "is_producing": False,
        "current_power": 0,
        "production_enabled": False,
    }
    coordinator.async_request_refresh = AsyncMock()
    
    switch = EnphaseProductionSwitch(coordinator, mock_config_entry)
    
    await switch.async_turn_on()
    
    # Verify client method was called
    mock_envoy_client.set_production_power.assert_called_once_with(True)
    coordinator.async_request_refresh.assert_called_once()


async def test_switch_turn_off(hass: HomeAssistant, mock_config_entry, mock_envoy_client):
    """Test turning the switch off."""
    from custom_components.enphase_production_toggle.coordinator import EnphaseDataUpdateCoordinator
    
    coordinator = EnphaseDataUpdateCoordinator(hass, mock_config_entry)
    coordinator.client = mock_envoy_client
    coordinator.data = {
        "is_producing": True,
        "current_power": 5000,
        "production_enabled": True,
    }
    coordinator.async_request_refresh = AsyncMock()
    
    switch = EnphaseProductionSwitch(coordinator, mock_config_entry)
    
    await switch.async_turn_off()
    
    # Verify client method was called
    mock_envoy_client.set_production_power.assert_called_once_with(False)
    coordinator.async_request_refresh.assert_called_once()


async def test_switch_turn_on_error(hass: HomeAssistant, mock_config_entry, mock_envoy_client):
    """Test error handling when turning switch on."""
    from custom_components.enphase_production_toggle.coordinator import EnphaseDataUpdateCoordinator
    
    coordinator = EnphaseDataUpdateCoordinator(hass, mock_config_entry)
    coordinator.client = mock_envoy_client
    coordinator.data = {
        "is_producing": False,
        "current_power": 0,
        "production_enabled": False,
    }
    coordinator.async_request_refresh = AsyncMock()
    
    # Mock client to raise exception
    mock_envoy_client.set_production_power.side_effect = Exception("Connection failed")
    
    switch = EnphaseProductionSwitch(coordinator, mock_config_entry)
    
    with pytest.raises(Exception, match="Connection failed"):
        await switch.async_turn_on()


async def test_switch_turn_off_error(hass: HomeAssistant, mock_config_entry, mock_envoy_client):
    """Test error handling when turning switch off."""
    from custom_components.enphase_production_toggle.coordinator import EnphaseDataUpdateCoordinator
    
    coordinator = EnphaseDataUpdateCoordinator(hass, mock_config_entry)
    coordinator.client = mock_envoy_client
    coordinator.data = {
        "is_producing": True,
        "current_power": 5000,
        "production_enabled": True,
    }
    coordinator.async_request_refresh = AsyncMock()
    
    # Mock client to raise exception
    mock_envoy_client.set_production_power.side_effect = Exception("Connection failed")
    
    switch = EnphaseProductionSwitch(coordinator, mock_config_entry)
    
    with pytest.raises(Exception, match="Connection failed"):
        await switch.async_turn_off()