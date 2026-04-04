"""Config API routes."""

from fastapi import APIRouter

from agriwater.data.generator import create_demo_farm
from api.schemas import CropOut, FarmConfigOut, PumpOut, TariffOut

router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config/demo", response_model=FarmConfigOut)
def get_demo_config():
    farm = create_demo_farm()
    return FarmConfigOut(
        name=farm.name,
        pumps=[
            PumpOut(
                id=p.id, name=p.name, capacity_m3h=p.capacity_m3h,
                power_kw=p.power_kw, actual_power_kw=p.actual_power_kw,
                efficiency=p.efficiency, age_years=p.age_years,
                pump_type=p.pump_type, max_startups_per_day=p.max_startups_per_day,
                startup_cost_fcfa=p.startup_cost_fcfa,
            )
            for p in farm.pumps
        ],
        crops=[
            CropOut(name=c.name, area_ha=c.area_ha,
                    water_need_mm_day=c.water_need_mm_day, kc=c.kc,
                    priority=c.priority)
            for c in farm.crops
        ],
        tariffs=[
            TariffOut(name=t.name, start_hour=t.start_hour,
                      end_hour=t.end_hour, price_fcfa_kwh=t.price_fcfa_kwh)
            for t in farm.tariffs
        ],
        subscribed_power_kw=farm.subscribed_power_kw,
        penalty_rate_fcfa=farm.penalty_rate_fcfa,
        solar_capacity_kw=farm.solar_capacity_kw,
        solar_contribution=farm.solar_contribution,
        reservoir_capacity_m3=farm.reservoir_capacity_m3,
    )
