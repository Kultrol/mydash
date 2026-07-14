"""Shared Rich panels and helpers for ``mydash set`` subcommands."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from mydash.services.user_config import UserConfigurationService

console = Console()

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
    return ", ".join(sorted(values))


def config_service() -> UserConfigurationService:
    return UserConfigurationService()


def panel(
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


def success(message: str, *, title: str = "✅ Success") -> None:
    panel(Text.from_markup(message), title=title, border_style="bright_green")


def error(message: str) -> None:
    panel(
        Text.from_markup(f"[bright_white]{message}[/bright_white]"),
        title="❌ Error",
        border_style="bright_red",
    )


def info(body: Any, *, title: str = "ℹ️  Info") -> None:
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
    """Return *value* or print a hint panel and exit if it is missing."""
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
    """Run *action*; show an error panel on failure or a success panel on success."""
    try:
        action()
    except Exception as exc:
        error(str(exc))
        raise typer.Exit(1) from exc
    success(success_message(), title=success_title)


def print_set_options() -> None:
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
