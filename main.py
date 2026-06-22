import time

import httpx
import typer
from rich.console import Console
from rich.live import Live

from src.api.geocoding_api import GeocodingClient, Coordinates
from src.api.weather_api import WeatherClient

console = Console()
app = typer.Typer()

@app.command("cur_temp")
def display_current_temperature(city:str = "Miami"):
    geocoding_url = httpx.URL("https://geocoding-api.open-meteo.com/v1/search")
    geocoding_client = GeocodingClient(base_url = geocoding_url)
    coordinates : Coordinates = geocoding_client.get_coordinates(city)
    weather_url = httpx.URL("https://api.open-meteo.com/v1/forecast")
    weather_client = WeatherClient(base_url = weather_url)
    weather_client.set_forecast(coordinates)
    console.print(weather_client.get_weather_forecast())


@app.command("brief")
def explore():
    timer = 0
    with Live(f"{timer}", refresh_per_second=4) as live:
        for num in range(61):
            time.sleep(1)
            timer += 1
            live.update(f"{timer}")




if __name__ == "__main__":
    app()
