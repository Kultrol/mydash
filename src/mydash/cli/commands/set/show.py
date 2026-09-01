"""``mydash set show`` — show the current user configuration.

Kept as an alias for ``mydash config show``, which is where configuration
management lives now.
"""

from __future__ import annotations

from mydash.cli import ui
from mydash.cli.commands.config import config_table
from mydash.cli.commands.set._helpers import config_service


def show() -> None:
    """Print the stored user configuration as a settings table."""
    with config_service() as service:
        config = service.get_configuration()
        path = service.database_path

    ui.console.print(
        ui.panel(
            config_table(config),
            title="⚙️  Config",
            border="border.info",
            subtitle=str(path),
        )
    )
