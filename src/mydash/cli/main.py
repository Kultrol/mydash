import typer
from rich.console import Console
from rich.pretty import pprint
from src.mydash.client.weather.factory import get_weather_client
from src.mydash.client.geocoding.factory import get_geocoding_client
from rich.traceback import install

#Custom Rich Traceback displays
install(show_locals=True)


console = Console()
app = typer.Typer()

@app.command("cur_weather")
def display_current_weather(city:str = "Miami"):
    geocoding_client = get_geocoding_client()
    geocoding_coordinates = geocoding_client.get_coordinates(city)
    weather_client = get_weather_client()
    weather_client.set_coordinates(geocoding_coordinates)
    weather_client.set_forecast()
    weather_data = weather_client.get_weather_forecast()
    pprint(weather_data)





if __name__ == "__main__":
    app()
