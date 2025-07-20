"""Unit tests for EnphaseProductionSwitch."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.enphase_production_toggle.const import DEFAULT_NAME, DOMAIN
from custom_components.enphase_production_toggle.switch import EnphaseProductionSwitch


class TestEnphaseProductionSwitchUnit:
    """Unit tests for EnphaseProductionSwitch class."""

    def test_switch_initialization(self):
        """Test switch initialization with various configurations."""
        mock_coordinator = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry_123"

        switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

        assert switch._entry == mock_entry
        assert switch._attr_name == DEFAULT_NAME
        assert switch._attr_unique_id == "test_entry_123_production_switch"

    def test_switch_unique_id_generation(self):
        """Test switch unique ID generation with different entry IDs."""
        mock_coordinator = MagicMock()
        
        test_entry_ids = [
            "short_id",
            "very_long_entry_id_with_many_characters",
            "id-with-dashes",
            "id_with_underscores",
            "id123with456numbers",
        ]

        for entry_id in test_entry_ids:
            mock_entry = MagicMock()
            mock_entry.entry_id = entry_id

            switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

            expected_unique_id = f"{entry_id}_production_switch"
            assert switch._attr_unique_id == expected_unique_id
            assert switch.unique_id == expected_unique_id

    def test_device_info_structure(self):
        """Test device info structure and content."""
        mock_coordinator = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)
        device_info = switch.device_info

        # Verify required fields
        assert "identifiers" in device_info
        assert "name" in device_info
        assert "manufacturer" in device_info
        assert "model" in device_info

        # Verify values
        assert device_info["identifiers"] == {(DOMAIN, "test_entry")}
        assert device_info["name"] == "Enphase Envoy"
        assert device_info["manufacturer"] == "Enphase"
        assert device_info["model"] == "Envoy"

        # Verify types
        assert isinstance(device_info["identifiers"], set)
        assert isinstance(device_info["name"], str)
        assert isinstance(device_info["manufacturer"], str)
        assert isinstance(device_info["model"], str)

    def test_is_on_property_with_various_data(self):
        """Test is_on property with various coordinator data states."""
        mock_coordinator = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

        test_cases = [
            # (coordinator_data, expected_is_on)
            (None, False),  # No data
            ({}, False),  # Empty data
            ({"production_enabled": True}, True),  # Enabled
            ({"production_enabled": False}, False),  # Disabled
            ({"other_key": "value"}, False),  # Missing production_enabled key
            ({"production_enabled": True, "current_power": 5000}, True),  # With power data
            ({"production_enabled": False, "current_power": 0}, False),  # Disabled with zero power
        ]

        for coordinator_data, expected_is_on in test_cases:
            mock_coordinator.data = coordinator_data
            assert switch.is_on == expected_is_on

    def test_available_property(self):
        """Test available property based on coordinator update success."""
        mock_coordinator = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

        # Test available when last update was successful
        mock_coordinator.last_update_success = True
        assert switch.available is True

        # Test unavailable when last update failed
        mock_coordinator.last_update_success = False
        assert switch.available is False

    def test_extra_state_attributes_various_data(self):
        """Test extra state attributes with various data configurations."""
        mock_coordinator = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

        test_cases = [
            # (coordinator_data, expected_attrs)
            (None, {}),  # No data
            ({}, {"current_power": 0, "is_producing": False}),  # Empty data
            (
                {"current_power": 5000, "is_producing": True},
                {"current_power": 5000, "is_producing": True},
            ),
            (
                {"current_power": 0, "is_producing": False},
                {"current_power": 0, "is_producing": False},
            ),
            (
                {"other_key": "value"},
                {"current_power": 0, "is_producing": False},
            ),  # Missing keys
            (
                {"current_power": 15000, "is_producing": True, "extra": "ignored"},
                {"current_power": 15000, "is_producing": True},
            ),  # Extra data ignored
        ]

        for coordinator_data, expected_attrs in test_cases:
            mock_coordinator.data = coordinator_data
            attrs = switch.extra_state_attributes
            assert attrs == expected_attrs

    def test_extra_state_attributes_data_types(self):
        """Test extra state attributes data type handling."""
        mock_coordinator = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

        # Test with various data types
        test_data_types = [
            {"current_power": 5000, "is_producing": True},  # int, bool
            {"current_power": 5000.5, "is_producing": True},  # float, bool
            {"current_power": "5000", "is_producing": "true"},  # string values
            {"current_power": None, "is_producing": None},  # None values
        ]

        for data in test_data_types:
            mock_coordinator.data = data
            attrs = switch.extra_state_attributes

            # Should always return the data as-is (with defaults for missing keys)
            expected_power = data.get("current_power", 0)
            expected_producing = data.get("is_producing", False)

            assert attrs["current_power"] == expected_power
            assert attrs["is_producing"] == expected_producing

    @pytest.mark.asyncio
    async def test_async_turn_on_success(self):
        """Test successful turn on operation."""
        mock_coordinator = MagicMock()
        mock_coordinator.client.set_production_power = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()
        
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

        await switch.async_turn_on()

        mock_coordinator.client.set_production_power.assert_called_once_with(True)
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_off_success(self):
        """Test successful turn off operation."""
        mock_coordinator = MagicMock()
        mock_coordinator.client.set_production_power = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()
        
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

        await switch.async_turn_off()

        mock_coordinator.client.set_production_power.assert_called_once_with(False)
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_on_with_kwargs(self):
        """Test turn on operation with various kwargs."""
        mock_coordinator = MagicMock()
        mock_coordinator.client.set_production_power = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()
        
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

        # Test with various kwargs (should be ignored)
        test_kwargs = [
            {},
            {"extra_param": "value"},
            {"multiple": "params", "should": "be", "ignored": True},
        ]

        for kwargs in test_kwargs:
            mock_coordinator.client.set_production_power.reset_mock()
            mock_coordinator.async_request_refresh.reset_mock()

            await switch.async_turn_on(**kwargs)

            mock_coordinator.client.set_production_power.assert_called_once_with(True)
            mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_on_error_handling(self):
        """Test turn on error handling with various exceptions."""
        mock_coordinator = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

        error_types = [
            Exception("General error"),
            ConnectionError("Connection failed"),
            TimeoutError("Request timed out"),
            ValueError("Invalid value"),
        ]

        for error in error_types:
            mock_coordinator.client.set_production_power = AsyncMock(side_effect=error)
            mock_coordinator.async_request_refresh = AsyncMock()

            with pytest.raises(type(error)):
                await switch.async_turn_on()

            mock_coordinator.client.set_production_power.assert_called_once_with(True)
            # Refresh should not be called if set_production_power fails
            mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_turn_off_error_handling(self):
        """Test turn off error handling with various exceptions."""
        mock_coordinator = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

        error_types = [
            Exception("General error"),
            ConnectionError("Connection failed"),
            TimeoutError("Request timed out"),
            ValueError("Invalid value"),
        ]

        for error in error_types:
            mock_coordinator.client.set_production_power = AsyncMock(side_effect=error)
            mock_coordinator.async_request_refresh = AsyncMock()

            with pytest.raises(type(error)):
                await switch.async_turn_off()

            mock_coordinator.client.set_production_power.assert_called_once_with(False)
            # Refresh should not be called if set_production_power fails
            mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_error_handling(self):
        """Test error handling when refresh fails."""
        mock_coordinator = MagicMock()
        mock_coordinator.client.set_production_power = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock(
            side_effect=Exception("Refresh failed")
        )
        
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

        # If refresh fails, the whole operation should fail
        with pytest.raises(Exception, match="Refresh failed"):
            await switch.async_turn_on()

        # But set_production_power should still have been called
        mock_coordinator.client.set_production_power.assert_called_once_with(True)

    def test_switch_name_property(self):
        """Test switch name property."""
        mock_coordinator = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

        assert switch.name == DEFAULT_NAME
        assert isinstance(switch.name, str)
        assert len(switch.name) > 0

    def test_switch_inheritance(self):
        """Test that switch properly inherits from required base classes."""
        mock_coordinator = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        switch = EnphaseProductionSwitch(mock_coordinator, mock_entry)

        # Should have methods from both parent classes
        assert hasattr(switch, "async_turn_on")
        assert hasattr(switch, "async_turn_off")
        assert hasattr(switch, "is_on")
        assert hasattr(switch, "available")
        assert hasattr(switch, "device_info")
        assert hasattr(switch, "extra_state_attributes")
        
        # Should have coordinator-related attributes
        assert hasattr(switch, "coordinator")
        assert switch.coordinator == mock_coordinator