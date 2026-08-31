"""Process-wide CLI state.

Commands ask here for the user's configuration and for runtime flags set by the
root callback, so there is one place to patch in tests and one place to change
how the CLI reaches storage.
"""

from __future__ import annotations

from dataclasses import dataclass

from mydash.services.user_config import UserConfigurationService
from mydash.storage.cache import ResponseCache


@dataclass
class RuntimeFlags:
    """Flags parsed by the root callback, before any command runs."""

    debug: bool = False


#: Mutated by the root callback in ``mydash.cli.main``.
flags = RuntimeFlags()


def config_service() -> UserConfigurationService:
    """Open the user's configuration on the default database.

    Tests patch :class:`UserConfigurationService` on this module so every
    command shares one mock site.
    """
    return UserConfigurationService()


def response_cache(service: UserConfigurationService) -> ResponseCache:
    """Return a response cache sharing *service*'s database connection."""
    return ResponseCache(service.database)
