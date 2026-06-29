import datetime
from pydantic import BaseModel


class StockQuote(BaseModel):
    ticker_name : str
    ask_price : float
    bid_price : float
    time : datetime.datetime

class StockQuotes(BaseModel):
    quotes : list[StockQuote]