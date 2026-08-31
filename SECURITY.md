# Security

## Reporting an issue

Please report suspected vulnerabilities privately through
[GitHub Security Advisories](https://github.com/Kultrol/mydash/security/advisories/new)
rather than a public issue. Include what you did, what happened, and the mydash
version from `mydash --version`.

This is a personal project maintained in spare time. Expect an initial response
within a couple of weeks.

## What mydash does with your data

Worth knowing before you go looking:

- **Credentials never leave your machine except to the provider they
  authenticate.** The Alpaca key and secret are read from the environment or a
  local file (`mydash config env` shows exactly which), and are sent only to
  `data.alpaca.markets` as request headers.
- **Nothing is sent to the maintainer.** There is no telemetry, no crash
  reporting, and no update check.
- **Credentials are never written to the database.** `mydash.db` holds your
  preferences and cached provider responses. Cache keys are derived from the
  request method, URL, and query parameters — auth headers are deliberately
  excluded, so no secret ends up in a cached row.
- **Your location is sent to the weather and geocoding provider.** Setting a city
  sends that name to Open-Meteo; each forecast sends the resulting coordinates.
  Open-Meteo requires no account.
- **`mydash config env --create` writes a file with `0600` permissions**, which
  restricts access on Linux and macOS. Windows is not a supported platform, and
  Python's `chmod` does not provide the same restriction there.

## Scope

In scope: anything that discloses your credentials, writes them somewhere they
should not be, executes code from a provider response, or lets a malicious
response corrupt the local database.

Out of scope: the security of the upstream providers themselves, and anything
that requires an attacker to already have write access to your home directory.
