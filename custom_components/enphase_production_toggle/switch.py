"""Switch platform for Enphase Production Toggle."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import EnphaseDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Enphase production switch from a config entry."""
    _LOGGER.debug("Setting up switch platform for entry: %s", entry.title)
    coordinator = hass.data[DOMAIN][entry.entry_id]

    switch = EnphaseProductionSwitch(coordinator, entry)
    async_add_entities([switch])
    _LOGGER.info("Enphase production switch added successfully")


class EnphaseProductionSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of an Enphase production switch."""

    def __init__(
        self,
        coordinator: EnphaseDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        _LOGGER.debug(
            "Initializing EnphaseProductionSwitch for entry: %s", entry.entry_id
        )
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = DEFAULT_NAME
        self._attr_unique_id = f"{entry.entry_id}_production_switch"
        _LOGGER.debug("Switch initialized with unique_id: %s", self._attr_unique_id)

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Enphase Envoy",
            "manufacturer": "Enphase",
            "model": "Envoy",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        if self.coordinator.data is None:
            _LOGGER.debug("No coordinator data available, returning False")
            return False

        is_enabled = self.coordinator.data.get("production_enabled", False)
        _LOGGER.debug("Switch is_on state: %s", is_enabled)
        return is_enabled

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        available = self.coordinator.last_update_success
        _LOGGER.debug("Switch availability: %s", available)
        return available

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if self.coordinator.data is None:
            _LOGGER.debug("No coordinator data for extra attributes")
            return {}

        attrs = {
            "current_power": self.coordinator.data.get("current_power", 0),
            "is_producing": self.coordinator.data.get("is_producing", False),
        }
        _LOGGER.debug("Switch extra attributes: %s", attrs)
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        _LOGGER.info("User requested to turn ON production")
        try:
            await self.coordinator.client.set_production_power(True)  # type: ignore[attr-defined]
            _LOGGER.debug("Production power command sent, requesting data refresh")
            await self.coordinator.async_request_refresh()
            _LOGGER.info("Production turned ON successfully")
        except Exception as err:
            _LOGGER.error("Failed to turn on production: %s", err)
            _LOGGER.exception("Turn on error details")
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        _LOGGER.info("User requested to turn OFF production")
        try:
            await self.coordinator.client.set_production_power(False)  # type: ignore[attr-defined]
            _LOGGER.debug("Production power command sent, requesting data refresh")
            await self.coordinator.async_request_refresh()
            _LOGGER.info("Production turned OFF successfully")
        except Exception as err:
            _LOGGER.error("Failed to turn off production: %s", err)
            _LOGGER.exception("Turn off error details")
            raise
