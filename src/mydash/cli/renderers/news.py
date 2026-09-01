"""Headlines panel: a short list with clickable sources and relative times."""

from __future__ import annotations

from rich.panel import Panel

from mydash.cli import ui
from mydash.cli.renderers import _common
from mydash.models.news import NewsHeadlines

DEFAULT_LIMIT = 8


def headlines_panel(
    headlines: NewsHeadlines,
    *,
    category: str,
    limit: int = DEFAULT_LIMIT,
    failure: str | None = None,
    compact: bool = False,
) -> Panel:
    """Build the headlines panel.

    :param headlines: Headlines to show, already newest-first.
    :param category: Category name for the panel title.
    :param limit: Maximum rows to display.
    :param failure: Why headlines are missing, if they are.
    :param compact: Drop the source column.
    """
    title = f"📰 Headlines · {category}"

    if failure is not None:
        return ui.panel(ui.unavailable(failure), title=title, border="border.news")

    items = headlines.headlines[:limit]
    if not items:
        return ui.panel(
            ui.empty("No headlines right now"), title=title, border="border.news"
        )

    table = ui.data_table()
    table.add_column("#", style="muted", width=2, justify="right")
    table.add_column("Headline", style="value", overflow="ellipsis", ratio=3)
    if not compact:
        table.add_column("Source", overflow="ellipsis", ratio=1, no_wrap=True)
    table.add_column("When", style="muted", justify="right", no_wrap=True)

    for index, item in enumerate(items, start=1):
        row = [str(index), item.headline]
        if not compact:
            row.append(_common.source_link(item.publication, item.source_url))
        row.append(_common.published(item.published_time))
        table.add_row(*row)

    shown = len(items)
    total = len(headlines.headlines)
    subtitle = f"{shown} of {total}" if total > shown else None
    return ui.panel(table, title=title, border="border.news", subtitle=subtitle)
