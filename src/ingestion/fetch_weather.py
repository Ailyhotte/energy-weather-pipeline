#import requests
import pandas as pd

API_URL = "https://api.open-meteo.com/v1/forecast?latitude=47.2172&longitude=-1.5534&hourly=temperature_2m,rain,wind_speed_10m&timezone=Europe%2FLondon&forecast_days=1"

print(API_URL)