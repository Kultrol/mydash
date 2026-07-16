"""mydash — personal daily dashboard (multi-package).

Installable products:

- ``mydash`` (CLI): Rich → Typer → ``mydash.core``
- ``mydash-web`` (API): FastAPI → ``mydash.core``; UI in monorepo ``frontend/``

Shared domain lives in :mod:`mydash.core` (services, models, client).

``__path__`` is extended so sibling distributions (``mydash``, ``mydash-web``)
merge into this namespace under editable and wheel installs.
"""

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

__version__ = "0.5.0"
