"""``mydash set`` command tree for user configuration."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from typing import Any

import typer
from rich.console import Console, Group
from rich.json import JSON
from rich.panel import Panel
from rich.text import Text

from mydash.services.user_config import (
    KNOWN_GEOCODING_PROVIDERS,
    KNOWN_NEWS_PROVIDERS,
    KNOWN_STOCK_PROVIDERS,
    KNOWN_WEATHER_PROVIDERS,
    KNOWN_WEATHER_UNITS,
    UserConfigurationService,
)

console = Console()

set_app = typer.Typer(
    help="⚙️  Update mydash user preferences.",
    no_args_is_help=False,
)
weather_app = typer.Typer(
    help="🌤️  Weather-related preferences (city, units, provider).",
    no_args_is_help=False,
)
stocks_app = typer.Typer(
    help="📈  Stocks-related preferences (symbols, provider).",
    no_args_is_help=False,
)
news_app = typer.Typer(
    help="📰  News-related preferences (category, provider).",
    no_args_is_help=False,
)
geocoding_app = typer.Typer(
    help="📍  Geocoding-related preferences (provider).",
    no_args_is_help=False,
)

set_app.add_typer(weather_app, name="weather")
set_app.add_typer(stocks_app, name="stocks")
set_app.add_typer(news_app, name="news")
set_app.add_typer(geocoding_app, name="geocoding")

SET_OPTIONS: list[tuple[str, str]] = [
    ("🌤️", "weather city <city>"),
    ("🌤️", "weather units <metric|imperial>"),
    ("🌤️", "weather provider <name>"),
    ("📈", "stocks add <symbol>"),
    ("📈", "stocks remove <symbol>"),
    ("📈", "stocks provider <name>"),
    ("📰", "news category <category>"),
    ("📰", "news provider <name>"),
    ("📍", "geocoding provider <name>"),
    ("⚙️", "show"),
]


def _fmt_choices(values: frozenset[str]) -> str:
    return ", ".join(sorted(values))


def _config_service() -> UserConfigurationService:
    return UserConfigurationService()


def _panel(
    body: Any,
    *,
    title: str,
    border_style: str,
) -> None:
    console.print(
        Panel(
            body,
            title=title,
            border_style=border_style,
            title_align="left",
            padding=(0, 1),
        )
    )


def _success(message: str, *, title: str = "✅ Success") -> None:
    _panel(Text.from_markup(message), title=title, border_style="bright_green")


def _error(message: str) -> None:
    _panel(
        Text.from_markup(f"[bright_white]{message}[/bright_white]"),
        title="❌ Error",
        border_style="bright_red",
    )


def _info(body: Any, *, title: str = "ℹ️  Info") -> None:
    _panel(body, title=title, border_style="bright_cyan")


def _hint_panel(
    *,
    title: str,
    intro: str,
    next_steps: Sequence[str],
    examples: Sequence[str] | None = None,
    available: str | None = None,
    tip: str | None = None,
) -> None:
    """Show a guided next-step info panel for incomplete commands."""
    body = Text()
    body.append(f"{intro}\n\n", style="bright_white")
    body.append("Next steps:\n", style="bold bright_white")
    for step in next_steps:
        body.append("  • ", style="bright_cyan")
        body.append(f"{step}\n", style="bright_white")
    if available is not None:
        body.append("\nAvailable: ", style="bold bright_yellow")
        body.append(f"{available}\n", style="bright_cyan")
    if examples:
        body.append("\nExamples:\n", style="bold bright_white")
        for example in examples:
            body.append("  ", style="bright_white")
            body.append(f"{example}\n", style="bold bright_cyan")
    if tip is not None:
        body.append("\nTip: ", style="bold bright_yellow")
        body.append(f"{tip}", style="bright_white")
    _info(body, title=title)


def _require_arg(
    value: str | None,
    *,
    title: str,
    intro: str,
    next_steps: Sequence[str],
    examples: Sequence[str] | None = None,
    available: str | None = None,
    tip: str | None = None,
) -> str:
    """Return *value* or print a hint panel and exit if it is missing."""
    if value is None or not str(value).strip():
        _hint_panel(
            title=title,
            intro=intro,
            next_steps=next_steps,
            examples=examples,
            available=available,
            tip=tip,
        )
        raise typer.Exit(0)
    return value


def _run(
    action: Callable[[], None],
    *,
    success_message: Callable[[], str],
    success_title: str,
) -> None:
    """Run *action*; show an error panel on failure or a success panel on success."""
    try:
        action()
    except Exception as exc:
        _error(str(exc))
        raise typer.Exit(1) from exc
    _success(success_message(), title=success_title)


def _print_set_options() -> None:
    lines = Text()
    lines.append("Available subcommands:\n\n", style="bold bright_white")
    for emoji, option in SET_OPTIONS:
        lines.append(f"  {emoji}  ", style="bold")
        lines.append("set ", style="bright_black")
        lines.append(f"{option}\n", style="bright_white")
    lines.append("\n")
    lines.append("Tip: ", style="bold bright_yellow")
    lines.append("run ", style="bright_white")
    lines.append("mydash set --help", style="bold bright_cyan")
    lines.append(" for full usage.", style="bright_white")
    _info(lines, title="📋  set options")


@set_app.callback(invoke_without_command=True)
def set_root(
    ctx: typer.Context,
    list_options: bool = typer.Option(
        False,
        "--list-options",
        "-lo",
        help="List all set subcommands with domain grouping.",
    ),
) -> None:
    """Configure mydash preferences. Use a subcommand or --list-options."""
    if list_options:
        _print_set_options()
        raise typer.Exit(0)
    if ctx.invoked_subcommand is None:
        body = Text()
        body.append("No configuration change specified.\n\n", style="bright_white")
        body.append("  • Run ", style="bright_white")
        body.append("mydash set --help", style="bold bright_cyan")
        body.append(" for command help\n", style="bright_white")
        body.append("  • Run ", style="bright_white")
        body.append("mydash set -lo", style="bold bright_cyan")
        body.append(" to list all subcommands", style="bright_white")
        _info(body, title="ℹ️  mydash set")
        raise typer.Exit(0)


@set_app.command("show")
def set_show() -> None:
    """Print the current user configuration as JSON."""
    cfg = _config_service().get_configuration()
    payload = cfg.model_dump(mode="json")
    body = Group(
        Text("Current user configuration:", style="bold bright_white"),
        Text(""),
        JSON(json.dumps(payload)),
    )
    _info(body, title="⚙️  Config")


# ---------------------------------------------------------------------------
# Domain groups — incomplete path hints
# ---------------------------------------------------------------------------


@weather_app.callback(invoke_without_command=True)
def weather_root(ctx: typer.Context) -> None:
    """Weather preferences. Choose a subcommand."""
    if ctx.invoked_subcommand is not None:
        return
    _hint_panel(
        title="🌤️  set weather",
        intro="Choose a weather setting to update.",
        next_steps=[
            "city <city> — set location (geocodes and stores coordinates)",
            f"units <preset> — forecast units ({_fmt_choices(KNOWN_WEATHER_UNITS)})",
            f"provider <name> — weather API ({_fmt_choices(KNOWN_WEATHER_PROVIDERS)})",
        ],
        examples=[
            'mydash set weather city "New York"',
            "mydash set weather units imperial",
            "mydash set weather provider open-meteo",
        ],
        tip="mydash set weather --help  ·  mydash set -lo",
    )
    raise typer.Exit(0)


@stocks_app.callback(invoke_without_command=True)
def stocks_root(ctx: typer.Context) -> None:
    """Stocks preferences. Choose a subcommand."""
    if ctx.invoked_subcommand is not None:
        return
    _hint_panel(
        title="📈  set stocks",
        intro="Choose a stocks setting to update.",
        next_steps=[
            "add <symbol> — add a ticker to your watch list",
            "remove <symbol> — remove a ticker from your watch list",
            f"provider <name> — market data API ({_fmt_choices(KNOWN_STOCK_PROVIDERS)})",
        ],
        examples=[
            "mydash set stocks add AAPL",
            "mydash set stocks remove MSFT",
            "mydash set stocks provider alpaca",
        ],
        tip="mydash set stocks --help  ·  mydash set -lo",
    )
    raise typer.Exit(0)


@news_app.callback(invoke_without_command=True)
def news_root(ctx: typer.Context) -> None:
    """News preferences. Choose a subcommand."""
    if ctx.invoked_subcommand is not None:
        return
    _hint_panel(
        title="📰  set news",
        intro="Choose a news setting to update.",
        next_steps=[
            "category <category> — headline category (e.g. tech, politics)",
            f"provider <name> — news API ({_fmt_choices(KNOWN_NEWS_PROVIDERS)})",
        ],
        examples=[
            "mydash set news category tech",
            "mydash set news provider noozra",
        ],
        tip="mydash set news --help  ·  mydash set -lo",
    )
    raise typer.Exit(0)


@geocoding_app.callback(invoke_without_command=True)
def geocoding_root(ctx: typer.Context) -> None:
    """Geocoding preferences. Choose a subcommand."""
    if ctx.invoked_subcommand is not None:
        return
    _hint_panel(
        title="📍  set geocoding",
        intro="Choose a geocoding setting to update.",
        next_steps=[
            f"provider <name> — geocoding API ({_fmt_choices(KNOWN_GEOCODING_PROVIDERS)})",
        ],
        examples=[
            "mydash set geocoding provider open-meteo",
        ],
        tip="mydash set geocoding --help  ·  mydash set -lo",
    )
    raise typer.Exit(0)


# ---------------------------------------------------------------------------
# Weather leaf commands
# ---------------------------------------------------------------------------


@weather_app.command("city")
def weather_city(
    city: str | None = typer.Argument(
        None,
        help="City name to geocode and store (updates city + coordinates).",
    ),
) -> None:
    city = _require_arg(
        city,
        title="🌤️  set weather city",
        intro="A city name is required.",
        next_steps=[
            'Provide a city: mydash set weather city "<city>"',
            "This geocodes the city and stores coordinates in your config.",
        ],
        examples=[
            'mydash set weather city "New York"',
            "mydash set weather city Miami",
        ],
        tip="mydash set weather city --help",
    )
    svc = _config_service()

    def action() -> None:
        svc.set_city(city)

    def message() -> str:
        coords = svc.get_coordinates()
        return (
            f"City set to [bold bright_white]{svc.get_city()}[/bold bright_white]\n"
            f"Coordinates: [bright_cyan]{coords.latitude}[/bright_cyan], "
            f"[bright_cyan]{coords.longitude}[/bright_cyan]"
        )

    _run(action, success_message=message, success_title="🌤️  Weather · city")


@weather_app.command("units")
def weather_units(
    units: str | None = typer.Argument(
        None,
        help=(
            "Forecast unit preset. "
            f"Available: {_fmt_choices(KNOWN_WEATHER_UNITS)}"
        ),
    ),
) -> None:
    units = _require_arg(
        units,
        title="🌤️  set weather units",
        intro="A unit preset is required.",
        next_steps=[
            "Provide a preset: mydash set weather units <metric|imperial>",
        ],
        available=_fmt_choices(KNOWN_WEATHER_UNITS),
        examples=[
            "mydash set weather units metric",
            "mydash set weather units imperial",
        ],
        tip="mydash set weather units --help",
    )
    svc = _config_service()

    def action() -> None:
        svc.set_weather_forecast_units(units)

    def message() -> str:
        return (
            f"Weather units set to "
            f"[bold bright_white]{svc.get_weather_forecast_units()}[/bold bright_white]\n"
            f"Available: [bright_cyan]{_fmt_choices(KNOWN_WEATHER_UNITS)}[/bright_cyan]"
        )

    _run(action, success_message=message, success_title="🌤️  Weather · units")


@weather_app.command("provider")
def weather_provider(
    provider: str | None = typer.Argument(
        None,
        help=(
            "Weather data provider. "
            f"Available: {_fmt_choices(KNOWN_WEATHER_PROVIDERS)}"
        ),
    ),
) -> None:
    provider = _require_arg(
        provider,
        title="🌤️  set weather provider",
        intro="A weather provider name is required.",
        next_steps=[
            "Provide a provider: mydash set weather provider <name>",
        ],
        available=_fmt_choices(KNOWN_WEATHER_PROVIDERS),
        examples=[
            "mydash set weather provider open-meteo",
        ],
        tip="mydash set weather provider --help",
    )
    svc = _config_service()

    def action() -> None:
        svc.set_weather_provider(provider)

    def message() -> str:
        return (
            f"Weather provider set to "
            f"[bold bright_white]{svc.get_weather_provider()}[/bold bright_white]\n"
            f"Available: [bright_cyan]{_fmt_choices(KNOWN_WEATHER_PROVIDERS)}[/bright_cyan]"
        )

    _run(action, success_message=message, success_title="🌤️  Weather · provider")


# ---------------------------------------------------------------------------
# Stocks leaf commands
# ---------------------------------------------------------------------------


@stocks_app.command("add")
def stocks_add(
    symbol: str | None = typer.Argument(
        None,
        help="Ticker symbol to add (case-insensitive; stored uppercase).",
    ),
) -> None:
    symbol = _require_arg(
        symbol,
        title="📈  set stocks add",
        intro="A ticker symbol is required.",
        next_steps=[
            "Provide a symbol: mydash set stocks add <SYMBOL>",
        ],
        examples=[
            "mydash set stocks add AAPL",
            "mydash set stocks add GOOG",
        ],
        tip="mydash set stocks add --help",
    )
    svc = _config_service()

    def action() -> None:
        svc.add_stock_symbol(symbol)

    def message() -> str:
        symbols = ", ".join(svc.get_stock_symbols())
        return (
            f"Added [bold bright_white]{symbol.strip().upper()}[/bold bright_white]\n"
            f"Symbols: [bright_cyan]{symbols}[/bright_cyan]"
        )

    _run(action, success_message=message, success_title="📈  Stocks · add")


@stocks_app.command("remove")
def stocks_remove(
    symbol: str | None = typer.Argument(
        None,
        help="Ticker symbol to remove (case-insensitive).",
    ),
) -> None:
    symbol = _require_arg(
        symbol,
        title="📈  set stocks remove",
        intro="A ticker symbol is required.",
        next_steps=[
            "Provide a symbol: mydash set stocks remove <SYMBOL>",
        ],
        examples=[
            "mydash set stocks remove MSFT",
        ],
        tip="mydash set stocks remove --help",
    )
    svc = _config_service()

    def action() -> None:
        svc.remove_stock_symbol(symbol)

    def message() -> str:
        symbols = ", ".join(svc.get_stock_symbols()) or "(none)"
        return (
            f"Removed [bold bright_white]{symbol.strip().upper()}[/bold bright_white]\n"
            f"Symbols: [bright_cyan]{symbols}[/bright_cyan]"
        )

    _run(action, success_message=message, success_title="📈  Stocks · remove")


@stocks_app.command("provider")
def stocks_provider(
    provider: str | None = typer.Argument(
        None,
        help=(
            "Market data provider. "
            f"Available: {_fmt_choices(KNOWN_STOCK_PROVIDERS)}"
        ),
    ),
) -> None:
    provider = _require_arg(
        provider,
        title="📈  set stocks provider",
        intro="A stocks provider name is required.",
        next_steps=[
            "Provide a provider: mydash set stocks provider <name>",
        ],
        available=_fmt_choices(KNOWN_STOCK_PROVIDERS),
        examples=[
            "mydash set stocks provider alpaca",
        ],
        tip="mydash set stocks provider --help",
    )
    svc = _config_service()

    def action() -> None:
        svc.set_stock_provider(provider)

    def message() -> str:
        return (
            f"Stocks provider set to "
            f"[bold bright_white]{svc.get_stock_provider()}[/bold bright_white]\n"
            f"Available: [bright_cyan]{_fmt_choices(KNOWN_STOCK_PROVIDERS)}[/bright_cyan]"
        )

    _run(action, success_message=message, success_title="📈  Stocks · provider")


# ---------------------------------------------------------------------------
# News leaf commands
# ---------------------------------------------------------------------------


@news_app.command("category")
def news_category(
    category: str | None = typer.Argument(
        None,
        help="News category to request (e.g. tech, politics).",
    ),
) -> None:
    category = _require_arg(
        category,
        title="📰  set news category",
        intro="A news category is required.",
        next_steps=[
            "Provide a category: mydash set news category <category>",
            "Common values: tech, politics (provider-dependent).",
        ],
        examples=[
            "mydash set news category tech",
            "mydash set news category politics",
        ],
        tip="mydash set news category --help",
    )
    svc = _config_service()

    def action() -> None:
        svc.set_news_category(category)

    def message() -> str:
        return (
            f"News category set to "
            f"[bold bright_white]{svc.get_news_category()}[/bold bright_white]"
        )

    _run(action, success_message=message, success_title="📰  News · category")


@news_app.command("provider")
def news_provider(
    provider: str | None = typer.Argument(
        None,
        help=(
            "News provider. "
            f"Available: {_fmt_choices(KNOWN_NEWS_PROVIDERS)}"
        ),
    ),
) -> None:
    provider = _require_arg(
        provider,
        title="📰  set news provider",
        intro="A news provider name is required.",
        next_steps=[
            "Provide a provider: mydash set news provider <name>",
        ],
        available=_fmt_choices(KNOWN_NEWS_PROVIDERS),
        examples=[
            "mydash set news provider noozra",
        ],
        tip="mydash set news provider --help",
    )
    svc = _config_service()

    def action() -> None:
        svc.set_news_provider(provider)

    def message() -> str:
        return (
            f"News provider set to "
            f"[bold bright_white]{svc.get_news_provider()}[/bold bright_white]\n"
            f"Available: [bright_cyan]{_fmt_choices(KNOWN_NEWS_PROVIDERS)}[/bright_cyan]"
        )

    _run(action, success_message=message, success_title="📰  News · provider")


# ---------------------------------------------------------------------------
# Geocoding leaf commands
# ---------------------------------------------------------------------------


@geocoding_app.command("provider")
def geocoding_provider(
    provider: str | None = typer.Argument(
        None,
        help=(
            "Geocoding provider. "
            f"Available: {_fmt_choices(KNOWN_GEOCODING_PROVIDERS)}"
        ),
    ),
) -> None:
    provider = _require_arg(
        provider,
        title="📍  set geocoding provider",
        intro="A geocoding provider name is required.",
        next_steps=[
            "Provide a provider: mydash set geocoding provider <name>",
        ],
        available=_fmt_choices(KNOWN_GEOCODING_PROVIDERS),
        examples=[
            "mydash set geocoding provider open-meteo",
        ],
        tip="mydash set geocoding provider --help",
    )
    svc = _config_service()

    def action() -> None:
        svc.set_geocoding_provider(provider)

    def message() -> str:
        return (
            f"Geocoding provider set to "
            f"[bold bright_white]{svc.get_geocoding_provider()}[/bold bright_white]\n"
            f"Available: [bright_cyan]{_fmt_choices(KNOWN_GEOCODING_PROVIDERS)}[/bright_cyan]"
        )

    _run(action, success_message=message, success_title="📍  Geocoding · provider")
