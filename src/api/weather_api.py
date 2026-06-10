from pydantic import BaseModel
import httpx
from src.api.geocoding_api import Coordinates


class WeatherClient:
    """
        Concerns: Communicating with the API and Transforming Raw API response into dataclasses/models
    """ 

    def __init__(self, http_client : httpx.Client | None = None, base_url : (str|None) = None, timeout: float = 10.0):
        self.base_url = base_url
        self.timout = timeout
        if http_client is None:
            self._client = httpx.Client(base_url = base_url, timeout = timeout)
        else:
            self._client = http_client

    def _make_request(self, url_parameters:dict):
        try:
            response = self._client.get(self.base_url, params=url_parameters)
            return response
        except httpx.RequestError as err:
            print(f"An error occurred while requesting: {err}")
        
    def _transform_response(self, response):
        return response.json()
   
    def get_current_weather(self, coordinates: Coordinates) -> CurrentTemperature:
        params = {
                    "latitude": coordinates["latitude"],
                    "longitude": coordinates["longitude"],
                    "current": ["temperature_2m", "apparent_temperature"],
                    "timezone": "auto",
            }
        response = self._make_request(params)
        data = self._transform_response(response)
        current_weather: CurrentTemperature = {
            "temperature" : data["current"]["temperature_2m"],
            "feels_like" : data["current"]["apparent_temperature"],
            "time" : data["current"]["time"]
        } 

        return current_weather




class CurrentTemperature(BaseModel):
    temperature : float
    feels_like : float
    time : str 



