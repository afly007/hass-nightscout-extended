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
    API_ENTRIES,
    API_TREATMENTS,
    CAGE_LOOKBACK_DAYS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    KEY_CAGE,
    KEY_CAGE_STALE,
    KEY_LAST_READING,
    KEY_PUMP_BATTERY,
    KEY_PUMP_RESERVOIR,
    KEY_SAGE,
    KEY_SAGE_STALE,
    SAGE_LOOKBACK_DAYS,
    TREATMENT_CAGE_CHANGE,
    TREATMENT_SAGE_CHANGE,
)

_LOGGER = logging.getLogger(__name__)


class NightscoutExtendedCoordinator(DataUpdateCoordinator[dict]):
    """Fetches and caches all Nightscout data used by sensors."""

    def __init__(self, hass: HomeAssistant, url: str, token: str) -> None:
        """Initialise the coordinator with the Nightscout URL and API token."""
        self.url = url.rstrip("/")
        self.token = token
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_url(self, path: str, params: dict) -> str:
        """Build a URL preserving bracket notation in query parameter keys.

        aiohttp's ``params=`` argument percent-encodes ``[`` and ``]`` into
        ``%5B`` / ``%5D``, which Nightscout's MongoDB-style query API does not
        recognise. We therefore build the query string manually, encoding only
        the *values* while leaving the *keys* untouched.
        """
        parts: list[str] = []
        if self.token:
            parts.append(f"token={quote(self.token, safe='')}")
        for key, value in params.items():
            parts.append(f"{key}={quote(str(value), safe='-.:T')}")
        full_url = f"{self.url}{path}?{'&'.join(parts)}"
        _LOGGER.debug(
            "Nightscout request: %s",
            full_url.replace(self.token, "***") if self.token else full_url,
        )
        return full_url

    async def _fetch_json(
        self, session: aiohttp.ClientSession, path: str, params: dict
    ) -> list | dict:
        """GET a Nightscout API endpoint and return the parsed JSON body."""
        url = self._build_url(path, params)
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                raise UpdateFailed(
                    f"Nightscout returned HTTP {resp.status} for {path}"
                )
            data = await resp.json()
            _LOGGER.debug("Nightscout response for %s: %s", path, data)
            return data

    @staticmethod
    def _parse_timestamp(timestamp_str: str | None) -> datetime | None:
        """Parse an ISO-8601 timestamp string into a timezone-aware datetime."""
        if not timestamp_str:
            return None
        try:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            _LOGGER.warning("Could not parse Nightscout timestamp: %s", timestamp_str)
            return None

    @staticmethod
    def _hours_since(timestamp_str: str | None) -> float | None:
        """Return decimal hours elapsed since an ISO-8601 timestamp string."""
        if not timestamp_str:
            return None
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            delta = datetime.now(timezone.utc) - dt
            return round(delta.total_seconds() / 3600, 1)
        except (ValueError, TypeError):
            _LOGGER.warning("Could not parse Nightscout timestamp: %s", timestamp_str)
            return None

    @staticmethod
    def _lookback_date_str(days: int) -> str:
        """Return an ISO-8601 UTC date string for ``days`` ago."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return cutoff.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # ------------------------------------------------------------------
    # Main update — called by HA on the configured interval
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict:
        """Fetch the latest data from Nightscout and return a unified dict."""
        async with aiohttp.ClientSession() as session:
            devicestatus = await self._fetch_json(
                session, API_DEVICESTATUS, {"count": 1}
            )

            # Latest CGM entry — used to detect stale readings
            entries = await self._fetch_json(
                session, API_ENTRIES, {"count": 1}
            )

            # Cannula age — infusion sets are typically replaced every 1–4 days
            cage_results = await self._fetch_json(
                session,
                API_TREATMENTS,
                {
                    "find[eventType]": TREATMENT_CAGE_CHANGE,
                    "find[created_at][$gte]": self._lookback_date_str(CAGE_LOOKBACK_DAYS),
                    "count": 1,
                },
            )

            # Sensor age — Dexcom sensors last up to 15 days
            sage_results = await self._fetch_json(
                session,
                API_TREATMENTS,
                {
                    "find[eventType]": TREATMENT_SAGE_CHANGE,
                    "find[created_at][$gte]": self._lookback_date_str(SAGE_LOOKBACK_DAYS),
                    "count": 1,
                },
            )

        # --- Last CGM reading timestamp ---
        last_reading: datetime | None = None
        if entries and isinstance(entries, list):
            entry = entries[0]
            # Prefer the ISO string; fall back to the Unix ms timestamp
            last_reading = self._parse_timestamp(entry.get("dateString"))
            if last_reading is None and entry.get("date"):
                try:
                    last_reading = datetime.fromtimestamp(
                        entry["date"] / 1000, tz=timezone.utc
                    )
                except (ValueError, TypeError, OSError):
                    _LOGGER.warning("Could not parse entry date field: %s", entry.get("date"))

        # --- Pump data (battery + reservoir) ---
        pump_battery: float | None = None
        pump_reservoir: float | None = None
        if devicestatus and isinstance(devicestatus, list):
            pump = devicestatus[0].get("pump", {})
            battery = pump.get("battery", {})
            pump_battery = battery.get("percent") or battery.get("voltage")
            pump_reservoir = pump.get("reservoir")

        # --- Cannula age ---
        # ``cage_stale`` is True when no record was found in the lookback window,
        # indicating that the data is missing or overdue in Nightscout.
        cage_hours: float | None = None
        cage_stale = True
        if cage_results and isinstance(cage_results, list):
            ts = cage_results[0].get("created_at") or cage_results[0].get("timestamp")
            cage_hours = self._hours_since(ts)
            cage_stale = cage_hours is None

        # --- Sensor age ---
        sage_hours: float | None = None
        sage_stale = True
        if sage_results and isinstance(sage_results, list):
            ts = sage_results[0].get("created_at") or sage_results[0].get("timestamp")
            sage_hours = self._hours_since(ts)
            sage_stale = sage_hours is None

        return {
            KEY_CAGE: cage_hours,
            KEY_CAGE_STALE: cage_stale,
            KEY_LAST_READING: last_reading,
            KEY_PUMP_BATTERY: pump_battery,
            KEY_PUMP_RESERVOIR: pump_reservoir,
            KEY_SAGE: sage_hours,
            KEY_SAGE_STALE: sage_stale,
        }
