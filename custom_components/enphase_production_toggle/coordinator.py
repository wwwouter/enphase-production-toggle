"""DataUpdateCoordinator for Enphase Production Toggle."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .envoy_client import EnvoyClient

_LOGGER = logging.getLogger(__name__)


class EnphaseDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Enphase Envoy."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        _LOGGER.debug("Initializing coordinator for host: %s", entry.data[CONF_HOST])

        self.client = EnvoyClient(
            entry.data[CONF_HOST], entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
        )
        _LOGGER.debug("Created Envoy client for %s", entry.data[CONF_HOST])

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        _LOGGER.info(
            "Coordinator initialized with %s second update interval",
            DEFAULT_SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via library."""
        _LOGGER.debug("Starting data update")
        try:
            _LOGGER.debug("Authenticating with Enphase Envoy")
            await self.client.authenticate()
            _LOGGER.debug("Authentication successful, getting production status")

            data = await self.client.get_production_status()
            _LOGGER.info(
                "Data update successful - Production: %s W, Enabled: %s",
                data.get("current_power", "unknown"),
                data.get("production_enabled", "unknown"),
            )
            _LOGGER.debug("Full data received: %s", data)
            return data
        except Exception as err:
            _LOGGER.error("Error communicating with Enphase API: %s", err)
            _LOGGER.debug("Update failed, raising UpdateFailed exception")
            raise UpdateFailed(f"Error communicating with API: {err}") from err
