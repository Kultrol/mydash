"""``mydash config`` — inspect, locate, and reset stored preferences."""

from __future__ import annotations

import typer
from rich.console import Group
from rich.text import Text

from mydash.cli import ui
from mydash.cli.context import config_service
from mydash.env import (
    ALPACA_KEY_VAR,
    ALPACA_SECRET_VAR,
    candidate_paths,
    has_alpaca_credentials,
    load_environment,
    user_env_path,
    write_template,
)
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


@app.command("env")
def env(
    create: bool = typer.Option(
        False,
        "--create",
        help="Write a placeholder credentials file you can fill in.",
    ),
) -> None:
    """Show where mydash looks for API credentials, and whether it found any."""
    if create:
        _create_template()
        return

    loaded = {path for path in load_environment()}
    table = ui.detail_table()
    table.add_column("", width=3, no_wrap=True)
    table.add_column("Location", style="value", overflow="fold")
    table.add_column("Status", style="muted", no_wrap=True)

    for path in candidate_paths():
        if path in loaded:
            table.add_row("✅", str(path), "read")
        elif path.exists():
            table.add_row("⚠️", str(path), "present but unreadable")
        else:
            table.add_row("·", str(path), "not there")

    body = Group(
        table,
        Text(""),
        _credentials_line(),
    )
    ui.console.print(
        ui.panel(
            body,
            title="🔐 Credentials",
            border="border.info",
            subtitle="highest precedence first",
        )
    )


def _credentials_line() -> Text:
    """One line saying whether the Alpaca variables are actually set."""
    line = Text()
    if has_alpaca_credentials():
        line.append("Alpaca credentials found. ", style="success")
        line.append("The markets panel is on.", style="muted")
        return line

    line.append("Alpaca credentials not set", style="warn")
    line.append(
        f" ({ALPACA_KEY_VAR}, {ALPACA_SECRET_VAR}).\n", style="muted"
    )
    line.append("Weather and headlines work without them. Run ", style="muted")
    line.append("mydash config env --create", style="accent")
    line.append(" to start a credentials file.", style="muted")
    return line


def _create_template() -> None:
    """Write the placeholder credentials file, refusing to clobber a real one."""
    destination = user_env_path()
    try:
        written = write_template(destination)
    except FileExistsError:
        ui.error(
            f"[value]{destination}[/value] already exists — "
            "edit it rather than overwriting your keys.",
            title="🔐 Credentials",
        )
        raise typer.Exit(1) from None
    except OSError as err:
        ui.error(f"Could not write {destination}: {err}", title="🔐 Credentials")
        raise typer.Exit(1) from err

    body = Text()
    body.append("Wrote a placeholder credentials file:\n\n", style="value")
    body.append(f"  {written}\n\n", style="accent")
    body.append("Fill in your Alpaca key and secret, then run ", style="muted")
    body.append("mydash doctor", style="accent")
    body.append(" to check them.", style="muted")
    ui.console.print(
        ui.panel(body, title="🔐 Credentials", border="border.success")
    )
