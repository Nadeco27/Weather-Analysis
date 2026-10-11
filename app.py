import requests
import streamlit as st
import datetime
import pandas as pd

from weatherService import fetchAllCitiesHistoricalData, fetchBMKGForecast, fetchBMKGAirQuality, fetchOpenMeteoForecastVisibility, CITY_COORDINATES
from weatherIcons import WEATHER_ICONS
from dataProcessor import computeMonthlyAggregations, computeAnnualExtremeEvents, computeCityKpis
from charts import (
    AQI_COLORS,
    COLOR_PALETTE,
    buildTemperatureTrendChart,
    buildExtremePrecipitationChart,
    buildMicroclimateComparisonChart,
    buildPrecipitationDistributionChart,
    buildForecastTempChart,
    buildForecastWindChart,
    buildForecastHumidityCloudChart,
    buildAQIChart,
    buildPollutantsChart
)
from ui import (
    aqi_gauge,
    chip,
    fmt,
    footnote,
    forecast_carousel,
    hero_now,
    inject_theme,
    insights,
    kpi,
    kpi_row,
    mini,
    mini_row,
    note,
    section_header,
)

st.set_page_config(
    page_title="Jabodetabek Climate Analytics",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#9729;</text></svg>",
    layout="wide",
    initial_sidebar_state="expanded"
)
inject_theme()


def formatVisibility(value) -> str:
    if pd.notna(value) and value:
        return f"{float(value):.1f} km"
    return "N/A"


def getAQICategory(aqiValue):
    """Return (category, color, health advice) following US AQI bands."""
    if aqiValue is None or pd.isna(aqiValue):
        return ("N/A", AQI_COLORS["unknown"], "No air quality data available for this period.")
    try:
        aqiNum = float(aqiValue)
    except (TypeError, ValueError):
        return ("N/A", AQI_COLORS["unknown"], "No air quality data available for this period.")

    if aqiNum <= 50:
        return ("Good", AQI_COLORS["good"], "Air quality is satisfactory. No health implications for outdoor activities.")
    elif aqiNum <= 100:
        return ("Moderate", AQI_COLORS["moderate"], "Acceptable air quality. Sensitive individuals should limit prolonged outdoor exertion.")
    elif aqiNum <= 150:
        return ("Unhealthy (Sensitive)", AQI_COLORS["sensitive"], "Children, elderly, and people with respiratory conditions should reduce outdoor activities.")
    elif aqiNum <= 200:
        return ("Unhealthy", AQI_COLORS["unhealthy"], "Everyone may experience health effects. Avoid prolonged outdoor exertion.")
    elif aqiNum <= 300:
        return ("Very Unhealthy", AQI_COLORS["very_unhealthy"], "Serious health risk. Avoid all outdoor activities.")
    else:
        return ("Hazardous", AQI_COLORS["hazardous"], "Emergency conditions. Remain indoors and keep windows closed.")


def attachVisibility(cityName, forecastDataFrame):
    """Merge BMKG forecast with Open-Meteo visibility, nearest timestamp."""
    if forecastDataFrame.empty or "visibility" not in forecastDataFrame.columns:
        return forecastDataFrame
    forecastDataFrame = forecastDataFrame.drop(columns=["visibility"])
    visStart = forecastDataFrame["local_datetime"].min().strftime("%Y-%m-%d")
    visEnd = forecastDataFrame["local_datetime"].max().strftime("%Y-%m-%d")
    visDataFrame = fetchOpenMeteoForecastVisibility(cityName, visStart, visEnd)
    if visDataFrame.empty:
        return forecastDataFrame
    return pd.merge_asof(
        forecastDataFrame.sort_values("local_datetime").reset_index(drop=True),
        visDataFrame.sort_values("local_datetime")[["local_datetime", "visibility"]],
        on="local_datetime",
        direction="nearest"
    )


def renderSidebar() -> str:
    st.sidebar.title("Jabodetabek Climate")
    st.sidebar.caption("Jakarta · Bogor · Depok · Tangerang · Bekasi")
    st.sidebar.markdown("---")

    mode = st.sidebar.radio(
        "Select Mode",
        options=["Dashboard", "Historical Analysis", "Weather Forecast"],
        index=0,
        key="modeSelector"
    )

    st.sidebar.markdown("---")
    with st.sidebar.expander("Data sources"):
        st.markdown(
            "Historical: Open-Meteo Archive (ERA5)\n\n"
            "Forecast: BMKG\n\n"
            "Visibility: Open-Meteo Forecast\n\n"
            "Air quality: Open-Meteo CAMS"
        )
    st.sidebar.caption("Climate analytics console")
    return mode


def renderHistoricalSidebar():
    defaultStartDate = datetime.date(2014, 1, 1)
    defaultEndDate = datetime.date(2024, 12, 31)

    selectedStartDate = st.sidebar.date_input(
        "Start Date",
        value=st.session_state.get("startDate", defaultStartDate),
        key="startDate"
    )
    selectedEndDate = st.sidebar.date_input(
        "End Date",
        value=st.session_state.get("endDate", defaultEndDate),
        key="endDate"
    )

    selectedCities = st.sidebar.multiselect(
        "Select Cities",
        options=list(CITY_COORDINATES.keys()),
        default=list(CITY_COORDINATES.keys())
    )

    extremeRainThreshold = st.sidebar.slider(
        "Extreme Rainfall Threshold (mm/day)",
        min_value=20.0,
        max_value=150.0,
        value=50.0,
        step=5.0,
        help="BMKG defines heavy rainfall as >=50 mm/day and very heavy as >=100 mm/day."
    )

    return selectedStartDate, selectedEndDate, selectedCities, extremeRainThreshold


def renderForecastSidebar():
    forecastCity = st.sidebar.selectbox(
        "Select City",
        options=list(CITY_COORDINATES.keys()),
        key="forecastCitySidebar"
    )
    st.sidebar.caption("Forecast: BMKG · Visibility: Open-Meteo")
    return forecastCity


def renderAQI(aqiDataFrame):
    st.markdown(section_header("Air quality", "CAMS model via Open-Meteo · US AQI"), unsafe_allow_html=True)
    if aqiDataFrame.empty or "aqi" not in aqiDataFrame.columns:
        st.info("No air quality data available for the selected city at this time.")
        return

    aqiValid = aqiDataFrame.dropna(subset=["aqi"])
    if aqiValid.empty:
        st.info("No air quality data available for the selected city at this time.")
        return

    latestRow = aqiValid.iloc[-1]
    latestAQI = latestRow["aqi"]
    category, color, advice = getAQICategory(latestAQI)

    st.markdown(aqi_gauge(latestAQI, category, color), unsafe_allow_html=True)
    st.caption(f"Latest reading · {latestRow['local_datetime'].strftime('%d/%m/%Y %H:%M')} WIB")
    st.markdown(note(advice), unsafe_allow_html=True)

    st.markdown("##### Pollutant levels")
    pollutants = [
        ("pm25", "PM2.5", "µg/m³"),
        ("pm10", "PM10", "µg/m³"),
        ("co", "CO", "µg/m³"),
        ("no2", "NO₂", "µg/m³"),
        ("so2", "SO₂", "µg/m³"),
        ("o3", "O₃", "µg/m³"),
    ]
    minis = []
    for col, label, unit in pollutants:
        val = latestRow[col] if col in latestRow.index else None
        if val is not None and pd.notna(val):
            minis.append(mini(label, fmt(val), unit))
    if minis:
        st.markdown(mini_row(*minis), unsafe_allow_html=True)

    st.markdown(section_header("AQI trend", "Colored bands show US AQI categories"), unsafe_allow_html=True)
    st.plotly_chart(buildAQIChart(aqiValid), width='stretch')

    st.markdown(section_header("Pollutant levels", "Individual pollutant concentrations"), unsafe_allow_html=True)
    st.plotly_chart(buildPollutantsChart(aqiValid), width='stretch')

    st.markdown("##### Health recommendations (BMKG & WHO guidelines)")
    st.markdown("""
    | AQI Range | Category | Health Advice |
    |-----------|----------|---------------|
    | 0–50 | **Good** | Air quality is satisfactory. Enjoy outdoor activities freely. |
    | 51–100 | **Moderate** | Acceptable air quality. Sensitive individuals should limit prolonged outdoor exertion. |
    | 101–150 | **Unhealthy for Sensitive Groups** | Children, elderly, and people with heart/lung conditions should reduce outdoor activities. |
    | 151–200 | **Unhealthy** | Everyone may experience health effects. Wear a mask outdoors and limit exertion. |
    | 201–300 | **Very Unhealthy** | Serious health risk. Avoid all outdoor activities. Use air purifiers indoors. |
    | 301+ | **Hazardous** | Emergency conditions. Remain indoors, keep windows closed, and use N95 masks if going out is necessary. |
    """)


def generateCityInsights(cityName, histKPIs, forecastDataFrame, aqiDataFrame, aqiValid):
    insights = []

    if histKPIs:
        meanTemp = histKPIs.get('overallMeanTemp', 0)
        maxTemp = histKPIs.get('maxRecordedTemp', 0)
        maxRain = histKPIs.get('highestDailyRainfall', 0)
        extremeDays = histKPIs.get('totalExtremeRainDays', 0)

        if cityName == "Bogor":
            insights.append(("<strong>Climate Profile</strong>: Bogor has a cooler climate due to its higher elevation (290m above sea level) near Mount Salak. The mean temperature is typically 1-2°C lower than lowland areas.", "#059669"))
            insights.append(("<strong>Rainfall Pattern</strong>: Bogor receives the highest annual rainfall in Jabodetabek (3,500-4,000mm/year), earning it the nickname 'Rain City' (Kota Hujan).", "#059669"))
        elif cityName == "Jakarta":
            insights.append(("<strong>Climate Profile</strong>: Jakarta is the hottest city in Jabodetabek with a mean temperature of ~28°C. The Urban Heat Island (UHI) effect causes nighttime temperatures to remain elevated.", "#dc2626"))
            insights.append(("<strong>Flood Risk</strong>: Jakarta faces significant flood risk during peak rainfall months (Dec-Feb) due to low-lying topography (only 7m above sea level) and urban drainage challenges.", "#dc2626"))
        elif cityName in ["Tangerang", "Bekasi", "Depok"]:
            insights.append(("<strong>Climate Profile</strong>: " + cityName + " has a warm tropical climate with mean temperatures around 27-28°C, typical of lowland urban areas in western Java.", "#D97706"))
            insights.append(("<strong>Rainfall</strong>: " + cityName + " experiences similar monsoonal rainfall patterns to Jakarta, with wet season peaks from November to April.", "#D97706"))

        if maxRain > 100:
            insights.append(("<strong>Historical Extreme</strong>: The highest daily rainfall recorded reached " + str(maxRain) + "mm, which exceeds the BMKG 'very heavy rainfall' threshold (>=100 mm/day). This indicates potential flash flood risk.", "#EF4444"))

    if not forecastDataFrame.empty:
        maxTemp = forecastDataFrame["temperature"].max()
        if maxTemp > 35:
            insights.append(("<strong>Heat Warning</strong>: Forecast shows temperatures reaching " + str(maxTemp) + "°C. According to WHO guidelines, prolonged exposure to temperatures above 35°C increases heat-related illness risk. Stay hydrated and limit outdoor activities.", "#EF4444"))
        elif maxTemp > 32:
            insights.append(("<strong>Warm Conditions</strong>: Forecast shows temperatures up to " + str(maxTemp) + "°C. WHO recommends staying hydrated and avoiding prolonged sun exposure during peak hours (10:00-15:00).", "#F59E0B"))

    if not aqiValid.empty:
        latestAQI = aqiValid["aqi"].iloc[-1]
        if latestAQI > 150:
            insights.append(("<strong>Health Alert</strong>: Current AQI is " + str(int(latestAQI)) + " (Unhealthy). WHO and BMKG recommend wearing N95 masks outdoors, limiting physical exertion, and keeping windows closed. Sensitive groups should remain indoors.", "#EF4444"))
        elif latestAQI > 100:
            insights.append(("<strong>Air Quality Notice</strong>: Current AQI is " + str(int(latestAQI)) + " (Unhealthy for Sensitive Groups). Children, elderly, and those with respiratory conditions should reduce outdoor activities per WHO guidelines.", "#F97316"))
        elif latestAQI > 50:
            insights.append(("<strong>Air Quality</strong>: Current AQI is " + str(int(latestAQI)) + " (Moderate). Air quality is acceptable, but sensitive individuals should monitor symptoms.", "#EAB308"))
        else:
            insights.append(("<strong>Good Air Quality</strong>: Current AQI is " + str(int(latestAQI)) + " (Good). Air quality is satisfactory per WHO guidelines.", "#22C55E"))

    if not insights:
        insights.append(("<strong>General</strong>: No significant climate or health alerts for the selected conditions.", "#64748b"))

    return insights


def renderDashboard():
    dashboardCity = st.sidebar.selectbox(
        "Select City",
        options=list(CITY_COORDINATES.keys()),
        key="dashboardCity"
    )
    extremeRainThreshold = st.sidebar.slider(
        "Extreme Rainfall Threshold (mm/day)",
        min_value=20.0,
        max_value=150.0,
        value=50.0,
        step=5.0,
        help="BMKG defines heavy rainfall as >=50 mm/day and very heavy as >=100 mm/day."
    )

    st.title(f"{dashboardCity} — Climate Console")
    st.caption("Historical climate, BMKG forecast and air quality in one view")

    with st.spinner("Loading dashboard data..."):
        dailyDataFrame = fetchAllCitiesHistoricalData(
            cityNames=[dashboardCity],
            startDate="2014-01-01",
            endDate="2024-12-31"
        )
        forecastDataFrame = fetchBMKGForecast(dashboardCity)
        aqiDataFrame = fetchBMKGAirQuality(dashboardCity)

    if dailyDataFrame.empty and forecastDataFrame.empty:
        st.error("No data available for the selected city.")
        return

    forecastDataFrame = attachVisibility(dashboardCity, forecastDataFrame)

    aqiDataFrame = pd.DataFrame() if forecastDataFrame.empty else aqiDataFrame
    if not aqiDataFrame.empty:
        forecastDates = forecastDataFrame["local_datetime"].dt.date.unique()
        aqiDataFrame = aqiDataFrame[
            aqiDataFrame["local_datetime"].dt.date.isin(forecastDates)
        ]
    aqiValid = aqiDataFrame.dropna(subset=["aqi"]) if not aqiDataFrame.empty else pd.DataFrame()

    monthlyDataFrame = computeMonthlyAggregations(dailyDataFrame) if not dailyDataFrame.empty else pd.DataFrame()
    kpiMetrics = computeCityKpis(dailyDataFrame, extremeThreshold=extremeRainThreshold) if not dailyDataFrame.empty else {}
    cityColor = COLOR_PALETTE.get(dashboardCity, "#4CC9F0")

    if not forecastDataFrame.empty:
        heroRow = forecastDataFrame.sort_values("local_datetime").iloc[0]
        iconUrl = WEATHER_ICONS.get(str(heroRow.get("weather_desc_en", "Unknown")), WEATHER_ICONS["Unknown"])
        st.markdown(
            hero_now(dashboardCity, heroRow, iconUrl, formatVisibility(heroRow.get("visibility")), accent=cityColor),
            unsafe_allow_html=True
        )

    metricCards = [
        kpi("Mean temperature", f"{kpiMetrics.get('overallMeanTemp', 0)} °C",
            sub="2014–2024 · ERA5 reanalysis", accent=cityColor),
        kpi("Peak daily rainfall", f"{kpiMetrics.get('highestDailyRainfall', 0)} mm",
            sub=kpiMetrics.get("highestDailyRainCity", "N/A"), accent="#4CC9F0"),
    ]
    if not forecastDataFrame.empty:
        metricCards.append(kpi("Forecast max", f"{fmt(forecastDataFrame['temperature'].max())} °C",
                                sub="Next 3 days · BMKG", accent="#F5A524"))
        metricCards.append(kpi("Max wind", f"{fmt(forecastDataFrame['wind_speed'].max())} km/h",
                                sub="Next 3 days · BMKG", accent="#818CF8"))
    else:
        metricCards.append(kpi("Forecast max", "N/A", sub="BMKG unavailable", accent="#F5A524"))
        metricCards.append(kpi("Max wind", "N/A", sub="BMKG unavailable", accent="#818CF8"))

    if not aqiValid.empty:
        category, color, _ = getAQICategory(aqiValid["aqi"].iloc[-1])
        metricCards.append(kpi("Air quality", f"{int(aqiValid['aqi'].iloc[-1])} AQI",
                               sub=category, accent=color, value_color=color))
    else:
        metricCards.append(kpi("Air quality", "N/A", sub="CAMS unavailable", accent=AQI_COLORS["unknown"]))
    st.markdown(kpi_row(*metricCards), unsafe_allow_html=True)

    dashTab1, dashTab2, dashTab3, dashTab4 = st.tabs([
        "Forecast",
        "Historical Climate",
        "Air Quality",
        "Insights & Findings"
    ])

    with dashTab1:
        st.markdown(section_header("3-hour interval forecast", "BMKG · scroll or drag the cards"), unsafe_allow_html=True)
        if not forecastDataFrame.empty:
            st.html(forecast_carousel(forecastDataFrame), unsafe_allow_javascript=True)
            st.caption(f"Showing {len(forecastDataFrame)} forecast intervals")

            st.markdown(section_header("Temperature forecast", None), unsafe_allow_html=True)
            st.plotly_chart(buildForecastTempChart(forecastDataFrame), width='stretch')
            st.markdown(section_header("Wind forecast", None), unsafe_allow_html=True)
            st.plotly_chart(buildForecastWindChart(forecastDataFrame), width='stretch')
            st.markdown(section_header("Humidity & cloud cover", None), unsafe_allow_html=True)
            st.plotly_chart(buildForecastHumidityCloudChart(forecastDataFrame), width='stretch')
        else:
            st.info("No forecast data available.")

    with dashTab2:
        if not dailyDataFrame.empty:
            st.markdown(section_header("Temperature trends", "Monthly means with 12-month moving averages"), unsafe_allow_html=True)
            st.plotly_chart(buildTemperatureTrendChart(monthlyDataFrame), width='stretch')

            annualDataFrame = computeAnnualExtremeEvents(dailyDataFrame, extremeThreshold=extremeRainThreshold)
            st.markdown(section_header("Extreme rainfall events", f"Days per year ≥ {extremeRainThreshold:.0f} mm"), unsafe_allow_html=True)
            st.plotly_chart(buildExtremePrecipitationChart(annualDataFrame), width='stretch')

            st.markdown(section_header("Microclimate distribution", "Box plot of monthly means by city"), unsafe_allow_html=True)
            st.plotly_chart(buildMicroclimateComparisonChart(monthlyDataFrame), width='stretch')
        else:
            st.info("No historical data available.")

    with dashTab3:
        renderAQI(aqiValid)

    with dashTab4:
        st.markdown(section_header("Key findings & recommendations", None), unsafe_allow_html=True)
        insightItems = generateCityInsights(dashboardCity, kpiMetrics, forecastDataFrame, aqiDataFrame, aqiValid)
        st.markdown(insights(insightItems), unsafe_allow_html=True)

        st.markdown(footnote([
            "Historical climate data: Open-Meteo Archive API (ERA5 reanalysis, 2014–2024)",
            "Weather forecast: BMKG 3-day outlook at 3-hour intervals",
            "Air quality index: Open-Meteo Air Quality API (CAMS global model)",
            "Health guidelines: WHO Air Quality Guidelines (2021) and BMKG standards",
        ]), unsafe_allow_html=True)


def renderHistoricalAnalysis(selectedStartDate, selectedEndDate, selectedCities, extremeRainThreshold):
    if not selectedCities:
        st.warning("Please select at least one city in the sidebar to begin analysis.")
        return

    if selectedStartDate >= selectedEndDate:
        st.error("Start Date must be before End Date.")
        return

    with st.spinner("Fetching historical data from Open-Meteo API..."):
        try:
            dailyDataFrame = fetchAllCitiesHistoricalData(
                cityNames=selectedCities,
                startDate=selectedStartDate.strftime("%Y-%m-%d"),
                endDate=selectedEndDate.strftime("%Y-%m-%d")
            )
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                st.error("""
                **API Rate Limit Exceeded** ⚠️
                
                The Open-Meteo historical data API has temporarily blocked requests due to too many calls in a short period.
                
                **What you can do:**
                - Wait 30–60 seconds and try again
                - Reduce the number of selected cities
                - Narrow the date range
                
                The data is cached for 24 hours, so repeated requests with the same parameters will be instant.
                """)
            else:
                st.error(f"Failed to fetch historical data: {e}")
            return
        except requests.exceptions.RequestException as e:
            st.error(f"Network error while fetching data: {e}")
            return

    if dailyDataFrame.empty:
        st.error("No historical data found for the selected parameters.")
        return

    monthlyDataFrame = computeMonthlyAggregations(dailyDataFrame)
    annualDataFrame = computeAnnualExtremeEvents(dailyDataFrame, extremeThreshold=extremeRainThreshold)
    kpiMetrics = computeCityKpis(dailyDataFrame, extremeThreshold=extremeRainThreshold)

    st.title("Historical Climate Analysis")
    st.caption(f"ERA5 reanalysis · {selectedStartDate.strftime('%d/%m/%Y')} – {selectedEndDate.strftime('%d/%m/%Y')} · {len(dailyDataFrame):,} records")

    st.markdown(kpi_row(
        kpi("Mean temperature", f"{kpiMetrics['overallMeanTemp']} °C",
            sub=f"Across {len(selectedCities)} cities", accent="#5AC8FA"),
        kpi("Max recorded temp", f"{kpiMetrics['maxRecordedTemp']} °C",
            sub="Highest daily maximum on record", accent="#F5A524"),
        kpi("Peak daily rainfall", f"{kpiMetrics['highestDailyRainfall']} mm",
            sub=kpiMetrics["highestDailyRainCity"], accent="#4CC9F0"),
        kpi("Extreme rain days", str(kpiMetrics["totalExtremeRainDays"]),
            sub=f"Days ≥ {extremeRainThreshold:.0f} mm", accent="#A78BFA"),
    ), unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Temperature",
        "Rainfall",
        "Microclimate",
        "Raw Data"
    ])

    with tab1:
        st.markdown(section_header("Monthly temperature trajectory", "Solid lines are 12-month moving averages"), unsafe_allow_html=True)
        st.plotly_chart(buildTemperatureTrendChart(monthlyDataFrame), width='stretch')
        st.markdown(note("The 12-month moving average smooths seasonal monsoonal variations to reveal long-term warming or baseline stability."), unsafe_allow_html=True)

    with tab2:
        st.markdown(section_header("Extreme rainfall frequency", f"Days per year with rainfall ≥ {extremeRainThreshold:.0f} mm"), unsafe_allow_html=True)
        st.plotly_chart(buildExtremePrecipitationChart(annualDataFrame), width='stretch')
        st.markdown(section_header("Daily rainfall distribution", "Rain days only"), unsafe_allow_html=True)
        st.plotly_chart(buildPrecipitationDistributionChart(dailyDataFrame), width='stretch')

    with tab3:
        colLeft, colRight = st.columns([1.2, 1])
        with colLeft:
            st.markdown(section_header("Temperature distribution by city", "Box plot of monthly means"), unsafe_allow_html=True)
            st.plotly_chart(buildMicroclimateComparisonChart(monthlyDataFrame), width='stretch')
        with colRight:
            st.markdown("#### Regional Microclimate Findings")
            st.markdown("""
            - **Bogor vs. Lowland Metros**: Higher elevation and proximity to Mount Salak consistently produce cooler median temperatures and higher precipitation frequency.
            - **Urban Heat Island (UHI)**: Jakarta and Bekasi exhibit elevated nighttime minimums and higher median monthly temperatures.
            """)

    with tab4:
        st.dataframe(dailyDataFrame.head(100), width='stretch')
        st.download_button(
            label="Download Processed Dataset (CSV)",
            data=dailyDataFrame.to_csv(index=False),
            file_name="jabodetabek_climate_data.csv",
            mime="text/csv"
        )

    st.markdown(footnote([
        "Historical climate data: Open-Meteo Archive API (ERA5 reanalysis)",
        "Extreme rainfall threshold: BMKG defines heavy rainfall as ≥50 mm/day and very heavy as ≥100 mm/day",
    ]), unsafe_allow_html=True)


def renderWeatherForecast(forecastCity):
    with st.spinner(f"Fetching BMKG forecast for {forecastCity}..."):
        forecastDataFrame = fetchBMKGForecast(forecastCity)

    if forecastDataFrame.empty:
        st.warning("No BMKG forecast data available for the selected city.")
        return

    forecastDataFrame = attachVisibility(forecastCity, forecastDataFrame)

    st.title(f"Weather Forecast — {forecastCity}")
    st.caption("BMKG 3-day outlook merged with Open-Meteo visibility")

    availableDates = sorted(forecastDataFrame["local_datetime"].dt.date.unique())
    dateOptions = ["All Days"] + [d.strftime("%d/%m/%Y") for d in availableDates]
    selectedForecastDate = st.selectbox(
        "Select Forecast Date",
        options=dateOptions,
        key="forecastDate"
    )

    if selectedForecastDate == "All Days":
        filteredForecast = forecastDataFrame
    else:
        selectedDate = datetime.datetime.strptime(selectedForecastDate, "%d/%m/%Y").date()
        filteredForecast = forecastDataFrame[
            forecastDataFrame["local_datetime"].dt.date == selectedDate
        ]

    cityColor = COLOR_PALETTE.get(forecastCity, "#4CC9F0")
    heroRow = forecastDataFrame.sort_values("local_datetime").iloc[0]
    iconUrl = WEATHER_ICONS.get(str(heroRow.get("weather_desc_en", "Unknown")), WEATHER_ICONS["Unknown"])
    st.markdown(
        hero_now(forecastCity, heroRow, iconUrl, formatVisibility(heroRow.get("visibility")), accent=cityColor),
        unsafe_allow_html=True
    )

    with st.spinner("Fetching AQI data..."):
        aqiDataFrame = fetchBMKGAirQuality(forecastCity)
    if not aqiDataFrame.empty and "aqi" in aqiDataFrame.columns and not filteredForecast.empty:
        filteredDates = filteredForecast["local_datetime"].dt.date.unique()
        aqiDataFrame = aqiDataFrame[
            aqiDataFrame["local_datetime"].dt.date.isin(filteredDates)
        ]
    aqiValid = aqiDataFrame.dropna(subset=["aqi"]) if not aqiDataFrame.empty else pd.DataFrame()

    if filteredForecast.empty:
        st.info("No forecast intervals for the selected date.")
        return

    forecastCards = [
        kpi("Max temperature", f"{fmt(filteredForecast['temperature'].max())} °C",
            sub=selectedForecastDate, accent="#F5A524"),
        kpi("Max wind", f"{fmt(filteredForecast['wind_speed'].max())} km/h",
            sub=selectedForecastDate, accent="#818CF8"),
        kpi("Avg humidity", f"{fmt(filteredForecast['humidity'].mean())}%",
            sub=selectedForecastDate, accent="#34D399"),
    ]
    if not aqiValid.empty:
        category, color, _ = getAQICategory(aqiValid["aqi"].iloc[-1])
        forecastCards.append(kpi("Air quality", f"{int(aqiValid['aqi'].iloc[-1])} AQI",
                                 sub=category, accent=color, value_color=color))
    else:
        forecastCards.append(kpi("Air quality", "N/A", sub="CAMS unavailable", accent=AQI_COLORS["unknown"]))
    st.markdown(kpi_row(*forecastCards), unsafe_allow_html=True)

    st.markdown(section_header("3-hour interval forecast", "BMKG · scroll or drag the cards"), unsafe_allow_html=True)
    st.html(forecast_carousel(filteredForecast), unsafe_allow_javascript=True)
    st.caption(f"Showing {len(filteredForecast)} forecast intervals")

    st.markdown(section_header("Forecast charts", None), unsafe_allow_html=True)
    st.plotly_chart(buildForecastTempChart(filteredForecast), width='stretch')
    st.plotly_chart(buildForecastWindChart(filteredForecast), width='stretch')
    st.plotly_chart(buildForecastHumidityCloudChart(filteredForecast), width='stretch')

    renderAQI(aqiValid)

    st.markdown(footnote([
        "Weather forecast: BMKG 3-day outlook at 3-hour intervals",
        "Visibility: Open-Meteo Forecast API (nearest-hour merge)",
        "Air quality index: Open-Meteo Air Quality API (CAMS global model)",
        "Health guidelines: WHO Air Quality Guidelines (2021) and BMKG standards",
    ]), unsafe_allow_html=True)


def main():
    mode = renderSidebar()

    if mode == "Dashboard":
        renderDashboard()
    elif mode == "Historical Analysis":
        params = renderHistoricalSidebar()
        if params:
            renderHistoricalAnalysis(*params)
    else:
        forecastCity = renderForecastSidebar()
        if forecastCity:
            renderWeatherForecast(forecastCity)


if __name__ == "__main__":
    main()
