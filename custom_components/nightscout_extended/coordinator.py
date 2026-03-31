"""DataUpdateCoordinator for Nightscout Extended."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_DEVICESTATUS,
    API_TREATMENTS,
    CAGE_LOOKBACK_DAYS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SAGE_LOOKBACK_DAYS,
    TREATMENT_CAGE_CHANGE,
    TREATMENT_SAGE_CHANGE,
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

    def _build_url(self, path: str, params: dict) -> str:
        """Build a URL with bracket-notation query params left unencoded.

        aiohttp's params= argument percent-encodes '[' and ']' into %5B/%5D,
        which Nightscout's MongoDB-style API does not recognise. We therefore
        build the query string manually, only encoding param *values*.
        """
        parts = []
        if self.token:
            parts.append(f"token={quote(self.token, safe='')}")
        for key, value in params.items():
            # Keys are trusted bracket-notation strings — leave them as-is.
            # Values are encoded to handle spaces, special characters, etc.
            parts.append(f"{key}={quote(str(value), safe=':')}")
        query_string = "&".join(parts)
        full_url = f"{self.url}{path}?{query_string}"
        safe_url = full_url.replace(self.token, "***") if self.token else full_url
        _LOGGER.warning("Nightscout request URL: %s", safe_url)
        return full_url

    async def _fetch_json(self, session: aiohttp.ClientSession, path: str, params: dict) -> list | dict:
        """GET a Nightscout API endpoint and return parsed JSON."""
        url = self._build_url(path, params)
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                raise UpdateFailed(
                    f"Nightscout returned HTTP {resp.status} for {path}"
                )
            data = await resp.json()
            _LOGGER.warning("Nightscout [%s] → %s", path, data)
            return data

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

    @staticmethod
    def _lookback_date_str(days: int) -> str:
        """Return an ISO-8601 date string for the given number of days ago (UTC)."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return cutoff.strftime("%Y-%m-%dT%H:%M:%S.000Z")

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

            # Fetch last cannula change (CAGE) — typically replaced every 1–4 days
            cage_results = await self._fetch_json(
                session,
                API_TREATMENTS,
                {
                    "find[eventType]": TREATMENT_CAGE_CHANGE,
                    "find[created_at][$gte]": self._lookback_date_str(CAGE_LOOKBACK_DAYS),
                    "count": 1,
                },
            )

            # Fetch last sensor start (SAGE) — Dexcom sensor lasts up to 15 days
            sage_results = await self._fetch_json(
                session,
                API_TREATMENTS,
                {
                    "find[eventType]": TREATMENT_SAGE_CHANGE,
                    "find[created_at][$gte]": self._lookback_date_str(SAGE_LOOKBACK_DAYS),
                    "count": 1,
                },
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
        # cage_stale=True means no cannula change was found within the lookback
        # window, which likely indicates missing data in Nightscout.
        cage_hours = None
        cage_stale = True
        if cage_results and isinstance(cage_results, list):
            last_cage = cage_results[0]
            cage_hours = self._hours_since(
                last_cage.get("created_at") or last_cage.get("timestamp")
            )
            cage_stale = cage_hours is None

        # --- Parse SAGE ---
        sage_hours = None
        sage_stale = True
        if sage_results and isinstance(sage_results, list):
            last_sage = sage_results[0]
            sage_hours = self._hours_since(
                last_sage.get("created_at") or last_sage.get("timestamp")
            )
            sage_stale = sage_hours is None

        return {
            "pump_battery": pump_battery,
            "pump_reservoir": pump_reservoir,
            "cage": cage_hours,
            "cage_stale": cage_stale,
            "sage": sage_hours,
            "sage_stale": sage_stale,
        }
