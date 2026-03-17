"""DataUpdateCoordinator for MyWhoosh."""
from __future__ import annotations

import logging
import uuid
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ACTIVE_SCAN_INTERVAL,
    ACTION_GET_DATA,
    ACTION_LOGIN,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FRIENDS_URL,
    LOGIN_URL,
    PLATFORM,
    PLAYER_DATA_URL,
    PLAYER_DISTANCE_URL,
)

ACTION_UPDATE_DATA = 1051

_LOGGER = logging.getLogger(__name__)


class MyWhooshCoordinator(DataUpdateCoordinator):

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        whoosh_id: str,
    ) -> None:
        self._username   = username
        self._password   = password
        self.whoosh_id   = whoosh_id
        self._token: str | None = None
        self._session: aiohttp.ClientSession | None = None
        # Full raw response cached for PUT updates
        self._raw_player_data: dict | None = None

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

    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _base_payload(action: int) -> dict:
        return {
            "Action": action,
            "CorrelationId": str(uuid.uuid4()),
            "DeviceId": str(uuid.uuid4()),
            "Authorization": "",
        }

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def login(self) -> str:
        """Authenticate and return the WhooshId.  Stores the access token."""
        session = await self._get_session()
        payload = {
            **self._base_payload(ACTION_LOGIN),
            "Username": self._username,
            "Password": self._password,
            "Platform": PLATFORM,
        }
        try:
            resp = await session.post(
                LOGIN_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=15),
            )
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"MyWhoosh: cannot connect — {err}") from err

        if resp.status != 200:
            raise UpdateFailed(f"MyWhoosh: login HTTP {resp.status}")

        data = await resp.json()
        if not data.get("Success"):
            raise UpdateFailed(
                f"MyWhoosh: login rejected — {data.get('Message', 'unknown')}"
            )

        self._token = data["AccessToken"]
        _LOGGER.debug("MyWhoosh: logged in as WhooshId=%s", data.get("WhooshId"))
        return data["WhooshId"]

    # ── Data fetch ────────────────────────────────────────────────────────────

    async def _post_authenticated(self, url: str, extra: dict) -> dict:
        """POST with bearer auth, re-login once on 401."""
        session = await self._get_session()
        payload = {**self._base_payload(ACTION_GET_DATA), **extra}

        async def _do_post():
            return await session.post(
                url,
                json=payload,
                headers=self._auth_headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            )

        try:
            resp = await _do_post()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"MyWhoosh: request failed — {err}") from err

        if resp.status == 401:
            _LOGGER.debug("MyWhoosh: token expired, re-logging in")
            await self.login()
            try:
                resp = await _do_post()
            except aiohttp.ClientError as err:
                raise UpdateFailed(f"MyWhoosh: request failed after re-login — {err}") from err

        if resp.status != 200:
            raise UpdateFailed(f"MyWhoosh: API error {resp.status} for {url}")

        return await resp.json()

    async def _fetch_player_data(self) -> dict:
        return await self._post_authenticated(
            PLAYER_DATA_URL,
            {"WhooshId": self.whoosh_id},
        )

    async def _fetch_friends(self) -> list:
        session = await self._get_session()
        try:
            resp = await session.get(
                FRIENDS_URL,
                headers=self._auth_headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            )
        except aiohttp.ClientError:
            return []
        if resp.status != 200:
            return []
        data = await resp.json()
        return data if isinstance(data, list) else []

    async def _fetch_distance(self) -> dict:
        session = await self._get_session()
        try:
            resp = await session.get(
                PLAYER_DISTANCE_URL,
                headers=self._auth_headers(),
                params={"days": 7},
                timeout=aiohttp.ClientTimeout(total=15),
            )
        except aiohttp.ClientError:
            return {}
        if resp.status != 200:
            return {}
        data = await resp.json()
        return data if isinstance(data, dict) else {}

    # ── Coordinator update ────────────────────────────────────────────────────

    async def _async_update_data(self) -> dict:
        if not self._token:
            await self.login()

        player_data = await self._fetch_player_data()
        # Cache the full raw response so update methods can do a read-modify-PUT
        self._raw_player_data = player_data
        friends     = await self._fetch_friends()
        distance    = await self._fetch_distance()

        profile  = (player_data.get("PlayerDataStruct") or {}).get("PlayerProfileStruct") or {}
        personal = (player_data.get("PlayerDataStruct") or {}).get("PlayerPersonalStruct") or {}
        game     = player_data.get("PlayerGameData") or {}

        _LOGGER.debug("MyWhoosh profile keys: %s", list(profile.keys()))
        _LOGGER.debug("MyWhoosh personal keys: %s", list(personal.keys()))

        # Adaptive polling: speed up if the player is currently in a session
        # (MyWhoosh doesn't expose a live session endpoint, so we approximate
        # "active" by checking if any friend is shown online — simple heuristic)
        is_active = any(f.get("IsOnline") or f.get("isOnline") for f in friends)
        new_interval = ACTIVE_SCAN_INTERVAL if is_active else DEFAULT_SCAN_INTERVAL
        if self.update_interval != timedelta(seconds=new_interval):
            self.update_interval = timedelta(seconds=new_interval)
            _LOGGER.debug("MyWhoosh: poll interval → %ss", new_interval)

        return {
            # ── Identity ────────────────────────────────────────────────────
            "whoosh_id":   self.whoosh_id,
            "first_name":  profile.get("PlayerFirstName", ""),
            "last_name":   profile.get("PlayerLastName", ""),
            "full_name":   f"{profile.get('PlayerFirstName', '')} {profile.get('PlayerLastName', '')}".strip(),
            "country_id":  profile.get("CountryId"),
            "category":    personal.get("PlayerCategoryId"),
            # ── Biometrics ──────────────────────────────────────────────────
            "height_cm":   profile.get("HeightCm"),
            "weight_kg":   profile.get("Weight"),
            "ftp":         personal.get("FtpPlayer"),
            # ── Progression ─────────────────────────────────────────────────
            "level":       personal.get("PlayerLevel"),
            "xp":          personal.get("PlayerXP"),
            "coins":       personal.get("Coins"),
            "gems":        personal.get("Gems"),
            # ── Lifetime stats ──────────────────────────────────────────────
            "total_km":         personal.get("TotalKilometers"),
            "total_elevation":  personal.get("TotalElevation"),
            "total_ride_time":  personal.get("TotalRideTime"),
            "total_calories":   personal.get("TotalCaloriesBurn"),
            "weekly_km":        personal.get("TotalKilometersInWeek"),
            # ── Avg / max ───────────────────────────────────────────────────
            "avg_power":   personal.get("AveragePower"),
            "avg_hr":      personal.get("AverageHeartRate"),
            "max_power":   personal.get("MaxPower"),
            # ── Power bests ─────────────────────────────────────────────────
            "best_5s":    personal.get("BestPower5Second"),
            "best_30s":   personal.get("BestPower30Second"),
            "best_1min":  personal.get("BestPower1Minute"),
            "best_3min":  personal.get("BestPower3Minute"),
            "best_5min":  personal.get("BestPower5Minute"),
            "best_12min": personal.get("BestPower12Minute"),
            "best_20min": personal.get("BestPower20Minute"),
            "best_30min": personal.get("BestPower30Minute"),
            "best_60min": personal.get("BestPower60Minute"),
            # ── Social ──────────────────────────────────────────────────────
            "friends":    friends,
            "friends_online": sum(
                1 for f in friends if f.get("IsOnline") or f.get("isOnline")
            ),
            # ── Distance (7-day) ────────────────────────────────────────────
            "distance_7d": distance,
            # ── Settings ────────────────────────────────────────────────────
            "measure_unit": game.get("MeasureUnit", 0),  # 0=metric, 1=imperial
        }

    # ── Profile update ────────────────────────────────────────────────────────

    async def update_profile(self, profile_patch: dict, personal_patch: dict | None = None) -> None:
        """Patch fields in PlayerProfileStruct (and optionally PlayerPersonalStruct) then PUT.

        The API requires the full PlayerDataStruct + PlayerGameData sent back as a
        stringified JSON string in the `PlayerData` field.
        """
        import json

        if not self._raw_player_data:
            # Fetch fresh if we don't have cached data yet
            self._raw_player_data = await self._fetch_player_data()

        import copy
        raw = copy.deepcopy(self._raw_player_data)

        # Apply patches
        struct = raw.setdefault("PlayerDataStruct", {})
        struct.setdefault("PlayerProfileStruct", {}).update(profile_patch)
        if personal_patch:
            struct.setdefault("PlayerPersonalStruct", {}).update(personal_patch)

        player_data_str = json.dumps({
            "PlayerDataStruct": struct,
            "PlayerGameData":   raw.get("PlayerGameData") or {},
        })

        payload = {
            **self._base_payload(ACTION_UPDATE_DATA),
            "WhooshId":   self.whoosh_id,
            "PlayerData": player_data_str,
        }

        session = await self._get_session()
        try:
            resp = await session.put(
                PLAYER_DATA_URL,
                json=payload,
                headers=self._auth_headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            )
        except aiohttp.ClientError as err:
            raise Exception(f"MyWhoosh: update failed — {err}") from err

        if resp.status == 401:
            await self.login()
            resp = await session.put(
                PLAYER_DATA_URL,
                json=payload,
                headers=self._auth_headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            )

        if resp.status not in (200, 201):
            text = await resp.text()
            raise Exception(f"MyWhoosh: update failed ({resp.status}): {text}")

        _LOGGER.debug("MyWhoosh: profile updated — %s / %s", profile_patch, personal_patch)
        await self.async_request_refresh()

    async def update_weight(self, weight_kg: float) -> None:
        await self.update_profile(
            profile_patch={"Weight": weight_kg},
            personal_patch={"VerifiedWeight": weight_kg},
        )

    async def update_ftp(self, ftp_watts: int) -> None:
        await self.update_profile(
            profile_patch={},
            personal_patch={"FtpPlayer": float(ftp_watts)},
        )

    # ── Cleanup ───────────────────────────────────────────────────────────────

    async def async_close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
