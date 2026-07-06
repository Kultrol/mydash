from mydash.client.news.errors import NewsClientError


class NoozraClientError(NewsClientError): ...


class MissingArticlesError(NoozraClientError):
    def __init__(self, url: str):
        super().__init__(f"Missing Articles from :{url}.")
