class StockClientError(Exception): ...


class StockFactoryError(Exception):
    def __init__(self, provider: str):
        super().__init__(
            f"Unknown Provider: {provider}. Please choose a valid provider"
        )
