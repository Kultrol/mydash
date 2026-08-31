"""Shared guidance helpers for ``mydash set`` subcommands.

Panels and styling come from :mod:`mydash.cli.ui`; what lives here is the
*behaviour* the set tree shares: an incomplete path prints next steps and exits
0 (:func:`require_arg`), while a failed mutation prints an error panel and
exits 1 (:func:`run`).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import typer
from rich.text import Text

from mydash.cli import ui
from mydash.cli.context import config_service as _config_service
from mydash.services.user_config import UserConfigurationService

# Re-exported so subcommands keep importing panels from one place.
console = ui.console
error = ui.error
info = ui.info
success = ui.success

# Static catalog for ``mydash set -lo`` (emoji, relative usage string).
SET_OPTIONS: list[tuple[str, str]] = [
    ("🌤️", "weather city <city>"),
    ("🌤️", "weather units <metric|imperial>"),
    ("🌤️", "weather provider <name>"),
    ("📈", "stocks add <symbol>"),
    ("📈", "stocks remove <symbol>"),
    ("📈", "stocks list"),
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
    """Open the user's configuration (see :mod:`mydash.cli.context`)."""
    return _config_service()


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
    body.append(f"{intro}\n\n", style="value")
    body.append("Next steps:\n", style="heading")
    body.append_text(ui.bullets(next_steps))
    if available is not None:
        body.append("\nAvailable: ", style="warn")
        body.append(f"{available}\n", style="accent")
    if examples:
        body.append("\nExamples:\n", style="heading")
        for example in examples:
            body.append("  ")
            body.append(f"{example}\n", style="accent")
    if tip is not None:
        body.append("\nTip: ", style="warn")
        body.append(f"{tip}", style="value")
    ui.info(body, title=title)


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
    Click's default "Missing argument" error.
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
        ui.error(str(exc) or exc.__class__.__name__)
        raise typer.Exit(1) from exc
    ui.success(success_message(), title=success_title)


def print_set_options() -> None:
    """Render the ``-lo`` / ``--list-options`` catalog panel."""
    lines = Text()
    lines.append("Available subcommands:\n\n", style="heading")
    for emoji, option in SET_OPTIONS:
        lines.append(f"  {emoji}  ")
        lines.append("set ", style="muted")
        lines.append(f"{option}\n", style="value")
    lines.append("\nTip: ", style="warn")
    lines.append("run ", style="value")
    lines.append("mydash set --help", style="accent")
    lines.append(" for full usage.", style="value")
    ui.info(lines, title="📋  set options")
