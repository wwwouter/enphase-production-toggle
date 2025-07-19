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
        self.client = EnvoyClient(
            entry.data[CONF_HOST], entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            await self.client.authenticate()
            return await self.client.get_production_status()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
