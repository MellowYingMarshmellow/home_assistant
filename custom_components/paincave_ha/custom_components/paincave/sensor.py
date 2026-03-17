"""Sensor platform — primary + secondary metric entities per saved sensor."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPE_META
from .coordinator import PainCaveCoordinator

_LOGGER = logging.getLogger(__name__)

# ── Field metadata ────────────────────────────────────────────────────────────

_FIELD_META: dict[str, dict[str, Any]] = {
    "heartRate":        {"unit": "bpm",   "icon": "mdi:heart-pulse",          "device_class": None},
    "power":            {"unit": "W",     "icon": "mdi:lightning-bolt",        "device_class": SensorDeviceClass.POWER},
    "cadence":          {"unit": "rpm",   "icon": "mdi:rotate-right",          "device_class": None},
    "speed":            {"unit": "km/h",  "icon": "mdi:speedometer",           "device_class": SensorDeviceClass.SPEED},
    "distance":         {"unit": "m",     "icon": "mdi:map-marker-distance",   "device_class": None},
    "inclination":      {"unit": "%",     "icon": "mdi:slope-uphill",          "device_class": None},
    "resistance":       {"unit": "",      "icon": "mdi:tune",                  "device_class": None},
    "energy":           {"unit": "kJ",    "icon": "mdi:fire",                  "device_class": None},
    "elapsed":          {"unit": "s",     "icon": "mdi:timer",                 "device_class": SensorDeviceClass.DURATION},
    "strokeRate":       {"unit": "spm",   "icon": "mdi:rowing",                "device_class": None},
    "strokeCount":      {"unit": "",      "icon": "mdi:counter",               "device_class": None},
    "strideLength":     {"unit": "m",     "icon": "mdi:walk",                  "device_class": None},
    "wheelRevolutions": {"unit": "",      "icon": "mdi:tire",                  "device_class": None},
    "crankRevolutions": {"unit": "",      "icon": "mdi:bike",                  "device_class": None},
}

# Secondary fields to create per sensor type (excluding the primary state_key)
_TYPE_SECONDARY_FIELDS: dict[str, list[str]] = {
    "heart-rate":            [],
    "power":                 ["cadence", "heartRate"],
    "speed":                 [],
    "cadence":               [],
    "stride-speed-distance": ["cadence", "distance"],
    "treadmill":             ["inclination", "heartRate", "energy", "elapsed"],
    "indoor-bike":           ["cadence", "speed", "heartRate", "resistance", "energy", "elapsed"],
    "rower":                 ["strokeCount", "distance", "power", "heartRate", "energy", "elapsed"],
    "csc":                   ["speed"],
    "rsc":                   ["cadence", "strideLength", "distance"],
}


def _device_info(saved: dict) -> DeviceInfo:
    source_label = "Bluetooth" if saved.get("source") == "ble" else "ANT+"
    return DeviceInfo(
        identifiers={(DOMAIN, str(saved["device_id"]))},
        name=saved["name"],
        manufacturer="PainCave",
        model=f"{saved.get('device_type') or saved['sensor_type']} ({source_label})",
        via_device=(DOMAIN, "paincave_hub"),
    )


# ── Platform setup ────────────────────────────────────────────────────────────

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PainCaveCoordinator = hass.data[DOMAIN][entry.entry_id]
    known_ids: set[str] = set()

    @callback
    def _add_new_sensors() -> None:
        new_entities: list = []
        for saved in coordinator.data.get("sensors", []):
            uid = str(saved["device_id"])
            if uid in known_ids:
                continue
            known_ids.add(uid)

            sensor_type = saved["sensor_type"]
            meta        = SENSOR_TYPE_META.get(sensor_type, {})
            primary_key = meta.get("state_key")

            # Primary entity
            new_entities.append(PainCavePrimarySensor(coordinator, saved, meta))

            # Secondary entities — only fields that make sense for this sensor type
            for field in _TYPE_SECONDARY_FIELDS.get(sensor_type, []):
                if field == primary_key:
                    continue
                field_meta = _FIELD_META.get(field)
                if field_meta:
                    new_entities.append(PainCaveFieldSensor(coordinator, saved, field, field_meta))

        if new_entities:
            async_add_entities(new_entities)

    coordinator.async_add_listener(_add_new_sensors)
    _add_new_sensors()


# ── Entity classes ────────────────────────────────────────────────────────────

class PainCavePrimarySensor(CoordinatorEntity, SensorEntity):
    """Primary entity for a saved sensor — shows its headline metric."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: PainCaveCoordinator, saved: dict, meta: dict) -> None:
        super().__init__(coordinator)
        self._saved     = saved
        self._device_id = str(saved["device_id"])
        self._state_key = meta.get("state_key")

        self._attr_unique_id                  = f"paincave_{self._device_id}_primary"
        self._attr_name                       = saved["name"]
        self._attr_native_unit_of_measurement = meta.get("unit")
        self._attr_icon                       = meta.get("icon", "mdi:gauge")
        self._attr_device_info                = _device_info(saved)

        # Map to HA device class where one exists
        dc_map = {"power": SensorDeviceClass.POWER, "speed": SensorDeviceClass.SPEED}
        if (dc := dc_map.get(saved["sensor_type"])):
            self._attr_device_class = dc

    @property
    def _live(self) -> dict | None:
        return self.coordinator.data.get("live", {}).get(self._device_id)

    @property
    def native_value(self) -> float | None:
        live = self._live
        if live and self._state_key:
            return live.get("data", {}).get(self._state_key)
        return None

    @property
    def available(self) -> bool:
        # Unavailable if the sensor is disabled OR not transmitting
        saved = next(
            (s for s in self.coordinator.data.get("sensors", []) if str(s["device_id"]) == self._device_id),
            None,
        )
        if saved and not saved.get("is_active", True):
            return False
        return self.coordinator.last_update_success and self._live is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        live = self._live
        if not live:
            return {"source": self._saved.get("source", "ant"), "status": "no signal"}
        data = live.get("data") or {}
        # All data fields as attributes (secondary field sensors duplicate the most useful ones)
        attrs = {k: v for k, v in data.items() if k != "timestamp" and k != self._state_key}
        attrs["source"]    = live.get("source", self._saved.get("source", "ant"))
        attrs["last_seen"] = live.get("lastSeen")
        return attrs


class PainCaveFieldSensor(CoordinatorEntity, SensorEntity):
    """Secondary entity exposing one additional data field from a multi-metric device."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PainCaveCoordinator,
        saved: dict,
        field: str,
        field_meta: dict,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = str(saved["device_id"])
        self._field     = field

        # Make the name readable: "Tacx NEO 2 Cadence"
        label = field.replace("Rate", " Rate").replace("Count", " Count")
        label = "".join(f" {c}" if c.isupper() and i > 0 else c for i, c in enumerate(label)).title().strip()

        self._attr_unique_id                  = f"paincave_{self._device_id}_{field}"
        self._attr_name                       = f"{saved['name']} {label}"
        self._attr_native_unit_of_measurement = field_meta.get("unit") or None
        self._attr_icon                       = field_meta.get("icon", "mdi:gauge")
        self._attr_device_info                = _device_info(saved)

        if (dc := field_meta.get("device_class")):
            self._attr_device_class = dc

    @property
    def native_value(self) -> float | None:
        live = self.coordinator.data.get("live", {}).get(self._device_id)
        if live:
            return live.get("data", {}).get(self._field)
        return None

    @property
    def available(self) -> bool:
        live = self.coordinator.data.get("live", {}).get(self._device_id)
        return (
            self.coordinator.last_update_success
            and live is not None
            and self._field in (live.get("data") or {})
        )
