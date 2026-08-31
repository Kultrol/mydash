"""Where mydash looks for provider credentials.

Installed globally, mydash runs from wherever you happen to be standing, so a
project-local ``.env`` is not something it can rely on. Credentials are read
from the first source that has them, highest precedence first:

1. Real environment variables — always win
2. ``MYDASH_ENV_FILE``, if you point it at a file
3. A ``.env`` beside (or above) the current directory — the developer path
4. ``.env`` in the mydash data directory — the one that works from anywhere

Nothing here ever writes a secret: :func:`write_template` only lays down a file
of placeholders for you to fill in.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from mydash.storage.database import default_database_path

ENV_FILENAME = ".env"

#: Point this at a file to override every other location.
ENV_FILE_ENV_VAR = "MYDASH_ENV_FILE"

#: Credentials mydash knows how to use.
ALPACA_KEY_VAR = "STOCK_ALPACA_API_KEY_ID"
ALPACA_SECRET_VAR = "STOCK_ALPACA_API_SECRET_KEY"

#: The values :data:`TEMPLATE` ships with. A file still holding these has not
#: been filled in, and must not read as configured credentials.
PLACEHOLDERS = frozenset({"your_alpaca_key_id", "your_alpaca_secret"})

TEMPLATE = f"""\
# mydash credentials
#
# Weather (Open-Meteo) and news (Noozra) need no API keys.
# Markets (Alpaca) need free credentials: https://alpaca.markets/
# Paper-trading keys work fine for market data.

{ALPACA_KEY_VAR}=your_alpaca_key_id
{ALPACA_SECRET_VAR}=your_alpaca_secret
"""


def user_env_path() -> Path:
    """Return the user-level env file, which lives beside the database.

    Following the database means ``MYDASH_DB_PATH`` isolates credentials too,
    so a throwaway setup never picks up your real keys.
    """
    return Path(default_database_path()).parent / ENV_FILENAME


def project_env_path() -> Path | None:
    """Return a ``.env`` found from the current directory upward, if any."""
    found = find_dotenv(filename=ENV_FILENAME, usecwd=True)
    return Path(found) if found else None


def explicit_env_path() -> Path | None:
    """Return the file named by ``MYDASH_ENV_FILE``, if it is set."""
    override = os.getenv(ENV_FILE_ENV_VAR)
    if override and override.strip():
        return Path(override.strip()).expanduser()
    return None


def candidate_paths() -> list[Path]:
    """Every env file mydash would consult, highest precedence first."""
    candidates = [explicit_env_path(), project_env_path(), user_env_path()]
    seen: list[Path] = []
    for candidate in candidates:
        if candidate is None:
            continue
        resolved = candidate.expanduser()
        if resolved not in seen:
            seen.append(resolved)
    return seen


def load_environment() -> list[Path]:
    """Load credentials into the environment and report which files were used.

    Values already in the real environment are never overwritten, and neither
    are values set by a higher-precedence file.
    """
    loaded: list[Path] = []
    for path in candidate_paths():
        if path.is_file():
            load_dotenv(path, override=False)
            loaded.append(path)
    return loaded


def is_configured(value: str | None) -> bool:
    """True when *value* is a real credential rather than blank or a placeholder.

    A freshly created template is not credentials. Saying "found" for one would
    send ``your_alpaca_key_id`` to Alpaca and turn a clear "fill this in" into a
    confusing 403.
    """
    if value is None:
        return False
    cleaned = value.strip()
    return bool(cleaned) and cleaned.lower() not in PLACEHOLDERS


def missing_alpaca_variables() -> list[str]:
    """Return the Alpaca variables that are unset, blank, or still placeholders."""
    return [
        name
        for name in (ALPACA_KEY_VAR, ALPACA_SECRET_VAR)
        if not is_configured(os.getenv(name))
    ]


def has_alpaca_credentials() -> bool:
    """True when both Alpaca variables hold real values."""
    return not missing_alpaca_variables()


def write_template(path: Path | None = None, *, overwrite: bool = False) -> Path:
    """Write a placeholder credentials file and return where it went.

    The file is written ``0600``, which restricts it to your account on Linux
    and macOS. Windows is not a supported platform and does not honour those
    bits the same way, so treat the file as world-readable there.

    :param path: Destination; defaults to :func:`user_env_path`.
    :param overwrite: Replace an existing file instead of refusing.
    :raises FileExistsError: If the file exists and *overwrite* is false — the
        one thing worse than no credentials is clobbering the real ones.
    """
    destination = Path(path) if path is not None else user_env_path()
    if destination.exists() and not overwrite:
        raise FileExistsError(f"{destination} already exists")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(TEMPLATE, encoding="utf-8")
    # Credentials file: owner-only on the platforms mydash supports.
    destination.chmod(0o600)
    return destination
