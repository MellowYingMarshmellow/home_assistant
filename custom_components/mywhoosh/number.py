"""Number platform for MyWhoosh — writable profile values."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MyWhooshCoordinator
from .sensor import _device

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MyWhooshCoordinator = hass.data[DOMAIN][entry.entry_id]
    wid = coordinator.whoosh_id

    async_add_entities([
        WeightNumber(coordinator, wid),
        FtpNumber(coordinator, wid),
    ])


# ── Base ──────────────────────────────────────────────────────────────────────

class _BaseNumber(CoordinatorEntity, NumberEntity):
    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: MyWhooshCoordinator, whoosh_id: str) -> None:
        super().__init__(coordinator)
        self._whoosh_id = whoosh_id

    @property
    def device_info(self) -> DeviceInfo:
        return _device(self._whoosh_id, self.coordinator.data or {})

    def _d(self, key, default=None):
        return (self.coordinator.data or {}).get(key, default)


# ── Weight ────────────────────────────────────────────────────────────────────

class WeightNumber(_BaseNumber):
    _attr_name                       = "Weight"
    _attr_icon                       = "mdi:weight-kilogram"
    _attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
    _attr_native_min_value           = 20.0
    _attr_native_max_value           = 250.0
    _attr_native_step                = 0.1

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_weight_input"

    @property
    def native_value(self) -> float | None:
        v = self._d("weight_kg")
        return float(v) if v else None

    async def async_set_native_value(self, value: float) -> None:
        _LOGGER.debug("MyWhoosh: setting weight to %.1f kg", value)
        await self.coordinator.update_weight(round(value, 1))


# ── FTP ───────────────────────────────────────────────────────────────────────

class FtpNumber(_BaseNumber):
    _attr_name                       = "FTP"
    _attr_icon                       = "mdi:lightning-bolt-circle"
    _attr_native_unit_of_measurement = "W"
    _attr_native_min_value           = 50
    _attr_native_max_value           = 600
    _attr_native_step                = 1

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_ftp_input"

    @property
    def native_value(self) -> float | None:
        v = self._d("ftp")
        return float(v) if v else None

    async def async_set_native_value(self, value: float) -> None:
        _LOGGER.debug("MyWhoosh: setting FTP to %d W", int(value))
        await self.coordinator.update_ftp(int(value))
