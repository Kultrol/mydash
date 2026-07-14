# Changelog

All notable changes to **mydash** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `UserConfigurationService` and `UserConfig` with JSON persistence via platformdirs
- `mydash set` command tree (weather, stocks, news, geocoding, show) with Rich panels and next-step hints
- Weather forecast unit presets (`metric` | `imperial`) end-to-end (Open-Meteo params + brief display)
- Brief reads city, symbols, news category, units, and providers from user config

### Changed

- Docs (README, architecture) describe configurable prefs instead of hardcoded-only MVP notes

## [0.5.0] — 2026-07-13

### MVP release

This is the first public **MVP** of mydash: a focused terminal demo, not a production-ready daily app. City, news category, and stock symbols remain hardcoded; the only command is `brief`.

### Added

- Daily brief CLI: `mydash brief` with three Rich panels (markets, weather, headlines)
- Three-layer layout: CLI → services → clients
- Weather via Open-Meteo (no API key)
- News via Noozra (no API key)
- Market data via Alpaca (API key + secret in `.env`)
- Installable package with console entry point `mydash`
- GitHub Release artifacts (wheel + sdist) for download and `pip install`

### Known MVP limits

- Configuration (city, symbols, news category) is not user-configurable yet
- Only the `brief` subcommand is exposed
- No stability or uptime guarantees; treat as a demo / learning project on the path to 1.0

[0.5.0]: https://github.com/Kultrol/mydash/releases/tag/v0.5.0
