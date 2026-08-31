"""mydash — terminal daily dashboard for weather, news, markets, and briefs.

Package layout:
    cli       Typer entry point, theme, and Rich panel renderers
    client    Pluggable API clients by domain (weather, geocoding, news, stocks)
    models    Shared domain Pydantic types
    services  Orchestration (BriefService, DailyBrief, UserConfigurationService)
    storage   SQLite schema and the provider response cache

Each client domain uses a Protocol, factory, and one or more provider
implementations. Domain schemas live in ``models/``.
"""

__version__ = "0.6.0"
