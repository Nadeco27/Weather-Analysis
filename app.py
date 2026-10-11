import streamlit as st
import datetime
import pandas as pd

from weatherService import fetchAllCitiesHistoricalData, fetchBMKGForecast, CITY_COORDINATES
from weatherIcons import WEATHER_ICONS
from dataProcessor import computeMonthlyAggregations, computeAnnualExtremeEvents, computeCityKpis
from charts import (
    buildTemperatureTrendChart,
    buildExtremePrecipitationChart,
    buildMicroclimateComparisonChart,
    buildPrecipitationDistributionChart,
    buildForecastTempChart,
    buildForecastWindChart,
    buildForecastHumidityCloudChart
)

st.set_page_config(
    page_title="Jabodetabek Climate Analytics",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#9729;</text></svg>",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metricCard {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .metricTitle {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metricValue {
        font-size: 1.75rem;
        color: #0f172a;
        font-weight: 700;
        margin-top: 4px;
    }
    .modeButton {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def renderSidebar() -> str:
    st.sidebar.title("Jabodetabek Climate")
    st.sidebar.markdown("---")

    mode = st.sidebar.radio(
        "Select Mode",
        options=["Historical Analysis", "Weather Forecast"],
        index=0,
        key="modeSelector"
    )

    st.sidebar.markdown("---")
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

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Data Sources:**")
    st.sidebar.caption(
        "Historical data: Open-Meteo Archive API\n\n"
        "Forecast data: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)"
    )

    return selectedStartDate, selectedEndDate, selectedCities, extremeRainThreshold


def renderForecastSidebar():
    forecastCity = st.sidebar.selectbox(
        "Select City",
        options=list(CITY_COORDINATES.keys()),
        key="forecastCitySidebar"
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Data source: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)"
    )

    return forecastCity


def renderHistoricalAnalysis(selectedStartDate, selectedEndDate, selectedCities, extremeRainThreshold):
    if not selectedCities:
        st.warning("Please select at least one city in the sidebar to begin analysis.")
        return

    if selectedStartDate >= selectedEndDate:
        st.error("Start Date must be before End Date.")
        return

    with st.spinner("Fetching historical data from Open-Meteo API..."):
        dailyDataFrame = fetchAllCitiesHistoricalData(
            cityNames=selectedCities,
            startDate=selectedStartDate.strftime("%Y-%m-%d"),
            endDate=selectedEndDate.strftime("%Y-%m-%d")
        )

    if dailyDataFrame.empty:
        st.error("No historical data found for the selected parameters.")
        return

    monthlyDataFrame = computeMonthlyAggregations(dailyDataFrame)
    annualDataFrame = computeAnnualExtremeEvents(dailyDataFrame, extremeThreshold=extremeRainThreshold)
    kpiMetrics = computeCityKpis(dailyDataFrame, extremeThreshold=extremeRainThreshold)

    st.markdown("### Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metricCard">
            <div class="metricTitle">Mean Temperature</div>
            <div class="metricValue">{kpiMetrics['overallMeanTemp']} °C</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metricCard">
            <div class="metricTitle">Max Recorded Temp</div>
            <div class="metricValue">{kpiMetrics['maxRecordedTemp']} °C</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metricCard">
            <div class="metricTitle">Peak Daily Rainfall</div>
            <div class="metricValue">{kpiMetrics['highestDailyRainfall']} mm</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metricCard">
            <div class="metricTitle">Extreme Rain Days</div>
            <div class="metricValue">{kpiMetrics['totalExtremeRainDays']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Temperature",
        "Rainfall",
        "Microclimate",
        "Raw Data"
    ])

    with tab1:
        st.plotly_chart(buildTemperatureTrendChart(monthlyDataFrame), use_container_width=True)
        st.info(
            "Insight: The 12-month moving average smooths seasonal monsoonal variations to reveal long-term warming or baseline stability."
        )

    with tab2:
        st.plotly_chart(buildExtremePrecipitationChart(annualDataFrame), use_container_width=True)
        st.plotly_chart(buildPrecipitationDistributionChart(dailyDataFrame), use_container_width=True)

    with tab3:
        colLeft, colRight = st.columns([1.2, 1])
        with colLeft:
            st.plotly_chart(buildMicroclimateComparisonChart(monthlyDataFrame), use_container_width=True)
        with colRight:
            st.markdown("#### Regional Microclimate Findings")
            st.markdown("""
            - **Bogor vs. Lowland Metros**: Higher elevation and proximity to Mount Salak consistently produce cooler median temperatures and higher precipitation frequency.
            - **Urban Heat Island (UHI)**: Jakarta and Bekasi exhibit elevated nighttime minimums and higher median monthly temperatures.
            """)

    with tab4:
        st.dataframe(dailyDataFrame.head(100), use_container_width=True)
        st.download_button(
            label="Download Processed Dataset (CSV)",
            data=dailyDataFrame.to_csv(index=False),
            file_name="jabodetabek_climate_data.csv",
            mime="text/csv"
        )


def renderWeatherForecast(forecastCity):
    with st.spinner(f"Fetching BMKG forecast for {forecastCity}..."):
        forecastDataFrame = fetchBMKGForecast(forecastCity)

    if forecastDataFrame.empty:
        st.warning("No BMKG forecast data available for the selected city.")
        return

    availableDates = sorted(forecastDataFrame["local_datetime"].dt.date.unique())
    dateOptions = ["All Days"] + [d.strftime("%Y-%m-%d") for d in availableDates]
    selectedForecastDate = st.selectbox(
        "Select Forecast Date",
        options=dateOptions,
        key="forecastDate"
    )

    if selectedForecastDate == "All Days":
        filteredForecast = forecastDataFrame
    else:
        selectedDate = datetime.date.fromisoformat(selectedForecastDate)
        filteredForecast = forecastDataFrame[
            forecastDataFrame["local_datetime"].dt.date == selectedDate
        ]

    st.markdown("### Forecast Summary")
    colForecast1, colForecast2, colForecast3 = st.columns(3)
    with colForecast1:
        maxTemp = filteredForecast["temperature"].max()
        minTemp = filteredForecast["temperature"].min()
        st.markdown(f"""
        <div class="metricCard">
            <div class="metricTitle">Max Temperature</div>
            <div class="metricValue">{maxTemp} °C</div>
        </div>
        """, unsafe_allow_html=True)
    with colForecast2:
        maxWind = filteredForecast["wind_speed"].max()
        st.markdown(f"""
        <div class="metricCard">
            <div class="metricTitle">Max Wind Speed</div>
            <div class="metricValue">{maxWind} km/h</div>
        </div>
        """, unsafe_allow_html=True)
    with colForecast3:
        avgHumidity = round(filteredForecast["humidity"].mean(), 1)
        st.markdown(f"""
        <div class="metricCard">
            <div class="metricTitle">Avg Humidity</div>
            <div class="metricValue">{avgHumidity}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 3-Hour Interval Weather Cards")

    if "carouselIndex" not in st.session_state:
        st.session_state.carouselIndex = 0

    totalCards = len(filteredForecast)
    if st.session_state.carouselIndex >= totalCards:
        st.session_state.carouselIndex = 0

    colPrev, colCard, colNext, colJump = st.columns([1, 6, 1, 2])

    with colPrev:
        if st.button("<<<", key="carouselPrev"):
            st.session_state.carouselIndex = max(0, st.session_state.carouselIndex - 1)
            st.rerun()

    with colNext:
        if st.button(">>>", key="carouselNext"):
            st.session_state.carouselIndex = min(totalCards - 1, st.session_state.carouselIndex + 1)
            st.rerun()

    with colJump:
        jumpTo = st.text_input(
            "Go to card",
            value=str(st.session_state.carouselIndex + 1),
            key="carouselJump"
        )
        try:
            jumpVal = int(jumpTo)
            if 1 <= jumpVal <= totalCards and jumpVal != st.session_state.carouselIndex + 1:
                st.session_state.carouselIndex = jumpVal - 1
                st.rerun()
        except ValueError:
            pass

    with colCard:
        if totalCards > 0:
            currentRow = filteredForecast.iloc[st.session_state.carouselIndex]

            cardCol1, cardCol2, cardCol3 = st.columns([1, 2, 1])

            with cardCol1:
                weatherDesc = currentRow.get("weather_desc_en", "Unknown")
                iconUrl = WEATHER_ICONS.get(weatherDesc, WEATHER_ICONS["Unknown"])
                st.image(iconUrl, width=100)

            with cardCol2:
                st.markdown(f"##### {currentRow['weather_desc_en']}")
                st.markdown(f"**Time:** {currentRow['local_datetime'].strftime('%Y-%m-%d %H:%M')} WIB")
                st.markdown(f"**Temperature:** {currentRow['temperature']} °C")
                st.markdown(f"**Humidity:** {currentRow['humidity']}%")
                st.markdown(f"**Cloud Cover:** {currentRow['cloud_cover']}%")

            with cardCol3:
                st.markdown(f"**Wind:** {currentRow['wind_speed']} km/h")
                st.markdown(f"**Direction:** {currentRow['wind_direction']}")
                visibility = currentRow.get("visibility")
                if pd.notna(visibility) and visibility:
                    st.markdown(f"**Visibility:** {visibility}")
                else:
                    st.markdown("**Visibility:** N/A")

            st.caption(f"Card {st.session_state.carouselIndex + 1} of {totalCards}")

    st.markdown("---")

    st.markdown("#### Forecast Charts")
    st.plotly_chart(buildForecastTempChart(filteredForecast), use_container_width=True)
    st.plotly_chart(buildForecastWindChart(filteredForecast), use_container_width=True)
    st.plotly_chart(buildForecastHumidityCloudChart(filteredForecast), use_container_width=True)


def main():
    mode = renderSidebar()

    if mode == "Historical Analysis":
        st.title("Historical Climate Analysis")
        st.caption("Decadal microclimate analysis across Jabodetabek using Open-Meteo Archive API")
        params = renderHistoricalSidebar()
        if params:
            renderHistoricalAnalysis(*params)
    else:
        st.title("BMKG Weather Forecast")
        st.caption("3-day weather forecast from BMKG for Jabodetabek cities")
        forecastCity = renderForecastSidebar()
        if forecastCity:
            renderWeatherForecast(forecastCity)


if __name__ == "__main__":
    main()
