"""Config flow for PainCave."""
from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_URL, CONF_EMAIL, CONF_PASSWORD

STEP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL,      description={"suggested_value": "http://192.168.1.100:5000"}): str,
        vol.Required(CONF_EMAIL):   str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def _validate_connection(hass: HomeAssistant, data: dict) -> str | None:
    """Try to authenticate. Returns error key string on failure, None on success."""
    url = data[CONF_URL].rstrip("/")
    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"{url}/api/auth/login",
                json={"email": data[CONF_EMAIL], "password": data[CONF_PASSWORD]},
                timeout=aiohttp.ClientTimeout(total=10),
            )
            if resp.status == 401:
                return "invalid_auth"
            if resp.status != 200:
                return "cannot_connect"
            body = await resp.json()
            if "token" not in body:
                return "cannot_connect"
    except aiohttp.ClientConnectionError:
        return "cannot_connect"
    except Exception:  # noqa: BLE001
        return "unknown"
    return None


class PainCaveConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial setup UI."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            user_input[CONF_URL] = user_input[CONF_URL].rstrip("/")
            error = await _validate_connection(self.hass, user_input)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(user_input[CONF_URL])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"PainCave ({user_input[CONF_URL]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_SCHEMA,
            errors=errors,
        )
