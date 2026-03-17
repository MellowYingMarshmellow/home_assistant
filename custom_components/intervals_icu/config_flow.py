"""Config flow for Intervals ICU integration."""
from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import BASE_URL, DOMAIN

STEP_SCHEMA = vol.Schema({
    vol.Required("athlete_id"): str,
    vol.Required("api_key"):    str,
})


async def _validate_credentials(athlete_id: str, api_key: str) -> str | None:
    """Return None on success or an error key string on failure."""
    auth = aiohttp.BasicAuth("API_KEY", api_key)
    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.get(
                f"{BASE_URL}/athlete/{athlete_id}",
                auth=auth,
                timeout=aiohttp.ClientTimeout(total=10),
            )
            if resp.status == 401:
                return "invalid_auth"
            if resp.status == 404:
                return "invalid_athlete_id"
            if resp.status != 200:
                return "cannot_connect"
            return None
    except aiohttp.ClientError:
        return "cannot_connect"


class IntervalsIcuConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Intervals ICU."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            athlete_id = user_input["athlete_id"].strip()
            api_key    = user_input["api_key"].strip()

            # Prevent duplicate entries for the same athlete
            await self.async_set_unique_id(athlete_id)
            self._abort_if_unique_id_configured()

            error = await _validate_credentials(athlete_id, api_key)
            if error:
                errors["base"] = error
            else:
                return self.async_create_entry(
                    title=f"Intervals ICU ({athlete_id})",
                    data={"athlete_id": athlete_id, "api_key": api_key},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_SCHEMA,
            errors=errors,
            description_placeholders={
                "help": "Find your Athlete ID in your Intervals.icu profile URL (e.g. i12345). "
                        "Generate an API key in Settings → Developer Settings."
            },
        )
