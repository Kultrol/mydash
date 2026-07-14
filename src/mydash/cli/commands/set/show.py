"""``mydash set show`` — dump the current user configuration as JSON."""

from __future__ import annotations

import json

from rich.console import Group
from rich.json import JSON
from rich.text import Text

from mydash.cli.commands.set._helpers import config_service, info


def show() -> None:
    """Print the on-disk user configuration inside a Rich info panel."""
    cfg = config_service().get_configuration()
    payload = cfg.model_dump(mode="json")
    body = Group(
        Text("Current user configuration:", style="bold bright_white"),
        Text(""),
        JSON(json.dumps(payload)),
    )
    info(body, title="⚙️  Config")
