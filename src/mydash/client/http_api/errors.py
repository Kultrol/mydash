class HttpApiError(Exception):
    def __init__(self, general_err):
        super().__init__(general_err)


class RequestError(HttpApiError):
    def __init__(self, url, method=None, error=None):
        self.url = url
        self.method = method
        if method is not None and error is not None:
            super().__init__(
                f"Error while requesting {method} {url!r}. \n Error: {error}"
            )
        elif error is not None:
            super().__init__(f"Error while requesting {url!r}. \n Error: {error}")
        elif method is not None:
            super().__init__(f"Error while requesting {method} {url!r}")
        else:
            super().__init__(f"Error while requesting {url!r}")


class HttpTimeoutError(RequestError):
    # Named HttpTimeoutError so it doesn't clash with the built-in TimeoutError
    def __init__(self, url, timeout=None, method=None, error=None):
        self.url = url
        self.method = method
        self.timeout = timeout
        timeout_info = f" (timeout={timeout}s)" if timeout is not None else ""
        method_info = f"{method} " if method is not None else ""
        error_info = f" \n Error: {error}" if error is not None else ""
        # Call HttpApiError directly so we keep a timeout-specific message
        HttpApiError.__init__(
            self,
            f"Request timed out while requesting {method_info}{url!r}"
            f"{timeout_info}.{error_info} The server did not respond in time. "
            f"Try again later or increase the timeout.",
        )


class StatusCodeError(HttpApiError):
    def __init__(self, url, status_code, method=None, response_text=None):
        self.url = url
        self.status_code = status_code
        self.method = method
        self.response_text = response_text

        method_info = f"{method} " if method is not None else ""

        # Give a more helpful message depending on the status code
        if status_code == 400:
            message = (
                f"Bad Request (400) while requesting {method_info}{url!r}. "
                f"The request was malformed or had invalid parameters. "
                f"Check your parameters/URL before calling the API."
            )
        elif status_code == 401:
            message = (
                f"Unauthorized (401) while requesting {method_info}{url!r}. "
                f"Authentication failed or credentials are missing/invalid. "
                f"Check your API key/secret headers and env variables."
            )
        elif status_code == 403:
            message = (
                f"Forbidden (403) while requesting {method_info}{url!r}. "
                f"You are authenticated but not allowed to access this resource. "
                f"Check account permissions or scopes."
            )
        elif status_code == 404:
            message = (
                f"Not Found (404) while requesting {method_info}{url!r}. "
                f"The resource or endpoint was not found. "
                f"Check the URL path and any resource identifiers."
            )
        elif status_code == 405:
            message = (
                f"Method Not Allowed (405) while requesting {method_info}{url!r}. "
                f"This HTTP method is not supported for this URL. "
                f"Use the method the API documents (usually GET)."
            )
        elif status_code == 409:
            message = (
                f"Conflict (409) while requesting {method_info}{url!r}. "
                f"The request conflicts with the current server state. "
                f"Resolve the conflict, then try again."
            )
        elif status_code == 422:
            message = (
                f"Unprocessable Entity (422) while requesting {method_info}{url!r}. "
                f"The request was understood but failed validation. "
                f"Check your body/params against what the API expects."
            )
        elif status_code == 429:
            message = (
                f"Too Many Requests (429) while requesting {method_info}{url!r}. "
                f"You are being rate limited by the API. "
                f"Wait and retry; try making fewer requests."
            )
        elif status_code == 500:
            message = (
                f"Internal Server Error (500) while requesting {method_info}{url!r}. "
                f"The remote server failed while handling the request. "
                f"Try again later — this is not always a client bug."
            )
        elif status_code == 502:
            message = (
                f"Bad Gateway (502) while requesting {method_info}{url!r}. "
                f"An upstream gateway got a bad response. "
                f"Try again; the provider or proxy may be down temporarily."
            )
        elif status_code == 503:
            message = (
                f"Service Unavailable (503) while requesting {method_info}{url!r}. "
                f"The service is temporarily unavailable. "
                f"Retry later and check the provider status if it keeps happening."
            )
        elif status_code == 504:
            message = (
                f"Gateway Timeout (504) while requesting {method_info}{url!r}. "
                f"An upstream server took too long to respond. "
                f"Try again later."
            )
        elif 400 <= status_code < 500:
            message = (
                f"Client Error ({status_code}) while requesting {method_info}{url!r}. "
                f"The server rejected the request as a client-side error. "
                f"Inspect the status code, URL, and response body."
            )
        elif 500 <= status_code < 600:
            message = (
                f"Server Error ({status_code}) while requesting {method_info}{url!r}. "
                f"The remote server failed while handling the request. "
                f"Try again later; report it if it keeps happening."
            )
        else:
            message = (
                f"Error response {status_code} while requesting {method_info}{url!r}."
            )

        if response_text is not None:
            message = f"{message} \n Response body: {response_text}"

        super().__init__(message)


class ResponseDecodeError(HttpApiError):
    def __init__(self, url, status_code=None, response_text=None, error=None):
        self.url = url
        self.status_code = status_code
        self.response_text = response_text

        status_info = f" (status {status_code})" if status_code is not None else ""
        message = (
            f"Invalid JSON response from {url!r}{status_info}. "
            f"The server returned a body that could not be parsed as JSON. "
            f"Make sure the endpoint returns JSON."
        )
        if response_text is not None:
            message = f"{message} \n Response body: {response_text}"
        if error is not None:
            message = f"{message} \n Error: {error}"

        super().__init__(message)
