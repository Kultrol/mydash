"""Shared terminal styling for mydash.

One :class:`~rich.console.Console` and one :class:`~rich.theme.Theme` so every
command looks like it came from the same program. Modules ask for *meaning*
(``success``, ``money.up``, ``muted``) rather than a colour, which keeps the
palette in one place and makes a retheme a one-file change.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

THEME = Theme(
    {
        # Structure
        "brand": "bold bright_cyan",
        "heading": "bold bright_white",
        "value": "bright_white",
        "muted": "bright_black",
        "accent": "bright_cyan",
        "link": "bold bright_blue",
        # Status
        "success": "bold bright_green",
        "warn": "bold bright_yellow",
        "danger": "bold bright_red",
        # Markets
        "money": "bright_cyan",
        "money.up": "bold bright_green",
        "money.down": "bold bright_red",
        "money.flat": "bright_white",
        # Weather
        "temp.hot": "bold bright_yellow",
        "temp.mild": "bright_white",
        "temp.cold": "bold bright_cyan",
        "rain.wet": "bold bright_magenta",
        "rain.damp": "bold bright_yellow",
        "rain.dry": "bright_green",
        # Panel borders, one hue per domain
        "border.stocks": "green",
        "border.weather": "yellow",
        "border.news": "blue",
        "border.info": "cyan",
        "border.success": "green",
        "border.error": "red",
    }
)

console = Console(theme=THEME)

#: Panels are rounded; tables inside them stay light so borders do not stack.
PANEL_BOX = box.ROUNDED
TABLE_BOX = box.SIMPLE_HEAD


def set_color(enabled: bool) -> None:
    """Turn colour on or off for the shared console (``--no-color``)."""
    console.no_color = not enabled


# -- panels ----------------------------------------------------------------


def panel(
    body: Any,
    *,
    title: str,
    border: str = "border.info",
    subtitle: str | None = None,
) -> Panel:
    """Build a panel with mydash's shared padding and alignment."""
    return Panel(
        body,
        title=title,
        subtitle=subtitle,
        border_style=border,
        title_align="left",
        subtitle_align="right",
        box=PANEL_BOX,
        padding=(0, 1),
    )


def print_panel(body: Any, *, title: str, border: str = "border.info") -> None:
    """Print a panel to the shared console."""
    console.print(panel(body, title=title, border=border))


def success(message: str, *, title: str = "✅ Success") -> None:
    """Green panel for a completed change (Rich markup allowed)."""
    print_panel(Text.from_markup(message), title=title, border="border.success")


def error(message: str, *, title: str = "❌ Error") -> None:
    """Red panel for validation or provider failures."""
    print_panel(Text.from_markup(message), title=title, border="border.error")


def info(body: Any, *, title: str = "ℹ️  Info") -> None:
    """Cyan panel for guidance, option lists, and config dumps."""
    print_panel(body, title=title, border="border.info")


def warn(message: str, *, title: str = "⚠️  Heads up") -> None:
    """Yellow-bordered panel for a non-fatal problem."""
    print_panel(Text.from_markup(message), title=title, border="warn")


def render_exception(exc: BaseException, *, hint: str | None = None) -> None:
    """Show an unexpected failure as a readable panel instead of a traceback.

    :param exc: The failure to describe.
    :param hint: Optional next step for the reader.
    """
    body = Text()
    body.append(str(exc) or exc.__class__.__name__, style="value")
    if hint:
        body.append("\n\n")
        body.append(hint, style="muted")
    body.append("\n\nRun with ", style="muted")
    body.append("--debug", style="accent")
    body.append(" for the full traceback.", style="muted")
    print_panel(body, title="❌ Something went wrong", border="border.error")


# -- tables ----------------------------------------------------------------


def data_table(*, header: bool = True) -> Table:
    """Build a full-width table styled for panel interiors."""
    return Table(
        expand=True,
        box=TABLE_BOX,
        show_header=header,
        show_edge=False,
        pad_edge=False,
        header_style="heading",
        border_style="muted",
    )


def detail_table() -> Table:
    """Build a left-hugging table for label/value listings.

    Unlike :func:`data_table` this does not stretch to the panel width, so a
    two-column settings list reads as a list instead of two far-apart columns.
    """
    return Table(
        expand=False,
        box=None,
        show_header=False,
        show_edge=False,
        pad_edge=False,
        padding=(0, 2, 0, 0),
    )


def empty(message: str) -> Text:
    """Body for a panel that has nothing to show."""
    return Text(message, style="muted italic")


def unavailable(reason: str) -> Text:
    """Body for a panel whose provider failed, explaining why."""
    body = Text()
    body.append("Unavailable — ", style="danger")
    body.append(reason, style="value")
    return body


def bullets(items: Sequence[str], *, marker: str = "•") -> Text:
    """Render a simple bulleted list."""
    body = Text()
    for item in items:
        body.append(f"  {marker} ", style="accent")
        body.append(f"{item}\n", style="value")
    return body


# -- progress --------------------------------------------------------------


@contextmanager
def spinner(message: str) -> Iterator[None]:
    """Show a status spinner while a network call is in flight.

    Silent when output is redirected, so piping stays clean.
    """
    if not console.is_terminal:
        yield
        return
    with console.status(f"[accent]{message}[/accent]", spinner="dots"):
        yield


# -- formatting helpers ----------------------------------------------------


def money(value: float) -> str:
    """Format a price with a currency symbol and thousands separators."""
    return f"${value:,.2f}"


def local_time(when: datetime) -> str:
    """Format a timestamp as a short local clock time."""
    if when.tzinfo is not None:
        when = when.astimezone()
    return when.strftime("%-I:%M %p") if _supports_dash() else when.strftime("%I:%M %p")


def relative_time(when: datetime) -> str:
    """Describe *when* relative to now, e.g. ``12m ago`` or ``3d ago``."""
    reference = datetime.now(UTC) if when.tzinfo else datetime.now()
    seconds = (reference - when).total_seconds()

    if seconds < 0:
        return "just now"
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    if seconds < 7 * 86400:
        return f"{int(seconds // 86400)}d ago"
    return when.strftime("%b %d")


def _supports_dash() -> bool:
    """True where ``%-I`` strips the leading zero (glibc, BSD, macOS)."""
    try:
        return datetime(2026, 1, 1, 9).strftime("%-I") == "9"
    except ValueError:
        return False
