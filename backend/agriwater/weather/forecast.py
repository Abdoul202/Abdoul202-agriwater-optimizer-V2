"""
Weather integration via Open-Meteo API (free, no key required).

Fetches forecast and historical data for the farm location
to adjust irrigation scheduling.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta

import httpx

from agriwater.config import settings

logger = logging.getLogger(__name__)

OPENMETEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPENMETEO_HISTORY = "https://archive-api.open-meteo.com/v1/archive"


@dataclass
class DailyWeather:
    date: str
    temp_max: float
    temp_min: float
    precipitation_mm: float
    et0_mm: float  # Reference evapotranspiration
    sunshine_hours: float
    wind_speed_max: float
    humidity_mean: float


@dataclass
class WeatherForecast:
    location: str
    latitude: float
    longitude: float
    days: list[DailyWeather]
    drought_risk: str = "low"  # low, moderate, high, severe


def fetch_forecast(days: int = 7) -> WeatherForecast:
    """Fetch weather forecast from Open-Meteo."""
    lat = settings.farm.latitude
    lon = settings.farm.longitude

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "et0_fao_evapotranspiration",
            "sunshine_duration",
            "wind_speed_10m_max",
            "relative_humidity_2m_mean",
        ]),
        "timezone": "Africa/Ouagadougou",
        "forecast_days": days,
    }

    try:
        resp = httpx.get(OPENMETEO_FORECAST, params=params, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("Weather API failed: %s", e)
        return WeatherForecast(
            location=settings.farm.name,
            latitude=lat, longitude=lon,
            days=[], drought_risk="unknown",
        )

    daily = data.get("daily", {})
    weather_days = []
    dates = daily.get("time", [])

    for i, d in enumerate(dates):
        weather_days.append(DailyWeather(
            date=d,
            temp_max=daily["temperature_2m_max"][i],
            temp_min=daily["temperature_2m_min"][i],
            precipitation_mm=daily["precipitation_sum"][i] or 0,
            et0_mm=daily["et0_fao_evapotranspiration"][i] or 0,
            sunshine_hours=round((daily["sunshine_duration"][i] or 0) / 3600, 1),
            wind_speed_max=daily["wind_speed_10m_max"][i] or 0,
            humidity_mean=daily["relative_humidity_2m_mean"][i] or 0,
        ))

    drought_risk = _assess_drought_risk(weather_days)

    return WeatherForecast(
        location=settings.farm.name,
        latitude=lat, longitude=lon,
        days=weather_days,
        drought_risk=drought_risk,
    )


def fetch_history(days_back: int = 30) -> list[DailyWeather]:
    """Fetch recent historical weather for trend analysis."""
    lat = settings.farm.latitude
    lon = settings.farm.longitude

    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days_back)

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "et0_fao_evapotranspiration",
            "sunshine_duration",
            "wind_speed_10m_max",
            "relative_humidity_2m_mean",
        ]),
        "timezone": "Africa/Ouagadougou",
    }

    try:
        resp = httpx.get(OPENMETEO_HISTORY, params=params, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("History API failed: %s", e)
        return []

    daily = data.get("daily", {})
    results = []
    dates = daily.get("time", [])

    for i, d in enumerate(dates):
        results.append(DailyWeather(
            date=d,
            temp_max=daily["temperature_2m_max"][i] or 0,
            temp_min=daily["temperature_2m_min"][i] or 0,
            precipitation_mm=daily["precipitation_sum"][i] or 0,
            et0_mm=daily["et0_fao_evapotranspiration"][i] or 0,
            sunshine_hours=round((daily["sunshine_duration"][i] or 0) / 3600, 1),
            wind_speed_max=daily["wind_speed_10m_max"][i] or 0,
            humidity_mean=daily["relative_humidity_2m_mean"][i] or 0,
        ))

    return results


def _assess_drought_risk(days: list[DailyWeather]) -> str:
    """Simple drought risk assessment based on forecast."""
    if not days:
        return "unknown"

    total_rain = sum(d.precipitation_mm for d in days)
    total_et0 = sum(d.et0_mm for d in days)
    avg_temp = sum(d.temp_max for d in days) / len(days)

    if total_rain < 2 and avg_temp > 38:
        return "severe"
    if total_rain < 5 and total_et0 > total_rain * 3:
        return "high"
    if total_rain < total_et0 * 0.5:
        return "moderate"
    return "low"
