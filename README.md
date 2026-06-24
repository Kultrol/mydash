# mydash 🌟

> **Your personal daily dashboard in the terminal.**  
> Beautifully aggregated insights on weather, news, markets, calendar, and AI-powered briefs.

[![Python](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-active%20development-orange)](https://github.com/Kultrol/mydash)

**mydash** is a modern, extensible command-line interface (CLI) dashboard built with Python. It fetches data from multiple public APIs and presents it in a clean, information-dense, and visually appealing way using Rich.

Currently focused on weather with plans to expand into a full daily briefing tool.

## ✨ Current Features (v0.1.0)

- 🌍 **Smart Geocoding** — Enter any city name; automatically resolves to coordinates via Open-Meteo Geocoding API.
- 🌤️ **Weather Dashboard** — Detailed current conditions + forecast using the excellent free [Open-Meteo](https://open-meteo.com/) API.
  - Clean Rich-formatted output (tables, panels, colors)
- 🏗️ **Clean Architecture** — Factory + abstract base + implementation pattern for easy addition of new data sources.
- ⚡ **Fast & Async-ready** — Built on `httpx` for efficient HTTP requests.

### Example

```bash
uv run python -m cli.main cur_weather "Miami"
uv run python -m cli.main cur_weather "Tokyo"
```

## 🚀 Roadmap & Planned Features

- [ ] `daily-brief` command — One command to rule them all (weather + news + markets + calendar + AI summary)
- [ ] 📰 News integration (top headlines, personalized topics)
- [ ] 📊 Financial markets overview (indices, watchlist, crypto?)
- [ ] 📅 Calendar & tasks integration (local iCal, Google Calendar via API, or simple todo)
- [ ] 🤖 AI Post-processing — Use LLMs (local or API) to generate personalized insights, "what matters today", summaries
- [ ] 📍 Reverse geocoding + auto location detection (IP-based or GPS via companion app?)
- [ ] Configuration system (`.env`, TOML config, API keys management)
- [ ] Theming / more Rich components (spinners, live updates, ASCII art weather icons?)
- [ ] Packaging & distribution (`pip install mydash`, Homebrew, etc.)
- [ ] Tests, CI/CD, docs

See [GitHub Projects](https://github.com/Kultrol/mydash/projects) or open issues for detailed user stories and progress.

## 🛠 Tech Stack & Design

| Component     | Technology                  | Purpose                          |
|---------------|-----------------------------|----------------------------------|
| CLI Framework | [Typer](https://typer.tiangolo.com/) | Intuitive commands & help        |
| Terminal UI   | [Rich](https://rich.readthedocs.io/) | Beautiful tables, colors, panels |
| HTTP Client   | [httpx](https://www.python-httpx.org/) | Async-capable API calls         |
| Validation    | [Pydantic](https://docs.pydantic.dev/) | Schemas & settings               |
| Env Vars      | python-dotenv               | Secure credential management     |
| Packaging     | uv + pyproject.toml         | Fast, modern Python tooling      |

**Architecture highlights**:
- `client/` package with pluggable data sources (weather, geocoding, future: news, finance)
- Each domain has `base.py` (abstract), `factory.py`, concrete impl (e.g. `open_meteo.py`), and `schemas.py`
- Easy to add new providers (e.g. WeatherAPI, NewsAPI, Alpha Vantage, etc.)

## 📦 Installation

### 1. Clone & Setup

```bash
git clone https://github.com/Kultrol/mydash.git
cd mydash
```

### 2. Install dependencies (recommended: uv)

```bash
# Install uv if you don't have it: https://docs.astral.sh/uv/getting-started/installation/
uv sync
```

Or with pip:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .
```

### 3. Run it

```bash
# Current weather for a city
uv run python -m cli.main cur_weather "San Francisco"

# Help
uv run python -m cli.main --help
```

> **Note**: No API keys required for current features (Open-Meteo is free & keyless). Future features will support optional keys via `.env`.

## 🧪 Development

```bash
uv run pytest
```

Contributions, ideas, and feedback are welcome! This is a personal learning/experimentation project focused on clean code, good UX in the terminal, and practical data aggregation.

### Adding a new data source

1. Implement the abstract base in `client/<domain>/base.py`
2. Create concrete class in e.g. `client/<domain>/my_provider.py`
3. Register in `factory.py`
4. Add Typer command in `cli/main.py`

## 📄 License

This project is licensed under the MIT License. See `LICENSE` file for details (to be added shortly).

## 🙏 Acknowledgments

- [Open-Meteo](https://open-meteo.com/) for fantastic free weather & geocoding APIs
- The amazing Python CLI community (Typer, Rich authors)
- Inspiration from tools like `wttr.in`, `neofetch`, and various TUI dashboards

---

**Built with ❤️ by [Kevin Medina](https://github.com/Kultrol) • Miami, FL**

*Last updated: June 2026 • Actively iterating*