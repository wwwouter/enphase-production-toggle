"""Test the Enphase Production Toggle config flow."""
import pytest
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.enphase_production_toggle.const import (
    DOMAIN,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
)
from custom_components.enphase_production_toggle.config_flow import CannotConnect


async def test_form(hass: HomeAssistant, mock_envoy_client) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "custom_components.enphase_production_toggle.config_flow.validate_input",
        return_value={"title": "Enphase Envoy (192.168.1.100)"},
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_USERNAME: "test@example.com",
                CONF_PASSWORD: "testpassword",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Enphase Envoy (192.168.1.100)"
    assert result2["data"] == {
        CONF_HOST: "192.168.1.100",
        CONF_USERNAME: "test@example.com",
        CONF_PASSWORD: "testpassword",
    }


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.enphase_production_toggle.config_flow.validate_input",
        side_effect=CannotConnect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_USERNAME: "test@example.com",
                CONF_PASSWORD: "wrongpassword",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unexpected_exception(hass: HomeAssistant) -> None:
    """Test we handle unexpected exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.enphase_production_toggle.config_flow.validate_input",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_USERNAME: "test@example.com",
                CONF_PASSWORD: "testpassword",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}


async def test_validate_input_success(hass: HomeAssistant, mock_envoy_client) -> None:
    """Test input validation with successful connection."""
    from custom_components.enphase_production_toggle.config_flow import validate_input
    
    with patch(
        "custom_components.enphase_production_toggle.config_flow.EnvoyClient"
    ) as mock_client_class:
        mock_client_class.return_value = mock_envoy_client
        
        result = await validate_input(hass, {
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "testpassword",
        })
        
        assert result == {"title": "Enphase Envoy (192.168.1.100)"}
        mock_envoy_client.authenticate.assert_called_once()


async def test_validate_input_cannot_connect(hass: HomeAssistant) -> None:
    """Test input validation with connection failure."""
    from custom_components.enphase_production_toggle.config_flow import validate_input
    
    with patch(
        "custom_components.enphase_production_toggle.config_flow.EnvoyClient"
    ) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.authenticate.side_effect = Exception("Connection failed")
        
        with pytest.raises(CannotConnect):
            await validate_input(hass, {
                CONF_HOST: "192.168.1.100",
                CONF_USERNAME: "test@example.com",
                CONF_PASSWORD: "testpassword",
            })