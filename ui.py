"""Reusable UI primitives for the Jabodetabek Climate Analytics theme."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from weatherIcons import WEATHER_ICONS

_CSS_PATH = Path(__file__).resolve().parent / "assets" / "style.css"


_CAROUSEL_SCRIPT = """
<script>
(function() {
  if (window.__carouselDragBound) { return; }
  window.__carouselDragBound = true;
  let isDown = false, startX = 0, scrollLeft = 0, el = null;
  document.addEventListener('mousedown', function(e) {
    el = e.target.closest ? e.target.closest('.carouselContainer') : null;
    if (!el) return;
    isDown = true; startX = e.clientX; scrollLeft = el.scrollLeft;
    el.style.cursor = 'grabbing';
    e.preventDefault();
  });
  document.addEventListener('mouseleave', function() {
    isDown = false; if (el) el.style.cursor = 'grab';
  });
  document.addEventListener('mouseup', function() {
    isDown = false; if (el) el.style.cursor = 'grab';
  });
  document.addEventListener('mousemove', function(e) {
    if (!isDown || !el) return;
    e.preventDefault();
    el.scrollLeft = scrollLeft - (e.clientX - startX) * 2;
  });
})();
</script>
"""


def inject_theme() -> None:
    """Deliver the design-system CSS on every run so it survives reruns."""
    st.html(_CSS_PATH)


def fmt(value) -> str:
    """Compact number formatting: 28.0 -> '28', 27.83 -> '27.8'."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.1f}"


def kpi(label: str, value: str, sub: str | None = None, accent: str = "#4CC9F0",
        value_color: str | None = None) -> str:
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    color_style = f' style="color:{value_color};"' if value_color else ""
    return (
        f'<div class="kpi" style="--accent:{accent};">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value"{color_style}>{value}</div>'
        f"{sub_html}</div>"
    )


def kpi_row(*cards: str) -> str:
    return f'<div class="kpi-row">{"".join(cards)}</div>'


def section_header(title: str, subtitle: str | None = None) -> str:
    sub_html = f'<div class="section-sub">{subtitle}</div>' if subtitle else ""
    return (
        '<div class="section-header"><span class="section-marker"></span>'
        f"<div><h2>{title}</h2>{sub_html}</div></div>"
    )


def chip(text: str, color: str) -> str:
    return (
        f'<span class="chip" style="color:{color}; border-color:{color}; '
        f'background:{color}14;">{text}</span>'
    )


def note(text: str) -> str:
    return f'<div class="note">{text}</div>'


def insights(items) -> str:
    blocks = []
    for text, color in items:
        blocks.append(
            f'<div class="insight" style="border-left-color:{color};">{text}</div>'
        )
    return "".join(blocks)


def mini(label: str, value: str, unit: str | None = None) -> str:
    unit_html = f'<span class="m-unit"> {unit}</span>' if unit else ""
    return (
        f'<div class="mini"><div class="m-label">{label}</div>'
        f'<div class="m-value">{value}{unit_html}</div></div>'
    )


def mini_row(*cards: str) -> str:
    return f'<div class="mini-row">{"".join(cards)}</div>'


def hero_now(city_name, row, icon_url: str, vis_text: str, accent: str = "#4CC9F0") -> str:
    params = [
        ("Humidity", f"{fmt(row['humidity'])}%"),
        ("Wind", f"{fmt(row['wind_speed'])} km/h"),
        ("Cloud cover", f"{fmt(row['cloud_cover'])}%"),
        ("Visibility", vis_text),
    ]
    grid = "".join(
        f'<div><div class="hp-label">{label}</div><div class="hp-value">{value}</div></div>'
        for label, value in params
    )
    return f"""
<div class="hero">
  <div class="hero-icon"><img src="{icon_url}" alt=""/></div>
  <div>
    <div class="hero-city" style="color:{accent};">{city_name} · next weather window</div>
    <div class="hero-cond">{row.get("weather_desc_en", "Unknown")}</div>
    <div class="hero-time">{row["local_datetime"].strftime("%a %d %b %Y · %H:%M")} WIB</div>
  </div>
  <div class="hero-temp">{fmt(row["temperature"])}<span> °C</span></div>
  <div class="hero-params">{grid}</div>
</div>"""


def aqi_gauge(aqi: float, category: str, color: str) -> str:
    pct = min(max(float(aqi) / 300.0 * 100.0, 2.5), 100.0)
    return f"""
<div class="gauge-wrap">
  <div class="gauge-top">
    {chip(category, color)}
    <span class="gauge-value" style="color:{color};">AQI {int(round(float(aqi)))}</span>
  </div>
  <div class="gauge-track"><div class="gauge-marker" style="left:{pct:.1f}%;"></div></div>
  <div class="gauge-scale"><span>0</span><span>50</span><span>100</span><span>150</span><span>200</span><span>300+</span></div>
</div>"""


def forecast_carousel(forecast) -> str:
    cards = []
    for _, row in forecast.iterrows():
        weather_desc = row.get("weather_desc_en", "Unknown")
        icon_url = WEATHER_ICONS.get(weather_desc, WEATHER_ICONS["Unknown"])
        time_str = row["local_datetime"].strftime("%d %b · %H:%M")
        vis_raw = row.get("visibility")
        vis_text = f"{float(vis_raw):.1f} km" if pd.notna(vis_raw) and vis_raw else "N/A"
        cards.append(f"""
<div class="carouselCard">
  <div class="cardIcon"><img src="{icon_url}" alt=""/></div>
  <div class="cardTitle">{weather_desc}</div>
  <div class="cardTime">{time_str} WIB</div>
  <div class="cardDetails">
    <span><span class="detail-label">Temp</span><span class="detail-value">{fmt(row['temperature'])}°C</span></span>
    <span><span class="detail-label">Humidity</span><span class="detail-value">{fmt(row['humidity'])}%</span></span>
    <span><span class="detail-label">Wind</span><span class="detail-value">{fmt(row['wind_speed'])} km/h</span></span>
    <span><span class="detail-label">Cloud</span><span class="detail-value">{fmt(row['cloud_cover'])}%</span></span>
    <span><span class="detail-label">Direction</span><span class="detail-value">{row['wind_direction']}</span></span>
    <span><span class="detail-label">Visibility</span><span class="detail-value">{vis_text}</span></span>
  </div>
</div>""")
    return (
        f'<div class="carouselContainer" id="carousel">{"".join(cards)}</div>'
        f"{_CAROUSEL_SCRIPT}"
    )


def footnote(items) -> str:
    lis = "".join(f"<li>{item}</li>" for item in items)
    return f'<div class="footnote"><strong>Data sources</strong><ul>{lis}</ul></div>'