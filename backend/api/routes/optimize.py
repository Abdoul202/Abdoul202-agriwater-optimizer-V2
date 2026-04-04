"""Optimization API routes."""

from fastapi import APIRouter

from agriwater.data.generator import generate_solar_profile
from agriwater.optimizer.engine import IrrigationOptimizer
from agriwater.optimizer.models import Crop, FarmConfig, Pump, TariffPeriod
from api.schemas import HourlyScheduleOut, OptimizeRequest, OptimizeResponse

router = APIRouter(prefix="/api", tags=["optimize"])


def _build_farm(req: OptimizeRequest) -> FarmConfig:
    """Build FarmConfig from request parameters."""
    pump_specs = [
        ("P1", "Pompe principale", 60.0, 45.0, 0.75, 5, "principale"),
        ("P2", "Pompe secondaire", 50.0, 38.0, 0.72, 8, "secondaire"),
        ("P3", "Pompe d'appoint", 55.0, 42.0, 0.73, 3, "appoint"),
        ("P4", "Pompe reserve 1", 40.0, 30.0, 0.70, 2, "reserve"),
        ("P5", "Pompe reserve 2", 35.0, 25.0, 0.68, 1, "reserve"),
    ]

    pumps = [
        Pump(id=pid, name=pname, capacity_m3h=cap, power_kw=pw,
             efficiency=eff, age_years=age, pump_type=pt)
        for pid, pname, cap, pw, eff, age, pt in pump_specs[:req.num_pumps]
    ]

    tariffs = [
        TariffPeriod("Heures creuses", 0, req.peak_start, req.tariff_offpeak),
        TariffPeriod("Heures pleines", req.peak_start, req.peak_end, req.tariff_peak),
        TariffPeriod("Heures creuses", req.peak_end, 24, req.tariff_offpeak),
    ]

    crops = [
        Crop("Mil", req.area_ha * 0.30, 4.5, kc=0.85, priority=1),
        Crop("Sorgho", req.area_ha * 0.25, 5.0, kc=0.90, priority=1),
        Crop("Mais", req.area_ha * 0.15, 6.0, kc=1.05, priority=2),
        Crop("Niebe", req.area_ha * 0.15, 3.5, kc=0.80, priority=2),
        Crop("Maraichage", req.area_ha * 0.15, 7.0, kc=1.10, priority=1),
    ]

    return FarmConfig(
        name="Ferme AgriWater", pumps=pumps, crops=crops, tariffs=tariffs,
        subscribed_power_kw=req.subscribed_power_kw,
        penalty_rate_fcfa=req.penalty_rate_fcfa,
        solar_capacity_kw=req.solar_capacity_kw,
        reservoir_capacity_m3=req.reservoir_m3,
    )


@router.post("/optimize", response_model=OptimizeResponse)
def run_optimization(req: OptimizeRequest):
    farm = _build_farm(req)
    solar = generate_solar_profile(req.solar_capacity_kw, req.cloud_factor)
    optimizer = IrrigationOptimizer(farm)
    result = optimizer.optimize(solar_profile=solar, et0_mm=req.et0_mm)

    return OptimizeResponse(
        total_cost_fcfa=result.total_cost_fcfa,
        baseline_cost_fcfa=result.baseline_cost_fcfa,
        savings_fcfa=result.savings_fcfa,
        savings_pct=result.savings_pct,
        energy_cost_fcfa=result.energy_cost_fcfa,
        penalty_cost_fcfa=result.penalty_cost_fcfa,
        startup_cost_fcfa=result.startup_cost_fcfa,
        baseline_penalty_fcfa=result.baseline_penalty_fcfa,
        total_water_m3=result.total_water_m3,
        water_demand_m3=result.water_demand_m3,
        total_energy_kwh=result.total_energy_kwh,
        peak_power_kw=result.peak_power_kw,
        num_startups=result.num_startups,
        schedule=[
            HourlyScheduleOut(
                hour=s.hour, pump_id=s.pump_id, active=s.active,
                power_kw=s.power_kw, actual_power_kw=s.actual_power_kw,
                flow_m3h=s.flow_m3h, cost_fcfa=s.cost_fcfa,
                tariff_name=s.tariff_name, tariff_price=s.tariff_price,
                solar_offset_kw=s.solar_offset_kw, is_startup=s.is_startup,
            )
            for s in result.schedule
        ],
        hourly_costs=result.hourly_costs,
        hourly_power=result.hourly_power,
        hourly_baseline=result.hourly_baseline,
        hourly_demand=result.hourly_demand,
        reservoir_levels=result.reservoir_levels,
        solver_status=result.solver_status,
        solve_time_s=result.solve_time_s,
    )
