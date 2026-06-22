from pydantic import BaseModel
import httpx

from src.api.geocoding_api import Coordinates
from rich.console import Console

from datetime import datetime


class WeatherClient:
    """
        Concerns: Communicating with the Weather API and Transforming Raw API response into dataclasses/models
    """ 

    def __init__(self, http_client : httpx.Client | None = None, base_url : httpx.URL | None = None, timeout: float = 10.0):
        self.weather_forecast = None
        self.base_url = base_url
        self.timeout = timeout
        if http_client is None:
            if base_url is not None:
                self._client = httpx.Client(base_url = base_url, timeout = timeout)
            else:
                self._client = http_client
        else:
            self._client = http_client

    def _make_request(self, url_parameters:dict) -> httpx.Response|None:
        """
        _make_request is an internal method that calls an API with parameters and returns the response. Its sole concern is calling the API.
        :param url_parameters: parameters that modify the API's response. For example: asking for current weather or changing units
        :return: api response.
        """
        try:
            if self.base_url is not None:
                if self._client is not None:
                    response: httpx.Response = self._client.get(self.base_url, params=url_parameters)
                    return response
                else:
                    Console().log(f"In '_make_request', self._client is of type {type(self._client)}")
            else:
                Console().log(f"In '_make_request', self.base_url is of type {type(self.base_url)}")
        except httpx.RequestError as err:
            Console().log(f"An error occurred while requesting: {err}")
            return None

    def _transform_response(self, response: httpx.Response):
        """
        _transform_response is a method that transforms the response given into JSON
        :param response: a response from an API
        :return: the response in a JSON format
        """
        return response.json()


    def set_forecast(self, coordinates:Coordinates, forecast_length: int = 3) -> None:
        params = {
            "latitude" : coordinates.latitude,
            "longitude" : coordinates.longitude,
            "hourly": ["temperature_2m", "apparent_temperature", "precipitation_probability", "precipitation", "weather_code", "cloud_cover", "wind_speed_10m", "uv_index"],
            "past_days" : 1,
            "forecast_days": forecast_length,
        }
        api_response = self._make_request(url_parameters=params)
        if api_response is not None:
            weather_data = self._transform_response(response = api_response)
        else:
            Console().log(f"In 'set_forecast', api_response is of type {type(api_response)}")
            return None

        current_day = DayForecast(month=0, day = 0, hours = [])

        weather_forecast: MultiDayForecast = MultiDayForecast(days = [])

        for index in range(0, len(weather_data["hourly"]["time"])):
            hourly_data = weather_data["hourly"]
            time : datetime = datetime.strptime(hourly_data["time"][index], "%Y-%m-%dT%H:%M")
            temperature = hourly_data["temperature_2m"][index]
            feels_like_temperature: float= hourly_data["apparent_temperature"][index]
            cloud_cover: int= hourly_data["cloud_cover"][index]
            wind_speed: float= hourly_data["wind_speed_10m"][index]
            chance_of_rain: int= hourly_data["precipitation_probability"][index]
            amount_of_rain: float= hourly_data["precipitation"][index]
            weather_code: int = hourly_data["weather_code"][index]
            uv_index : float = hourly_data["uv_index"][index]


            if current_day.day != time.day:
                current_day = DayForecast(month=time.month ,day = time.day, hours = [])
                if index != 0:
                    weather_forecast.days.append(current_day)
            current_day.hours.append(HourForecast(
                hour = str(time.hour),
                temperature = temperature,
                feels_like_temperature = feels_like_temperature,
                cloud_cover = cloud_cover,
                wind_speed = wind_speed,
                chance_of_rain = chance_of_rain,
                amount_of_rain = amount_of_rain,
                weather_code = weather_code,
                uv_index = uv_index
            ))

        self.weather_forecast = weather_forecast
        return None

    def get_weather_forecast(self) -> MultiDayForecast:
        return self.weather_forecast

# -------------------------------------------
# --------------- Models --------------------
# -------------------------------------------
class HourForecast(BaseModel):
    hour : str|int
    temperature : float
    feels_like_temperature : float
    cloud_cover : int
    wind_speed : float
    chance_of_rain : int
    amount_of_rain : float
    weather_code : int
    uv_index : float



class DayForecast(BaseModel):
    month : str|int
    day : str|int
    hours : list[HourForecast]

class MultiDayForecast(BaseModel):
    days: list[DayForecast]
