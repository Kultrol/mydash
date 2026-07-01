from mydash.client.stocks.base import StockClient
from .alpaca import AlpacaClient


def get_stock_client(provider : str = "alpaca", **config) -> StockClient:
    if provider == "alpaca":
        return AlpacaClient()
    else:
        raise ValueError("Unknown provider. Please choose a valid provider")


