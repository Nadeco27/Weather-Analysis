import requests
import pandas as pd
import streamlit as st
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

    response = requests.get(ARCHIVE_API_URL, params=requestParams, timeout=30)
    response.raise_for_status()
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
    for cityName in cityNames:
        cityDataFrame = fetchCityHistoricalData(cityName, startDate, endDate)
        if not cityDataFrame.empty:
            dataFrames.append(cityDataFrame)

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
