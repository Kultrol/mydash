"""Shared domain models used by clients, services, and CLI.

Domain-specific Pydantic types live here so orchestration and presentation
layers do not import from client packages for pure data shapes.

Provider-only request/response helpers stay under ``client/*/providers/``.
"""
