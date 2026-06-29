from pydantic import BaseModel


class Coordinates(BaseModel):
    latitude : float
    longitude : float


#Open Meteo's Geocoding API is mature, thus we can model the API's parameters and expect them to remain fixed.
class GeocodingParams(BaseModel):
    name : str = ""