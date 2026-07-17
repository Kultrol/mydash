# mydash 🌟

> **Your personal daily dashboard in the terminal.**  
> Weather, news, and markets — one command, three stacked panels.

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.5.0%20MVP-blue.svg)](https://github.com/Kultrol/mydash/releases/tag/v0.5.0)
[![Release](https://img.shields.io/github/v/release/Kultrol/mydash?label=latest%20release)](https://github.com/Kultrol/mydash/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-MVP-brightgreen.svg)](https://github.com/Kultrol/mydash/releases/tag/v0.5.0)

**mydash** is a friendly command-line daily brief for Python folks who live in the terminal. It pulls live data from public APIs and paints it with Rich so your morning check-in feels quick and clear.

> **Still an MVP** — not a polished 1.0 product. You get a daily **`brief`**, user **`set`** preferences, and two products on a shared core (**CLI: Rich → Typer → core**; **Web: Next.js → FastAPI → core**). Defaults ship out of the box; personalize city, symbols, news category, units, and providers with `mydash set`.

---

## ✨ Demo

Fire it up:

```bash
mydash brief
```

![mydash brief screenshot](docs/assets/brief-screenshot.png)

*Three stacked panels: markets, weather, and headlines.*

![mydash brief demo](docs/assets/brief-demo.gif)

*Short walkthrough of the daily brief in the terminal.*

You’ll get three full-width panels:

| Panel | What you see |
|-------|----------------|
| 📈 **Markets** | Quotes & bars with `$`, ↑/↓ markers, and “As of” times |
| 🌤️ **Weather** | Next six hours for your configured city (metric or imperial) |
| 📰 **Headlines** | A short list; source names are clickable links in supported terminals |

---

## 📋 Requirements

- 🐍 **Python 3.12+**
- 🌐 Network access
- ☁️ Weather & geocoding: [Open-Meteo](https://open-meteo.com/) (**no API key**)
- 🗞️ News: Noozra (**no API key**)
- 📊 Stocks: [Alpaca](https://alpaca.markets/) API key + secret in `.env` (**optional** — only for the markets panel)

---

## 📦 Install

mydash is split into **separate installables** so you can take only what you need:

| Package | What you get | Pulls in |
|---------|--------------|----------|
| **`mydash`** | CLI (`mydash brief`, `mydash set`) | `mydash-core` + Typer + Rich |
| **`mydash-web`** | FastAPI app (`mydash.api.main:app`) | `mydash-core` + FastAPI + Uvicorn |
| **`mydash-core`** | Shared domain (usually transitive) | httpx, Pydantic, platformdirs, dotenv |

The Next.js UI lives in `frontend/` (npm) and talks to **`mydash-web`** over HTTP.

### Option A — CLI only (end users)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install mydash          # or a release wheel from GitHub Releases
mydash brief
```

Published **v0.5.0** monolithic wheel (pre-split) still works from the [Releases page](https://github.com/Kultrol/mydash/releases):

```bash
pip install https://github.com/Kultrol/mydash/releases/download/v0.5.0/mydash-0.5.0-py3-none-any.whl
```

### Option B — Web API only

```bash
pip install mydash-web
uvicorn mydash.api.main:app --reload --port 8000
```

Then run the frontend separately (`cd frontend && npm install && npm run dev`).

### Option C — develop from source (both products)

```bash
git clone https://github.com/Kultrol/mydash.git
cd mydash
uv sync --group dev    # workspace: mydash + mydash-web + mydash-core
```

This monorepo is a **uv workspace**. Packages live under `packages/mydash-{core,cli,web}/`.

---

## 🔐 Environment setup

Weather and news work **with no configuration**. Markets need Alpaca credentials.

1. Create a free account at [Alpaca](https://alpaca.markets/) and generate API keys (paper-trading keys are fine for market data).
2. Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

3. Edit `.env`:

```bash
STOCK_ALPACA_API_KEY_ID=your_alpaca_key_id
STOCK_ALPACA_API_SECRET_KEY=your_alpaca_secret
```

| Variable | Required? | Used for |
|----------|-----------|----------|
| `STOCK_ALPACA_API_KEY_ID` | For markets panel | Alpaca API key ID |
| `STOCK_ALPACA_API_SECRET_KEY` | For markets panel | Alpaca API secret |

- Place `.env` in the directory from which you run `mydash` (the CLI loads it via `python-dotenv` at startup).
- **Never commit `.env`** — it is gitignored. Only `.env.example` (placeholders) is tracked.

If you skip Alpaca keys, you can still run `mydash brief`; weather and headlines should appear, while markets may fail or look empty.

---

## 🚀 Usage

```bash
mydash brief
mydash --help

# Preferences (persisted as JSON via platformdirs)
mydash set                 # hint: use --help or -lo
mydash set -lo             # list all set subcommands
mydash set weather units imperial
mydash set weather city "Austin"
mydash set stocks add GOOG
mydash set news category politics
mydash set show            # dump current config

# Same thing via the module path
python -m mydash.cli.main brief
```

### User config file

Preferences live in a platform-appropriate user config directory (via [platformdirs](https://platformdirs.readthedocs.io/)):

| Platform | Typical path |
|----------|----------------|
| macOS | `~/Library/Application Support/mydash/config.json` |
| Linux | `~/.config/mydash/config.json` (respects `XDG_CONFIG_HOME`) |
| Windows | `%APPDATA%\mydash\config.json` |

The file is created automatically with defaults (Miami, tech news, SPY/AAPL/MSFT, metric units) on first use.

---

## 🔧 Troubleshooting

| Problem | What to try |
|---------|-------------|
| `mydash: command not found` | Activate your venv, or reinstall (`pip install …` / `uv sync`) so the `mydash` entry point is on `PATH` |
| Markets panel empty or errors | Confirm `.env` has both Alpaca vars, keys are valid, and you started the app from a directory that can see that `.env` |
| Wrong city / symbols / units | Run `mydash set show`, then `mydash set weather city …`, `mydash set stocks add …`, or `mydash set weather units …` |
| Config JSON errors | Delete or fix the config file path above; mydash recreates defaults if the file is missing |
| Wrong Python version | Use **3.12+** (`python --version`) |
| Network / API errors | Check connectivity; Open-Meteo and Noozra need outbound HTTPS |

---

## 🏗️ Architecture

**Two products, one shared core package** — presentation never owns providers; core never imports Typer, Rich, FastAPI, or React.

| Product | Install | Stack (outer → inner) |
|---------|---------|------------------------|
| **CLI** | `mydash` | Rich → Typer → `mydash.core` |
| **Web** | `mydash-web` + `frontend/` | Next.js → FastAPI → `mydash.core` |

```mermaid
flowchart LR
    RICH["Rich"]
    TYPER["Typer"]
    API["mydash-web FastAPI"]
    FE["frontend/ Next.js"]
    CORE["mydash-core"]
    RICH --> TYPER --> CORE
    FE -.->|HTTP| API --> CORE
```

| Layer | Role |
|-------|------|
| 🎨 **CLI** | package `mydash` — `mydash.cli` (Rich + Typer) |
| 🌐 **Web** | package `mydash-web` — `mydash.api` + monorepo `frontend/` |
| ⚙️ **Core** | package `mydash-core` — services, models, clients |

Want the deeper map? See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 🌐 Web (development)

Install **`mydash-web`** (or `uv sync` at the monorepo root) and run the Next.js app in `frontend/`.

### Frontend (Next.js)

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Details: [frontend/README.md](frontend/README.md).

### API

```bash
# monorepo
uv run uvicorn mydash.api.main:app --reload --port 8000

# or after: pip install mydash-web
uvicorn mydash.api.main:app --reload --port 8000
```

Point the frontend at the API via `NEXT_PUBLIC_API_BASE_URL` (see `frontend/.env.local.example`).

### Deploy frontend to Vercel

1. Import this GitHub repo in [Vercel](https://vercel.com/) (Hobby plan is free for personal projects — confirm current limits).
2. Set **Root Directory** to `frontend`.
3. Framework preset: Next.js.
4. The API is **not** part of that deploy; host FastAPI separately when you leave local-only mode, then set `NEXT_PUBLIC_API_BASE_URL` and CORS.

---

## 🛠️ Tech stack

| Component | Technology |
|-----------|------------|
| ⌨️ CLI | [Typer](https://typer.tiangolo.com/) |
| 🌈 Terminal UI | [Rich](https://rich.readthedocs.io/) |
| 🌐 HTTP API | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn (`mydash-web`) |
| 🖥️ Web UI | [Next.js](https://nextjs.org/) + [shadcn/ui](https://ui.shadcn.com/) + Tailwind (`frontend/`) |
| 🌍 HTTP client | [httpx](https://www.python-httpx.org/) |
| 📐 Schemas | [Pydantic](https://docs.pydantic.dev/) |
| 📁 Config path | [platformdirs](https://platformdirs.readthedocs.io/) |
| 🔐 Secrets | python-dotenv |
| 🧰 Tooling | [uv](https://docs.astral.sh/uv/) workspace + hatchling |
| 📦 Python packages | `mydash` · `mydash-web` · `mydash-core` |
| ☁️ Frontend host | [Vercel](https://vercel.com/) (`frontend/` root) |

---

## 🧪 Development

```bash
uv sync --group dev
uv run pytest
```

Tests cover clients (providers + factories), services (brief + user config), and CLI paths for `brief` and `set`. Frontend: `cd frontend && npm run build`.

---

## 🔭 Looking ahead

**Today** is a working MVP: daily `brief`, user `set` preferences, three panels, shared `core/` under CLI and API, plus a `frontend/` scaffold for the web UI.

**Version 1.0** means a production-ready *terminal* app you can rely on day to day. FastAPI routes and a live web brief can proceed in parallel on the same services.

### Path to 1.0

- ⌨️ **CLI polish** — flags to override prefs for a single run; optional focused commands (weather / news / stocks) through the service layer  
- 🔌 **Solid data layer** — fix remaining edge cases in clients, consistent request timeouts, cleaner shared HTTP plumbing  
- 🧪 **Tests & automation** — shared fixtures, CI on every push, enough coverage that refactors stay safe  
- 📚 **Docs for a stable release** — keep [CHANGELOG](CHANGELOG.md) current and a command surface that feels intentional for daily use  

### After 1.0 / web track

- 🌐 Add FastAPI presentation layer and wire `frontend/lib/api.ts` to live brief/config routes  
- ⚡ Optional caching for faster repeat views  
- 📅 More dashboard domains over time (calendar, tasks, AI-assisted briefs, and similar)

Layer boundaries today are documented in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 🤖 AI-assisted development

Parts of this codebase were built with help from [Grok Build](https://x.ai/cli) (Cursor and the CLI) and related tooling. Typical uses included:

- 🩹 **Small fixes** — bug fixes, comment cleanups, and other limited changes I could check file by file  
- 🧪 **Quick experiments** — trying CLI layout ideas and how the service layer wires to clients before locking in an approach  
- 🧹 **Tedious refactors** — mechanical work such as import renames or test layout cleanup  
- 📝 **Boilerplate & docs** — starting test files, improving docstrings, and polishing README/architecture notes  

Design decisions and larger features are still reviewed and owned manually. AI-assisted work is meant to speed up the boring parts, not replace judgment on architecture or product direction.

---

## 📄 License

MIT — see [`LICENSE`](LICENSE).

## 🙏 Acknowledgments

- ☁️ [Open-Meteo](https://open-meteo.com/) for weather and geocoding  
- 🐍 Typer, Rich, and the Python CLI community  
- 💡 Inspiration from `wttr.in`, neofetch, and other terminal dashboards  

---

**Built with ❤️ by [Kevin Medina](https://github.com/Kultrol) · Miami, FL**

*v0.5.0 · MVP · happy briefing ☕*
