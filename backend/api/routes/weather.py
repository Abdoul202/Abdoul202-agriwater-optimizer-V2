"""Weather API routes."""

from fastapi import APIRouter

from agriwater.weather.forecast import fetch_forecast, fetch_history
from api.schemas import DayWeatherOut, ForecastResponse, HistoryResponse

router = APIRouter(prefix="/api/weather", tags=["weather"])


def _day_to_out(d) -> DayWeatherOut:
    return DayWeatherOut(
        date=d.date, temp_max=d.temp_max, temp_min=d.temp_min,
        precipitation_mm=d.precipitation_mm, et0_mm=d.et0_mm,
        sunshine_hours=d.sunshine_hours, wind_speed_max=d.wind_speed_max,
        humidity_mean=d.humidity_mean,
    )


@router.get("/forecast", response_model=ForecastResponse)
def get_forecast(days: int = 7):
    forecast = fetch_forecast(days=days)
    return ForecastResponse(
        days=[_day_to_out(d) for d in forecast.days],
        drought_risk=forecast.drought_risk,
    )


@router.get("/history", response_model=HistoryResponse)
def get_history(days_back: int = 30):
    history = fetch_history(days_back=days_back)
    return HistoryResponse(days=[_day_to_out(d) for d in history])
