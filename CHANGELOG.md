# Changelog

All notable changes to this project will be documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.3.0] - 2026-03-31

### Added
- **Last Reading** sensor — reports the timestamp of the most recent CGM value
  as a `datetime`. Use this to detect stale data when the CGM stops reporting.
  Example automation trigger: `now() - states('sensor.last_reading') > 00:15:00`

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
