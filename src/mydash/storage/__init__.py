"""SQLite-backed persistence for mydash.

One database file holds everything the CLI needs between runs:

* ``settings`` / ``watchlist`` — user preferences (see
  :mod:`mydash.services.user_config`)
* ``response_cache`` — short-lived provider responses (see
  :mod:`mydash.storage.cache`)
"""

from mydash.storage.database import Database, default_database_path

__all__ = ["Database", "default_database_path"]
