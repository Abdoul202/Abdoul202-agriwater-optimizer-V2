"""Pydantic schemas for API request/response."""

from __future__ import annotations

from pydantic import BaseModel, Field


# --- Requests ---

class OptimizeRequest(BaseModel):
    area_ha: float = 50.0
    num_pumps: int = 3
    subscribed_power_kw: float = 150.0
    penalty_rate_fcfa: float = 200.0
    tariff_peak: float = 110.0
    tariff_offpeak: float = 75.0
    peak_start: int = 7
    peak_end: int = 23
    solar_capacity_kw: float = 10.0
    cloud_factor: float = 0.1
    reservoir_m3: float = 500.0
    et0_mm: float | None = None


# --- Responses ---

class HourlyScheduleOut(BaseModel):
    hour: int
    pump_id: str
    active: bool
    power_kw: float
    actual_power_kw: float
    flow_m3h: float
    cost_fcfa: float
    tariff_name: str
    tariff_price: float
    solar_offset_kw: float
    is_startup: bool


class OptimizeResponse(BaseModel):
    total_cost_fcfa: float
    baseline_cost_fcfa: float
    savings_fcfa: float
    savings_pct: float
    energy_cost_fcfa: float
    penalty_cost_fcfa: float
    startup_cost_fcfa: float
    baseline_penalty_fcfa: float
    total_water_m3: float
    water_demand_m3: float
    total_energy_kwh: float
    peak_power_kw: float
    num_startups: int
    schedule: list[HourlyScheduleOut]
    hourly_costs: list[float]
    hourly_power: list[float]
    hourly_baseline: list[float]
    hourly_demand: list[float]
    reservoir_levels: list[float]
    solver_status: str
    solve_time_s: float


class PumpOut(BaseModel):
    id: str
    name: str
    capacity_m3h: float
    power_kw: float
    actual_power_kw: float
    efficiency: float
    age_years: int
    pump_type: str
    max_startups_per_day: int
    startup_cost_fcfa: float


class CropOut(BaseModel):
    name: str
    area_ha: float
    water_need_mm_day: float
    kc: float
    priority: int


class TariffOut(BaseModel):
    name: str
    start_hour: int
    end_hour: int
    price_fcfa_kwh: float


class FarmConfigOut(BaseModel):
    name: str
    pumps: list[PumpOut]
    crops: list[CropOut]
    tariffs: list[TariffOut]
    subscribed_power_kw: float
    penalty_rate_fcfa: float
    solar_capacity_kw: float
    solar_contribution: float
    reservoir_capacity_m3: float


class DayWeatherOut(BaseModel):
    date: str
    temp_max: float
    temp_min: float
    precipitation_mm: float
    et0_mm: float
    sunshine_hours: float
    wind_speed_max: float
    humidity_mean: float


class ForecastResponse(BaseModel):
    days: list[DayWeatherOut]
    drought_risk: str


class HistoryResponse(BaseModel):
    days: list[DayWeatherOut]
