from dataclasses import dataclass


@dataclass
class CurrentWeather:
    temperature : float # Actual temperature in C or F
    feels_like_temperature : float # Apperent temperature in C or F
    wind_speed : float # Wind speed in MPH or KPH
    cloud_cover : int # Percentage of cloud cover at the current latitude and longitude
    uv_index : float  
    time: str  # Format: YYYY-MM-DD

    
@dataclass
class HourForecast:
    hour : str
    temperature : float
    feels_like_temperature : float
    chance_of_percipitation : float
    amount_of_percipitation : float
    cloud_cover : int
    wind_speed : float
    uv_index : float





@dataclass
class DayForecast:
    day : str
    hours : list[str] 
    temperature : list[float]
    feels_like_temperature : list[float]
    chance_of_percipitation : list[float]
    amount_of_percipitation : list[float] #Total precipitation in the preceding hour in mm or inches
    cloud_cover : list[int]
    wind_speed : list[float]
    uv_index : list[float]
    max_uv_index: float
    max_temperature: float
    min_temperature: float

    weather_code : int | None # Specific to the MeteoAPI this 


@dataclass
class MultiDayForecast:
    multi_day_forecast : list[DayForecast]

@dataclass
class WeatherReport:
    current_weather : CurrentWeather
    multi_day_forecast : MultiDayForecast





    

