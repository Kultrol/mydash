"""Shared domain core for mydash products.

Holds orchestration (``services``), domain types (``models``), and data
access (``client``). Presentation layers (``cli``, ``api``) depend on
this package; core must not import Typer, Rich, FastAPI, or Next.js.

``mydash`` is a PEP 420 namespace package: ``mydash-core``, ``mydash`` (CLI),
and ``mydash-web`` each contribute a portion (``core/``, ``cli/``, ``api/``)
with no root ``mydash/__init__.py``.
"""

__version__ = "0.5.0"
