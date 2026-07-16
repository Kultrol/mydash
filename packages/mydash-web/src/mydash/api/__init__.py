"""HTTP API presentation layer for mydash (FastAPI).

This package is the web-server half of the web product, parallel to
:mod:`mydash.cli` for the terminal product.

Architecture::

    CLI product:  Rich → Typer → core/
    Web product:  Next.js → FastAPI (this package) → core/

Owns HTTP routes, request/response wiring, CORS, and status codes.
Does not own provider HTTP, JSON parsing, or multi-step fetch
orchestration (those live in :mod:`mydash.core.services`).
"""
