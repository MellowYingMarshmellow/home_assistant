"""Switch platform — scanning toggles and per-sensor active switches."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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


def _sensor_device_info(saved: dict) -> DeviceInfo:
    source_label = "Bluetooth" if saved.get("source") == "ble" else "ANT+"
    return DeviceInfo(
        identifiers={(DOMAIN, str(saved["device_id"]))},
        name=saved["name"],
        manufacturer="PainCave",
        model=f"{saved.get('device_type') or saved['sensor_type']} ({source_label})",
        via_device=(DOMAIN, "paincave_hub"),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PainCaveCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Hub-level power and scanning switches (always present)
    async_add_entities([
        AntPowerSwitch(coordinator),
        AntScanSwitch(coordinator),
        BlePowerSwitch(coordinator),
        BleScanSwitch(coordinator),
    ])

    # Per-sensor active switches — created dynamically as sensors are discovered
    known_ids: set[str] = set()

    @callback
    def _add_sensor_switches() -> None:
        new_switches = []
        for saved in coordinator.data.get("sensors", []):
            uid = str(saved["device_id"])
            if uid in known_ids:
                continue
            known_ids.add(uid)
            new_switches.append(SensorActiveSwitch(coordinator, saved))
        if new_switches:
            async_add_entities(new_switches)

    coordinator.async_add_listener(_add_sensor_switches)
    _add_sensor_switches()


# ── Hub switches ──────────────────────────────────────────────────────────────

class AntPowerSwitch(CoordinatorEntity, SwitchEntity):
    """Power ANT+ radio on/off — persisted across restarts."""

    _attr_unique_id   = "paincave_ant_enabled"
    _attr_name        = "ANT+ Power"
    _attr_icon        = "mdi:antenna"
    _attr_device_info = HUB_DEVICE

    def __init__(self, coordinator: PainCaveCoordinator) -> None:
        super().__init__(coordinator)

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("ant_enabled", False)

    @property
    def available(self) -> bool:
        return self.coordinator.data.get("ant_ready", False)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.ant_enable()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.ant_disable()


class AntScanSwitch(CoordinatorEntity, SwitchEntity):
    """Pause/resume ANT+ scanning within the current session (no restart persistence)."""

    _attr_unique_id   = "paincave_ant_scanning"
    _attr_name        = "ANT+ Scanning"
    _attr_icon        = "mdi:radar"
    _attr_device_info = HUB_DEVICE

    def __init__(self, coordinator: PainCaveCoordinator) -> None:
        super().__init__(coordinator)

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("ant_scanning", False)

    @property
    def available(self) -> bool:
        return self.coordinator.data.get("ant_enabled", False)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.ant_start()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.ant_stop()


class BlePowerSwitch(CoordinatorEntity, SwitchEntity):
    """Power Bluetooth radio on/off — persisted across restarts."""

    _attr_unique_id   = "paincave_ble_enabled"
    _attr_name        = "Bluetooth Power"
    _attr_icon        = "mdi:bluetooth"
    _attr_device_info = HUB_DEVICE

    def __init__(self, coordinator: PainCaveCoordinator) -> None:
        super().__init__(coordinator)

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("ble_enabled", False)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.ble_enable()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.ble_disable()


class BleScanSwitch(CoordinatorEntity, SwitchEntity):
    """Pause/resume Bluetooth scanning within the current session (no restart persistence)."""

    _attr_unique_id   = "paincave_ble_scanning"
    _attr_name        = "Bluetooth Scanning"
    _attr_icon        = "mdi:bluetooth-audio"
    _attr_device_info = HUB_DEVICE

    def __init__(self, coordinator: PainCaveCoordinator) -> None:
        super().__init__(coordinator)

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("ble_scanning", False)

    @property
    def available(self) -> bool:
        return self.coordinator.data.get("ble_enabled", False)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.ble_start()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.ble_stop()


# ── Per-sensor active switch ──────────────────────────────────────────────────

class SensorActiveSwitch(CoordinatorEntity, SwitchEntity):
    """Enable / disable a saved sensor (controls MQTT publishing and active flag)."""

    _attr_icon = "mdi:toggle-switch"

    def __init__(self, coordinator: PainCaveCoordinator, saved: dict) -> None:
        super().__init__(coordinator)
        self._sensor_id  = saved["id"]
        self._device_id  = str(saved["device_id"])

        self._attr_unique_id   = f"paincave_{self._device_id}_active"
        self._attr_name        = f"{saved['name']} Active"
        self._attr_device_info = _sensor_device_info(saved)

    def _current_saved(self) -> dict | None:
        """Return the up-to-date saved sensor row from coordinator data."""
        for s in self.coordinator.data.get("sensors", []):
            if s["id"] == self._sensor_id:
                return s
        return None

    @property
    def is_on(self) -> bool:
        saved = self._current_saved()
        return bool(saved["is_active"]) if saved else False

    @property
    def extra_state_attributes(self) -> dict:
        saved = self._current_saved()
        if not saved:
            return {}
        return {
            "sensor_type": saved.get("sensor_type"),
            "category":    saved.get("category"),
            "source":      saved.get("source", "ant"),
            "device_id":   self._device_id,
            "mqtt_topic":  saved.get("mqtt_topic"),
        }

    async def async_turn_on(self, **kwargs) -> None:
        saved = self._current_saved()
        if saved and not saved["is_active"]:
            await self.coordinator.toggle_sensor(self._sensor_id)

    async def async_turn_off(self, **kwargs) -> None:
        saved = self._current_saved()
        if saved and saved["is_active"]:
            await self.coordinator.toggle_sensor(self._sensor_id)
