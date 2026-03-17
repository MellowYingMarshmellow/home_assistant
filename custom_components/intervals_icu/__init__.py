"""Intervals ICU Home Assistant integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN
from .coordinator import IntervalsIcuCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

SERVICE_UPDATE_WELLNESS = "update_wellness"
SERVICE_CREATE_ACTIVITY = "create_manual_activity"
SERVICE_UPDATE_ACTIVITY = "update_activity"
SERVICE_UPDATE_ATHLETE  = "update_athlete"
SERVICE_UPDATE_SPORT    = "update_sport_settings"

ALL_SERVICES = [
    SERVICE_UPDATE_WELLNESS,
    SERVICE_CREATE_ACTIVITY,
    SERVICE_UPDATE_ACTIVITY,
    SERVICE_UPDATE_ATHLETE,
    SERVICE_UPDATE_SPORT,
]

# ── Service schemas ───────────────────────────────────────────────────────────

_S10 = vol.All(vol.Coerce(int), vol.Range(min=1, max=10))

WELLNESS_SCHEMA = vol.Schema({
    vol.Optional("date"):             cv.string,
    # Body
    vol.Optional("weight"):           vol.Coerce(float),
    vol.Optional("temp_weight"):      vol.Coerce(float),
    vol.Optional("body_fat"):         vol.Coerce(float),
    vol.Optional("abdomen"):          vol.Coerce(float),
    # Cardiovascular
    vol.Optional("resting_hr"):       vol.Coerce(int),
    vol.Optional("temp_resting_hr"):  vol.Coerce(int),
    vol.Optional("hrv"):              vol.Coerce(float),
    vol.Optional("hrv_sdnn"):         vol.Coerce(float),
    vol.Optional("avg_sleeping_hr"):  vol.Coerce(int),
    vol.Optional("spo2"):             vol.Coerce(float),
    vol.Optional("systolic"):         vol.Coerce(int),
    vol.Optional("diastolic"):        vol.Coerce(int),
    vol.Optional("baevsky_si"):       vol.Coerce(float),
    # Sleep
    vol.Optional("sleep_secs"):       vol.Coerce(int),
    vol.Optional("sleep_score"):      vol.Coerce(int),
    vol.Optional("sleep_quality"):    _S10,
    # Nutrition & hydration
    vol.Optional("kcal_consumed"):    vol.Coerce(int),
    vol.Optional("carbohydrates"):    vol.Coerce(float),
    vol.Optional("protein"):          vol.Coerce(float),
    vol.Optional("fat_total"):        vol.Coerce(float),
    vol.Optional("hydration"):        _S10,
    vol.Optional("hydration_volume"): vol.Coerce(float),
    # Activity
    vol.Optional("steps"):            vol.Coerce(int),
    vol.Optional("respiration"):      vol.Coerce(float),
    # Performance
    vol.Optional("vo2max"):           vol.Coerce(float),
    vol.Optional("blood_glucose"):    vol.Coerce(float),
    vol.Optional("lactate"):          vol.Coerce(float),
    # Subjective
    vol.Optional("soreness"):         _S10,
    vol.Optional("fatigue"):          _S10,
    vol.Optional("stress"):           _S10,
    vol.Optional("mood"):             _S10,
    vol.Optional("motivation"):       _S10,
    vol.Optional("injury"):           _S10,
    vol.Optional("readiness"):        _S10,
    # Other
    vol.Optional("menstrual_phase"):  vol.Coerce(int),
    vol.Optional("comments"):         cv.string,
    vol.Optional("locked"):           cv.boolean,
})

_WELLNESS_FIELD_MAP = {
    # Body
    "weight":           "weight",
    "temp_weight":      "tempWeight",
    "body_fat":         "bodyFat",
    "abdomen":          "abdomen",
    # Cardiovascular
    "resting_hr":       "restingHR",
    "temp_resting_hr":  "tempRestingHR",
    "hrv":              "hrv",
    "hrv_sdnn":         "hrvSDNN",
    "avg_sleeping_hr":  "avgSleepingHR",
    "spo2":             "spO2",
    "systolic":         "systolic",
    "diastolic":        "diastolic",
    "baevsky_si":       "baevskySI",
    # Sleep
    "sleep_secs":       "sleepSecs",
    "sleep_score":      "sleepScore",
    "sleep_quality":    "sleepQuality",
    # Nutrition & hydration
    "kcal_consumed":    "kcalConsumed",
    "carbohydrates":    "carbohydrates",
    "protein":          "protein",
    "fat_total":        "fatTotal",
    "hydration":        "hydration",
    "hydration_volume": "hydrationVolume",
    # Activity
    "steps":            "steps",
    "respiration":      "respiration",
    # Performance
    "vo2max":           "vo2max",
    "blood_glucose":    "bloodGlucose",
    "lactate":          "lactate",
    # Subjective
    "soreness":         "soreness",
    "fatigue":          "fatigue",
    "stress":           "stress",
    "mood":             "mood",
    "motivation":       "motivation",
    "injury":           "injury",
    "readiness":        "readiness",
    # Other
    "menstrual_phase":  "menstrualPhase",
    "comments":         "comments",
    "locked":           "locked",
}

CREATE_ACTIVITY_SCHEMA = vol.Schema({
    vol.Required("name"):                      cv.string,
    vol.Optional("description"):               cv.string,
    vol.Optional("type", default="Ride"):      cv.string,
    vol.Optional("start_date_local"):          cv.string,
    vol.Optional("moving_time"):               vol.Coerce(int),
    vol.Optional("distance"):                  vol.Coerce(float),
    vol.Optional("average_heartrate"):         vol.Coerce(int),
    vol.Optional("max_heartrate"):             vol.Coerce(int),
    vol.Optional("average_watts"):             vol.Coerce(float),
    vol.Optional("max_watts"):                 vol.Coerce(int),
    vol.Optional("kilojoules"):                vol.Coerce(float),
    vol.Optional("normalized_power"):          vol.Coerce(int),
    vol.Optional("total_elevation_gain"):      vol.Coerce(float),
    vol.Optional("feel"):                      vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
    vol.Optional("external_id"):               cv.string,
})

UPDATE_ACTIVITY_SCHEMA = vol.Schema({
    vol.Required("activity_id"):               cv.string,
    vol.Optional("name"):                      cv.string,
    vol.Optional("description"):               cv.string,
    vol.Optional("feel"):                      vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
    vol.Optional("icu_rpe"):                   vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
})

UPDATE_ATHLETE_SCHEMA = vol.Schema({
    vol.Optional("weight"):                    vol.Coerce(float),
    vol.Optional("max_hr"):                    vol.Coerce(int),
    vol.Optional("resting_hr"):                vol.Coerce(int),
    vol.Optional("icu_notes"):                 cv.string,
    vol.Optional("icu_tags"):                  cv.string,
})

UPDATE_SPORT_SCHEMA = vol.Schema({
    vol.Required("type"):                      cv.string,
    vol.Optional("ftp"):                       vol.Coerce(int),
    vol.Optional("indoor_ftp"):                vol.Coerce(int),
    vol.Optional("lthr"):                      vol.Coerce(int),
    vol.Optional("max_hr"):                    vol.Coerce(int),
    vol.Optional("threshold_pace"):            vol.Coerce(float),
})

# ── Setup ─────────────────────────────────────────────────────────────────────

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = IntervalsIcuCoordinator(
        hass,
        athlete_id=entry.data["athlete_id"],
        api_key=entry.data["api_key"],
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    def _coord() -> IntervalsIcuCoordinator:
        return coordinator

    async def handle_update_wellness(call: ServiceCall) -> None:
        from datetime import date as _date
        date_str = call.data.get("date") or _date.today().isoformat()
        payload = {
            api_field: call.data[svc_field]
            for svc_field, api_field in _WELLNESS_FIELD_MAP.items()
            if svc_field in call.data
        }
        if not payload:
            _LOGGER.warning("intervals_icu.update_wellness: no fields provided")
            return
        await _coord().update_wellness(date_str, payload)

    async def handle_create_activity(call: ServiceCall) -> None:
        fields = dict(call.data)
        if "normalized_power" in fields:
            fields["icu_weighted_avg_watts"] = fields.pop("normalized_power")
        await _coord().create_manual_activity(fields)

    async def handle_update_activity(call: ServiceCall) -> None:
        activity_id = call.data["activity_id"]
        fields = {k: v for k, v in call.data.items() if k != "activity_id"}
        await _coord().update_activity(activity_id, fields)

    async def handle_update_athlete(call: ServiceCall) -> None:
        await _coord().update_athlete(dict(call.data))

    async def handle_update_sport(call: ServiceCall) -> None:
        sport_type = call.data["type"]
        fields = {k: v for k, v in call.data.items() if k != "type"}
        await _coord().update_sport_settings(sport_type, fields)

    hass.services.async_register(DOMAIN, SERVICE_UPDATE_WELLNESS, handle_update_wellness, schema=WELLNESS_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CREATE_ACTIVITY, handle_create_activity, schema=CREATE_ACTIVITY_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_UPDATE_ACTIVITY, handle_update_activity, schema=UPDATE_ACTIVITY_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_UPDATE_ATHLETE,  handle_update_athlete,  schema=UPDATE_ATHLETE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_UPDATE_SPORT,    handle_update_sport,    schema=UPDATE_SPORT_SCHEMA)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        coordinator: IntervalsIcuCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_close()
        if not hass.data[DOMAIN]:
            for svc in ALL_SERVICES:
                hass.services.async_remove(DOMAIN, svc)
    return ok
