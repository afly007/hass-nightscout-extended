# Changelog

All notable changes to this project will be documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.4.0] - 2026-03-31

### Added
- **Cannula Last Changed** — timestamp of the last `Site Change` treatment
- **Sensor Last Started** — timestamp of the last `Sensor Start` treatment
- **Pump Last Reported** — timestamp of the last devicestatus entry from the pump
- Renamed "Last Reading" to **CGM Last Reading** for clarity

### Changed
- All four timestamp sensors use `SensorDeviceClass.TIMESTAMP` so HA displays
  them in local time and they can be used directly in automation triggers

## [1.3.0] - 2026-03-31

### Added
- **CGM Last Reading** sensor — timestamp of the most recent blood glucose entry,
  useful for detecting when the CGM has stopped reporting

## [1.2.0] - 2026-03-31

### Added
- CAGE and SAGE sensors now use `device_class: duration`, enabling native unit
  conversion in Home Assistant. Change the display unit between hours and days
  directly from the entity settings UI — no extra sensors or configuration needed.

## [1.1.3] - 2026-03-31

### Fixed
- GitHub Actions not triggering on push — allowlist now uses wildcards
- `manifest.json` key ordering to satisfy hassfest validation

### Added
- `workflow_dispatch` trigger so CI can be run manually from the Actions tab
- Brand assets (`brand/icon.png`, `brand/logo.png`) for HACS
- GitHub repo description and topics for HACS discoverability
- Automated release workflow — pushing a tag now creates the GitHub release automatically
- Dependabot to keep GitHub Actions dependencies up to date

### Changed
- Suppressed Node.js 20 deprecation warning in CI runners

## [1.0.0] - 2026-03-31

### Added
- Initial release
- Cannula Age (CAGE) sensor — hours since last `Site Change` treatment, 7-day lookback
- Sensor Age (SAGE) sensor — hours since last `Sensor Start` treatment, 15-day lookback
- Pump Battery sensor — percentage from device status
- Pump Reservoir sensor — remaining insulin units from device status
- `data_available` attribute on CAGE and SAGE for use in automations
- UI-based configuration via config flow (no YAML required)
