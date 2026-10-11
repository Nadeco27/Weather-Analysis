import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

COLOR_PALETTE = {
    "Jakarta": "#2563EB",
    "Bogor": "#059669",
    "Depok": "#D97706",
    "Tangerang": "#DC2626",
    "Bekasi": "#7C3AED"
}


def buildTemperatureTrendChart(monthlyDataFrame: pd.DataFrame) -> go.Figure:
    """
    Build monthly average temperature trend with 12-month rolling average.
    """
    figure = go.Figure()

    for cityName, cityData in monthlyDataFrame.groupby("cityName"):
        color = COLOR_PALETTE.get(cityName, "#64748B")
        figure.add_trace(
            go.Scatter(
                x=cityData["yearMonth"],
                y=cityData["meanTemperature"],
                mode="lines",
                name=f"{cityName} (Monthly Mean)",
                line=dict(color=color, width=1.2),
                opacity=0.45
            )
        )
        figure.add_trace(
            go.Scatter(
                x=cityData["yearMonth"],
                y=cityData["rollingMeanTemp12M"],
                mode="lines",
                name=f"{cityName} (12M Trend)",
                line=dict(color=color, width=2.8)
            )
        )

    figure.update_layout(
        title="Monthly Average Temperature Trajectory & 12-Month Moving Averages",
        xaxis_title="Timeline",
        yaxis_title="Mean Temperature (°C)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=60, b=60)
    )
    return figure


def buildExtremePrecipitationChart(annualDataFrame: pd.DataFrame) -> go.Figure:
    """
    Build bar chart showing extreme precipitation event frequencies per year.
    """
    figure = px.bar(
        annualDataFrame,
        x="year",
        y="heavyRainDays",
        color="cityName",
        barmode="group",
        color_discrete_map=COLOR_PALETTE,
        title="Frequency of Extreme Rainfall Days (≥ Threshold) by Year",
        labels={"year": "Year", "heavyRainDays": "Number of Extreme Days", "cityName": "City"}
    )
    figure.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=100, b=20),
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5)
    )
    return figure


def buildMicroclimateComparisonChart(monthlyDataFrame: pd.DataFrame) -> go.Figure:
    """
    Build box plot comparing temperature distributions to highlight microclimates (e.g. Bogor vs others).
    """
    figure = px.box(
        monthlyDataFrame,
        x="cityName",
        y="meanTemperature",
        color="cityName",
        color_discrete_map=COLOR_PALETTE,
        points="all",
        title="Microclimate Temperature Distribution Comparison",
        labels={"cityName": "City", "meanTemperature": "Monthly Mean Temperature (°C)"}
    )
    figure.update_layout(
        template="plotly_white",
        showlegend=False,
        margin=dict(l=20, r=20, t=100, b=20)
    )
    return figure


def buildPrecipitationDistributionChart(dailyDataFrame: pd.DataFrame) -> go.Figure:
    """
    Build cumulative/annual precipitation comparison chart.
    """
    figure = px.histogram(
        dailyDataFrame[dailyDataFrame["precipitation_sum"] > 0],
        x="precipitation_sum",
        color="cityName",
        color_discrete_map=COLOR_PALETTE,
        marginal="box",
        nbins=50,
        title="Daily Precipitation Distribution (Rain Days Only)",
        labels={"precipitation_sum": "Daily Rainfall (mm)", "cityName": "City"}
    )
    figure.update_layout(
        template="plotly_white",
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=60, b=60)
    )
    return figure


def buildForecastTempChart(forecastDataFrame: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    color = COLOR_PALETTE.get(forecastDataFrame["cityName"].iloc[0], "#2563EB")

    figure.add_trace(
        go.Scatter(
            x=forecastDataFrame["local_datetime"],
            y=forecastDataFrame["temperature"],
            mode="lines+markers",
            name="Temperature",
            line=dict(color=color, width=2.5),
            marker=dict(size=6),
            hovertemplate="%{x|%Y-%m-%d %H:%M}<br>%{y} °C<extra></extra>"
        )
    )

    figure.update_layout(
        title=f"BMKG Temperature Forecast - {forecastDataFrame['cityName'].iloc[0]}",
        xaxis_title="Date & Time (WIB)",
        yaxis_title="Temperature (°C)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20)
    )
    return figure


def buildForecastWindChart(forecastDataFrame: pd.DataFrame) -> go.Figure:
    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=forecastDataFrame["local_datetime"],
            y=forecastDataFrame["wind_speed"],
            name="Wind Speed",
            marker_color="#0EA5E9",
            hovertemplate="%{x|%Y-%m-%d %H:%M}<br>%{y} km/h<extra></extra>"
        )
    )

    figure.update_layout(
        title=f"BMKG Wind Speed Forecast - {forecastDataFrame['cityName'].iloc[0]}",
        xaxis_title="Date & Time (WIB)",
        yaxis_title="Wind Speed (km/h)",
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20)
    )
    return figure


def buildForecastHumidityCloudChart(forecastDataFrame: pd.DataFrame) -> go.Figure:
    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=forecastDataFrame["local_datetime"],
            y=forecastDataFrame["humidity"],
            mode="lines",
            name="Humidity (%)",
            line=dict(color="#10B981", width=2),
            fill="tozeroy",
            fillcolor="rgba(16, 185, 129, 0.15)"
        )
    )

    figure.add_trace(
        go.Scatter(
            x=forecastDataFrame["local_datetime"],
            y=forecastDataFrame["cloud_cover"],
            mode="lines",
            name="Cloud Cover (%)",
            line=dict(color="#6366F1", width=2, dash="dash")
        )
    )

    figure.update_layout(
        title=f"BMKG Humidity & Cloud Cover - {forecastDataFrame['cityName'].iloc[0]}",
        xaxis_title="Date & Time (WIB)",
        yaxis_title="Percentage (%)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=60, b=60)
    )
    return figure
