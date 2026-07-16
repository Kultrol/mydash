from pydantic import ValidationError

from mydash.core.client.stocks.base_errors import StockClientError


class AlpacaClientErrors(StockClientError): ...


class HeaderValidationError(AlpacaClientErrors):
    def __init__(self, api_key_type, api_secret_type, type_of_content_type):
        super().__init__(
            f"Header validation failed. /Potentially invalid api key, secret, content-type. API key Type: {api_key_type}. API secret Type: {api_secret_type}. Content-Type Type: {type_of_content_type}"
        )


class MissingStockQuotesError(AlpacaClientErrors):
    def __init__(self):
        super().__init__(
            "Stock Quotes not found. Stock Quotes must be fetched and set by 'set_current_stock_quotes'."
        )


class MissingStockBarsError(AlpacaClientErrors):
    def __init__(self):
        super().__init__(
            "Stock Bars not found. Stock Bars must be fetched and set by 'set_current_stock_bars'."
        )


class ParameterSettingError(AlpacaClientErrors):
    def __init__(self, validation_err: ValidationError):
        super().__init__(
            f"Failure to set parameters. Error occured: {validation_err.errors}"
        )


class StockQuotesSettingError(AlpacaClientErrors):
    def __init__(self, validation_err: ValidationError):
        super().__init__(
            f"Failure to set stock quotes. Error occured: {validation_err.errors}"
        )


class StockBarsSettingError(AlpacaClientErrors):
    def __init__(self, validation_err: ValidationError):
        super().__init__(
            f"Failure to set stock bars. Error occured: {validation_err.errors}"
        )


class ResponseError(AlpacaClientErrors):
    def __init__(self, query, api_response, error: None | KeyError = None):
        if error is not None:
            super().__init__(
                f"Response error occurred. \n Parameters provided: {query} \n API Response: {api_response} \n\n Error: {error}"
            )
        else:
            super().__init__(
                f"Response error occurred. \n Parameters provided: {query} \n API Response: {api_response}"
            )
