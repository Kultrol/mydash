import typer
import httpx
from rich.console import Console
from rich.panel import Panel
from dataclasses import dataclass


console = Console()

#console.print(Panel("Hello, [red]World!"))

geocoding_params = {
    "name" : str
}

app = typer.Typer()


#======================================
#          Calling the API 
#======================================
def geocoding_info(city : str, verbose:bool = False):
    geocoding_params["name"] = city.lower()
    try:
        geocoding_resp = httpx.get("https://geocoding-api.open-meteo.com/v1/search", params=geocoding_params)
        geocoding_data = geocoding_resp.json()

        if verbose:
            console.rule("GEOCODING API RESPONSE")
            console.print_json(data=geocoding_data["results"][0])
            console.rule()

        geocoding_latitude = geocoding_data["results"][0]["latitude"]
        geocoding_longitude = geocoding_data["results"][0]["longitude"]
        return (geocoding_latitude, geocoding_longitude)
    except Exception as error:
        console.print(f"[red]Geocoding Error: {error}[/red]")
        console.print(f"City - {city}, not found. Try again.")
        exit(1)



def weather_caller(latitude, longitude, verbose:bool = False, url = "https://api.open-meteo.com/v1/forecast", params = {
    "latitude" : 25.823131,
    "longitude" : -80.2256272
}):
    try:
        weather_resp = httpx.get(url, params=params)
        weather_data = weather_resp.json() 
        if verbose:
            console.rule("API RESPONSE")
            console.print_json(data=weather_data)
            console.rule()
        return weather_data
    except Exception as e:
       console.print(f"Weather API ERROR: {e}")

#==============================================
#        Creating Models and Loading Data
#===============================================

@dataclass
class CurrentTemperature:
    current_temperature : float
    feels_like_temperature : float
    time : str
    units : str

def current_temperature_loader(weather_data, verbose:bool):
    return CurrentTemperature(
        current_temperature = weather_data["current"]["temperature_2m"],
        feels_like_temperature = weather_data["current"]["apparent_temperature"],
        time = weather_data["current"]["time"],
        units = weather_data["current_units"]["temperature_2m"]
    )
   

#current_temp = current_temperature_loader(weather_caller("Miami"))
#console.print(current_temp)

#================================================
#Display Current Temperature
#================================================
def display_current_temperature(current_temp: CurrentTemperature):
    console.print(Panel(f"[{current_temp.time}] - Current temperature: {current_temp.current_temperature}{current_temp.units}, 'Feels Like': {current_temp.feels_like_temperature}{current_temp.units}", ))

@app.command()
def current_temperature(city: str = "Miami", verbose:bool = False):

    weather_params = {
        "latitude": None,
        "longitude":None, 
        "current": ["temperature_2m", "apparent_temperature"],
        "timezone": "auto"
    }

    geocoding_latitude, geocoding_longitude = geocoding_info(city, verbose)
    weather_params["latitude"] = geocoding_latitude
    weather_params["longitude"] = geocoding_longitude
    weather_data = weather_caller(geocoding_latitude, geocoding_longitude, verbose, params=weather_params)
    current_temperature = current_temperature_loader(weather_data, verbose)
    display_current_temperature(current_temperature)



if __name__ == "__main__":
    app()
