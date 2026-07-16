"""Shared domain core for mydash products.

Holds orchestration (``services``), domain types (``models``), and data
access (``client``). Presentation layers (``cli``, ``api``) depend on
this package; core must not import Typer, Rich, FastAPI, or Next.js.
"""
