from typing import Any

from pydantic import ValidationError

from mydash.client.news.base_errors import NewsClientError


class NoozraClientError(NewsClientError): ...


class MissingArticlesError(NoozraClientError):
    def __init__(self, url: str, category: str | None = None):
        detail = f" for category {category!r}" if category else ""
        super().__init__(f"No articles returned from {url}{detail}.")


class NoUsableArticlesError(NoozraClientError):
    """Articles came back, but not one of them had the fields we need."""

    def __init__(self, url: str, details: Any = None):
        super().__init__(
            f"Articles from {url} were all missing required fields "
            "(headline, source, url, or published_at)."
        )
        self.details = details


class ParameterSettingError(NoozraClientError):
    def __init__(self, validation_err: ValidationError):
        super().__init__(
            f"Failure to set parameters. Error occured: {validation_err.errors}"
        )
