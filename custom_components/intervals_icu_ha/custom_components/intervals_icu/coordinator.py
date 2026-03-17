"""DataUpdateCoordinator for Intervals ICU."""
from __future__ import annotations

import asyncio
import logging
from datetime import date, timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import BASE_URL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class IntervalsIcuCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, athlete_id: str, api_key: str) -> None:
        self.athlete_id = athlete_id
        self._auth = aiohttp.BasicAuth("API_KEY", api_key)
        self._session: aiohttp.ClientSession | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    # ── Session ───────────────────────────────────────────────────────────────

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    async def _get(self, path: str) -> dict | list | None:
        session = await self._get_session()
        try:
            resp = await session.get(
                f"{BASE_URL}{path}",
                auth=self._auth,
                timeout=aiohttp.ClientTimeout(total=15),
            )
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Cannot reach Intervals ICU: {err}") from err

        if resp.status == 404:
            return None
        if resp.status == 401:
            raise UpdateFailed("Intervals ICU: invalid API key or athlete ID")
        if resp.status != 200:
            raise UpdateFailed(f"Intervals ICU API error {resp.status} for {path}")

        return await resp.json()

    async def _put(self, path: str, data: dict) -> dict:
        session = await self._get_session()
        try:
            resp = await session.put(
                f"{BASE_URL}{path}",
                auth=self._auth,
                json=data,
                timeout=aiohttp.ClientTimeout(total=15),
            )
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Cannot reach Intervals ICU: {err}") from err

        if resp.status not in (200, 201):
            text = await resp.text()
            raise UpdateFailed(f"Intervals ICU PUT {path} failed ({resp.status}): {text}")

        return await resp.json()

    async def _post(self, path: str, data: dict | list) -> dict | list:
        session = await self._get_session()
        try:
            resp = await session.post(
                f"{BASE_URL}{path}",
                auth=self._auth,
                json=data,
                timeout=aiohttp.ClientTimeout(total=15),
            )
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Cannot reach Intervals ICU: {err}") from err

        if resp.status not in (200, 201):
            text = await resp.text()
            raise UpdateFailed(f"Intervals ICU POST {path} failed ({resp.status}): {text}")

        return await resp.json()

    # ── Data fetch ────────────────────────────────────────────────────────────

    async def _async_update_data(self) -> dict:
        today     = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        two_weeks = (date.today() - timedelta(days=14)).isoformat()

        athlete, wellness_today, wellness_yesterday, activities, events = await asyncio.gather(
            self._get(f"/athlete/{self.athlete_id}"),
            self._get(f"/athlete/{self.athlete_id}/wellness/{today}"),
            self._get(f"/athlete/{self.athlete_id}/wellness/{yesterday}"),
            self._get(f"/athlete/{self.athlete_id}/activities?oldest={two_weeks}&newest={today}"),
            self._get(f"/athlete/{self.athlete_id}/events?oldest={today}&newest={today}&category=WORKOUT"),
            return_exceptions=True,
        )

        for result in (athlete, wellness_today, wellness_yesterday, activities, events):
            if isinstance(result, UpdateFailed):
                raise result

        athlete_data   = athlete if isinstance(athlete, dict) else {}
        sport_settings = athlete_data.get("sportSettings") or []

        # Wellness — fall back to yesterday for CTL/ATL if today's not populated yet
        wellness = wellness_today if isinstance(wellness_today, dict) else {}
        if not wellness.get("ctl") and isinstance(wellness_yesterday, dict):
            wellness.setdefault("ctl",      wellness_yesterday.get("ctl"))
            wellness.setdefault("atl",      wellness_yesterday.get("atl"))
            wellness.setdefault("rampRate", wellness_yesterday.get("rampRate"))

        activity_list = sorted(
            (a for a in (activities or []) if isinstance(a, dict)),
            key=lambda a: a.get("start_date_local", ""),
            reverse=True,
        )

        event_list    = events if isinstance(events, list) else []
        today_workout = next(
            (e for e in event_list if isinstance(e, dict) and e.get("category") == "WORKOUT"),
            None,
        )

        # Log the raw keys so we can confirm the exact field names from the API
        _LOGGER.debug("Wellness keys: %s", list(wellness.keys()))
        _LOGGER.debug("Wellness values: %s", wellness)
        _LOGGER.debug("Athlete keys: %s", list(athlete_data.keys()))
        _LOGGER.debug("Sport settings: %s", athlete_data.get("sportSettings"))

        ctl = wellness.get("ctl")
        atl = wellness.get("atl")

        def _f(v):
            return float(v) if v is not None else None

        return {
            "athlete":         athlete_data,
            "sport_settings":  sport_settings,
            "wellness":        wellness,
            "ctl":             _f(ctl),
            "atl":             _f(atl),
            "tsb":             round(float(ctl) - float(atl), 1) if (ctl is not None and atl is not None) else None,
            "ctl_load":        _f(wellness.get("ctlLoad")),
            "atl_load":        _f(wellness.get("atlLoad")),
            "sport_info":      wellness.get("sportInfo") or [],
            "activities":      activity_list,
            "latest_activity": activity_list[0] if activity_list else None,
            "today_workout":   today_workout,
        }

    # ── Wellness ──────────────────────────────────────────────────────────────

    async def update_wellness(self, date_str: str, fields: dict) -> None:
        payload = {"id": date_str, **fields}
        await self._put(f"/athlete/{self.athlete_id}/wellness/{date_str}", payload)
        await self.async_request_refresh()

    # ── Activities ────────────────────────────────────────────────────────────

    async def create_manual_activity(self, fields: dict) -> dict:
        result = await self._post(f"/athlete/{self.athlete_id}/activities/manual", fields)
        await self.async_request_refresh()
        return result

    async def update_activity(self, activity_id: str, fields: dict) -> dict:
        result = await self._put(f"/activity/{activity_id}", fields)
        await self.async_request_refresh()
        return result

    # ── Sport settings ────────────────────────────────────────────────────────

    async def update_sport_settings(self, sport_type: str, fields: dict) -> dict:
        result = await self._put(
            f"/athlete/{self.athlete_id}/sport-settings/{sport_type}",
            fields,
        )
        await self.async_request_refresh()
        return result

    # ── Athlete profile ───────────────────────────────────────────────────────

    async def update_athlete(self, fields: dict) -> dict:
        result = await self._put(f"/athlete/{self.athlete_id}", fields)
        await self.async_request_refresh()
        return result

    # ── Cleanup ───────────────────────────────────────────────────────────────

    async def async_close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
