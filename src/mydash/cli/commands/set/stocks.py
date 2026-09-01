"""``mydash set stocks`` — watch-list symbols and market data provider."""

from __future__ import annotations

import typer

from mydash.cli import ui
from mydash.cli.commands.set._helpers import (
    config_service,
    fmt_choices,
    hint_panel,
    require_arg,
    run,
)
from mydash.services.user_config import KNOWN_STOCK_PROVIDERS

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
            "list — show the current watch list",
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
    symbol = require_arg(
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
        svc.add_stock_symbol(symbol)

    def message() -> str:
        symbols = ", ".join(svc.get_stock_symbols())
        return (
            f"Added [heading]{symbol.strip().upper()}[/heading]\n"
            f"Symbols: [accent]{symbols}[/accent]"
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
    symbol = require_arg(
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
        svc.remove_stock_symbol(symbol)

    def message() -> str:
        symbols = ", ".join(svc.get_stock_symbols()) or "(none)"
        return (
            f"Removed [heading]{symbol.strip().upper()}[/heading]\n"
            f"Symbols: [accent]{symbols}[/accent]"
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
            f"[heading]{svc.get_stock_provider()}[/heading]\n"
            f"Available: [accent]{fmt_choices(KNOWN_STOCK_PROVIDERS)}[/accent]"
        )

    run(action, success_message=message, success_title="📈  Stocks · provider")


@app.command("list")
def list_symbols() -> None:
    """Show the tickers currently on your watch list."""
    symbols = config_service().get_stock_symbols()
    if not symbols:
        hint_panel(
            title="📈  set stocks list",
            intro="Your watch list is empty.",
            next_steps=["Add a ticker: mydash set stocks add <SYMBOL>"],
            examples=["mydash set stocks add AAPL"],
            tip="mydash stocks -s AAPL,MSFT shows tickers without saving them.",
        )
        return

    table = ui.detail_table()
    table.add_column("#", style="muted", width=3, justify="right")
    table.add_column("Ticker", style="value")
    for index, symbol in enumerate(symbols, start=1):
        table.add_row(str(index), symbol)
    ui.console.print(
        ui.panel(table, title="📈  Watch list", border="border.stocks")
    )
