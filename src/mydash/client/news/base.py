from typing import Protocol, Any
from abc import abstractmethod
from .schemas import NewsHeadlines




class NewsClient(Protocol):

    @abstractmethod
    def _make_request(self, params) -> Any:
        """

        :param params:
        :return:
        """

    @abstractmethod
    def set_news_headlines(self) -> None:
        """

        :return:
        """

    @abstractmethod
    def get_news_headlines(self) -> NewsHeadlines:
        """

        :return:
        """


