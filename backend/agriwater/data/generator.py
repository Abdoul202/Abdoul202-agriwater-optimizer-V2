"""
Sample data generator for demo and testing.

Based on the original agriwater-optimizer by Abdoulaye Ouedraogo.
Generates realistic farm configurations for the Sahel/SONABEL context
with correct pump specs, tariff structure, and seasonal patterns.
"""

from __future__ import annotations

import math

from agriwater.config import settings
from agriwater.optimizer.models import Crop, FarmConfig, Pump, TariffPeriod


def create_demo_farm(
    name: str | None = None,
    num_pumps: int = 3,
    area_ha: float = 50.0,
) -> FarmConfig:
    """
    Create a realistic demo farm matching the original agriwater-optimizer.

    Pump specs from generator_config.json:
      P1: 60 m3/h, 45 kW, eff=0.75, age=5, principale
      P2: 50 m3/h, 38 kW, eff=0.72, age=8, secondaire
      P3: 55 m3/h, 42 kW, eff=0.73, age=3, appoint
    """
    tariff = settings.tariff

    # SONABEL two-tier tariff: peak 7h-23h, offpeak 23h-7h
    tariffs = [
        TariffPeriod("Heures creuses", 0, tariff.peak_start, tariff.offpeak),
        TariffPeriod("Heures pleines", tariff.peak_start, tariff.peak_end, tariff.peak),
        TariffPeriod("Heures creuses", tariff.peak_end, 24, tariff.offpeak),
    ]

    # Pump configs from the original repo
    pump_specs = [
        ("P1", "Pompe principale", 60.0, 45.0, 0.75, 5, "principale"),
        ("P2", "Pompe secondaire", 50.0, 38.0, 0.72, 8, "secondaire"),
        ("P3", "Pompe d'appoint", 55.0, 42.0, 0.73, 3, "appoint"),
    ]

    pumps = [
        Pump(
            id=pid, name=pname, capacity_m3h=cap,
            power_kw=power, efficiency=eff,
            age_years=age, pump_type=ptype,
        )
        for pid, pname, cap, power, eff, age, ptype in pump_specs[:num_pumps]
    ]

    # Crops - typical Sahelian farm
    crops = [
        Crop(name="Mil", area_ha=area_ha * 0.30, water_need_mm_day=4.5, kc=0.85, priority=1),
        Crop(name="Sorgho", area_ha=area_ha * 0.25, water_need_mm_day=5.0, kc=0.90, priority=1),
        Crop(name="Mais", area_ha=area_ha * 0.15, water_need_mm_day=6.0, kc=1.05, priority=2),
        Crop(name="Niebe", area_ha=area_ha * 0.15, water_need_mm_day=3.5, kc=0.80, priority=2),
        Crop(name="Maraichage", area_ha=area_ha * 0.15, water_need_mm_day=7.0, kc=1.10, priority=1),
    ]

    return FarmConfig(
        name=name or settings.farm.name,
        pumps=pumps,
        crops=crops,
        tariffs=tariffs,
        subscribed_power_kw=tariff.subscribed_power_kw,
        penalty_rate_fcfa=tariff.penalty_rate_fcfa,
        solar_capacity_kw=10.0,
        solar_contribution=0.3,
        reservoir_capacity_m3=500.0,
        reservoir_initial_m3=100.0,
    )


def generate_solar_profile(
    capacity_kw: float,
    cloud_factor: float = 0.0,
) -> list[float]:
    """
    Generate a daily solar production profile for the Sahel.

    Peak production around 12:00-14:00. Cloud factor 0-1 reduces output.
    """
    solar_curve = [
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0,       # 00-05
        0.05, 0.20, 0.45, 0.70, 0.88, 0.95,   # 06-11
        1.0, 0.98, 0.90, 0.75, 0.50, 0.20,    # 12-17
        0.03, 0.0, 0.0, 0.0, 0.0, 0.0,        # 18-23
    ]
    factor = 1.0 - cloud_factor
    return [round(s * capacity_kw * factor, 2) for s in solar_curve]


def generate_seasonal_demand(
    base_demand_m3: float,
    month: int,
) -> list[float]:
    """
    Generate 24h hourly demand with Sahelian seasonal adjustment.

    From the original data_generator.py:
    - Dry season (Nov-Apr): x1.35
    - Rainy season (Jun-Sep): x0.60
    - Transition (May, Oct): x0.85
    - Morning peak (5-8h), evening peak (18-21h), minimal midday (11-15h)
    """
    # Seasonal factor
    if month in (11, 12, 1, 2, 3, 4):
        season_factor = 1.35
    elif month in (6, 7, 8, 9):
        season_factor = 0.60
    else:
        season_factor = 0.85

    adjusted = base_demand_m3 * season_factor

    # Hourly distribution pattern from original
    hourly_weights = {
        range(0, 5): 0.02,     # Night minimal
        range(5, 9): 0.09,     # Morning peak
        range(9, 11): 0.04,    # Mid-morning
        range(11, 16): 0.025,  # Midday low (evaporation)
        range(16, 18): 0.045,  # Pre-evening
        range(18, 22): 0.07,   # Evening peak
        range(22, 24): 0.035,  # Night
    }

    demand = []
    for h in range(24):
        for hr_range, weight in hourly_weights.items():
            if h in hr_range:
                demand.append(adjusted * weight)
                break

    # Normalize to match total
    total = sum(demand)
    if total > 0:
        demand = [d * adjusted / total for d in demand]

    return demand
