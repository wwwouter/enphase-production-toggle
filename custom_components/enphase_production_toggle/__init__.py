"""Enphase Production Toggle integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import EnphaseDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Enphase Production Toggle from a config entry."""
    _LOGGER.info("Setting up Enphase Production Toggle integration for %s", entry.title)
    _LOGGER.debug(
        "Entry data: host=%s, username=%s",
        entry.data.get("host"),
        entry.data.get("username"),
    )

    coordinator = EnphaseDataUpdateCoordinator(hass, entry)
    _LOGGER.debug("Created data update coordinator")

    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info("Initial data refresh completed successfully")
    except Exception as err:
        _LOGGER.error("Failed to perform initial data refresh: %s", err)
        raise

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    _LOGGER.debug("Coordinator stored in hass.data")

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Platform setup completed for %s", PLATFORMS)

    _LOGGER.info("Enphase Production Toggle integration setup completed successfully")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Enphase Production Toggle integration for %s", entry.title)

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Successfully unloaded integration and cleaned up data")
    else:
        _LOGGER.warning("Failed to unload platforms for entry %s", entry.entry_id)

    _LOGGER.debug("Unload result: %s", unload_ok)
    return unload_ok
