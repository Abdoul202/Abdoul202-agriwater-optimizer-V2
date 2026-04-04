"""Tests for weather module (basic, no API calls)."""

from agriwater.weather.forecast import DailyWeather, _assess_drought_risk


def _make_day(rain: float = 0, et0: float = 5, temp_max: float = 35) -> DailyWeather:
    return DailyWeather(
        date="2026-04-01", temp_max=temp_max, temp_min=20,
        precipitation_mm=rain, et0_mm=et0, sunshine_hours=8,
        wind_speed_max=10, humidity_mean=40,
    )


def test_severe_drought():
    days = [_make_day(rain=0, temp_max=40) for _ in range(7)]
    assert _assess_drought_risk(days) == "severe"


def test_low_drought_with_rain():
    days = [_make_day(rain=10, et0=3) for _ in range(7)]
    assert _assess_drought_risk(days) == "low"


def test_moderate_drought():
    days = [_make_day(rain=1, et0=6, temp_max=36) for _ in range(7)]
    risk = _assess_drought_risk(days)
    assert risk in ("moderate", "high")


def test_empty_days():
    assert _assess_drought_risk([]) == "unknown"
