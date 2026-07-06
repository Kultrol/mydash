class AlpacaClientErrors(Exception): ...


class HeaderValidationError(AlpacaClientErrors):
    def __init__(self, api_key_type, api_secret_type, type_of_content_type):
        super().__init__(
            f"Header validation failed. /Potentially invalid api key, secret, content-type. API key Type: {api_key_type}. API secret Type: {api_secret_type}. Content-Type Type: {type_of_content_type}"
        )
