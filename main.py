import typer
from rich.console import Console
from rich.panel import Panel
from src.api.geocoding_api import GeocodingClient
from src.api.weather_api import WeatherClient  

console = Console()
app = typer.Typer()

@app.command()
def display_current_temperature(city:str = "Miami"):
    geocoding_client = GeocodingClient(base_url = "https://geocoding-api.open-meteo.com/v1/search")
    coordinates = geocoding_client.get_coordinates(city)

    weather_client = WeatherClient(base_url = "https://api.open-meteo.com/v1/forecast")
    current_weather = weather_client.get_current_weather(coordinates)
    console.print(Panel(f"[{current_weather["time"]}] - Current temperature: {current_weather["temperature"]}C, 'Feels Like': {current_weather["feels_like"]}C", ))




if __name__ == "__main__":
    app()
