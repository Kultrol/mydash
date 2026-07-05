from typing import Any, Dict

import httpx

from mydash.client.http_api.errors import (
    HttpApiError,
    HttpApiRequestError,
    HttpStatusCodeError,
)


class HttpApiClient:
    def make_request(
        self,
        url: httpx.URL,
        request_method: str,
        timeout: int = 5,
        headers: httpx.Headers | None = None,
        parameters: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        parameters' values should be validated before being passed as a dictionary to 'make_request'
            - it's implementation dependent, so ensure it matches what you're API expects.
        """
        client: httpx.Client = httpx.Client(timeout=timeout)
        request = httpx.Request(
            method=request_method, url=url, headers=headers, params=parameters
        )

        try:
            response = client.send(request=request)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as err:
            raise HttpApiRequestError(url=err.request.url)
        except httpx.HTTPStatusError as err:
            raise HttpStatusCodeError(err.request.url, err.response.status_code)
        except httpx.HTTPError as err:
            raise HttpApiError(err)
        finally:
            client.close()
