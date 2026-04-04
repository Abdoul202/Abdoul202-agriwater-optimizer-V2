"""
Data models for the optimization engine.

Aligned with the original agriwater-optimizer by Abdoulaye Ouedraogo.
Pump configs, tariffs, and constraints match the real SONABEL context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import json


@dataclass
class Pump:
    id: str
    name: str
    capacity_m3h: float
    power_kw: float
    efficiency: float = 0.75
    age_years: int = 0
    pump_type: str = "principale"
    max_startups_per_day: int = 8
    max_hours_per_day: float = 20.0
    startup_cost_fcfa: float = 5000.0

    @property
    def actual_power_kw(self) -> float:
        """Real power consumption accounting for efficiency and age."""
        age_factor = 1 + (self.age_years * 0.02)
        return (self.power_kw / self.efficiency) * age_factor


@dataclass
class Crop:
    name: str
    area_ha: float
    water_need_mm_day: float
    kc: float = 1.0  # Crop coefficient for ET0-based demand
    priority: int = 1

    def daily_demand_m3(self, et0_mm: float | None = None) -> float:
        """Compute daily water demand in m3. Uses ET0 if available."""
        if et0_mm is not None and et0_mm > 0:
            need = et0_mm * self.kc
        else:
            need = self.water_need_mm_day
        return need * self.area_ha * 10  # mm * ha * 10 = m3


@dataclass
class TariffPeriod:
    name: str
    start_hour: int
    end_hour: int
    price_fcfa_kwh: float


@dataclass
class FarmConfig:
    name: str
    pumps: list[Pump]
    crops: list[Crop]
    tariffs: list[TariffPeriod]
    subscribed_power_kw: float = 150.0
    penalty_rate_fcfa: float = 200.0
    solar_capacity_kw: float = 0.0
    solar_contribution: float = 0.3
    reservoir_capacity_m3: float = 500.0
    reservoir_initial_m3: float = 100.0

    def total_pump_capacity_m3h(self) -> float:
        return sum(p.capacity_m3h for p in self.pumps)

    def total_pump_power_kw(self) -> float:
        return sum(p.power_kw for p in self.pumps)

    def to_json(self, path: str | Path) -> None:
        """Export config to JSON for reproducibility."""
        data = {
            "name": self.name,
            "subscribed_power_kw": self.subscribed_power_kw,
            "penalty_rate_fcfa": self.penalty_rate_fcfa,
            "solar_capacity_kw": self.solar_capacity_kw,
            "solar_contribution": self.solar_contribution,
            "reservoir_capacity_m3": self.reservoir_capacity_m3,
            "pumps": [
                {
                    "id": p.id, "name": p.name, "capacity_m3h": p.capacity_m3h,
                    "power_kw": p.power_kw, "efficiency": p.efficiency,
                    "age_years": p.age_years, "type": p.pump_type,
                }
                for p in self.pumps
            ],
            "crops": [
                {
                    "name": c.name, "area_ha": c.area_ha,
                    "water_need_mm_day": c.water_need_mm_day, "kc": c.kc,
                }
                for c in self.crops
            ],
            "tariffs": [
                {
                    "name": t.name, "start_hour": t.start_hour,
                    "end_hour": t.end_hour, "price_fcfa_kwh": t.price_fcfa_kwh,
                }
                for t in self.tariffs
            ],
        }
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False))

    @classmethod
    def from_json(cls, path: str | Path) -> FarmConfig:
        """Load config from JSON file."""
        data = json.loads(Path(path).read_text())
        pumps = [
            Pump(
                id=p["id"], name=p.get("name", p["id"]),
                capacity_m3h=p["capacity_m3h"], power_kw=p["power_kw"],
                efficiency=p.get("efficiency", 0.75),
                age_years=p.get("age_years", 0),
                pump_type=p.get("type", "principale"),
            )
            for p in data["pumps"]
        ]
        crops = [
            Crop(
                name=c["name"], area_ha=c["area_ha"],
                water_need_mm_day=c["water_need_mm_day"],
                kc=c.get("kc", 1.0),
            )
            for c in data["crops"]
        ]
        tariffs = [
            TariffPeriod(
                name=t["name"], start_hour=t["start_hour"],
                end_hour=t["end_hour"], price_fcfa_kwh=t["price_fcfa_kwh"],
            )
            for t in data["tariffs"]
        ]
        return cls(
            name=data["name"], pumps=pumps, crops=crops, tariffs=tariffs,
            subscribed_power_kw=data.get("subscribed_power_kw", 150),
            penalty_rate_fcfa=data.get("penalty_rate_fcfa", 200),
            solar_capacity_kw=data.get("solar_capacity_kw", 0),
            solar_contribution=data.get("solar_contribution", 0.3),
            reservoir_capacity_m3=data.get("reservoir_capacity_m3", 500),
        )


@dataclass
class HourlySchedule:
    hour: int
    pump_id: str
    active: bool
    power_kw: float
    actual_power_kw: float
    flow_m3h: float
    cost_fcfa: float
    tariff_name: str
    tariff_price: float
    solar_offset_kw: float = 0.0
    is_startup: bool = False


@dataclass
class OptimizationResult:
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
    schedule: list[HourlySchedule] = field(default_factory=list)
    hourly_costs: list[float] = field(default_factory=list)
    hourly_power: list[float] = field(default_factory=list)
    hourly_baseline: list[float] = field(default_factory=list)
    hourly_demand: list[float] = field(default_factory=list)
    reservoir_levels: list[float] = field(default_factory=list)
    solver_status: str = ""
    solve_time_s: float = 0.0
