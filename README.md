# mydash 🌟

> **Your personal daily dashboard in the terminal.**  
> Weather, news, markets, and eventually calendar and AI-powered briefs — all in one place.

[![Python](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-active%20development-orange)](https://github.com/Kultrol/mydash)

**mydash** is a command-line dashboard built with Python. It pulls data from public APIs and presents it in the terminal using Rich. The goal is a **production-ready three-layer application** — presentation, orchestration, and data — with clear boundaries invested in early so the CLI can grow without costly rewrites later.

> ⚠️ **Active development:** APIs, commands, configuration, and project layout are all evolving. Expect breaking changes.

---

## 📍 Status

### What you can try today (v0.1)

| Area | State |
|------|--------|
| 🌍 Geocoding + weather | Open-Meteo integration; forecast day-boundary handling in place; provider + factory tests |
| 📰 News headlines | Noozra integration; replace-on-refetch cache; category still hardcoded; provider + factory tests |
| 📊 Stock quotes & bars | Alpaca integration; shared HTTP client with timeout; requires `.env` keys; provider + factory tests |
| 🔌 Data layer | `HttpApiClient` centralizes HTTP; providers under `client/*/providers/`; domain errors evolving |
| 📋 CLI / `brief` | Typer commands call client factories directly and print models; `brief` chains weather → news → stocks |
| 🧪 Tests | Client provider/factory coverage for each domain; CLI smoke tests; shared fixtures still incomplete |

### What we're building toward

A stable terminal app where commands stay thin, business logic lives in a services layer, and the client layer focuses on provider APIs and parsing. Presentation (Rich tables and panels) stays separate from data fetching.

The **data layer** is the furthest along. Next focus is the **MVP of orchestration** (services + config) and the **MVP of presentation** (commands + renderers), then deeper refactors once those pieces work end-to-end.

---

## 🏗️ Architecture

Target shape — three layers, one direction of dependency:

```mermaid
flowchart LR
    CLI["Presentation: Typer + Rich"]
    SVC["Orchestration: services + config"]
    DATA["Data: client providers"]
    CLI --> SVC --> DATA
```

| Layer | Responsibility |
|-------|----------------|
| **Presentation** | Commands, flags, terminal layout — no HTTP or provider parsing |
| **Orchestration** | Multi-step flows, user settings, brief aggregation, DTOs |
| **Data** | Factories, protocols, API calls, schemas per domain (geocoding, weather, news, stocks) |

Each data domain follows a factory + protocol + provider implementation pattern so new sources can be added without rewriting the stack.

### Current shape (today)

The CLI still calls client factories directly. `services/`, `cli/commands/`, and `cli/renderers/` exist as package placeholders for the next MVPs — they are not wired up yet.

```mermaid
flowchart LR
    CLI["cli/main.py"]
    Factories["client/*/factory.py"]
    Providers["client/*/providers/*"]
    HttpApi["client/http_api"]
    CLI --> Factories --> Providers --> HttpApi
```

| Piece | Location | Notes |
|-------|----------|-------|
| **Shared HTTP** | `client/http_api/` | `HttpApiClient.make_request()` for all providers |
| **Providers** | `client/<domain>/providers/<name>/` | Open-Meteo, Noozra, Alpaca |
| **Factories** | `client/<domain>/factory.py` | One factory per domain |
| **CLI** | `cli/main.py` | Commands + `load_dotenv()` at bootstrap |

More detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 🛠 Tech stack

| Component | Technology | Role |
|-----------|------------|------|
| CLI | [Typer](https://typer.tiangolo.com/) | Commands and help |
| Terminal UI | [Rich](https://rich.readthedocs.io/) | Tables, panels, color |
| HTTP | [httpx](https://www.python-httpx.org/) | Provider API calls |
| Schemas | [Pydantic](https://docs.pydantic.dev/) | Models, settings, DTOs |
| Secrets | python-dotenv | `.env` for API keys |
| Tooling | [uv](https://docs.astral.sh/uv/) + hatchling | Install, run, package |

Likely additions as the CLI matures: TOML user config, broader test fixtures, coverage reporting, and CI.

---

## 📦 Installation

```bash
git clone https://github.com/Kultrol/mydash.git
cd mydash
```

Optional — stock data requires Alpaca credentials:

```bash
cp .env.example .env
# Add STOCK_ALPACA_API_KEY_ID and STOCK_ALPACA_API_SECRET_KEY
```

```bash
# Install uv: https://docs.astral.sh/uv/getting-started/installation/
uv sync
```

Or with pip: `python -m venv .venv`, activate, then `pip install -e .`.

Open-Meteo (geocoding and weather) needs no API key. Commands and flags may change between releases while the project is in active development.

---

## Usage

Under the **current application regime**, these commands are available:

```bash
uv run python -m mydash.cli.main weather
uv run python -m mydash.cli.main news
uv run python -m mydash.cli.main stocks    # requires .env Alpaca keys
uv run python -m mydash.cli.main brief
uv run python -m mydash.cli.main --help
```

Output is largely raw model dumps for now — richer Rich layouts land with the presentation MVP. City, news category, and stock symbols are still hardcoded. If something fails, check that dependencies are installed (`uv sync`) and that stock keys are set when using `stocks` or `brief`.

---

## 🔭 Looking ahead

Direction of travel is intentional, though priorities and sequencing may shift as the project evolves.

**How work is paced:** ship an **MVP of each core component** before deep refactors of that component. In practice that means getting the initial **service / orchestration** path and the **CLI / UI** path working end-to-end first, then refactoring, hardening, and polishing once those layers exist. Broad cleanup is not a gate that blocks the first useful version of a layer.

Themes we're steering toward:

- **Orchestration** — domain services, brief aggregation, config-driven inputs instead of hardcodes
- **Presentation** — thin commands and Rich renderers instead of printing models
- **Quality follow-through** — tests, errors, and client hygiene after each MVP; among later refactors, shared fixtures for client tests so sample payloads and helpers live in one place
- **Longer horizon** — more dashboard domains (calendar, tasks, AI-assisted briefs, and so on) and eventually other interfaces that reuse the same orchestration

How new domains get added (client → service → renderer → brief) will be documented properly once the three-layer CLI is stable. Until then, treat the multi-domain future as vision more than a fixed guide.

---

## 🧪 Development

```bash
uv sync --group dev
uv run pytest
```

Client tests cover geocoding, weather, news, and stocks (factories and providers). There is a small CLI smoke path. Shared fixtures in `test/conftest.py` are still mostly stubs — provider tests currently own their own sample data.

Contributions, ideas, and feedback are welcome. This is a personal project — I'm learning as I go — focused on clean structure, good terminal UX, and reliable data aggregation.

---

## AI-assisted development

Parts of this codebase were built with [Grok Build](https://x.ai/cli) — in the Cursor editor and on the command line, using models including Grok 4.5 and earlier Cursor-hosted Grok variants. That work includes small fixes, comments, `TODO` markers, and targeted patches. Design and larger features are reviewed manually. AI-assisted changes land on `grok/*` branches before merge and `pytest`.

---

## 📄 License

MIT — see [`LICENSE`](LICENSE).

## 🙏 Acknowledgments

- [Open-Meteo](https://open-meteo.com/) for free weather and geocoding APIs
- Typer and Rich maintainers and the Python CLI community
- Inspiration from `wttr.in`, neofetch, and terminal dashboards

---

**Built with ❤️ by [Kevin Medina](https://github.com/Kultrol) · Miami, FL**

*Last updated: July 2026 · Actively iterating*
