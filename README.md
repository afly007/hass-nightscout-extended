# Nightscout Extended

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate with hassfest](https://github.com/afly007/hass-nightscout-extended/actions/workflows/hassfest.yml/badge.svg)](https://github.com/afly007/hass-nightscout-extended/actions/workflows/hassfest.yml)
[![Validate with HACS](https://github.com/afly007/hass-nightscout-extended/actions/workflows/hacs.yml/badge.svg)](https://github.com/afly007/hass-nightscout-extended/actions/workflows/hacs.yml)

A custom Home Assistant integration that extends Nightscout with additional sensors beyond the built-in blood glucose reading.

## Sensors

| Sensor | Unit | Description |
|--------|------|-------------|
| Cannula Age (CAGE) | hours | Time since last infusion set change (`Site Change` treatment) |
| Sensor Age (SAGE) | hours | Time since last Dexcom sensor insertion (`Sensor Start` treatment) |
| Pump Battery | % | Pump battery level from device status |
| Pump Reservoir | U | Remaining insulin units in reservoir |

All sensors report a `data_available` attribute (`true`/`false`) that reflects whether a recent record was found in Nightscout within the expected replacement window. This is useful for automations that alert when a change is overdue or data is missing.

## Requirements

- Home Assistant 2023.1.0 or newer
- A running [Nightscout](https://nightscout.github.io/) instance with API v1 enabled

## Installation

### Via HACS (recommended)

1. In Home Assistant, open **HACS → Integrations**
2. Click the three-dot menu (top right) → **Custom repositories**
3. Add `https://github.com/afly007/hass-nightscout-extended` and select **Integration**
4. Search for **Nightscout Extended** and click **Download**
5. Restart Home Assistant

### Manual

1. Download the latest release from [GitHub](https://github.com/afly007/hass-nightscout-extended/releases)
2. Copy the `custom_components/nightscout_extended` folder into your HA `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Nightscout Extended**
3. Enter your Nightscout URL (e.g. `https://yoursite.fly.dev`) and API token

### Generating an API token

In Nightscout, go to **Admin → Auth Tokens** and create a new token with the `readable` role. Using a dedicated read-only token is strongly recommended over using your API secret.

## Uploader compatibility

Treatment event type names vary by uploader. This integration is tested with:

| Uploader | CAGE event type | SAGE event type |
|----------|----------------|----------------|
| Loop / Trio | `Site Change` | `Sensor Start` |

If your uploader uses different event type names, open a [bug report](https://github.com/afly007/hass-nightscout-extended/issues/new?template=bug_report.yml) and include your uploader name.

## Sensor staleness

| Sensor | Lookback window | Flagged stale when... |
|--------|----------------|----------------------|
| CAGE | 7 days | No site change found in last 7 days |
| SAGE | 15 days | No sensor start found in last 15 days |

When a sensor is stale, its state will be **Unavailable** and `data_available` will be `false`.

### Example automation

```yaml
automation:
  - alias: "Alert when CAGE is overdue"
    trigger:
      - platform: numeric_state
        entity_id: sensor.cannula_age
        above: 72
    action:
      - service: notify.mobile_app
        data:
          message: "Cannula has been in for over 72 hours — time for a site change!"
```

## Debugging

If sensors are not populating, enable debug logging by adding the following to `configuration.yaml` and restarting HA:

```yaml
logger:
  logs:
    custom_components.nightscout_extended: debug
```

Check **Settings → System → Logs** for request URLs and API responses.

## Contributing

Pull requests and feature requests are welcome. Please open an issue first to discuss significant changes.

## License

[MIT](LICENSE)
