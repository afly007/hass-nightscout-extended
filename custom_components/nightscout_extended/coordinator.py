"""DataUpdateCoordinator for Nightscout Extended."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_DEVICESTATUS,
    API_TREATMENTS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    TREATMENT_SENSOR_CHANGE,
    TREATMENT_SITE_CHANGE,
)

_LOGGER = logging.getLogger(__name__)


class NightscoutExtendedCoordinator(DataUpdateCoordinator):
    """Fetches and caches all Nightscout data used by sensors."""

    def __init__(self, hass: HomeAssistant, url: str, token: str) -> None:
        self.url = url.rstrip("/")
        self.token = token
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _auth_params(self) -> dict:
        """Return query params for authentication."""
        if self.token:
            return {"token": self.token}
        return {}

    async def _fetch_json(self, session: aiohttp.ClientSession, path: str, params: dict) -> list | dict:
        """GET a Nightscout API endpoint and return parsed JSON."""
        params = {**self._auth_params(), **params}
        url = f"{self.url}{path}"
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                raise UpdateFailed(f"Nightscout returned HTTP {resp.status} for {path}")
            return await resp.json()

    @staticmethod
    def _hours_since(timestamp_str: str | None) -> float | None:
        """Return hours elapsed since an ISO-8601 timestamp string."""
        if not timestamp_str:
            return None
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            delta = datetime.now(timezone.utc) - dt
            return round(delta.total_seconds() / 3600, 1)
        except (ValueError, TypeError):
            _LOGGER.warning("Could not parse timestamp: %s", timestamp_str)
            return None

    # ------------------------------------------------------------------
    # Main update method — called by HA on the update interval
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict:
        """Fetch latest data from Nightscout and return a unified dict."""
        async with aiohttp.ClientSession() as session:
            # Fetch device status (pump battery, reservoir)
            devicestatus = await self._fetch_json(
                session, API_DEVICESTATUS, {"count": 1}
            )

            # Fetch last site change (CAGE)
            site_changes = await self._fetch_json(
                session,
                API_TREATMENTS,
                {"find[eventType]": TREATMENT_SITE_CHANGE, "count": 1},
            )

            # Fetch last sensor change (SAGE)
            sensor_changes = await self._fetch_json(
                session,
                API_TREATMENTS,
                {"find[eventType]": TREATMENT_SENSOR_CHANGE, "count": 1},
            )

        # --- Parse pump data ---
        pump_battery = None
        pump_reservoir = None
        if devicestatus and isinstance(devicestatus, list):
            status = devicestatus[0]
            pump = status.get("pump", {})
            battery = pump.get("battery", {})
            pump_battery = battery.get("percent") or battery.get("voltage")
            pump_reservoir = pump.get("reservoir")

        # --- Parse CAGE ---
        cage_hours = None
        if site_changes and isinstance(site_changes, list):
            last_site = site_changes[0]
            cage_hours = self._hours_since(
                last_site.get("created_at") or last_site.get("timestamp")
            )

        # --- Parse SAGE ---
        sage_hours = None
        if sensor_changes and isinstance(sensor_changes, list):
            last_sensor = sensor_changes[0]
            sage_hours = self._hours_since(
                last_sensor.get("created_at") or last_sensor.get("timestamp")
            )

        return {
            "pump_battery": pump_battery,
            "pump_reservoir": pump_reservoir,
            "cage": cage_hours,
            "sage": sage_hours,
        }
