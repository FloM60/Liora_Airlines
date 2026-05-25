import pandas as pd
import requests as requests
from typing import Optional
from datetime import datetime, timedelta
from tqdm import tqdm
import time
import asyncio
import httpx

API_WEATHER = "https://archive-api.open-meteo.com/v1/archive?"



def build_weather_cache(cities: list) -> dict:
    """
    Récupère toutes les données météo pour chaque ville
    et les stocke en mémoire dans un dict
    """
    cache = {}  # { id_city: DataFrame }


    for city in tqdm(cities, desc="Téléchargement météo"):
        id_city, lat, lon, min_date, max_date = city

        # print(id_city)
        # if id_city == 'MHT' or id_city == 'EWR' or id_city == 'IAD':
        weather_json = get_weather(lat, lon, str(min_date), str(max_date))

        if weather_json is not None:
            cache[id_city] = weather_json

        #time.sleep(3)

    print(f"Cache météo : {len(cache)} villes chargées")
    return cache



def get_weather(latitude: float, longitude: float, start_date: str, end_date: str, max_retries: int = 5) -> Optional[pd.DataFrame]:
    parameters = {
        'latitude': latitude,
        'longitude': longitude,
        'start_date': start_date,
        'end_date': (pd.to_datetime(end_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"), # Pour gérer les arrivés le jour après la date max
        'timezone': 'auto',
        'hourly': [
            "temperature_2m",
            "relative_humidity_2m",
            "dew_point_2m",
            "apparent_temperature",
            "precipitation",
            "rain",
            "snowfall",
            "snow_depth",
            "vapour_pressure_deficit",
            "wind_speed_10m",
            "wind_speed_100m",
            "wind_gusts_10m",
            "weather_code"
        ]
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(API_WEATHER, params=parameters, timeout=30)  # ⬆️ 10 → 30s

            if response.status_code == 429:
                wait = 60 * (attempt + 1)  # ⬆️ 60s, 120s, 180s...
                print(f"Rate limit, attente {wait}s... ({attempt + 1}/{max_retries})")
                time.sleep(wait)
                continue

            response.raise_for_status()
            data = response.json()

            if 'hourly' not in data:
                return None

            df = pd.DataFrame(data['hourly'])
            # df['time'] = pd.to_datetime(df['time'])
            df['time'] = pd.to_datetime(df['time']).dt.strftime("%Y-%m-%dT%H:%M")
            return df

        except requests.exceptions.Timeout:
            print(f"Timeout ({attempt + 1}/{max_retries}), attente 10s...")
            time.sleep(10)  # ⬆️ 3 → 10s

        except requests.RequestException as error:
            print(f"Erreur API ({latitude}, {longitude}) : {error}")
            return None

    print(f"Échec après {max_retries} tentatives pour ({latitude}, {longitude})")
    return None



async def get_weather_async(session: httpx.AsyncClient, sem: asyncio.Semaphore, latitude: float, longitude: float, start_date: str, end_date: str, max_retries: int = 5) -> Optional[pd.DataFrame]:
    parameters = {
        'latitude': latitude,
        'longitude': longitude,
        'start_date': start_date,
        'end_date': (pd.to_datetime(end_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"), # Pour gérer les arrivés le jour après la date max
        'timezone': 'auto',
        'hourly': [
            "temperature_2m",
            "relative_humidity_2m",
            "dew_point_2m",
            "apparent_temperature",
            "precipitation",
            "rain",
            "snowfall",
            "snow_depth",
            "vapour_pressure_deficit",
            "wind_speed_10m",
            "wind_speed_100m",
            "wind_gusts_10m",
            "weather_code"
        ]
    }

    await asyncio.sleep(1)
    async with sem:
        await asyncio.sleep(0.2)

        for attempt in range(max_retries):
            try:
                response = await session.get(API_WEATHER, params=parameters, timeout=30)

                if response.status_code == 429:
                    wait = 10 * (attempt + 1)
                    print(f"Rate limit, attente {wait}s... ({attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait)
                    continue

                response.raise_for_status()
                data = response.json()

                if 'hourly' not in data:
                    return None

                df = pd.DataFrame(data['hourly'])
                df['time'] = pd.to_datetime(df['time']).dt.strftime("%Y-%m-%dT%H:%M")
                return df

            except httpx.TimeoutException:
                print(f"Timeout ({attempt + 1}/{max_retries}), attente 10s...")
                await asyncio.sleep(10) 

            except httpx.RequestError as error:
                print(f"Erreur API ({latitude}, {longitude}) : {error}")
                return None

        print(f"Échec après {max_retries} tentatives pour ({latitude}, {longitude})")
        return None