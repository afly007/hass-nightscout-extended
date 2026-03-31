"""Config flow for Nightscout Extended."""
from __future__ import annotations

import logging

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_TOKEN, CONF_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Optional(CONF_TOKEN, default=""): str,
    }
)


async def _validate_connection(hass: HomeAssistant, data: dict) -> None:
    """Attempt a real API call to verify the URL and token are valid.

    Raises:
        ValueError: with a translation key describing the error.
        aiohttp.ClientError: on network / connection failures.
    """
    base_url = data[CONF_URL].rstrip("/")
    url = f"{base_url}/api/v1/devicestatus.json"
    params: dict = {"count": 1}
    if data.get(CONF_TOKEN):
        params["token"] = data[CONF_TOKEN]

    session = async_get_clientsession(hass)
    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
        if resp.status == 401:
            raise ValueError("invalid_token")
        if resp.status != 200:
            raise ValueError("cannot_connect")
        result = await resp.json()
        if not isinstance(result, list):
            raise ValueError("cannot_connect")


class NightscoutExtendedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the UI setup dialog for Nightscout Extended."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_URL] = user_input[CONF_URL].rstrip("/")

            try:
                await _validate_connection(self.hass, user_input)
            except ValueError as exc:
                errors["base"] = str(exc)
            except aiohttp.ClientConnectionError:
                errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error validating Nightscout connection")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_URL])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_URL],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
