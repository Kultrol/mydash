"""Shared async HTTP plumbing for every provider client.

Adds three things on top of raw httpx:

* **Retries** — timeouts, connection errors, 429s, and 5xx are retried with
  exponential backoff and jitter, honouring ``Retry-After`` when the server
  sends one. Transient provider blips no longer fail a brief.
* **Connection reuse** — pass one client into several providers (via
  ``async with HttpApiClient() as http``) and they share a connection pool.
  Used standalone, each request opens and closes its own client.
* **Caching** — a ``cache_ttl`` on a GET routes through
  :class:`~mydash.storage.cache.ResponseCache`, so repeat runs are instant.

Errors are normalized into the exception family in
:mod:`mydash.client.http_api.errors`.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Final

import httpx

from mydash import __version__
from mydash.client.http_api.errors import (
    HttpApiError,
    HttpTimeoutError,
    RequestError,
    ResponseDecodeError,
    StatusCodeError,
)
from mydash.storage.cache import ResponseCache, build_key

#: Total seconds allowed for one attempt (connect + read + write + pool).
DEFAULT_TIMEOUT: Final[float] = 8.0
#: Retries *after* the first attempt, so 2 means up to three sends.
DEFAULT_RETRIES: Final[int] = 2
#: First backoff step; doubles per attempt, plus jitter.
DEFAULT_BACKOFF: Final[float] = 0.4
#: Never wait longer than this between attempts.
MAX_BACKOFF: Final[float] = 8.0

# Statuses worth a second try: the request itself was fine, the server was not.
RETRYABLE_STATUS_CODES: Final[frozenset[int]] = frozenset(
    {408, 425, 429, 500, 502, 503, 504}
)

USER_AGENT: Final[str] = f"mydash/{__version__} (+https://github.com/Kultrol/mydash)"

_CONNECTION_LIMITS: Final = httpx.Limits(
    max_connections=10, max_keepalive_connections=5
)


class HttpApiClient:
    """Make JSON requests with retries, optional caching, and shared connections."""

    def __init__(
        self,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        backoff: float = DEFAULT_BACKOFF,
        cache: ResponseCache | None = None,
        refresh: bool = False,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Configure request behaviour.

        :param timeout: Seconds allowed per attempt.
        :param retries: Extra attempts after the first (0 disables retrying).
        :param backoff: First backoff step in seconds; set 0 to retry at once.
        :param cache: Response cache; without one, ``cache_ttl`` is ignored.
        :param refresh: Skip cached reads but still refill the cache, so
            ``--refresh`` gets live data without throwing away the benefit.
        :param transport: Custom httpx transport, e.g. ``httpx.MockTransport``.
        """
        self.timeout = timeout
        self.retries = max(0, retries)
        self.backoff = max(0.0, backoff)
        self.cache = cache
        self.refresh = refresh
        self.transport = transport
        self._shared: httpx.AsyncClient | None = None

    # -- lifecycle ------------------------------------------------------

    async def __aenter__(self) -> HttpApiClient:
        """Open one connection pool shared by every request on this instance."""
        self._shared = self._build_client()
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the shared connection pool, if one is open."""
        if self._shared is not None:
            await self._shared.aclose()
            self._shared = None

    def _build_client(self) -> httpx.AsyncClient:
        """Build an httpx client with mydash's timeout, limits, and User-Agent."""
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=_CONNECTION_LIMITS,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            transport=self.transport,
        )

    @asynccontextmanager
    async def _client(self) -> AsyncIterator[httpx.AsyncClient]:
        """Yield the shared client, or a throwaway one closed on exit."""
        if self._shared is not None:
            yield self._shared
            return
        client = self._build_client()
        try:
            yield client
        finally:
            await client.aclose()

    # -- requests -------------------------------------------------------

    async def make_request(
        self,
        url: httpx.URL | str,
        request_method: str,
        timeout: float | None = None,
        headers: httpx.Headers | None = None,
        parameters: dict[str, Any] | None = None,
        cache_ttl: float | None = None,
    ) -> dict[str, Any]:
        """Send a request and return the decoded JSON body.

        Parameter values should already be validated by the caller — what a
        provider accepts is provider-specific.

        :param url: Endpoint URL, without query parameters.
        :param request_method: HTTP method, e.g. ``"GET"``.
        :param timeout: Per-call override of the instance timeout.
        :param headers: Extra headers (auth, accept) merged over the defaults.
        :param parameters: Query parameters.
        :param cache_ttl: Seconds to cache a successful GET. Needs a ``cache``.
        :raises HttpTimeoutError: The server did not answer in time.
        :raises RequestError: Network or connection failure.
        :raises StatusCodeError: Non-2xx response.
        :raises ResponseDecodeError: Body was not valid JSON.
        :raises HttpApiError: Any other httpx failure.
        """
        method = request_method.upper()
        cache_key = self._cache_key(method, url, parameters, cache_ttl)
        if cache_key is not None and not self.refresh:
            assert self.cache is not None  # narrowed by _cache_key
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        effective_timeout = self.timeout if timeout is None else timeout
        payload = await self._send_with_retries(
            url=url,
            method=method,
            timeout=effective_timeout,
            headers=headers,
            parameters=parameters,
        )

        if cache_key is not None and self.cache is not None and cache_ttl:
            self.cache.set(cache_key, payload, ttl=cache_ttl)
        return payload

    def _cache_key(
        self,
        method: str,
        url: httpx.URL | str,
        parameters: dict[str, Any] | None,
        cache_ttl: float | None,
    ) -> str | None:
        """Return a cache key, or ``None`` when this request is not cacheable."""
        if self.cache is None or not cache_ttl or method != "GET":
            return None
        return build_key(method, str(url), parameters)

    async def _send_with_retries(
        self,
        *,
        url: httpx.URL | str,
        method: str,
        timeout: float,
        headers: httpx.Headers | None,
        parameters: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Send the request, retrying transient failures, and decode the body."""
        async with self._client() as client:
            # build_request (rather than httpx.Request) merges the client's own
            # headers, so every provider call carries the mydash User-Agent.
            request = client.build_request(
                method=method,
                url=url,
                headers=headers,
                params=parameters,
                timeout=httpx.Timeout(timeout),
            )

            for attempt in range(self.retries + 1):
                last_attempt = attempt == self.retries
                try:
                    response = await client.send(request)
                except httpx.TimeoutException as err:
                    if last_attempt:
                        raise HttpTimeoutError(
                            url=request.url,
                            timeout=timeout,
                            method=method,
                            error=err,
                        ) from err
                except httpx.RequestError as err:
                    if last_attempt:
                        raise RequestError(
                            url=request.url, method=method, error=err
                        ) from err
                except httpx.HTTPError as err:
                    raise HttpApiError(err) from err
                else:
                    if (
                        response.status_code in RETRYABLE_STATUS_CODES
                        and not last_attempt
                    ):
                        await self._wait(attempt, response)
                        continue
                    return self._decode(request, response, method)

                await self._wait(attempt, None)

        # Unreachable: the loop always returns or raises on the last attempt.
        raise HttpApiError(f"request to {url!r} produced no response")

    @staticmethod
    def _decode(
        request: httpx.Request, response: httpx.Response, method: str
    ) -> dict[str, Any]:
        """Raise for a bad status, then parse the JSON body."""
        if response.is_error:
            raise StatusCodeError(
                request.url,
                response.status_code,
                method=method,
                response_text=response.text,
            )
        try:
            return response.json()
        except ValueError as err:
            raise ResponseDecodeError(
                url=request.url,
                status_code=response.status_code,
                response_text=response.text,
                error=err,
            ) from err

    async def _wait(self, attempt: int, response: httpx.Response | None) -> None:
        """Sleep before the next attempt, preferring a server's ``Retry-After``."""
        delay = self._retry_after(response)
        if delay is None:
            # Exponential backoff with jitter so concurrent panels do not
            # retry in lockstep.
            delay = min(MAX_BACKOFF, self.backoff * (2**attempt))
            if delay:
                delay += random.uniform(0, self.backoff)
        if delay:
            await asyncio.sleep(delay)

    @staticmethod
    def _retry_after(response: httpx.Response | None) -> float | None:
        """Return the ``Retry-After`` delay in seconds, when given as seconds."""
        if response is None:
            return None
        raw = response.headers.get("Retry-After")
        if not raw:
            return None
        try:
            # The HTTP-date form is rare for these providers; ignore it and
            # fall back to normal backoff.
            return min(MAX_BACKOFF, max(0.0, float(raw.strip())))
        except ValueError:
            return None
