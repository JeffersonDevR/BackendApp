import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os

app = FastAPI()

load_dotenv()


API_KEY= os.getenv("API_KEY")
BASE_URL = "http://api.weatherapi.com/v1"

class City(BaseModel):
    name: str

def get_coordinates(city_name: str):
    """
    Fetches latitude and longitude for the given city name.
    """
    params = {'key': API_KEY, 'q': city_name}
    response = requests.get(f"{BASE_URL}/current.json", params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    data = response.json()
    lat = data['location']['lat']
    lon = data['location']['lon']
    return lat, lon

def get_air_quality(lat: float, lon: float):
    """
    Fetches air quality data for the given latitude and longitude.
    """
    params = {'key': API_KEY, 'q': f"{lat},{lon}", 'aqi': 'yes'}
    response = requests.get(f"{BASE_URL}/current.json", params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    data = response.json()
    # Extract air quality details
    aqi_data = data.get('current', {}).get('air_quality', {})
    if not aqi_data:
        raise HTTPException(status_code=404, detail="Air quality data not available.")

    return {
        "pm10": aqi_data.get("pm10", "N/A"),
        "us_epa_index": aqi_data.get("us-epa-index", "N/A"),
        "general_status": determine_air_quality_status(aqi_data.get("us-epa-index", 0))
    }

def determine_air_quality_status(us_epa_index):
    """
    Determines general air quality status based on the US EPA index.
    """
    if us_epa_index == 1:
        return "Buena"
    elif us_epa_index == 2:
        return "Moderada"
    elif us_epa_index == 3:
        return "Insalubre para cierto tipo de personas"
    elif us_epa_index == 4:
        return "Insalubre"
    elif us_epa_index == 5:
        return "Demasiado insalubre"
    elif us_epa_index == 6:
        return "Peligroso"
    else:
        return "Desconocido"

@app.post("/air_quality/")
async def air_quality(city: City):
    """
    Endpoint to fetch air quality data for a given city.
    """
    # Step 1: Get coordinates based on city name
    lat, lon = get_coordinates(city.name)

    # Step 2: Get air quality data using the coordinates
    air_quality_data = get_air_quality(lat, lon)

    # Step 3: Return formatted air quality data
    return {"air_quality": air_quality_data}
