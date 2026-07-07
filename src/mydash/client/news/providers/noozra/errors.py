from pydantic import ValidationError

from mydash.client.news.base_errors import NewsClientError


class NoozraClientError(NewsClientError): ...


class MissingArticlesError(NoozraClientError):
    def __init__(self, url: str):
        super().__init__(f"Missing Articles from :{url}.")


class ParameterSettingError(NoozraClientError):
    def __init__(self, validation_err: ValidationError):
        super().__init__(
            f"Failure to set parameters. Error occured: {validation_err.errors}"
        )


class HeadlineSettingError(NoozraClientError):
    def __init__(self, article, validation_err: ValidationError):
        super().__init__(f"Failed to validate article: {article}. \n {validation_err}")


class MissingNewsHeadlinesError(NoozraClientError):
    def __init__(self):
        super().__init__(
            "Headlines not found. Headlines must be set by 'set_news_headlines'."
        )
