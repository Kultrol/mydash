"""``mydash set stocks`` — watch-list symbols and market data provider."""

from __future__ import annotations

import typer

from mydash.cli.commands.set._helpers import (
    config_service,
    fmt_choices,
    hint_panel,
    require_arg,
    run,
)
from mydash.core.services.user_config import KNOWN_STOCK_PROVIDERS

app = typer.Typer(
    help="📈  Stocks-related preferences (symbols, provider).",
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def stocks_root(ctx: typer.Context) -> None:
    """If no leaf subcommand was given, print stocks next-step hints and exit."""
    if ctx.invoked_subcommand is not None:
        return
    hint_panel(
        title="📈  set stocks",
        intro="Choose a stocks setting to update.",
        next_steps=[
            "add <symbol> — add a ticker to your watch list",
            "remove <symbol> — remove a ticker from your watch list",
            f"provider <name> — market data API ({fmt_choices(KNOWN_STOCK_PROVIDERS)})",
        ],
        examples=[
            "mydash set stocks add AAPL",
            "mydash set stocks remove MSFT",
            "mydash set stocks provider alpaca",
        ],
        tip="mydash set stocks --help  ·  mydash set -lo",
    )
    raise typer.Exit(0)


@app.command("add")
def add(
    symbol: str | None = typer.Argument(
        None,
        help="Ticker symbol to add (case-insensitive; stored uppercase).",
    ),
) -> None:
    """Add a ticker symbol to the brief markets panel."""
    ticker = require_arg(
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
    svc = config_service()

    def action() -> None:
        svc.add_stock_symbol(ticker)

    def message() -> str:
        symbols = ", ".join(svc.get_stock_symbols())
        return (
            f"Added [bold bright_white]{ticker.strip().upper()}[/bold bright_white]\n"
            f"Symbols: [bright_cyan]{symbols}[/bright_cyan]"
        )

    run(action, success_message=message, success_title="📈  Stocks · add")


@app.command("remove")
def remove(
    symbol: str | None = typer.Argument(
        None,
        help="Ticker symbol to remove (case-insensitive).",
    ),
) -> None:
    """Remove a ticker symbol from the brief markets panel."""
    ticker = require_arg(
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
    svc = config_service()

    def action() -> None:
        svc.remove_stock_symbol(ticker)

    def message() -> str:
        symbols = ", ".join(svc.get_stock_symbols()) or "(none)"
        return (
            f"Removed [bold bright_white]{ticker.strip().upper()}[/bold bright_white]\n"
            f"Symbols: [bright_cyan]{symbols}[/bright_cyan]"
        )

    run(action, success_message=message, success_title="📈  Stocks · remove")


@app.command("provider")
def provider(
    provider: str | None = typer.Argument(
        None,
        help=(
            "Market data provider. "
            f"Available: {fmt_choices(KNOWN_STOCK_PROVIDERS)}"
        ),
    ),
) -> None:
    """Set the market data API provider used by the brief."""
    provider = require_arg(
        provider,
        title="📈  set stocks provider",
        intro="A stocks provider name is required.",
        next_steps=[
            "Provide a provider: mydash set stocks provider <name>",
        ],
        available=fmt_choices(KNOWN_STOCK_PROVIDERS),
        examples=[
            "mydash set stocks provider alpaca",
        ],
        tip="mydash set stocks provider --help",
    )
    svc = config_service()

    def action() -> None:
        svc.set_stock_provider(provider)

    def message() -> str:
        return (
            f"Stocks provider set to "
            f"[bold bright_white]{svc.get_stock_provider()}[/bold bright_white]\n"
            f"Available: [bright_cyan]{fmt_choices(KNOWN_STOCK_PROVIDERS)}[/bright_cyan]"
        )

    run(action, success_message=message, success_title="📈  Stocks · provider")
