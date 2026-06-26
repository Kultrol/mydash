from pydantic import BaseModel


class HourForecast(BaseModel):
    hour : int
    temperature : float
    feels_like_temperature : float
    cloud_cover : int
    wind_speed : float
    chance_of_rain : int
    amount_of_rain : float
    weather_code : int
    uv_index : float



class DayForecast(BaseModel):
    month : int
    day : int
    hours : list[HourForecast]

class MultiDayForecast(BaseModel):
    days: list[DayForecast]
