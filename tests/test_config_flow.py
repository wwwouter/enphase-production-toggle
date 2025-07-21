"""Test the Enphase Production Toggle config flow."""

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.enphase_production_toggle.config_flow import CannotConnect
from custom_components.enphase_production_toggle.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
)


async def test_validate_input_success() -> None:
    """Test input validation with successful connection."""
    from custom_components.enphase_production_toggle.config_flow import validate_input

    with patch(
        "custom_components.enphase_production_toggle.config_flow.EnvoyClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await validate_input(
            None,  # hass not needed for validation logic
            {
                CONF_HOST: "192.168.1.100",
                CONF_USERNAME: "test@example.com",
                CONF_PASSWORD: "testpassword",
            },
        )

        assert result == {"title": "Enphase Envoy (192.168.1.100)"}
        mock_client.authenticate.assert_called_once()
        mock_client.close.assert_called_once()


async def test_validate_input_cannot_connect() -> None:
    """Test input validation with connection failure."""
    from custom_components.enphase_production_toggle.config_flow import validate_input

    with patch(
        "custom_components.enphase_production_toggle.config_flow.EnvoyClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.authenticate.side_effect = Exception("Connection failed")
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        with pytest.raises(CannotConnect):
            await validate_input(
                None,  # hass not needed for validation logic
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_USERNAME: "test@example.com",
                    CONF_PASSWORD: "testpassword",
                },
            )

        mock_client.authenticate.assert_called_once()
        mock_client.close.assert_called_once()


def test_config_flow_imports():
    """Test config flow imports work correctly."""
    from custom_components.enphase_production_toggle.config_flow import (
        STEP_USER_DATA_SCHEMA,
        CannotConnect,
        ConfigFlow,
        validate_input,
    )

    # Test that key components can be imported
    assert ConfigFlow is not None
    assert validate_input is not None
    assert CannotConnect is not None
    assert STEP_USER_DATA_SCHEMA is not None


def test_cannot_connect_exception():
    """Test CannotConnect exception can be raised."""
    with pytest.raises(CannotConnect):
        raise CannotConnect("Test error")


def test_step_user_data_schema_validation():
    """Test the user data schema validation."""
    import voluptuous as vol

    from custom_components.enphase_production_toggle.config_flow import (
        STEP_USER_DATA_SCHEMA,
    )

    # Test valid data
    valid_data = {
        CONF_HOST: "192.168.1.100",
        CONF_USERNAME: "test@example.com",
        CONF_PASSWORD: "testpassword",
    }

    # Should not raise an exception
    result = STEP_USER_DATA_SCHEMA(valid_data)
    assert result[CONF_HOST] == "192.168.1.100"
    assert result[CONF_USERNAME] == "test@example.com"
    assert result[CONF_PASSWORD] == "testpassword"

    # Test missing required field
    invalid_data = {
        CONF_HOST: "192.168.1.100",
        CONF_USERNAME: "test@example.com",
        # Missing CONF_PASSWORD
    }

    with pytest.raises(vol.Invalid):
        STEP_USER_DATA_SCHEMA(invalid_data)


async def test_validate_input_with_different_hosts():
    """Test input validation with various host formats."""
    from custom_components.enphase_production_toggle.config_flow import validate_input

    test_hosts = [
        "192.168.1.100",
        "10.0.0.5",
        "envoy.local",
        "::1",  # IPv6
        "envoy-gateway.home.local",
    ]

    for host in test_hosts:
        with patch(
            "custom_components.enphase_production_toggle.config_flow.EnvoyClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate = AsyncMock()
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            # Should work for all host formats
            result = await validate_input(
                None,
                {
                    CONF_HOST: host,
                    CONF_USERNAME: "test@example.com",
                    CONF_PASSWORD: "testpassword",
                },
            )

            assert result == {"title": f"Enphase Envoy ({host})"}


async def test_validate_input_error_handling():
    """Test various error scenarios in validate_input."""
    from custom_components.enphase_production_toggle.config_flow import validate_input

    error_scenarios = [
        (ConnectionError("Network error"), CannotConnect),
        (TimeoutError("Request timeout"), CannotConnect),
        (ValueError("Invalid response"), CannotConnect),
        (RuntimeError("Unexpected error"), CannotConnect),
    ]

    for original_error, expected_exception in error_scenarios:
        with patch(
            "custom_components.enphase_production_toggle.config_flow.EnvoyClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.authenticate.side_effect = original_error
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            with pytest.raises(expected_exception):
                await validate_input(
                    None,
                    {
                        CONF_HOST: "192.168.1.100",
                        CONF_USERNAME: "test@example.com",
                        CONF_PASSWORD: "testpassword",
                    },
                )


def test_config_flow_constants():
    """Test that config flow constants are properly defined."""
    from custom_components.enphase_production_toggle.config_flow import (
        STEP_USER_DATA_SCHEMA,
    )
    from custom_components.enphase_production_toggle.const import (
        CONF_HOST,
        CONF_PASSWORD,
        CONF_USERNAME,
    )

    # Test that schema contains the expected fields
    schema_dict = STEP_USER_DATA_SCHEMA.schema

    # Check that all required fields are present
    required_fields = {CONF_HOST, CONF_USERNAME, CONF_PASSWORD}
    schema_fields = set()

    for key in schema_dict.keys():
        if hasattr(key, "schema"):
            schema_fields.add(key.schema)

    assert required_fields.issubset(schema_fields)


def test_exception_inheritance():
    """Test that CannotConnect properly inherits from HomeAssistantError."""
    from homeassistant.exceptions import HomeAssistantError

    from custom_components.enphase_production_toggle.config_flow import CannotConnect

    # Test inheritance
    assert issubclass(CannotConnect, HomeAssistantError)

    # Test instantiation
    error = CannotConnect("Test message")
    assert isinstance(error, HomeAssistantError)
    assert str(error) == "Test message"
