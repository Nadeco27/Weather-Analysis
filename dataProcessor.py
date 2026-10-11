import pandas as pd
import numpy as np
from typing import Tuple


def computeMonthlyAggregations(dailyDataFrame: pd.DataFrame) -> pd.DataFrame:
    """
    Compute monthly aggregates including mean temperature and total precipitation.
    """
    if dailyDataFrame.empty:
        return pd.DataFrame()

    workingDataFrame = dailyDataFrame.copy()
    workingDataFrame["yearMonth"] = workingDataFrame["time"].dt.to_period("M").dt.to_timestamp()

    monthlyGrouped = (
        workingDataFrame.groupby(["cityName", "yearMonth"])
        .agg(
            meanTemperature=("temperature_2m_mean", "mean"),
            maxTemperature=("temperature_2m_max", "max"),
            minTemperature=("temperature_2m_min", "min"),
            totalPrecipitation=("precipitation_sum", "sum"),
            maxDailyPrecipitation=("precipitation_sum", "max"),
            rainyDaysCount=("precipitation_sum", lambda values: (values > 1.0).sum()),
            extremeRainDaysCount=("precipitation_sum", lambda values: (values >= 50.0).sum())
        )
        .reset_index()
    )

    monthlyGrouped["rollingMeanTemp12M"] = (
        monthlyGrouped.groupby("cityName")["meanTemperature"]
        .transform(lambda series: series.rolling(window=12, min_periods=1).mean())
    )

    return monthlyGrouped


def computeAnnualExtremeEvents(dailyDataFrame: pd.DataFrame, extremeThreshold: float = 50.0) -> pd.DataFrame:
    """
    Compute yearly counts and metrics for extreme precipitation events.
    """
    if dailyDataFrame.empty:
        return pd.DataFrame()

    workingDataFrame = dailyDataFrame.copy()
    workingDataFrame["year"] = workingDataFrame["time"].dt.year

    annualGrouped = (
        workingDataFrame.groupby(["cityName", "year"])
        .agg(
            annualPrecipitation=("precipitation_sum", "sum"),
            maxDailyPrecipitation=("precipitation_sum", "max"),
            heavyRainDays=("precipitation_sum", lambda values: (values >= extremeThreshold).sum()),
            veryHeavyRainDays=("precipitation_sum", lambda values: (values >= 100.0).sum()),
            meanTemperature=("temperature_2m_mean", "mean")
        )
        .reset_index()
    )

    return annualGrouped


def computeCityKpis(dailyDataFrame: pd.DataFrame, extremeThreshold: float = 50.0) -> dict:
    """
    Compute headline KPI metrics across all selected cities.
    """
    if dailyDataFrame.empty:
        return {
            "overallMeanTemp": 0.0,
            "maxRecordedTemp": 0.0,
            "highestDailyRainfall": 0.0,
            "highestDailyRainCity": "N/A",
            "totalExtremeRainDays": 0
        }

    overallMeanTemp = round(float(dailyDataFrame["temperature_2m_mean"].mean()), 2)
    maxRecordedTemp = round(float(dailyDataFrame["temperature_2m_max"].max()), 2)
    
    maxRainRow = dailyDataFrame.loc[dailyDataFrame["precipitation_sum"].idxmax()]
    highestDailyRainfall = round(float(maxRainRow["precipitation_sum"]), 1)
    highestDailyRainCity = f"{maxRainRow['cityName']} ({maxRainRow['time'].strftime('%b %Y')})"
    
    totalExtremeRainDays = int((dailyDataFrame["precipitation_sum"] >= extremeThreshold).sum())

    return {
        "overallMeanTemp": overallMeanTemp,
        "maxRecordedTemp": maxRecordedTemp,
        "highestDailyRainfall": highestDailyRainfall,
        "highestDailyRainCity": highestDailyRainCity,
        "totalExtremeRainDays": totalExtremeRainDays
    }
