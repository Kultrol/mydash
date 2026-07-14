"""``mydash set news`` — headline category and news provider."""

from __future__ import annotations

import typer

from mydash.cli.commands.set._helpers import (
    config_service,
    fmt_choices,
    hint_panel,
    require_arg,
    run,
)
from mydash.services.user_config import KNOWN_NEWS_PROVIDERS

app = typer.Typer(
    help="📰  News-related preferences (category, provider).",
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def news_root(ctx: typer.Context) -> None:
    """If no leaf subcommand was given, print news next-step hints and exit."""
    if ctx.invoked_subcommand is not None:
        return
    hint_panel(
        title="📰  set news",
        intro="Choose a news setting to update.",
        next_steps=[
            "category <category> — headline category (e.g. tech, politics)",
            f"provider <name> — news API ({fmt_choices(KNOWN_NEWS_PROVIDERS)})",
        ],
        examples=[
            "mydash set news category tech",
            "mydash set news provider noozra",
        ],
        tip="mydash set news --help  ·  mydash set -lo",
    )
    raise typer.Exit(0)


@app.command("category")
def category(
    category: str | None = typer.Argument(
        None,
        help="News category to request (e.g. tech, politics).",
    ),
) -> None:
    """Set the news category used for brief headlines."""
    category = require_arg(
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
    svc = config_service()

    def action() -> None:
        svc.set_news_category(category)

    def message() -> str:
        return (
            f"News category set to "
            f"[bold bright_white]{svc.get_news_category()}[/bold bright_white]"
        )

    run(action, success_message=message, success_title="📰  News · category")


@app.command("provider")
def provider(
    provider: str | None = typer.Argument(
        None,
        help=(
            "News provider. "
            f"Available: {fmt_choices(KNOWN_NEWS_PROVIDERS)}"
        ),
    ),
) -> None:
    """Set the news API provider used by the brief."""
    provider = require_arg(
        provider,
        title="📰  set news provider",
        intro="A news provider name is required.",
        next_steps=[
            "Provide a provider: mydash set news provider <name>",
        ],
        available=fmt_choices(KNOWN_NEWS_PROVIDERS),
        examples=[
            "mydash set news provider noozra",
        ],
        tip="mydash set news provider --help",
    )
    svc = config_service()

    def action() -> None:
        svc.set_news_provider(provider)

    def message() -> str:
        return (
            f"News provider set to "
            f"[bold bright_white]{svc.get_news_provider()}[/bold bright_white]\n"
            f"Available: [bright_cyan]{fmt_choices(KNOWN_NEWS_PROVIDERS)}[/bright_cyan]"
        )

    run(action, success_message=message, success_title="📰  News · provider")
