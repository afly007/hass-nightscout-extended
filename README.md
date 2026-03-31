# Nightscout Extended — Home Assistant Integration

A custom HACS integration that extends the built-in Nightscout integration with additional sensors:

- **CAGE** — Cannula age in hours
- **SAGE** — Sensor age in hours
- **Pump Battery** — Pump battery percentage
- **Pump Reservoir** — Remaining insulin units

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → click the three-dot menu → **Custom repositories**
3. Add your repository URL and select **Integration** as the category
4. Search for "Nightscout Extended" and install it
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/nightscout_extended` folder into your HA `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Nightscout Extended"
3. Enter your Nightscout URL (e.g. `https://yoursite.herokuapp.com`) and API token

## Nightscout API Token

Generate a read-only token in Nightscout under **Admin** → **Auth Tokens**.

## Notes

- CAGE is calculated from the last `Site Change` treatment
- SAGE is calculated from the last `Sensor Change` treatment
- Pump battery and reservoir are read from `devicestatus`
- Data is refreshed every 5 minutes by default

## Requirements

- Home Assistant 2023.1.0 or newer
- Nightscout instance with API v1 enabled
