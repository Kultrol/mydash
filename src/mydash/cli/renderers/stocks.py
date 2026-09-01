"""Markets panel: latest close, movement, and the spread per ticker."""

from __future__ import annotations

from rich.console import Group
from rich.panel import Panel

from mydash.cli import ui
from mydash.cli.renderers import _common
from mydash.models.stocks import StockBars, StockQuotes

TITLE = "📈 Markets"


def stocks_panel(
    quotes: StockQuotes,
    bars: StockBars,
    *,
    symbols: list[str] | None = None,
    failure: str | None = None,
    compact: bool = False,
) -> Panel:
    """Build the markets panel.

    :param quotes: Latest bid/ask per ticker.
    :param bars: Latest daily bar per ticker, for close and movement.
    :param symbols: Watch list, shown in the panel subtitle.
    :param failure: Why market data is missing, if it is.
    :param compact: Drop the bid/ask columns for a denser table.
    """
    subtitle = ", ".join(symbols) if symbols else None

    if failure is not None:
        return ui.panel(
            ui.unavailable(failure), title=TITLE, border="border.stocks"
        )

    if not quotes.quotes and not bars.bars:
        body = ui.empty("No market data right now")
        note = _common.missing_note(sorted(set(quotes.missing) | set(bars.missing)))
        return ui.panel(
            Group(body, note) if note else body,
            title=TITLE,
            border="border.stocks",
            subtitle=subtitle,
        )

    table = ui.data_table()
    table.add_column("Ticker", style="heading", no_wrap=True)
    table.add_column("Close", justify="right", no_wrap=True)
    table.add_column("Change", justify="right", no_wrap=True)
    table.add_column("%", justify="right", no_wrap=True)
    if not compact:
        table.add_column("Bid", justify="right", no_wrap=True)
        table.add_column("Ask", justify="right", no_wrap=True)
    table.add_column("As of", justify="right", style="muted", no_wrap=True)

    quotes_by_ticker = {quote.ticker_name: quote for quote in quotes.quotes}
    bars_by_ticker = {bar.ticker_name: bar for bar in bars.bars}

    for ticker in _ordered_tickers(quotes, bars, symbols):
        quote = quotes_by_ticker.get(ticker)
        bar = bars_by_ticker.get(ticker)

        if bar is not None:
            close = ui.money(bar.close)
            change, percent = _common.price_change(bar.open, bar.close)
        else:
            close, change, percent = "—", "—", "—"

        as_of = quote.time if quote is not None else (bar.time if bar else None)
        row = [
            ticker,
            close,
            change,
            percent,
        ]
        if not compact:
            row += [
                _common.optional_money(quote.bid_price if quote else None),
                _common.optional_money(quote.ask_price if quote else None),
            ]
        row.append(ui.local_time(as_of) if as_of else "—")
        table.add_row(*row)

    note = _common.missing_note(sorted(set(quotes.missing) | set(bars.missing)))
    return ui.panel(
        Group(table, note) if note else table,
        title=TITLE,
        border="border.stocks",
        subtitle=subtitle,
    )


def _ordered_tickers(
    quotes: StockQuotes, bars: StockBars, symbols: list[str] | None
) -> list[str]:
    """Show tickers in watch-list order, then anything else that came back."""
    seen = [quote.ticker_name for quote in quotes.quotes]
    seen += [bar.ticker_name for bar in bars.bars if bar.ticker_name not in seen]

    if not symbols:
        return seen

    ordered = [symbol for symbol in symbols if symbol in seen]
    ordered += [ticker for ticker in seen if ticker not in ordered]
    return ordered
