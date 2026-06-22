import httpx
from pydantic import BaseModel


class GeocodingClient:

    def __init__(self, http_client: httpx.Client | None = None, base_url:httpx.URL | None = None, timeout:float = 10.0):
        self.base_url = base_url
        self.timeout = timeout
        if http_client is None:
            self._client = httpx.Client(base_url = self.base_url, timeout = self.timeout)
        else:
            self._client = http_client
    

    def _geocoding_request(self, url_params:dict):
        try:
            response = self._client.get(self.base_url, params = url_params)
            return response
        except httpx.RequestError as err:
            print(f"An error occured: {err}")

    def _geoconding_transform(self, response):
        return response.json()


    def get_coordinates(self, city:str) -> Coordinates:
        params = {
            "name" : city.lower(),
        }

        response = self._geocoding_request(params)
        data = self._geoconding_transform(response)
        coordinates : Coordinates = Coordinates(
            latitude = data["results"][0]["latitude"],
            longitude = data["results"][0]["longitude"]
        )
        return coordinates



class Coordinates(BaseModel):
    latitude : float
    longitude : float



