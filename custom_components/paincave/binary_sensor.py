"""Binary sensor platform — ANT+ stick connected."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PainCaveCoordinator

HUB_DEVICE = DeviceInfo(
    identifiers={(DOMAIN, "paincave_hub")},
    name="PainCave Hub",
    manufacturer="PainCave",
    model="ANT+/BLE Sensor Hub",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PainCaveCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        AntStickBinarySensor(coordinator),
        BleBinarySensor(coordinator),
    ])


class AntStickBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """True when an ANT+ USB stick is detected."""

    _attr_unique_id    = "paincave_ant_stick"
    _attr_name         = "ANT+ Stick"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon         = "mdi:usb"
    _attr_device_info  = HUB_DEVICE

    def __init__(self, coordinator: PainCaveCoordinator) -> None:
        super().__init__(coordinator)

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("ant_ready", False)


class BleBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """True when the Bluetooth adapter is available and scanning."""

    _attr_unique_id    = "paincave_ble_available"
    _attr_name         = "Bluetooth Adapter"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon         = "mdi:bluetooth"
    _attr_device_info  = HUB_DEVICE

    def __init__(self, coordinator: PainCaveCoordinator) -> None:
        super().__init__(coordinator)

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("ble_scanning", False)
