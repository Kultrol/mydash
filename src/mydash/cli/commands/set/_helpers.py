"""Shared Rich panels and helpers for ``mydash set`` subcommands.

Domain modules call these for consistent success / error / guidance UX.
Incomplete paths use :func:`require_arg` (exit 0 + info panel); failed
mutations use :func:`run` (exit 1 + error panel).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from mydash.services.user_config import UserConfigurationService

console = Console()

# Static catalog for ``mydash set -lo`` (emoji, relative usage string).
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


def fmt_choices(values: frozenset[str]) -> str:
    """Join allowed values sorted for help text and panels."""
    return ", ".join(sorted(values))


def config_service() -> UserConfigurationService:
    """Construct the default user-config service (platform config path).

    Tests patch :class:`UserConfigurationService` on this module so all
    set subcommands share one mock site.
    """
    return UserConfigurationService()


def panel(
    body: Any,
    *,
    title: str,
    border_style: str,
) -> None:
    """Print a Rich panel with shared padding and left-aligned title."""
    console.print(
        Panel(
            body,
            title=title,
            border_style=border_style,
            title_align="left",
            padding=(0, 1),
        )
    )


def success(message: str, *, title: str = "✅ Success") -> None:
    """Green panel for a completed preference change (markup allowed)."""
    panel(Text.from_markup(message), title=title, border_style="bright_green")


def error(message: str) -> None:
    """Red panel for validation or provider failures."""
    panel(
        Text.from_markup(f"[bright_white]{message}[/bright_white]"),
        title="❌ Error",
        border_style="bright_red",
    )


def info(body: Any, *, title: str = "ℹ️  Info") -> None:
    """Cyan panel for guidance, options lists, and config dumps."""
    panel(body, title=title, border_style="bright_cyan")


def hint_panel(
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
    info(body, title=title)


def require_arg(
    value: str | None,
    *,
    title: str,
    intro: str,
    next_steps: Sequence[str],
    examples: Sequence[str] | None = None,
    available: str | None = None,
    tip: str | None = None,
) -> str:
    """Return *value*, or print a hint panel and exit 0 if it is missing.

    Used so ``mydash set weather provider`` guides the user instead of
    Click's default “Missing argument” error.
    """
    if value is None or not str(value).strip():
        hint_panel(
            title=title,
            intro=intro,
            next_steps=next_steps,
            examples=examples,
            available=available,
            tip=tip,
        )
        raise typer.Exit(0)
    return value


def run(
    action: Callable[[], None],
    *,
    success_message: Callable[[], str],
    success_title: str,
) -> None:
    """Run *action*; error panel + exit 1 on failure, success panel otherwise.

    :param action: Side-effecting callable (usually a config service mutator).
    :param success_message: Called after success to build panel body markup.
    :param success_title: Panel title (often domain emoji + action name).
    """
    try:
        action()
    except Exception as exc:
        error(str(exc))
        raise typer.Exit(1) from exc
    success(success_message(), title=success_title)


def print_set_options() -> None:
    """Render the ``-lo`` / ``--list-options`` catalog panel."""
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
    info(lines, title="📋  set options")
