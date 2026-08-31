"""``mydash config`` — inspect, locate, and reset stored preferences."""

from __future__ import annotations

import typer
from rich.text import Text

from mydash.cli import ui
from mydash.cli.context import config_service
from mydash.services.user_config import UserConfig

app = typer.Typer(help="⚙️  Inspect and manage stored preferences.", no_args_is_help=True)


def config_table(config: UserConfig) -> object:
    """Render preferences as a two-column settings table."""
    table = ui.detail_table()
    table.add_column("Setting", style="muted", no_wrap=True)
    table.add_column("Value", style="value")

    coordinates = config.coordinates
    rows = [
        ("City", config.city),
        ("Coordinates", f"{coordinates.latitude:.4f}, {coordinates.longitude:.4f}"),
        ("Weather units", config.weather_units),
        ("News category", config.news_category),
        ("Watch list", ", ".join(config.stock_symbols) or "(none)"),
        ("Weather provider", config.provider_weather),
        ("Geocoding provider", config.provider_geocoding),
        ("News provider", config.provider_news),
        ("Stocks provider", config.provider_stocks),
    ]
    for label, value in rows:
        table.add_row(label, str(value))
    return table


@app.command("show")
def show(
    as_json: bool = typer.Option(
        False, "--json", help="Print raw JSON instead of a table."
    ),
) -> None:
    """Show the current user configuration."""
    with config_service() as service:
        config = service.get_configuration()
        path = service.database_path

    if as_json:
        ui.console.print_json(config.model_dump_json())
        return

    ui.console.print(
        ui.panel(
            config_table(config),
            title="⚙️  Configuration",
            border="border.info",
            subtitle=str(path),
        )
    )


@app.command("path")
def path() -> None:
    """Print the path of the database holding your preferences."""
    with config_service() as service:
        ui.console.print(str(service.database_path))


@app.command("reset")
def reset(
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip the confirmation prompt."
    ),
) -> None:
    """Restore the shipped defaults, discarding your preferences."""
    with config_service() as service:
        if not yes:
            current = service.get_configuration()
            ui.console.print(
                ui.panel(
                    config_table(current),
                    title="⚙️  About to reset",
                    border="warn",
                )
            )
            if not typer.confirm("Replace these with the shipped defaults?"):
                ui.console.print(Text("Left untouched.", style="muted"))
                raise typer.Exit(0)

        restored = service.reset()

    ui.success(
        f"Preferences reset to defaults — city is "
        f"[bold]{restored.city}[/bold] again.",
        title="⚙️  Config · reset",
    )
