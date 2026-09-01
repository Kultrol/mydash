from typing import Any

from pydantic import ValidationError

from mydash.client.stocks.base_errors import StockClientError


class AlpacaClientErrors(StockClientError): ...


class MissingCredentialsError(AlpacaClientErrors):
    """Alpaca needs an API key and secret; one or both were not in the env."""

    def __init__(self, missing: list[str]):
        self.missing = list(missing)
        names = ", ".join(self.missing)
        super().__init__(
            f"Alpaca credentials are missing: {names}. "
            "Market data needs a free Alpaca key — put the values in a .env "
            "file next to your project (see .env.example) or export them in "
            "your shell. Weather and headlines work without them."
        )


class ParameterSettingError(AlpacaClientErrors):
    def __init__(self, validation_err: ValidationError):
        super().__init__(
            f"Failure to set parameters. Error occured: {validation_err.errors}"
        )


class ResponseError(AlpacaClientErrors):
    def __init__(self, query: Any, api_response: Any, error: Exception | None = None):
        message = (
            f"Response error occurred. \n Parameters provided: {query} "
            f"\n API Response: {api_response}"
        )
        if error is not None:
            message = f"{message} \n\n Error: {error}"
        super().__init__(message)
