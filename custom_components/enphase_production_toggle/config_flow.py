"""Config flow for Enphase Production Toggle integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import voluptuous as vol

from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, DOMAIN
from .envoy_client import EnvoyClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    _LOGGER.debug("Validating input for host: %s", data[CONF_HOST])
    client = EnvoyClient(data[CONF_HOST], data[CONF_USERNAME], data[CONF_PASSWORD])

    try:
        _LOGGER.debug("Attempting to authenticate with Enphase Envoy")
        await client.authenticate()
        _LOGGER.info(
            "Successfully authenticated with Enphase Envoy at %s", data[CONF_HOST]
        )
        return {"title": f"Enphase Envoy ({data[CONF_HOST]})"}
    except Exception as err:
        _LOGGER.error(
            "Failed to authenticate with Enphase Envoy at %s: %s", data[CONF_HOST], err
        )
        _LOGGER.exception("Authentication error details")
        raise CannotConnect from err
    finally:
        _LOGGER.debug("Closing client connection")
        await client.close()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Enphase Production Toggle."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        _LOGGER.debug("Config flow step_user called with input: %s", bool(user_input))
        errors: dict[str, str] = {}

        if user_input is not None:
            _LOGGER.info(
                "Processing config flow with host: %s", user_input.get(CONF_HOST)
            )
            try:
                info = await validate_input(self.hass, user_input)
                _LOGGER.info("Validation successful, creating config entry")
            except CannotConnect:
                _LOGGER.warning("Cannot connect to Enphase Envoy during config flow")
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.error("Unexpected exception during config flow: %s", err)
                _LOGGER.exception("Config flow unexpected error details")
                errors["base"] = "unknown"
            else:
                _LOGGER.info("Config entry created successfully for %s", info["title"])
                return self.async_create_entry(title=info["title"], data=user_input)  # type: ignore[return-value]

        _LOGGER.debug("Showing config form to user with errors: %s", errors)
        return self.async_show_form(  # type: ignore[return-value]
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
