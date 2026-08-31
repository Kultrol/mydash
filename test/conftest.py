"""Shared pytest fixtures and stubs for mydash tests.

Provider clients take an ``http_client``, so tests inject
:class:`FakeHttpClient` instead of patching httpx. For tests that need the real
httpx stack — retries, header merging — see ``test/client/http_api``, which
drives ``httpx.MockTransport``.
"""

from typing import Any

import pytest

from mydash.storage.database import DB_PATH_ENV_VAR


@pytest.fixture(autouse=True)
def isolated_database(monkeypatch: pytest.MonkeyPatch, tmp_path_factory) -> None:
    """Point every test at a throwaway database.

    A test that builds ``UserConfigurationService()`` with no path would
    otherwise open the real user-data database — and on first run import and
    *rename* a developer's own config.json. This makes that impossible, and
    :func:`legacy_config_path` follows the override, so the legacy sweep stays
    inside the temp directory too.
    """
    directory = tmp_path_factory.mktemp("mydash-isolated")
    monkeypatch.setenv(DB_PATH_ENV_VAR, str(directory / "mydash.db"))


class FakeHttpClient:
    """Stand-in for ``HttpApiClient`` that replays canned responses.

    Pass payloads in call order; an ``Exception`` instance among them is raised
    when that call comes round, which is how provider error paths get tested.
    """

    def __init__(self, *responses: Any) -> None:
        self.responses: list[Any] = list(responses)
        self.calls: list[dict[str, Any]] = []

    async def make_request(self, **kwargs: Any) -> dict[str, Any]:
        """Record the call and return (or raise) the next canned response."""
        self.calls.append(kwargs)
        if not self.responses:
            raise AssertionError(
                f"unexpected request #{len(self.calls)} to {kwargs.get('url')}"
            )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    @property
    def call_count(self) -> int:
        return len(self.calls)

    def parameters(self, index: int = 0) -> dict[str, Any]:
        """Query parameters sent with call *index*."""
        return self.calls[index].get("parameters") or {}


@pytest.fixture
def alpaca_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide Alpaca credentials so header validation passes."""
    monkeypatch.setenv("STOCK_ALPACA_API_KEY_ID", "test-key-id")
    monkeypatch.setenv("STOCK_ALPACA_API_SECRET_KEY", "test-secret-key")


@pytest.fixture
def no_alpaca_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove Alpaca credentials from the environment."""
    monkeypatch.delenv("STOCK_ALPACA_API_KEY_ID", raising=False)
    monkeypatch.delenv("STOCK_ALPACA_API_SECRET_KEY", raising=False)
