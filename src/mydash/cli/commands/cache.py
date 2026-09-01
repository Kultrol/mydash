"""``mydash cache`` — inspect and drop cached provider responses."""

from __future__ import annotations

from datetime import datetime

import typer
from rich.text import Text

from mydash.cli import ui
from mydash.cli.context import config_service, response_cache
from mydash.storage.cache import TTL

app = typer.Typer(
    help="💾  Inspect and clear cached provider responses.", no_args_is_help=True
)


@app.command("info")
def info() -> None:
    """Show what the response cache is holding."""
    with config_service() as service:
        stats = response_cache(service).stats()
        path = service.database_path

    table = ui.detail_table()
    table.add_column("Metric", style="muted", no_wrap=True)
    table.add_column("Value", style="value")
    table.add_row("Fresh entries", str(stats.fresh))
    table.add_row("Expired entries", str(stats.expired))
    table.add_row("Size", _human_bytes(stats.total_bytes))
    table.add_row("Oldest entry", _age(stats.oldest))
    table.add_row("Newest entry", _age(stats.newest))
    table.add_row(
        "Freshness windows",
        "  ·  ".join(
            f"{domain} {_duration(seconds)}" for domain, seconds in TTL.items()
        ),
    )

    ui.console.print(
        ui.panel(
            table, title="💾 Cache", border="border.info", subtitle=str(path)
        )
    )


@app.command("clear")
def clear(
    expired_only: bool = typer.Option(
        False, "--expired", help="Only drop entries that are already stale."
    ),
) -> None:
    """Empty the response cache so the next run fetches live data."""
    with config_service() as service:
        cache = response_cache(service)
        removed = cache.purge_expired() if expired_only else cache.clear()

    what = "expired entries" if expired_only else "entries"
    if removed:
        ui.success(f"Removed [bold]{removed}[/bold] cached {what}.", title="💾 Cache")
    else:
        ui.console.print(Text(f"No cached {what} to remove.", style="muted"))


def _human_bytes(size: int) -> str:
    """Format a byte count for people."""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def _duration(seconds: float) -> str:
    """Format a TTL as a short human duration."""
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h"
    return f"{int(seconds // 86400)}d"


def _age(timestamp: float | None) -> str:
    """Describe a stored-at timestamp as an age, or a dash when absent."""
    if timestamp is None:
        return "—"
    return ui.relative_time(datetime.fromtimestamp(timestamp))
