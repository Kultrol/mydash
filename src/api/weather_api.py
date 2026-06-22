from typing import Dict

from pydantic import BaseModel
import httpx
from rich import console

from src.api.geocoding_api import Coordinates
from rich.console import Console
from rich.panel import Panel

from datetime import datetime


class WeatherClient:
    """
        Concerns: Communicating with the Weather API and Transforming Raw API response into dataclasses/models
    """ 

    def __init__(self, http_client : httpx.Client | None = None, base_url : (str|None) = None, timeout: float = 10.0):
        self.base_url = base_url
        self.timout = timeout
        if http_client is None:
            self._client = httpx.Client(base_url = base_url, timeout = timeout)
        else:
            self._client = http_client

    def _make_request(self, url_parameters:dict) -> httpx.Response|None:
        """
        _make_request is an internal method that calls an API with parameters and returns the response. Its sole concern is calling the API.
        :param url_parameters: parameters that modify the API's response. For example: asking for current weather or changing units
        :return: api response.
        """
        try:
            response: httpx.Response = self._client.get(self.base_url, params=url_parameters)
            return response
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


    def set_forecast(self, coordinates:Coordinates, forecast_length: int = 15):
        params = {
            "latitude" : coordinates.latitude,
            "longitude" : coordinates.longitude,
            "hourly" : "temperature_2m",
            "past_days" : 1,
            "forecast_days": forecast_length,
        }
        api_response = self._make_request(url_parameters=params)
        weather_data = self._transform_response(response = api_response)

        current_day = DayForecast(month=0, day = 0, hours = [])

        weather_forecast: MultiDayForecast = MultiDayForecast(days = [])

        for index in range(0, len(weather_data["hourly"]["time"])):
            time : datetime = datetime.strptime(weather_data["hourly"]["time"][index], "%Y-%m-%dT%H:%M")
            temperature = weather_data["hourly"]["temperature_2m"][index]
            if current_day.day != time.day:
                current_day = DayForecast(month=time.month ,day = time.day, hours = [])
                if index != 0:
                    weather_forecast.days.append(current_day)
            current_day.hours.append(HourForecast(hour = str(time.hour), temperature = temperature))

        Console().print(weather_forecast)




class HourForecast(BaseModel):
    hour : str|int
    temperature : float

class DayForecast(BaseModel):
    month : str|int
    day : str|int
    hours : list[HourForecast]



class MultiDayForecast(BaseModel):
    days: list[DayForecast]
