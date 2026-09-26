import requests
import pandas as pd

CITIES = {
    "Nantes": {"lat": 47.2172, "lon": -1.5534},
    "Bordeaux": {"lat": 44.8412, "lon": -0.5805},
    "Marseille": {"lat": 43.297, "lon": 5.3811},
    "Lyon": {"lat": 45.7491, "lon": 4.8479},
    "Dijon": {"lat": 47.3134, "lon": 5.0139},
    "Rennes": {"lat": 48.1111, "lon": -1.6743},
    "Orleans": {"lat": 47.9025, "lon": 1.9041},
    "Ajaccio": {"lat": 41.9189, "lon": 8.7381},
    "Strasbourg": {"lat": 48.5839, "lon": 7.7455},
    "Lille": {"lat": 50.6339, "lon": 3.0551},
    "Rouen": {"lat": 49.4431, "lon": 1.0993},
    "Toulouse": {"lat": 43.6043, "lon": 1.4437},
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
        "forecast_days": 1,
        "past_days": 30,
    }

    response = requests.get(url=BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()["hourly"]

    df = pd.DataFrame(data)
    df["city"] = city_name
    df = df.rename(
        columns={
            "time": "date",
            "temperature_2m": "temp_celsius",
            "rain": "rain_mm",
            "wind_speed_10m": "wind_speed_kmh",
        }
    )
    df["date"] = pd.to_datetime(df["date"])
    return df


def fetch_weather_all() -> pd.DataFrame:
    all_dfs = [fetch_weather_city(city) for city in CITIES.items()]
    return pd.concat(all_dfs)


if __name__ == "__main__":
    weather_df = fetch_weather_all()
    print("\nAperçu du jeu de données Météo :")
    print(weather_df.head())
    print(f"\nTotal enregistrements : {len(weather_df)}")
