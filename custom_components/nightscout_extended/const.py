"""Constants for the Nightscout Extended integration."""
DOMAIN = "nightscout_extended"

CONF_URL = "url"
CONF_TOKEN = "token"

DEFAULT_SCAN_INTERVAL = 300  # seconds (5 minutes)

# Nightscout API paths
API_DEVICESTATUS = "/api/v1/devicestatus.json"
API_ENTRIES = "/api/v1/entries.json"
API_TREATMENTS = "/api/v1/treatments.json"

# Treatment event types used to calculate cannula and sensor age.
# These are confirmed for Loop/Trio uploaders. Other uploaders may differ —
# see the README compatibility table.
TREATMENT_CAGE_CHANGE = "Site Change"   # infusion set / cannula change
TREATMENT_SAGE_CHANGE = "Sensor Start"  # CGM sensor insertion

# How far back to search for each treatment type.
# If no matching record is found within the window the sensor is flagged stale.
# CAGE: cannula is typically replaced every 1–4 days; 7-day window gives buffer.
# SAGE: Dexcom G6/G7 sensors last up to 10/15 days; search the full max lifespan.
CAGE_LOOKBACK_DAYS = 7
SAGE_LOOKBACK_DAYS = 15

# Coordinator data keys
KEY_CAGE = "cage"
KEY_CAGE_STALE = "cage_stale"
KEY_CAGE_TIMESTAMP = "cage_timestamp"
KEY_LAST_READING = "last_reading"
KEY_PUMP_BATTERY = "pump_battery"
KEY_PUMP_RESERVOIR = "pump_reservoir"
KEY_PUMP_TIMESTAMP = "pump_timestamp"
KEY_SAGE = "sage"
KEY_SAGE_STALE = "sage_stale"
KEY_SAGE_TIMESTAMP = "sage_timestamp"
