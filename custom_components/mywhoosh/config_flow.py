"""Config flow for MyWhoosh integration."""
from __future__ import annotations

import uuid

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import ACTION_LOGIN, DOMAIN, LOGIN_URL, PLATFORM

STEP_SCHEMA = vol.Schema({
    vol.Required("username"): str,
    vol.Required("password"): str,
})


async def _validate_credentials(username: str, password: str) -> tuple[str, str] | str:
    """Try to log in.

    Returns (whoosh_id, access_token) on success or an error key string on failure.
    """
    payload = {
        "Username":      username,
        "Password":      password,
        "Platform":      PLATFORM,
        "Action":        ACTION_LOGIN,
        "CorrelationId": str(uuid.uuid4()),
        "DeviceId":      str(uuid.uuid4()),
        "Authorization": "",
    }
    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                LOGIN_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=15),
            )
    except aiohttp.ClientError:
        return "cannot_connect"

    if resp.status != 200:
        return "cannot_connect"

    data = await resp.json()
    if not data.get("Success"):
        return "invalid_auth"

    whoosh_id    = data.get("WhooshId", "")
    access_token = data.get("AccessToken", "")
    if not whoosh_id or not access_token:
        return "invalid_auth"

    return whoosh_id, access_token


class MyWhooshConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            username = user_input["username"].strip()
            password = user_input["password"]

            result = await _validate_credentials(username, password)

            if isinstance(result, str):
                errors["base"] = result
            else:
                whoosh_id, _ = result

                await self.async_set_unique_id(whoosh_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"MyWhoosh ({username})",
                    data={
                        "username":  username,
                        "password":  password,
                        "whoosh_id": whoosh_id,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_SCHEMA,
            errors=errors,
        )
