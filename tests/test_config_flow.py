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
