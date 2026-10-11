import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

COLOR_PALETTE = {
    "Jakarta": "#5AC8FA",
    "Bogor": "#34D399",
    "Depok": "#FBBF24",
    "Tangerang": "#F87171",
    "Bekasi": "#A78BFA"
}

AQI_COLORS = {
    "good": "#34D399",
    "moderate": "#FBBF24",
    "sensitive": "#FB923C",
    "unhealthy": "#F0564A",
    "very_unhealthy": "#A78BFA",
    "hazardous": "#E11D48",
    "unknown": "#66738E",
}

GRID_COLOR = "#1C2947"
BORDER_COLOR = "#243354"
FONT_FAMILY = "'Space Grotesk', 'Segoe UI', system-ui, sans-serif"


def apply_dark_theme(figure: go.Figure) -> go.Figure:
    """Unify fonts, colors and chrome so every chart sits on the dark surface."""
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, color="#C7D2E8", size=12),
        title_font=dict(family=FONT_FAMILY, size=15, color="#E9EFFA"),
        hoverlabel=dict(
            bgcolor="#1B2542",
            bordercolor=BORDER_COLOR,
            font=dict(family=FONT_FAMILY, color="#E9EFFA", size=12),
        ),
        legend=dict(font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
    )
    figure.update_xaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=BORDER_COLOR,
        linecolor=BORDER_COLOR,
        tickfont=dict(size=11),
    )
    figure.update_yaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=BORDER_COLOR,
        linecolor=BORDER_COLOR,
        tickfont=dict(size=11),
    )
    return figure


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
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=60, b=60)
    )
    return apply_dark_theme(figure)


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
        margin=dict(l=20, r=20, t=100, b=20),
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5)
    )
    return apply_dark_theme(figure)


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
        showlegend=False,
        margin=dict(l=20, r=20, t=100, b=20)
    )
    return apply_dark_theme(figure)


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
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=60, b=60)
    )
    return apply_dark_theme(figure)


def buildForecastTempChart(forecastDataFrame: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    color = COLOR_PALETTE.get(forecastDataFrame["cityName"].iloc[0], "#5AC8FA")

    figure.add_trace(
        go.Scatter(
            x=forecastDataFrame["local_datetime"],
            y=forecastDataFrame["temperature"],
            mode="lines+markers",
            name="Temperature",
            line=dict(color=color, width=2.5),
            marker=dict(size=6),
            hovertemplate="%{x|%d/%m/%Y %H:%M}<br>%{y} °C<extra></extra>"
        )
    )

    figure.update_layout(
        title=f"BMKG Temperature Forecast - {forecastDataFrame['cityName'].iloc[0]}",
        xaxis_title="Date & Time (WIB)",
        yaxis_title="Temperature (°C)",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20)
    )
    return apply_dark_theme(figure)


def buildForecastWindChart(forecastDataFrame: pd.DataFrame) -> go.Figure:
    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=forecastDataFrame["local_datetime"],
            y=forecastDataFrame["wind_speed"],
            name="Wind Speed",
            marker_color="#38BDF8",
            hovertemplate="%{x|%d/%m/%Y %H:%M}<br>%{y} km/h<extra></extra>"
        )
    )

    figure.update_layout(
        title=f"BMKG Wind Speed Forecast - {forecastDataFrame['cityName'].iloc[0]}",
        xaxis_title="Date & Time (WIB)",
        yaxis_title="Wind Speed (km/h)",
        margin=dict(l=20, r=20, t=60, b=20)
    )
    return apply_dark_theme(figure)


def buildForecastHumidityCloudChart(forecastDataFrame: pd.DataFrame) -> go.Figure:
    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=forecastDataFrame["local_datetime"],
            y=forecastDataFrame["humidity"],
            mode="lines",
            name="Humidity (%)",
            line=dict(color="#34D399", width=2),
            fill="tozeroy",
            fillcolor="rgba(52, 211, 153, 0.15)"
        )
    )

    figure.add_trace(
        go.Scatter(
            x=forecastDataFrame["local_datetime"],
            y=forecastDataFrame["cloud_cover"],
            mode="lines",
            name="Cloud Cover (%)",
            line=dict(color="#818CF8", width=2, dash="dash")
        )
    )

    figure.update_layout(
        title=f"BMKG Humidity & Cloud Cover - {forecastDataFrame['cityName'].iloc[0]}",
        xaxis_title="Date & Time (WIB)",
        yaxis_title="Percentage (%)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=60, b=60)
    )
    return apply_dark_theme(figure)


def buildAQIChart(aqiDataFrame: pd.DataFrame) -> go.Figure:
    """
    Build clean AQI trend chart with colored threshold bands.
    """
    figure = go.Figure()

    if aqiDataFrame.empty:
        return figure

    cityName = aqiDataFrame["cityName"].iloc[0]

    aqiColors = []
    for val in aqiDataFrame["aqi"]:
        if pd.isna(val):
            aqiColors.append(AQI_COLORS["unknown"])
        elif val <= 50:
            aqiColors.append(AQI_COLORS["good"])
        elif val <= 100:
            aqiColors.append(AQI_COLORS["moderate"])
        elif val <= 150:
            aqiColors.append(AQI_COLORS["sensitive"])
        elif val <= 200:
            aqiColors.append(AQI_COLORS["unhealthy"])
        elif val <= 300:
            aqiColors.append(AQI_COLORS["very_unhealthy"])
        else:
            aqiColors.append(AQI_COLORS["hazardous"])

    # Add colored threshold bands as background shapes
    bands = [
        (0, 50, AQI_COLORS["good"], "Good"),
        (50, 100, AQI_COLORS["moderate"], "Moderate"),
        (100, 150, AQI_COLORS["sensitive"], "Unhealthy (Sensitive)"),
        (150, 200, AQI_COLORS["unhealthy"], "Unhealthy"),
        (200, 300, AQI_COLORS["very_unhealthy"], "Very Unhealthy"),
        (300, 500, AQI_COLORS["hazardous"], "Hazardous"),
    ]
    for y0, y1, color, label in bands:
        figure.add_hrect(
            y0=y0, y1=y1,
            fillcolor=color, opacity=0.08,
            line_width=0,
            layer="below"
        )
        # Add subtle label on the right edge
        figure.add_annotation(
            x=1.0, y=(y0 + y1) / 2,
            xref="paper", yref="y",
            text=label,
            showarrow=False,
            font=dict(size=9, color=color),
            xanchor="left", yanchor="middle",
            bgcolor="rgba(19, 28, 49, 0.8)",
            borderpad=2,
        )

    figure.add_trace(
        go.Scatter(
            x=aqiDataFrame["local_datetime"],
            y=aqiDataFrame["aqi"],
            mode="lines+markers",
            name="AQI",
            line=dict(color="#E9EFFA", width=2),
            marker=dict(size=5, color=aqiColors, line=dict(width=1, color="#fff")),
            hovertemplate="%{x|%d/%m/%Y %H:%M}<br>AQI: %{y}<extra></extra>"
        )
    )

    figure.update_layout(
        title=f"Air Quality Index (AQI) - {cityName}",
        xaxis_title="Date & Time (WIB)",
        yaxis_title="US AQI",
        yaxis=dict(range=[0, max(300, aqiDataFrame["aqi"].max() * 1.1 if not aqiDataFrame["aqi"].empty else 300)]),
        hovermode="x unified",
        showlegend=False,
        margin=dict(l=20, r=120, t=60, b=40),
    )
    return apply_dark_theme(figure)


def buildPollutantsChart(aqiDataFrame: pd.DataFrame) -> go.Figure:
    """
    Build small multiples chart for individual pollutants.
    """
    figure = go.Figure()

    if aqiDataFrame.empty:
        return figure

    cityName = aqiDataFrame["cityName"].iloc[0]

    pollutants = [
        ("pm25", "PM2.5", "#F87171", "µg/m³"),
        ("pm10", "PM10", "#FBBF24", "µg/m³"),
        ("no2", "NO₂", "#22D3EE", "µg/m³"),
        ("o3", "O₃", "#FB923C", "µg/m³"),
        ("so2", "SO₂", "#A3E635", "µg/m³"),
        ("co", "CO", "#A78BFA", "µg/m³"),
    ]

    # Only include pollutants that have data
    active_pollutants = [(c, l, cl, u) for c, l, cl, u in pollutants 
                         if c in aqiDataFrame.columns and aqiDataFrame[c].notna().any()]

    if not active_pollutants:
        return figure

    n = len(active_pollutants)
    cols = 3
    rows = (n + cols - 1) // cols

    from plotly.subplots import make_subplots
    figure = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[l for _, l, _, _ in active_pollutants],
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )

    for idx, (col, label, color, unit) in enumerate(active_pollutants):
        r = idx // cols + 1
        c = idx % cols + 1
        figure.add_trace(
            go.Scatter(
                x=aqiDataFrame["local_datetime"],
                y=aqiDataFrame[col],
                mode="lines",
                name=label,
                line=dict(color=color, width=1.5),
                fill="tozeroy",
                fillcolor=f"{color}15",
                hovertemplate=f"%{{x|%d/%m/%Y %H:%M}}<br>{label}: %{{y}} {unit}<extra></extra>",
                showlegend=False,
            ),
            row=r, col=c
        )
        figure.update_yaxes(title_text=unit, row=r, col=c, tickfont=dict(size=9))
        figure.update_xaxes(tickfont=dict(size=9), row=r, col=c)

    figure.update_layout(
        title=f"Pollutant Levels - {cityName}",
        height=180 * rows + 60,
        margin=dict(l=20, r=20, t=60, b=40),
    )
    return apply_dark_theme(figure)
