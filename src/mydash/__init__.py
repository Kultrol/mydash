"""mydash — a terminal daily dashboard for weather, news, markets, and briefs.

Package layout:
    cli     Typer entry point and command definitions
    client  Pluggable API clients organized by domain (weather, geocoding, news, stocks)
    models  Shared domain Pydantic types used by clients, services, and CLI
    services  Domain orchestration (in progress)

Each client domain follows the same pattern: Protocol base, factory, and one or more
provider implementations (e.g. Open-Meteo, Noozra, Alpaca). Domain schemas live in
``models/``; provider-only request helpers stay under each provider package.
"""
