import requests
import pandas as pd
import streamlit as st
import time
from typing import Dict, List, Any

# Coordinates as specified for Jabodetabek cities
CITY_COORDINATES: Dict[str, Dict[str, float]] = {
    "Jakarta": {"latitude": -6.2088, "longitude": 106.8456},
    "Bogor": {"latitude": -6.5971, "longitude": 106.7932},
    "Depok": {"latitude": -6.4025, "longitude": 106.7942},
    "Tangerang": {"latitude": -6.1702, "longitude": 106.6403},
    "Bekasi": {"latitude": -6.2383, "longitude": 106.9756}
}

ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"
BMKG_API_URL = "https://api.bmkg.go.id/publik/prakiraan-cuaca"

BMKG_ADM4_CODES: Dict[str, str] = {
    "Jakarta": "31.71.03.1001",
    "Bogor": "32.01.01.1001",
    "Depok": "32.76.01.1006",
    "Tangerang": "36.71.01.1001",
    "Bekasi": "32.75.01.1003"
}


def _fetch_with_retry(url: str, params: Dict[str, Any], max_retries: int = 3, base_delay: float = 1.0) -> requests.Response:
    """
    Fetch with exponential backoff retry for rate limiting (429) and server errors (5xx).
    """
    for attempt in range(max_retries):
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            return response
        
        # Retry on rate limit (429) or server errors (5xx)
        if response.status_code == 429 or 500 <= response.status_code < 600:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                time.sleep(delay)
                continue
        
        # For other errors, raise immediately
        response.raise_for_status()
    
    # If all retries exhausted, raise the last response's error
    response.raise_for_status()
    return response


@st.cache_data(ttl=86400, show_spinner=False)
def fetchCityHistoricalData(cityName: str, startDate: str, endDate: str) -> pd.DataFrame:
    """
    Fetch daily historical weather data for a single city from Open-Meteo Archive API.
    """
    if cityName not in CITY_COORDINATES:
        raise ValueError(f"Unknown city: {cityName}")

    coordinates = CITY_COORDINATES[cityName]
    requestParams: Dict[str, Any] = {
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "start_date": startDate,
        "end_date": endDate,
        "daily": [
            "temperature_2m_mean",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_hours"
        ],
        "timezone": "Asia/Jakarta"
    }

    response = _fetch_with_retry(ARCHIVE_API_URL, requestParams, max_retries=3, base_delay=1.0)
    apiPayload = response.json()

    if "daily" not in apiPayload:
        return pd.DataFrame()

    dailyData = apiPayload["daily"]
    dataFrame = pd.DataFrame(dailyData)
    dataFrame["time"] = pd.to_datetime(dataFrame["time"])
    dataFrame["cityName"] = cityName
    dataFrame["latitude"] = coordinates["latitude"]
    dataFrame["longitude"] = coordinates["longitude"]
    
    return dataFrame


def fetchAllCitiesHistoricalData(
    cityNames: List[str], 
    startDate: str, 
    endDate: str
) -> pd.DataFrame:
    """
    Fetch and concatenate historical weather data for multiple Jabodetabek cities.
    """
    dataFrames = []
    for i, cityName in enumerate(cityNames):
        cityDataFrame = fetchCityHistoricalData(cityName, startDate, endDate)
        if not cityDataFrame.empty:
            dataFrames.append(cityDataFrame)
        # Small delay between cities to avoid rate limiting
        if i < len(cityNames) - 1:
            time.sleep(0.5)

    if not dataFrames:
        return pd.DataFrame()

    return pd.concat(dataFrames, ignore_index=True)


@st.cache_data(ttl=3600, show_spinner=False)
def fetchBMKGForecast(cityName: str) -> pd.DataFrame:
    if cityName not in BMKG_ADM4_CODES:
        raise ValueError(f"Unknown city: {cityName}")

    adm4Code = BMKG_ADM4_CODES[cityName]
    try:
        response = requests.get(BMKG_API_URL, params={"adm4": adm4Code}, timeout=30)
        if response.status_code != 200:
            return pd.DataFrame()
        apiPayload = response.json()
    except (requests.RequestException, ValueError):
        return pd.DataFrame()

    if "data" not in apiPayload or not apiPayload["data"]:
        return pd.DataFrame()

    forecastList: List[Dict[str, Any]] = []
    for region in apiPayload["data"]:
        for dayEntries in region.get("cuaca", []):
            for entry in dayEntries:
                forecastList.append({
                    "local_datetime": entry.get("local_datetime"),
                    "utc_datetime": entry.get("utc_datetime"),
                    "temperature": entry.get("t"),
                    "humidity": entry.get("hu"),
                    "weather_desc": entry.get("weather_desc"),
                    "weather_desc_en": entry.get("weather_desc_en"),
                    "wind_speed": entry.get("ws"),
                    "wind_direction": entry.get("wd"),
                    "cloud_cover": entry.get("tcc"),
                    "visibility": entry.get("vs_text"),
                    "analysis_date": entry.get("analysis_date"),
                    "weather_icon": entry.get("image"),
                    "cityName": cityName
                })

    if not forecastList:
        return pd.DataFrame()

    dataFrame = pd.DataFrame(forecastList)
    dataFrame["local_datetime"] = pd.to_datetime(dataFrame["local_datetime"])
    dataFrame["utc_datetime"] = pd.to_datetime(dataFrame["utc_datetime"])

    return dataFrame


FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"


@st.cache_data(ttl=3600, show_spinner=False)
def fetchOpenMeteoForecastVisibility(cityName: str, startDate: str, endDate: str) -> pd.DataFrame:
    """
    Fetch visibility forecast data from Open-Meteo for a given city and date range.
    """
    if cityName not in CITY_COORDINATES:
        raise ValueError(f"Unknown city: {cityName}")

    coordinates = CITY_COORDINATES[cityName]
    requestParams: Dict[str, Any] = {
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "hourly": ["visibility"],
        "start_date": startDate,
        "end_date": endDate,
        "timezone": "Asia/Jakarta"
    }

    try:
        response = requests.get(FORECAST_API_URL, params=requestParams, timeout=30)
        response.raise_for_status()
        apiPayload = response.json()
    except (requests.RequestException, ValueError):
        return pd.DataFrame()

    if "hourly" not in apiPayload:
        return pd.DataFrame()

    hourlyData = apiPayload["hourly"]
    dataFrame = pd.DataFrame(hourlyData)
    dataFrame["local_datetime"] = pd.to_datetime(dataFrame["time"])
    dataFrame = dataFrame.drop(columns=["time"])
    dataFrame["visibility"] = dataFrame["visibility"] / 1000
    dataFrame["cityName"] = cityName

    return dataFrame


AIR_QUALITY_API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


@st.cache_data(ttl=3600, show_spinner=False)
def fetchBMKGAirQuality(cityName: str) -> pd.DataFrame:
    """
    Fetch air quality index (AQI) data for a city from Open-Meteo Air Quality API.
    """
    if cityName not in CITY_COORDINATES:
        raise ValueError(f"Unknown city: {cityName}")

    coordinates = CITY_COORDINATES[cityName]
    requestParams: Dict[str, Any] = {
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "hourly": [
            "pm2_5",
            "pm10",
            "carbon_monoxide",
            "nitrogen_dioxide",
            "sulphur_dioxide",
            "ozone",
            "us_aqi"
        ],
        "timezone": "Asia/Jakarta"
    }

    try:
        response = requests.get(AIR_QUALITY_API_URL, params=requestParams, timeout=30)
        response.raise_for_status()
        apiPayload = response.json()
    except (requests.RequestException, ValueError):
        return pd.DataFrame()

    if "hourly" not in apiPayload:
        return pd.DataFrame()

    hourlyData = apiPayload["hourly"]
    dataFrame = pd.DataFrame(hourlyData)
    dataFrame["local_datetime"] = pd.to_datetime(dataFrame["time"])
    dataFrame = dataFrame.drop(columns=["time"])

    columnMapping = {
        "pm2_5": "pm25",
        "carbon_monoxide": "co",
        "nitrogen_dioxide": "no2",
        "sulphur_dioxide": "so2",
        "ozone": "o3",
        "us_aqi": "aqi"
    }
    dataFrame = dataFrame.rename(columns=columnMapping)
    dataFrame["cityName"] = cityName

    if "aqi" in dataFrame.columns:
        dataFrame["category"] = dataFrame["aqi"].apply(
            lambda x: (
                "Good" if x <= 50
                else "Moderate" if x <= 100
                else "Unhealthy (Sensitive)" if x <= 150
                else "Unhealthy" if x <= 200
                else "Very Unhealthy" if x <= 300
                else "Hazardous"
            )
        )

    return dataFrame
