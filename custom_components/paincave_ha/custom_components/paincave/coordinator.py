"""DataUpdateCoordinator for PainCave."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class PainCaveCoordinator(DataUpdateCoordinator):
    """Polls the PainCave API and provides data to all platform entities."""

    def __init__(self, hass: HomeAssistant, url: str, email: str, password: str) -> None:
        self.url      = url.rstrip("/")
        self.email    = email
        self.password = password
        self._token: str | None = None
        self._session: aiohttp.ClientSession | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    # ── Session & auth ────────────────────────────────────────────────────────

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _login(self) -> None:
        session = await self._get_session()
        resp = await session.post(
            f"{self.url}/api/auth/login",
            json={"email": self.email, "password": self.password},
            timeout=aiohttp.ClientTimeout(total=10),
        )
        if resp.status != 200:
            text = await resp.text()
            raise UpdateFailed(f"PainCave login failed ({resp.status}): {text}")
        data = await resp.json()
        self._token = data["token"]
        _LOGGER.debug("PainCave: authenticated successfully")

    async def _get(self, path: str) -> dict | list:
        """GET with automatic re-auth on 401."""
        if self._token is None:
            await self._login()

        session = await self._get_session()
        headers = {"Authorization": f"Bearer {self._token}"}

        resp = await session.get(
            f"{self.url}{path}",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        )

        if resp.status == 401:
            _LOGGER.debug("PainCave: token expired, re-authenticating")
            await self._login()
            headers = {"Authorization": f"Bearer {self._token}"}
            resp = await session.get(
                f"{self.url}{path}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            )

        if resp.status != 200:
            raise UpdateFailed(f"PainCave API error {resp.status} for {path}")

        return await resp.json()

    async def _post(self, path: str) -> dict:
        """POST with automatic re-auth on 401."""
        if self._token is None:
            await self._login()

        session = await self._get_session()
        headers = {"Authorization": f"Bearer {self._token}"}

        resp = await session.post(
            f"{self.url}{path}",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        )

        if resp.status == 401:
            await self._login()
            headers = {"Authorization": f"Bearer {self._token}"}
            resp = await session.post(
                f"{self.url}{path}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            )

        return await resp.json()

    async def _patch(self, path: str) -> dict:
        """PATCH with automatic re-auth on 401."""
        if self._token is None:
            await self._login()

        session = await self._get_session()
        headers = {"Authorization": f"Bearer {self._token}"}

        resp = await session.patch(
            f"{self.url}{path}",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        )

        if resp.status == 401:
            await self._login()
            headers = {"Authorization": f"Bearer {self._token}"}
            resp = await session.patch(
                f"{self.url}{path}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            )

        return await resp.json()

    # ── Data fetch ────────────────────────────────────────────────────────────

    async def _async_update_data(self) -> dict:
        """Fetch saved sensors + live device data from PainCave."""
        try:
            saved_sensors, live = await asyncio.gather(
                self._get("/api/sensors"),
                self._get("/api/ant/"),
            )
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Cannot reach PainCave at {self.url}: {err}") from err

        # Build a map of device_id → live device object
        live_by_id: dict[str, dict] = {
            str(d["id"]): d for d in (live.get("devices") or [])
        }

        return {
            "sensors":      saved_sensors,          # list of saved sensor rows
            "live":         live_by_id,              # device_id → live device
            "ant_scanning": live.get("scanning", False),
            "ant_ready":    live.get("stickReady", False),
            "ant_enabled":  live.get("antEnabled", False),
            "ble_scanning": live.get("bleScanning", False),
            "ble_enabled":  live.get("bleEnabled", False),
        }

    # ── Control helpers (called by switch entities) ───────────────────────────

    async def ant_enable(self) -> None:
        await self._post("/api/ant/enable")
        await self.async_request_refresh()

    async def ant_disable(self) -> None:
        await self._post("/api/ant/disable")
        await self.async_request_refresh()

    async def ant_start(self) -> None:
        await self._post("/api/ant/start")
        await self.async_request_refresh()

    async def ant_stop(self) -> None:
        await self._post("/api/ant/stop")
        await self.async_request_refresh()

    async def ble_enable(self) -> None:
        await self._post("/api/ant/ble/enable")
        await self.async_request_refresh()

    async def ble_disable(self) -> None:
        await self._post("/api/ant/ble/disable")
        await self.async_request_refresh()

    async def ble_start(self) -> None:
        await self._post("/api/ant/ble/start")
        await self.async_request_refresh()

    async def ble_stop(self) -> None:
        await self._post("/api/ant/ble/stop")
        await self.async_request_refresh()

    async def toggle_sensor(self, sensor_id: int) -> None:
        """Toggle a saved sensor's is_active flag."""
        await self._patch(f"/api/sensors/{sensor_id}/toggle")
        await self.async_request_refresh()

    async def async_close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()


import asyncio  # noqa: E402 — imported at bottom to avoid circular issues at module level
