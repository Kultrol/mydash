from abc import abstractmethod
from typing import Protocol, runtime_checkable, Any

from client.weather.schemas import MultiDayForecast


@runtime_checkable
class WeatherClient(Protocol):

    @abstractmethod
    def _make_request(self, params) -> Any:
        """

        :param params:
        :return:
        """
        ...

    @abstractmethod
    def set_forecast(self, forecast_length: int = 0) -> None:
        """

        :param forecast_length:
        :return:
        """
        ...

    @abstractmethod
    def get_weather_forecast(self) -> MultiDayForecast:
        """

        :return:
        """
        ...

