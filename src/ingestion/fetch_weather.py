import requests
import pandas as pd

CITIES = {
    "Nantes": {"lat": 47.2172, "lon": -1.5534},
    "Bordeaux": {"lat": 44.8412, "lon": -0.5805},
}

BASE_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather_city(city: tuple[str, dict]) -> pd.DataFrame:
    city_name, coordinates = city
    params = {
        "latitude": coordinates["lat"],
        "longitude": coordinates["lon"],
        "hourly": [
            "temperature_2m",
            "rain",
            "wind_speed_10m",
        ],
        "timezone": "Europe/London",
        "forecast_days": 1
    }
    
    response = requests.get(url=BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()["hourly"]
    
    df = pd.DataFrame(data)
    df["City"] = city_name
    df = df.rename(
        columns={
            "time": "date",
            "temperature_2m": "temp_celcius",
            "rain": "rain_mm",
            "wind_speed_10m": "wind_speed_kmh",
        }
    )
    df["date"] = pd.to_datetime(df["date"])
    return df
    
def fetch_weather_all_cities() -> pd.DataFrame:
    all_dfs = [fetch_weather_city(city) for city in CITIES.items()]
    return(pd.concat(all_dfs))    
    
if __name__ == "__main__":
    weather_df = fetch_weather_all_cities()
    print("\nAperçu du jeu de données Météo :")
    print(weather_df.head())
    print(f"\nTotal enregistrements : {len(weather_df)}")