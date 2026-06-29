import datetime

from pydantic import BaseModel


class HeadLine(BaseModel):
    headline : str
    publication : str
    description : str
    source_url : str
    category : str
    published_time : datetime.datetime

class NewsHeadlines(BaseModel):
    headlines : list[HeadLine]


