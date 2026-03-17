"""Sensor platform for Intervals ICU."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfMass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import IntervalsIcuCoordinator


def _device(athlete_id: str, athlete: dict) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, athlete_id)},
        name=athlete.get("name") or f"Intervals ICU ({athlete_id})",
        manufacturer="Intervals ICU",
        model="Athlete Profile",
        configuration_url=f"https://intervals.icu/athlete/{athlete_id}/fitness",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: IntervalsIcuCoordinator = hass.data[DOMAIN][entry.entry_id]
    athlete_id = coordinator.athlete_id
    known_sport_types: set[str] = set()
    known_sport_info_types: set[str] = set()

    def _sport_sensors() -> list:
        new = []
        for sport in coordinator.data.get("sport_settings") or []:
            sport_type = sport.get("type")
            if sport_type and sport_type not in known_sport_types:
                new.append(SportSensor(coordinator, athlete_id, sport_type))
                known_sport_types.add(sport_type)
        return new

    def _sport_info_sensors() -> list:
        new = []
        for info in coordinator.data.get("sport_info") or []:
            sport_type = info.get("type")
            if sport_type and sport_type not in known_sport_info_types:
                new.append(SportInfoSensor(coordinator, athlete_id, sport_type))
                known_sport_info_types.add(sport_type)
        return new

    async_add_entities(
        [
            # ── Athlete profile ────────────────────────────────────────────
            AthleteNameSensor(coordinator, athlete_id),
            AthleteFtpSensor(coordinator, athlete_id),
            AthleteWeightSensor(coordinator, athlete_id),
            AthleteMaxHrSensor(coordinator, athlete_id),
            AthleteRestingHrSensor(coordinator, athlete_id),
            AthleteLthrSensor(coordinator, athlete_id),
            AthleteVo2MaxSensor(coordinator, athlete_id),
            AthleteCountrySensor(coordinator, athlete_id),
            # ── Wellness / fitness (read-only computed) ────────────────────
            CtlSensor(coordinator, athlete_id),
            AtlSensor(coordinator, athlete_id),
            TsbSensor(coordinator, athlete_id),
            CtlLoadSensor(coordinator, athlete_id),
            AtlLoadSensor(coordinator, athlete_id),
            RampRateSensor(coordinator, athlete_id),
            # ── Wellness / body metrics ────────────────────────────────────
            WellnessWeightSensor(coordinator, athlete_id),
            BodyFatSensor(coordinator, athlete_id),
            AbdomenSensor(coordinator, athlete_id),
            # ── Wellness / cardiovascular ──────────────────────────────────
            RestingHrSensor(coordinator, athlete_id),
            AvgSleepingHrSensor(coordinator, athlete_id),
            HrvSensor(coordinator, athlete_id),
            HrvSdnnSensor(coordinator, athlete_id),
            SpO2Sensor(coordinator, athlete_id),
            SystolicSensor(coordinator, athlete_id),
            DiastolicSensor(coordinator, athlete_id),
            BaevskySiSensor(coordinator, athlete_id),
            # ── Wellness / sleep ───────────────────────────────────────────
            SleepSensor(coordinator, athlete_id),
            SleepScoreSensor(coordinator, athlete_id),
            SleepQualitySensor(coordinator, athlete_id),
            # ── Wellness / nutrition & hydration ───────────────────────────
            KcalConsumedSensor(coordinator, athlete_id),
            CarbohydratesSensor(coordinator, athlete_id),
            ProteinSensor(coordinator, athlete_id),
            FatTotalSensor(coordinator, athlete_id),
            HydrationSensor(coordinator, athlete_id),
            HydrationVolumeSensor(coordinator, athlete_id),
            # ── Wellness / activity ────────────────────────────────────────
            StepsSensor(coordinator, athlete_id),
            RespirationSensor(coordinator, athlete_id),
            # ── Wellness / performance ─────────────────────────────────────
            Vo2MaxSensor(coordinator, athlete_id),
            BloodGlucoseSensor(coordinator, athlete_id),
            LactateSensor(coordinator, athlete_id),
            # ── Wellness / subjective ──────────────────────────────────────
            SorenesSensor(coordinator, athlete_id),
            FatigueSensor(coordinator, athlete_id),
            StressSensor(coordinator, athlete_id),
            MoodSensor(coordinator, athlete_id),
            MotivationSensor(coordinator, athlete_id),
            InjurySensor(coordinator, athlete_id),
            ReadinessSensor(coordinator, athlete_id),
            # ── Activities ─────────────────────────────────────────────────
            LatestActivitySensor(coordinator, athlete_id),
            LatestActivityDurationSensor(coordinator, athlete_id),
            LatestActivityLoadSensor(coordinator, athlete_id),
            LatestActivityAvgPowerSensor(coordinator, athlete_id),
            LatestActivityAvgHrSensor(coordinator, athlete_id),
            # ── Today's planned workout ────────────────────────────────────
            PlannedWorkoutSensor(coordinator, athlete_id),
        ]
        + _sport_sensors()
        + _sport_info_sensors()
    )

    @callback
    def _on_update() -> None:
        new = _sport_sensors() + _sport_info_sensors()
        if new:
            async_add_entities(new)

    entry.async_on_unload(coordinator.async_add_listener(_on_update))


# ── Base ──────────────────────────────────────────────────────────────────────

class _Base(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: IntervalsIcuCoordinator, athlete_id: str) -> None:
        super().__init__(coordinator)
        self._athlete_id = athlete_id

    @property
    def device_info(self) -> DeviceInfo:
        return _device(self._athlete_id, self.coordinator.data.get("athlete") or {})

    def _athlete(self) -> dict:
        return self.coordinator.data.get("athlete") or {}

    def _wellness(self) -> dict:
        return self.coordinator.data.get("wellness") or {}


# ── Athlete profile ───────────────────────────────────────────────────────────

class AthleteNameSensor(_Base):
    _attr_name = "Athlete Name"
    _attr_icon = "mdi:account"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_athlete_name"

    @property
    def native_value(self):
        return self._athlete().get("name")

    @property
    def extra_state_attributes(self):
        a = self._athlete()
        return {
            "athlete_id": self._athlete_id,
            "email":      a.get("email"),
            "country":    a.get("country"),
            "sex":        a.get("sex"),
            "dob":        a.get("dob"),
            "premium":    a.get("premium"),
            "icu_notes":  a.get("icu_notes"),
            "icu_tags":   a.get("icu_tags"),
        }


class AthleteFtpSensor(_Base):
    _attr_name        = "FTP"
    _attr_icon        = "mdi:lightning-bolt-circle"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "W"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_ftp"

    @property
    def native_value(self):
        a = self._athlete()
        ftp = a.get("ftp") or a.get("icuFtp") or a.get("icu_ftp")
        if ftp is None:
            for s in a.get("sportSettings", []):
                if s.get("type") == "Ride":
                    ftp = s.get("ftp") or s.get("icuFtp") or s.get("icu_ftp")
                    break
        return ftp


class AthleteWeightSensor(_Base):
    _attr_name        = "Profile Weight"
    _attr_icon        = "mdi:weight-kilogram"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_profile_weight"

    @property
    def native_value(self):
        v = self._athlete().get("weight") or self._athlete().get("icuWeight") or self._athlete().get("icu_weight")
        return float(v) if v is not None else None


class AthleteMaxHrSensor(_Base):
    _attr_name        = "Max Heart Rate"
    _attr_icon        = "mdi:heart-pulse"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "bpm"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_max_hr"

    @property
    def native_value(self):
        a = self._athlete()
        v = a.get("max_hr") or a.get("maxHR")
        if v is None:
            for s in a.get("sportSettings", []):
                v = s.get("max_hr") or s.get("maxHR")
                if v:
                    break
        return v


class AthleteRestingHrSensor(_Base):
    _attr_name        = "Profile Resting HR"
    _attr_icon        = "mdi:heart-pulse"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "bpm"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_profile_resting_hr"

    @property
    def native_value(self):
        a = self._athlete()
        return a.get("resting_hr") or a.get("restingHR")


class AthleteLthrSensor(_Base):
    _attr_name        = "LTHR"
    _attr_icon        = "mdi:heart-flash"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "bpm"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_lthr"

    @property
    def native_value(self):
        for s in self._athlete().get("sportSettings", []):
            lthr = s.get("lthr") or s.get("lt_hr")
            if lthr:
                return lthr
        return None

    @property
    def extra_state_attributes(self):
        return {
            s.get("type"): s.get("lthr") or s.get("lt_hr")
            for s in self._athlete().get("sportSettings", [])
            if s.get("lthr") or s.get("lt_hr")
        }


class AthleteVo2MaxSensor(_Base):
    _attr_name        = "Profile VO2 Max"
    _attr_icon        = "mdi:lungs"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "ml/kg/min"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_profile_vo2max"

    @property
    def native_value(self):
        v = (self._athlete().get("vo2max")
             or self._athlete().get("icu_vo2max")
             or self._athlete().get("icuVo2max"))
        return float(v) if v is not None else None


class AthleteCountrySensor(_Base):
    _attr_name = "Country"
    _attr_icon = "mdi:flag"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_country"

    @property
    def native_value(self):
        return self._athlete().get("country")


# ── Dynamic: one sensor per configured sport ─────────────────────────────────

class SportSensor(_Base):
    _attr_icon = "mdi:bike"

    def __init__(self, coordinator, athlete_id: str, sport_type: str) -> None:
        super().__init__(coordinator, athlete_id)
        self._sport_type = sport_type
        self._attr_unique_id = f"{athlete_id}_sport_{sport_type.lower()}"
        self._attr_name = f"{sport_type} Settings"

    def _sport(self) -> dict:
        return next(
            (s for s in (self.coordinator.data.get("sport_settings") or [])
             if s.get("type") == self._sport_type),
            {},
        )

    @property
    def available(self) -> bool:
        return bool(self._sport())

    @property
    def native_value(self):
        s = self._sport()
        return s.get("ftp") or s.get("lthr") or s.get("lt_hr")

    @property
    def native_unit_of_measurement(self):
        s = self._sport()
        if s.get("ftp"):
            return "W"
        if s.get("lthr") or s.get("lt_hr"):
            return "bpm"
        return None

    @property
    def extra_state_attributes(self):
        s = self._sport()
        return {
            "sport_type":     self._sport_type,
            "ftp":            s.get("ftp"),
            "indoor_ftp":     s.get("indoor_ftp") or s.get("indoorFtp"),
            "lthr":           s.get("lthr") or s.get("lt_hr"),
            "max_hr":         s.get("max_hr") or s.get("maxHR"),
            "threshold_pace": s.get("threshold_pace") or s.get("thresholdPace"),
        }


# ── Wellness / fitness sensors ────────────────────────────────────────────────

class CtlSensor(_Base):
    _attr_name        = "Fitness (CTL)"
    _attr_icon        = "mdi:trending-up"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_ctl"

    @property
    def native_value(self):
        return self.coordinator.data.get("ctl")


class AtlSensor(_Base):
    _attr_name        = "Fatigue (ATL)"
    _attr_icon        = "mdi:trending-down"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_atl"

    @property
    def native_value(self):
        return self.coordinator.data.get("atl")


class TsbSensor(_Base):
    _attr_name        = "Form (TSB)"
    _attr_icon        = "mdi:gauge"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_tsb"

    @property
    def native_value(self):
        return self.coordinator.data.get("tsb")


class RampRateSensor(_Base):
    _attr_name        = "Ramp Rate"
    _attr_icon        = "mdi:chart-line"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_native_unit_of_measurement = "CTL/wk"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_ramp_rate"

    @property
    def native_value(self):
        return self._wellness().get("rampRate")


class WellnessWeightSensor(_Base):
    _attr_name        = "Weight"
    _attr_icon        = "mdi:weight-kilogram"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_weight"

    @property
    def native_value(self):
        v = self._wellness().get("weight")
        return float(v) if v is not None else None


class RestingHrSensor(_Base):
    _attr_name        = "Resting Heart Rate"
    _attr_icon        = "mdi:heart-pulse"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "bpm"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_resting_hr"

    @property
    def native_value(self):
        return self._wellness().get("restingHR") or self._wellness().get("resting_hr")


class HrvSensor(_Base):
    _attr_name        = "HRV (rMSSD)"
    _attr_icon        = "mdi:heart-flash"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "ms"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_hrv"

    @property
    def native_value(self):
        v = self._wellness().get("hrv")
        return float(v) if v is not None else None


class SleepSensor(_Base):
    _attr_name        = "Sleep"
    _attr_icon        = "mdi:sleep"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "h"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_sleep_hours"

    @property
    def native_value(self):
        secs = self._wellness().get("sleepSecs")
        return round(float(secs) / 3600, 2) if secs is not None else None


class SleepScoreSensor(_Base):
    _attr_name        = "Sleep Score"
    _attr_icon        = "mdi:sleep"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_sleep_score"

    @property
    def native_value(self):
        return self._wellness().get("sleepScore")


class StepsSensor(_Base):
    _attr_name        = "Steps"
    _attr_icon        = "mdi:walk"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "steps"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_steps"

    @property
    def native_value(self):
        return self._wellness().get("steps")


class Vo2MaxSensor(_Base):
    _attr_name        = "VO2 Max"
    _attr_icon        = "mdi:lungs"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "ml/kg/min"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_vo2max"

    @property
    def native_value(self):
        v = self._wellness().get("vo2max")
        return float(v) if v is not None else None


class _Subjective(_Base):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "/10"
    _key: str

    @property
    def native_value(self):
        return self._wellness().get(self._key)


class SorenesSensor(_Subjective):
    _attr_name = "Soreness"
    _attr_icon = "mdi:bandage"
    _key = "soreness"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_soreness"


class FatigueSensor(_Subjective):
    _attr_name = "Perceived Fatigue"
    _attr_icon = "mdi:emoticon-tired"
    _key = "fatigue"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_fatigue"


class StressSensor(_Subjective):
    _attr_name = "Stress"
    _attr_icon = "mdi:head-alert"
    _key = "stress"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_stress"


class MoodSensor(_Subjective):
    _attr_name = "Mood"
    _attr_icon = "mdi:emoticon-happy"
    _key = "mood"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_mood"


class MotivationSensor(_Subjective):
    _attr_name = "Motivation"
    _attr_icon = "mdi:lightning-bolt"
    _key = "motivation"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_motivation"


class InjurySensor(_Subjective):
    _attr_name = "Injury"
    _attr_icon = "mdi:bandage"
    _key = "injury"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_injury"


class ReadinessSensor(_Subjective):
    _attr_name = "Readiness"
    _attr_icon = "mdi:check-circle-outline"
    _key = "readiness"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_readiness"


# ── Wellness: CTL/ATL load contributions ──────────────────────────────────────

class CtlLoadSensor(_Base):
    _attr_name        = "CTL Load"
    _attr_icon        = "mdi:trending-up"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_ctl_load"

    @property
    def native_value(self):
        return self.coordinator.data.get("ctl_load")


class AtlLoadSensor(_Base):
    _attr_name        = "ATL Load"
    _attr_icon        = "mdi:trending-down"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_atl_load"

    @property
    def native_value(self):
        return self.coordinator.data.get("atl_load")


# ── Wellness: cardiovascular extras ───────────────────────────────────────────

class HrvSdnnSensor(_Base):
    _attr_name        = "HRV (SDNN)"
    _attr_icon        = "mdi:heart-flash"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "ms"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_hrv_sdnn"

    @property
    def native_value(self):
        v = self._wellness().get("hrvSDNN")
        return float(v) if v is not None else None


class AvgSleepingHrSensor(_Base):
    _attr_name        = "Avg Sleeping HR"
    _attr_icon        = "mdi:heart-pulse"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "bpm"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_avg_sleeping_hr"

    @property
    def native_value(self):
        return self._wellness().get("avgSleepingHR")


class SpO2Sensor(_Base):
    _attr_name        = "SpO2"
    _attr_icon        = "mdi:lungs"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_spo2"

    @property
    def native_value(self):
        v = self._wellness().get("spO2")
        return float(v) if v is not None else None


class SystolicSensor(_Base):
    _attr_name        = "Blood Pressure (Systolic)"
    _attr_icon        = "mdi:heart"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "mmHg"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_systolic"

    @property
    def native_value(self):
        return self._wellness().get("systolic")


class DiastolicSensor(_Base):
    _attr_name        = "Blood Pressure (Diastolic)"
    _attr_icon        = "mdi:heart"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "mmHg"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_diastolic"

    @property
    def native_value(self):
        return self._wellness().get("diastolic")


class BaevskySiSensor(_Base):
    _attr_name        = "Baevsky SI"
    _attr_icon        = "mdi:heart-flash"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_baevsky_si"

    @property
    def native_value(self):
        v = self._wellness().get("baevskySI")
        return float(v) if v is not None else None


# ── Wellness: sleep extras ─────────────────────────────────────────────────────

class SleepQualitySensor(_Subjective):
    _attr_name = "Sleep Quality"
    _attr_icon = "mdi:sleep"
    _key = "sleepQuality"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_sleep_quality"


# ── Wellness: nutrition & hydration ───────────────────────────────────────────

class KcalConsumedSensor(_Base):
    _attr_name        = "Calories Consumed"
    _attr_icon        = "mdi:fire"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "kcal"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_kcal_consumed"

    @property
    def native_value(self):
        return self._wellness().get("kcalConsumed")


class CarbohydratesSensor(_Base):
    _attr_name        = "Carbohydrates"
    _attr_icon        = "mdi:bread-slice"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "g"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_carbohydrates"

    @property
    def native_value(self):
        v = self._wellness().get("carbohydrates")
        return float(v) if v is not None else None


class ProteinSensor(_Base):
    _attr_name        = "Protein"
    _attr_icon        = "mdi:food-steak"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "g"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_protein"

    @property
    def native_value(self):
        v = self._wellness().get("protein")
        return float(v) if v is not None else None


class FatTotalSensor(_Base):
    _attr_name        = "Fat (Total)"
    _attr_icon        = "mdi:oil"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "g"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_fat_total"

    @property
    def native_value(self):
        v = self._wellness().get("fatTotal")
        return float(v) if v is not None else None


class HydrationSensor(_Subjective):
    _attr_name = "Hydration"
    _attr_icon = "mdi:water"
    _key = "hydration"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_hydration"


class HydrationVolumeSensor(_Base):
    _attr_name        = "Hydration Volume"
    _attr_icon        = "mdi:water"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "ml"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_hydration_volume"

    @property
    def native_value(self):
        return self._wellness().get("hydrationVolume")


# ── Wellness: blood markers ────────────────────────────────────────────────────

class BloodGlucoseSensor(_Base):
    _attr_name        = "Blood Glucose"
    _attr_icon        = "mdi:blood-bag"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "mmol/L"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_blood_glucose"

    @property
    def native_value(self):
        v = self._wellness().get("bloodGlucose")
        return float(v) if v is not None else None


class LactateSensor(_Base):
    _attr_name        = "Lactate"
    _attr_icon        = "mdi:blood-bag"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "mmol/L"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_lactate"

    @property
    def native_value(self):
        v = self._wellness().get("lactate")
        return float(v) if v is not None else None


# ── Wellness: body composition extras ─────────────────────────────────────────

class BodyFatSensor(_Base):
    _attr_name        = "Body Fat"
    _attr_icon        = "mdi:human"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_body_fat"

    @property
    def native_value(self):
        v = self._wellness().get("bodyFat")
        return float(v) if v is not None else None


class AbdomenSensor(_Base):
    _attr_name        = "Abdomen"
    _attr_icon        = "mdi:human"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "cm"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_abdomen"

    @property
    def native_value(self):
        v = self._wellness().get("abdomen")
        return float(v) if v is not None else None


class RespirationSensor(_Base):
    _attr_name        = "Respiration"
    _attr_icon        = "mdi:lungs"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "rpm"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_respiration"

    @property
    def native_value(self):
        v = self._wellness().get("respiration")
        return float(v) if v is not None else None


# ── Dynamic: one sensor per sport in sportInfo (eftp, wPrime, pMax) ───────────

class SportInfoSensor(_Base):
    _attr_icon = "mdi:lightning-bolt-circle"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "W"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, athlete_id: str, sport_type: str) -> None:
        super().__init__(coordinator, athlete_id)
        self._sport_type = sport_type
        self._attr_unique_id = f"{athlete_id}_sport_info_{sport_type.lower()}"
        self._attr_name = f"{sport_type} eFTP"

    def _info(self) -> dict:
        return next(
            (s for s in (self.coordinator.data.get("sport_info") or [])
             if s.get("type") == self._sport_type),
            {},
        )

    @property
    def available(self) -> bool:
        return bool(self._info())

    @property
    def native_value(self):
        v = self._info().get("eftp")
        return float(v) if v is not None else None

    @property
    def extra_state_attributes(self):
        info = self._info()
        return {
            "sport_type": self._sport_type,
            "eftp":       info.get("eftp"),
            "w_prime":    info.get("wPrime"),
            "p_max":      info.get("pMax"),
        }


# ── Activity sensors ──────────────────────────────────────────────────────────

class LatestActivitySensor(_Base):
    _attr_name = "Latest Activity"
    _attr_icon = "mdi:run-fast"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_latest_activity"

    def _act(self) -> dict:
        return self.coordinator.data.get("latest_activity") or {}

    @property
    def native_value(self):
        act = self._act()
        return act.get("name") or act.get("type") or "No recent activity"

    @property
    def extra_state_attributes(self):
        act = self._act()
        if not act:
            return {}
        return {
            "activity_id":       act.get("id"),
            "type":              act.get("type"),
            "start_date":        act.get("start_date_local"),
            "distance_m":        act.get("distance"),
            "moving_time_secs":  act.get("moving_time"),
            "elapsed_time_secs": act.get("elapsed_time"),
            "elevation_gain_m":  act.get("total_elevation_gain"),
            "avg_speed":         act.get("average_speed"),
            "avg_watts":         act.get("average_watts"),
            "normalized_power":  act.get("icu_weighted_avg_watts"),
            "max_watts":         act.get("max_watts"),
            "avg_heartrate":     act.get("average_heartrate"),
            "max_heartrate":     act.get("max_heartrate"),
            "training_load":     act.get("icu_training_load"),
            "ctl_after":         act.get("icu_ctl"),
            "atl_after":         act.get("icu_atl"),
            "rpe":               act.get("feel") or act.get("icu_rpe"),
            "notes":             act.get("description"),
        }


class LatestActivityDurationSensor(_Base):
    _attr_name        = "Latest Activity Duration"
    _attr_icon        = "mdi:timer"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "min"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_latest_activity_duration"

    @property
    def native_value(self):
        act = self.coordinator.data.get("latest_activity") or {}
        secs = act.get("moving_time") or act.get("elapsed_time")
        return round(secs / 60) if secs else None


class LatestActivityLoadSensor(_Base):
    _attr_name        = "Latest Activity Load"
    _attr_icon        = "mdi:weight"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_latest_activity_load"

    @property
    def native_value(self):
        return (self.coordinator.data.get("latest_activity") or {}).get("icu_training_load")


class LatestActivityAvgPowerSensor(_Base):
    _attr_name        = "Latest Activity Avg Power"
    _attr_icon        = "mdi:flash"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "W"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_latest_activity_avg_power"

    @property
    def native_value(self):
        act = self.coordinator.data.get("latest_activity") or {}
        return act.get("average_watts") or act.get("icu_weighted_avg_watts")


class LatestActivityAvgHrSensor(_Base):
    _attr_name        = "Latest Activity Avg HR"
    _attr_icon        = "mdi:heart-pulse"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "bpm"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_latest_activity_avg_hr"

    @property
    def native_value(self):
        return (self.coordinator.data.get("latest_activity") or {}).get("average_heartrate")


# ── Today's planned workout ───────────────────────────────────────────────────

class PlannedWorkoutSensor(_Base):
    _attr_name = "Today's Workout"
    _attr_icon = "mdi:calendar-check"

    def __init__(self, coordinator, athlete_id):
        super().__init__(coordinator, athlete_id)
        self._attr_unique_id = f"{athlete_id}_planned_workout"

    @property
    def native_value(self):
        w = self.coordinator.data.get("today_workout")
        return w.get("name") or "Workout" if w else "Rest"

    @property
    def extra_state_attributes(self):
        w = self.coordinator.data.get("today_workout")
        if not w:
            return {}
        return {
            "description":  w.get("description"),
            "workout_type": w.get("type"),
            "load":         w.get("load"),
            "moving_time":  w.get("moving_time"),
            "distance":     w.get("distance"),
            "indoor":       w.get("indoor"),
            "event_id":     w.get("id"),
        }
