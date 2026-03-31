DOMAIN = "nightscout_extended"

CONF_URL = "url"
CONF_TOKEN = "token"

DEFAULT_SCAN_INTERVAL = 300  # seconds (5 minutes)

# Nightscout API paths
API_DEVICESTATUS = "/api/v1/devicestatus.json"
API_TREATMENTS = "/api/v1/treatments.json"

# Treatment event types — confirmed for this setup.
TREATMENT_CAGE_CHANGE = "Site Change"    # infusion set / cannula change
TREATMENT_SAGE_CHANGE = "Sensor Start"   # CGM sensor insertion

# How far back to search for CAGE/SAGE treatments (days).
# Sensors older than this are considered missing/stale in Nightscout.
CAGE_SAGE_LOOKBACK_DAYS = 16

# Sensor keys used internally
SENSOR_CAGE = "cage"
SENSOR_SAGE = "sage"
SENSOR_PUMP_BATTERY = "pump_battery"
SENSOR_PUMP_RESERVOIR = "pump_reservoir"
