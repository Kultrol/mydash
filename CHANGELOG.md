# Changelog

All notable changes to **mydash** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0] — 2026-08-31

First stable release. mydash is a terminal application, it works from any
directory once installed, and the surface documented here is one I intend to keep
working.

### Added

- **Continuous integration.** Tests run on Linux and macOS across Python 3.12,
  3.13, and 3.14 on every push and pull request, alongside ruff and a job that
  builds the wheel and runs it from a neutral directory
- **A dependency-floor job.** Dependencies are published as `>=` but were only
  ever exercised against `uv.lock`; CI now resolves with `--resolution
  lowest-direct` and runs the full suite against the oldest declared versions
- **Release automation.** Pushing a `v*` tag builds the artifacts and publishes a
  GitHub Release with that version's changelog as the notes. It refuses to
  publish when the tag and the packaged version disagree
- **Dependabot** for Python dependencies and workflow actions
- `SECURITY.md`, including what mydash does and does not do with your data:
  no telemetry, and credentials are never written to the database or into a
  cache key

### Changed

- **The version is single-sourced** from `src/mydash/__init__.py`, which is what
  `mydash --version` reports. It used to live there *and* in `pyproject.toml`,
  maintained by hand, so drift meant the CLI could lie about its own version
- **Classifiers now match what is verified**: Production/Stable, and Linux +
  macOS rather than "OS Independent". Windows is untested and the credentials
  file's `0600` permissions do not restrict access there
- The sdist no longer ships `docs/assets`; an unreferenced demo GIF was 1.4 MB of
  a 1.5 MB download, now 92 KB

### Fixed

- **`mydash brief --only <typo>` no longer crashes.** It raised a bare
  `ValueError` from inside `BriefService`, which surfaced as a generic "Something
  went wrong" panel advising you to run `mydash config show` — unrelated to the
  mistake — and exited 1. It is now a usage error naming the valid panels, with
  exit code 2, raised before any fetch begins
- **`.python-version` was tracked *and* gitignored**, pinning 3.14 while
  `requires-python` says `>=3.12`, so a fresh clone went looking for 3.14. It is
  no longer tracked

## [0.6.0] — 2026-08-31

mydash is a terminal app and stays one — the web front end the layering was
originally justified by is off the roadmap. This release is about making the
CLI worth living in: it starts faster, degrades gracefully, and says what went
wrong.

### Added

- `mydash init` — setup wizard for city, units, category, and tickers, offering
  a choice between same-named places. Every answer is also a flag, so it works
  non-interactively
- `mydash doctor` — checks storage, credentials, and provider reachability
- `mydash weather` / `news` / `stocks` — one panel each, with per-run overrides
  (`--city`, `--category`, `--symbols`) that leave saved preferences alone
- `mydash config show | path | reset` and `mydash cache info | clear`
- `mydash set stocks list`
- `brief` flags: `--refresh`, `--only`, `--compact`, `--json`
- Global `--version`, `--no-color`, and `--debug`
- Bare `mydash` shows your current setup and the command list, without touching
  the network
- Response caching in SQLite — a repeat brief is roughly 4× faster. Freshness
  windows: geocoding 30d, weather 15m, news 10m, quotes 60s
- HTTP retries with exponential backoff and jitter, honouring `Retry-After`
- `MYDASH_DB_PATH` to point mydash at a throwaway database

### Changed

- **Preferences moved from a JSON file to SQLite.** One setting is now one
  upsert instead of a rewrite of the whole file. An existing `config.json` is
  imported on first run and renamed to `config.json.migrated`
- **Weather is fetched in the forecast location's own timezone.** "The next six
  hours" now means six hours *there*
- **The brief survives a provider failing.** Domains are fetched concurrently
  and independently; a panel that could not load says why, and the others still
  render
- **Stocks return partial results.** A ticker Alpaca has no data for is listed
  as missing instead of discarding the whole batch
- **News skips malformed articles** rather than failing the panel, and returns
  headlines newest-first, deduplicated, and capped
- **Geocoding returns ranked places** with region and country, so `set weather
  city` shows which Springfield it matched
- Clients are stateless: `search()`, `fetch_forecast()`, `fetch_headlines()`,
  `fetch_quotes()` / `fetch_bars()` replace the two-phase `set_*` / `get_*` pair
- The brief no longer re-geocodes on every run — coordinates were already saved
- One HTTP client per brief, so requests share a connection pool
- Panels redesigned around a shared theme: percentage change, today's high/low
  and daylight, relative headline ages, and ▲▼▬ markers that work without colour
- Missing Alpaca credentials produce a message naming the variables and pointing
  at `.env.example`
- Errors print a short panel with a next step; `--debug` restores tracebacks

### Removed

- `rich.traceback.install(show_locals=True)` firing at users for ordinary
  mistakes
- The `Missing*Error` classes that existed only to police client call order
- Unused `**config` kwargs on the client factories; `get_stock_client` no longer
  accepts `""` or `None` as aliases for `alpaca`

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

[1.0.0]: https://github.com/Kultrol/mydash/releases/tag/v1.0.0
[0.6.0]: https://github.com/Kultrol/mydash/releases/tag/v0.6.0
[0.5.0]: https://github.com/Kultrol/mydash/releases/tag/v0.5.0
