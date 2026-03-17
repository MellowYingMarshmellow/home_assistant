"""Sensor platform for MyWhoosh."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength, UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MyWhooshCoordinator


def _format_duration(total_seconds: int) -> str:
    """Convert seconds into a human-readable string, e.g. '2y 3mo 1d 4h 20m'."""
    years, rem  = divmod(total_seconds, 365 * 24 * 3600)
    months, rem = divmod(rem,           30  * 24 * 3600)
    days, rem   = divmod(rem,           24  * 3600)
    hours, rem  = divmod(rem,           3600)
    minutes     = rem // 60

    parts = []
    if years:
        parts.append(f"{years}y")
    if months:
        parts.append(f"{months}mo")
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")   # always show minutes
    return " ".join(parts)


def _device(whoosh_id: str, data: dict) -> DeviceInfo:
    full_name = data.get("full_name") or f"MyWhoosh ({whoosh_id})"
    return DeviceInfo(
        identifiers={(DOMAIN, whoosh_id)},
        name=full_name,
        manufacturer="MyWhoosh",
        model="Rider Profile",
        configuration_url="https://app.mywhoosh.com",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MyWhooshCoordinator = hass.data[DOMAIN][entry.entry_id]
    wid = coordinator.whoosh_id

    async_add_entities([
        # ── Identity ──────────────────────────────────────────────────────────
        PlayerNameSensor(coordinator, wid),
        # ── Biometrics ────────────────────────────────────────────────────────
        HeightSensor(coordinator, wid),
        WeightSensor(coordinator, wid),
        FtpSensor(coordinator, wid),
        # ── Progression ───────────────────────────────────────────────────────
        LevelSensor(coordinator, wid),
        XpSensor(coordinator, wid),
        CoinsSensor(coordinator, wid),
        GemsSensor(coordinator, wid),
        # ── Lifetime stats ────────────────────────────────────────────────────
        TotalDistanceSensor(coordinator, wid),
        TotalElevationSensor(coordinator, wid),
        TotalRideTimeSensor(coordinator, wid),
        TotalCaloriesSensor(coordinator, wid),
        WeeklyDistanceSensor(coordinator, wid),
        # ── Averages / max ────────────────────────────────────────────────────
        AvgPowerSensor(coordinator, wid),
        AvgHrSensor(coordinator, wid),
        MaxPowerSensor(coordinator, wid),
        # ── Power bests ───────────────────────────────────────────────────────
        BestPowerSensor(coordinator, wid, "best_5s",    "Best 5s Power"),
        BestPowerSensor(coordinator, wid, "best_30s",   "Best 30s Power"),
        BestPowerSensor(coordinator, wid, "best_1min",  "Best 1min Power"),
        BestPowerSensor(coordinator, wid, "best_3min",  "Best 3min Power"),
        BestPowerSensor(coordinator, wid, "best_5min",  "Best 5min Power"),
        BestPowerSensor(coordinator, wid, "best_12min", "Best 12min Power"),
        BestPowerSensor(coordinator, wid, "best_20min", "Best 20min Power"),
        BestPowerSensor(coordinator, wid, "best_30min", "Best 30min Power"),
        BestPowerSensor(coordinator, wid, "best_60min", "Best 60min Power"),
        # ── Social ────────────────────────────────────────────────────────────
        FriendsOnlineSensor(coordinator, wid),
    ])


# ── Base ──────────────────────────────────────────────────────────────────────

class _Base(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: MyWhooshCoordinator, whoosh_id: str) -> None:
        super().__init__(coordinator)
        self._whoosh_id = whoosh_id

    @property
    def device_info(self) -> DeviceInfo:
        return _device(self._whoosh_id, self.coordinator.data or {})

    def _d(self, key, default=None):
        return (self.coordinator.data or {}).get(key, default)


# ── Identity ──────────────────────────────────────────────────────────────────

class PlayerNameSensor(_Base):
    _attr_name = "Rider Name"
    _attr_icon = "mdi:account"

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_name"

    @property
    def native_value(self):
        return self._d("full_name") or self._d("first_name")

    @property
    def extra_state_attributes(self):
        return {
            "whoosh_id":  self._whoosh_id,
            "first_name": self._d("first_name"),
            "last_name":  self._d("last_name"),
            "country_id": self._d("country_id"),
            "category":   self._d("category"),
        }


# ── Biometrics ────────────────────────────────────────────────────────────────

class HeightSensor(_Base):
    _attr_name        = "Height"
    _attr_icon        = "mdi:human-male-height"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "cm"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_height"

    @property
    def native_value(self):
        v = self._d("height_cm")
        return float(v) if v else None


class WeightSensor(_Base):
    _attr_name        = "Weight"
    _attr_icon        = "mdi:weight-kilogram"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_weight"

    @property
    def native_value(self):
        v = self._d("weight_kg")
        return float(v) if v else None


class FtpSensor(_Base):
    _attr_name        = "FTP"
    _attr_icon        = "mdi:lightning-bolt-circle"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "W"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_ftp"

    @property
    def native_value(self):
        v = self._d("ftp")
        return float(v) if v else None


# ── Progression ───────────────────────────────────────────────────────────────

class LevelSensor(_Base):
    _attr_name        = "Level"
    _attr_icon        = "mdi:chevron-triple-up"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_level"

    @property
    def native_value(self):
        return self._d("level")

    @property
    def extra_state_attributes(self):
        return {"xp": self._d("xp")}


class XpSensor(_Base):
    _attr_name        = "XP"
    _attr_icon        = "mdi:star-circle"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "XP"

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_xp"

    @property
    def native_value(self):
        return self._d("xp")


class CoinsSensor(_Base):
    _attr_name        = "Coins"
    _attr_icon        = "mdi:circle-multiple"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_coins"

    @property
    def native_value(self):
        return self._d("coins")


class GemsSensor(_Base):
    _attr_name        = "Gems"
    _attr_icon        = "mdi:diamond-stone"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_gems"

    @property
    def native_value(self):
        return self._d("gems")


# ── Lifetime stats ────────────────────────────────────────────────────────────

class TotalDistanceSensor(_Base):
    _attr_name        = "Total Distance"
    _attr_icon        = "mdi:map-marker-distance"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_total_distance"

    @property
    def native_value(self):
        v = self._d("total_km")
        return round(float(v), 1) if v else None


class TotalElevationSensor(_Base):
    _attr_name        = "Total Elevation"
    _attr_icon        = "mdi:elevation-rise"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "m"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_total_elevation"

    @property
    def native_value(self):
        v = self._d("total_elevation")
        return round(float(v)) if v else None


class TotalRideTimeSensor(_Base):
    _attr_name = "Total Ride Time"
    _attr_icon = "mdi:timer"

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_total_ride_time"

    @property
    def native_value(self) -> str | None:
        v = self._d("total_ride_time")
        if not v:
            return None
        return _format_duration(int(float(v)))

    @property
    def extra_state_attributes(self):
        v = self._d("total_ride_time")
        if not v:
            return {}
        return {"total_seconds": int(float(v))}


class TotalCaloriesSensor(_Base):
    _attr_name        = "Total Calories"
    _attr_icon        = "mdi:fire"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "kcal"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_total_calories"

    @property
    def native_value(self):
        v = self._d("total_calories")
        return round(float(v)) if v else None


class WeeklyDistanceSensor(_Base):
    _attr_name        = "Weekly Distance"
    _attr_icon        = "mdi:calendar-week"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_weekly_distance"

    @property
    def native_value(self):
        v = self._d("weekly_km")
        return round(float(v), 1) if v else None


# ── Averages / max ────────────────────────────────────────────────────────────

class AvgPowerSensor(_Base):
    _attr_name        = "Average Power"
    _attr_icon        = "mdi:flash"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "W"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_avg_power"

    @property
    def native_value(self):
        v = self._d("avg_power")
        return round(float(v)) if v else None


class AvgHrSensor(_Base):
    _attr_name        = "Average Heart Rate"
    _attr_icon        = "mdi:heart-pulse"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "bpm"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_avg_hr"

    @property
    def native_value(self):
        v = self._d("avg_hr")
        return round(float(v)) if v else None


class MaxPowerSensor(_Base):
    _attr_name        = "Max Power"
    _attr_icon        = "mdi:lightning-bolt"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "W"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_max_power"

    @property
    def native_value(self):
        v = self._d("max_power")
        return int(v) if v else None


# ── Power bests (parameterised) ───────────────────────────────────────────────

class BestPowerSensor(_Base):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "W"
    _attr_suggested_display_precision = 0
    _attr_icon = "mdi:trophy"

    def __init__(
        self,
        coordinator: MyWhooshCoordinator,
        whoosh_id: str,
        data_key: str,
        name: str,
    ) -> None:
        super().__init__(coordinator, whoosh_id)
        self._data_key = data_key
        self._attr_name = name
        self._attr_unique_id = f"{whoosh_id}_{data_key}"

    @property
    def native_value(self):
        v = self._d(self._data_key)
        return round(float(v)) if v else None


# ── Social ────────────────────────────────────────────────────────────────────

class FriendsOnlineSensor(_Base):
    _attr_name        = "Friends Online"
    _attr_icon        = "mdi:account-group"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, whoosh_id):
        super().__init__(coordinator, whoosh_id)
        self._attr_unique_id = f"{whoosh_id}_friends_online"

    @property
    def native_value(self):
        return self._d("friends_online", 0)

    @property
    def extra_state_attributes(self):
        friends = self._d("friends") or []
        return {
            "total_friends": len(friends),
            "online": [
                f.get("PlayerFirstName") or f.get("Username") or str(f.get("WhooshId", ""))
                for f in friends
                if f.get("IsOnline") or f.get("isOnline")
            ],
        }
