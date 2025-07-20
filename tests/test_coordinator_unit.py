"""Unit tests for EnphaseDataUpdateCoordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.enphase_production_toggle.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from custom_components.enphase_production_toggle.coordinator import (
    EnphaseDataUpdateCoordinator,
)


class TestEnphaseDataUpdateCoordinatorUnit:
    """Unit tests for EnphaseDataUpdateCoordinator class."""

    def test_coordinator_initialization(self):
        """Test coordinator initialization with various configurations."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "testpassword",
        }

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
            assert coordinator.update_interval == timedelta(
                seconds=DEFAULT_SCAN_INTERVAL
            )

    def test_coordinator_with_different_hosts(self):
        """Test coordinator initialization with different host formats."""
        mock_hass = MagicMock()
        test_hosts = [
            "192.168.1.100",
            "10.0.0.5",
            "envoy.local",
            "192.168.0.10",
        ]

        for host in test_hosts:
            mock_entry = MagicMock()
            mock_entry.data = {
                CONF_HOST: host,
                CONF_USERNAME: "user@example.com",
                CONF_PASSWORD: "password",
            }

            with patch(
                "custom_components.enphase_production_toggle.coordinator.EnvoyClient"
            ) as mock_client_class:
                coordinator = EnphaseDataUpdateCoordinator(mock_hass, mock_entry)

                # Verify correct host was passed
                mock_client_class.assert_called_once_with(
                    host, "user@example.com", "password"
                )

    def test_coordinator_with_special_characters_in_credentials(self):
        """Test coordinator with special characters in username/password."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "user+test@example.com",
            CONF_PASSWORD: "p@ssw0rd!#$%^&*()",
        }

        with patch(
            "custom_components.enphase_production_toggle.coordinator.EnvoyClient"
        ) as mock_client_class:
            coordinator = EnphaseDataUpdateCoordinator(mock_hass, mock_entry)

            # Verify special characters are preserved
            mock_client_class.assert_called_once_with(
                "192.168.1.100", "user+test@example.com", "p@ssw0rd!#$%^&*()"
            )

    @pytest.mark.asyncio
    async def test_update_data_success_various_responses(self):
        """Test update data with various successful response formats."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "testpassword",
        }

        test_responses = [
            # Normal production
            {
                "is_producing": True,
                "current_power": 5000,
                "production_enabled": True,
            },
            # Zero production
            {
                "is_producing": False,
                "current_power": 0,
                "production_enabled": True,
            },
            # High production
            {
                "is_producing": True,
                "current_power": 15000,
                "production_enabled": True,
            },
            # Production disabled
            {
                "is_producing": False,
                "current_power": 0,
                "production_enabled": False,
            },
        ]

        for response_data in test_responses:
            with patch(
                "custom_components.enphase_production_toggle.coordinator.EnvoyClient"
            ) as mock_client_class:
                mock_client = mock_client_class.return_value
                mock_client.authenticate = AsyncMock()
                mock_client.get_production_status = AsyncMock(
                    return_value=response_data
                )

                coordinator = EnphaseDataUpdateCoordinator(mock_hass, mock_entry)
                result = await coordinator._async_update_data()

                assert result == response_data
                mock_client.authenticate.assert_called_once()
                mock_client.get_production_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_data_authentication_errors(self):
        """Test update data with various authentication errors."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "testpassword",
        }

        auth_errors = [
            Exception("Authentication failed: 401"),
            Exception("Network timeout"),
            Exception("Invalid credentials"),
            ConnectionError("Cannot connect to host"),
            TimeoutError("Request timed out"),
        ]

        for auth_error in auth_errors:
            with patch(
                "custom_components.enphase_production_toggle.coordinator.EnvoyClient"
            ) as mock_client_class:
                mock_client = mock_client_class.return_value
                mock_client.authenticate = AsyncMock(side_effect=auth_error)

                coordinator = EnphaseDataUpdateCoordinator(mock_hass, mock_entry)

                with pytest.raises(UpdateFailed) as exc_info:
                    await coordinator._async_update_data()

                assert "Error communicating with API" in str(exc_info.value)
                assert str(auth_error) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_data_production_status_errors(self):
        """Test update data with various production status errors."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "testpassword",
        }

        status_errors = [
            Exception("Failed to get production status: 404"),
            Exception("Envoy not responding"),
            Exception("Invalid response format"),
            ConnectionError("Connection lost"),
            ValueError("Invalid JSON response"),
        ]

        for status_error in status_errors:
            with patch(
                "custom_components.enphase_production_toggle.coordinator.EnvoyClient"
            ) as mock_client_class:
                mock_client = mock_client_class.return_value
                mock_client.authenticate = AsyncMock()
                mock_client.get_production_status = AsyncMock(side_effect=status_error)

                coordinator = EnphaseDataUpdateCoordinator(mock_hass, mock_entry)

                with pytest.raises(UpdateFailed) as exc_info:
                    await coordinator._async_update_data()

                assert "Error communicating with API" in str(exc_info.value)
                assert str(status_error) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_data_call_sequence(self):
        """Test that update data calls methods in correct sequence."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "testpassword",
        }

        with patch(
            "custom_components.enphase_production_toggle.coordinator.EnvoyClient"
        ) as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.authenticate = AsyncMock()
            mock_client.get_production_status = AsyncMock(
                return_value={"is_producing": True, "current_power": 5000}
            )

            coordinator = EnphaseDataUpdateCoordinator(mock_hass, mock_entry)
            await coordinator._async_update_data()

            # Verify call sequence
            assert mock_client.authenticate.called
            assert mock_client.get_production_status.called

            # Verify authenticate was called before get_production_status
            handle = mock_client.method_calls
            auth_call_index = next(
                i for i, call in enumerate(handle) if call[0] == "authenticate"
            )
            status_call_index = next(
                i for i, call in enumerate(handle) if call[0] == "get_production_status"
            )
            assert auth_call_index < status_call_index

    def test_coordinator_client_property_access(self):
        """Test that client property is accessible and correct type."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "testpassword",
        }

        with patch(
            "custom_components.enphase_production_toggle.coordinator.EnvoyClient"
        ) as mock_client_class:
            mock_client = mock_client_class.return_value
            coordinator = EnphaseDataUpdateCoordinator(mock_hass, mock_entry)

            # Verify client is accessible
            assert coordinator.client == mock_client
            assert hasattr(coordinator.client, "authenticate")
            assert hasattr(coordinator.client, "get_production_status")
            assert hasattr(coordinator.client, "set_production_power")

    def test_coordinator_update_interval_customization(self):
        """Test coordinator with different update intervals."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "testpassword",
        }

        with patch(
            "custom_components.enphase_production_toggle.coordinator.EnvoyClient"
        ):
            coordinator = EnphaseDataUpdateCoordinator(mock_hass, mock_entry)

            # Verify default interval
            assert coordinator.update_interval == timedelta(
                seconds=DEFAULT_SCAN_INTERVAL
            )

            # Test that interval is reasonable
            total_seconds = coordinator.update_interval.total_seconds()
            assert 10 <= total_seconds <= 300  # Between 10 seconds and 5 minutes

    def test_coordinator_name_property(self):
        """Test that coordinator name is set correctly."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "testpassword",
        }

        with patch(
            "custom_components.enphase_production_toggle.coordinator.EnvoyClient"
        ):
            coordinator = EnphaseDataUpdateCoordinator(mock_hass, mock_entry)

            assert coordinator.name == DOMAIN
            assert isinstance(coordinator.name, str)
            assert len(coordinator.name) > 0

    def test_coordinator_error_handling_edge_cases(self):
        """Test coordinator error handling with edge cases."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "testpassword",
        }

        # Test with various exception types
        exception_types = [
            Exception,
            RuntimeError,
            ValueError,
            ConnectionError,
            TimeoutError,
            OSError,
        ]

        for exc_type in exception_types:
            with patch(
                "custom_components.enphase_production_toggle.coordinator.EnvoyClient"
            ) as mock_client_class:
                mock_client = mock_client_class.return_value
                mock_client.authenticate.side_effect = exc_type("Test error")

                coordinator = EnphaseDataUpdateCoordinator(mock_hass, mock_entry)

                # Should always wrap in UpdateFailed
                with pytest.raises(UpdateFailed):
                    # This is an async method, but we're testing the sync error handling
                    # In practice, this would be called with await
                    import asyncio

                    asyncio.run(coordinator._async_update_data())
