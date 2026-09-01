from typing import Any

from pydantic import ValidationError

from mydash.client.geocoding.base_errors import (
    CityNotFoundError,
    GeocodingClientError,
    ResponseError,
)


class OpenMeteoClientError(GeocodingClientError): ...


class OpenMeteoResponseError(OpenMeteoClientError, ResponseError):
    """The API returned a response, but the data was invalid or unexpected.

    This covers:
    - Missing required fields
    - Wrong data types
    - Unexpected JSON structure
    """

    def __init__(self, message: str, details: Any = None):
        super().__init__(message)
        self.details = details


class OpenMeteoCityNotFoundError(OpenMeteoClientError, CityNotFoundError):
    """The search succeeded, but no matching city/location was found."""

    def __init__(self, query: str, details: Any = None):
        super().__init__(f"No results found for '{query}'")
        self.query = query
        self.details = details


class ParameterSettingError(OpenMeteoClientError):
    def __init__(self, validation_err: ValidationError):
        super().__init__(
            f"Failure to set parameters. Error occured: {validation_err.errors}"
        )
