"""mydash — a terminal daily dashboard for weather, news, markets, and briefs.

Package layout:
    cli     Typer entry point and command definitions
    client  Pluggable API clients organized by domain (weather, geocoding, news, stocks)

Each client domain follows the same pattern: Protocol base, factory, Pydantic schemas,
and one or more provider implementations (e.g. Open-Meteo, Noozra, Alpaca).

TODO(docs): sync architecture overview and roadmap with README.md
TODO(config): document dev-dependency split and pytest settings in pyproject.toml
TODO(packaging): add __init__.py to client subpackages for explicit namespace documentation
"""