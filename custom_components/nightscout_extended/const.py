DOMAIN = "nightscout_extended"

CONF_URL = "url"
CONF_TOKEN = "token"

DEFAULT_SCAN_INTERVAL = 300  # seconds (5 minutes)

# Nightscout API paths
API_DEVICESTATUS = "/api/v1/devicestatus.json"
API_TREATMENTS = "/api/v1/treatments.json"

# Treatment event types — these are the default Nightscout strings.
# Some uploaders use different strings; users may need to adjust.
TREATMENT_SITE_CHANGE = "Site Change"
TREATMENT_SENSOR_CHANGE = "Sensor Change"

# Sensor keys used internally
SENSOR_CAGE = "cage"
SENSOR_SAGE = "sage"
SENSOR_PUMP_BATTERY = "pump_battery"
SENSOR_PUMP_RESERVOIR = "pump_reservoir"
