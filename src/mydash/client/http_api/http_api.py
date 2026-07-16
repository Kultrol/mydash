from typing import Any, Dict

import httpx

from mydash.client.http_api.errors import (
    HttpApiError,
    HttpTimeoutError,
    RequestError,
    ResponseDecodeError,
    StatusCodeError,
)


class HttpApiClient:
    async def make_request(
        self,
        url: httpx.URL,
        request_method: str,
        timeout: int = 5,
        headers: httpx.Headers | None = None,
        parameters: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Makes an HTTP request and returns the JSON response as a dict.

        parameters' values should be validated before being passed as a dictionary to 'make_request'
            - it's implementation dependent, so ensure it matches what your API expects.

        Raises:
            HttpTimeoutError: if the request times out
            RequestError: if a network/request error occurs (connection issues, etc.)
            StatusCodeError: if the response has a bad status code (4xx/5xx)
            ResponseDecodeError: if the response body is not valid JSON
            HttpApiError: for other httpx errors
        """
        request = httpx.Request(
            method=request_method, url=url, headers=headers, params=parameters
        )

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.send(request=request)
                response.raise_for_status()

                # Try to parse JSON — raise ResponseDecodeError if it fails
                try:
                    return response.json()
                except ValueError as err:
                    raise ResponseDecodeError(
                        url=request.url,
                        status_code=response.status_code,
                        response_text=response.text,
                        error=err,
                    ) from err

        # TimeoutException is a subclass of RequestError, so catch it first
        except httpx.TimeoutException as err:
            raise HttpTimeoutError(
                url=err.request.url,
                timeout=timeout,
                method=request_method,
                error=err,
            ) from err
        except httpx.HTTPStatusError as err:
            raise StatusCodeError(
                err.request.url,
                err.response.status_code,
                method=err.request.method,
                response_text=err.response.text,
            ) from err
        except httpx.RequestError as err:
            raise RequestError(
                url=err.request.url, method=request_method, error=err
            ) from err
        except httpx.HTTPError as err:
            raise HttpApiError(err) from err
