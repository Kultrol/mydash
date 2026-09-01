"""Rich layout for the daily brief (presentation only).

A header line, then one panel per requested domain. Each panel is the same
builder the single-domain commands use, so ``mydash weather`` and the weather
panel inside ``mydash brief`` can never drift apart.
"""

from __future__ import annotations

from rich.console import Console
from rich.rule import Rule
from rich.text import Text

from mydash.cli import ui
from mydash.cli.renderers.news import DEFAULT_LIMIT as HEADLINE_LIMIT
from mydash.cli.renderers.news import headlines_panel
from mydash.cli.renderers.stocks import stocks_panel
from mydash.cli.renderers.weather import DEFAULT_HOURS as WEATHER_HOURS
from mydash.cli.renderers.weather import weather_panel
from mydash.services.brief import DailyBrief


def render_brief(
    console: Console, brief: DailyBrief, *, compact: bool = False
) -> None:
    """Print the requested panels, stacked, in brief order.

    :param console: Console to print to.
    :param brief: Composed brief, including any per-domain failures.
    :param compact: Denser tables with fewer columns.
    """
    console.print(_header(brief))
    for domain in brief.domains:
        builder = _PANELS.get(domain)
        if builder is not None:
            console.print(builder(brief, compact))
    if not brief.is_complete:
        console.print(_failure_footer(brief))


def _header(brief: DailyBrief) -> Rule:
    """Title rule with the date and the city the brief was built for."""
    label = Text()
    label.append("mydash", style="brand")
    label.append("  ·  ", style="muted")
    label.append(brief.generated_at.strftime("%A %d %B"), style="heading")
    label.append("  ·  ", style="muted")
    label.append(brief.city, style="accent")
    label.append("  ·  ", style="muted")
    label.append(ui.local_time(brief.generated_at), style="muted")
    return Rule(label, style="muted", align="left")


def _failure_footer(brief: DailyBrief) -> Text:
    """One muted line naming the panels that came back empty."""
    footer = Text()
    footer.append("Some panels are unavailable: ", style="muted")
    footer.append(", ".join(sorted(brief.errors)), style="warn")
    footer.append("  ·  retry with ", style="muted")
    footer.append("mydash brief --refresh", style="accent")
    footer.append("  ·  diagnose with ", style="muted")
    footer.append("mydash doctor", style="accent")
    return footer


def _stocks(brief: DailyBrief, compact: bool):
    return stocks_panel(
        brief.stock_quotes,
        brief.stock_bars,
        symbols=brief.symbols,
        failure=brief.failed("stocks"),
        compact=compact,
    )


def _weather(brief: DailyBrief, compact: bool):
    return weather_panel(
        brief.weather,
        city=brief.city,
        units=brief.weather_units,
        hours=WEATHER_HOURS,
        failure=brief.failed("weather"),
        compact=compact,
    )


def _news(brief: DailyBrief, compact: bool):
    return headlines_panel(
        brief.headlines,
        category=brief.news_category,
        limit=HEADLINE_LIMIT,
        failure=brief.failed("news"),
        compact=compact,
    )


#: Panel builder per brief domain.
_PANELS = {"stocks": _stocks, "weather": _weather, "news": _news}
