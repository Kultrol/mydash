from abc import abstractmethod
from typing import Any, Protocol

from mydash.client.geocoding.schemas import Coordinates


class GeocodingClient(Protocol):
    @abstractmethod
    def _make_request(self, params) -> Any:
        """

        :param params:
        :return:
        """

    @abstractmethod
    def set_coordinates(self, city: str) -> None:
        """

        :param city:
        :return:
        """

    def get_coordinates(self, city: str) -> Coordinates:
        """

        :param city:
        :return:
        """
        ...
