"""mydash — terminal daily dashboard for weather, news, markets, and briefs.

Package layout:
    cli       Typer entry point and Rich renderers
    client    Pluggable API clients by domain (weather, geocoding, news, stocks)
    models    Shared domain Pydantic types
    services  Orchestration (BriefService, DailyBrief)

Each client domain uses a Protocol, factory, and one or more provider
implementations. Domain schemas live in ``models/``.
"""

__version__ = "0.5.0"
