class HttpApiError(Exception):
    def __init__(self, general_err):
        super().__init__(f"Error occured: {general_err}")


class HttpApiRequestError(HttpApiError):
    def __init__(self, url):
        super().__init__(f"Error while requesting {url!r}")
        self.url = url


class HttpStatusCodeError(HttpApiError):
    def __init__(self, url, status_code):
        super().__init__(f"Error response {status_code} while requesting {url!r}.")
        self.url = url
        self.status_code = status_code
