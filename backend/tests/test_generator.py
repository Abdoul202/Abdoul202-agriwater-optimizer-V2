"""Tests for data generator."""

from agriwater.data.generator import (
    create_demo_farm,
    generate_seasonal_demand,
    generate_solar_profile,
)


def test_demo_farm_has_pumps():
    farm = create_demo_farm(num_pumps=3)
    assert len(farm.pumps) == 3
    assert all(p.power_kw > 0 for p in farm.pumps)


def test_demo_farm_pump_specs_match_original():
    farm = create_demo_farm(num_pumps=3)
    p1, p2, p3 = farm.pumps

    assert p1.capacity_m3h == 60.0
    assert p1.power_kw == 45.0
    assert p1.efficiency == 0.75
    assert p1.age_years == 5

    assert p2.capacity_m3h == 50.0
    assert p2.power_kw == 38.0

    assert p3.capacity_m3h == 55.0
    assert p3.power_kw == 42.0


def test_demo_farm_has_crops():
    farm = create_demo_farm(area_ha=100)
    assert len(farm.crops) == 5
    total_area = sum(c.area_ha for c in farm.crops)
    assert abs(total_area - 100) < 0.01


def test_demo_farm_tariffs_match_sonabel():
    farm = create_demo_farm()
    assert farm.subscribed_power_kw == 150.0
    assert farm.penalty_rate_fcfa == 200.0
    # Check tariff values
    prices = {t.price_fcfa_kwh for t in farm.tariffs}
    assert 110.0 in prices  # peak
    assert 75.0 in prices   # offpeak


def test_solar_profile_24_hours():
    profile = generate_solar_profile(10.0)
    assert len(profile) == 24


def test_solar_peak_at_noon():
    profile = generate_solar_profile(10.0, cloud_factor=0.0)
    assert profile[12] == max(profile)
    assert profile[0] == 0.0
    assert profile[23] == 0.0


def test_cloud_reduces_solar():
    clear = generate_solar_profile(10.0, cloud_factor=0.0)
    cloudy = generate_solar_profile(10.0, cloud_factor=0.5)
    assert sum(cloudy) < sum(clear)


def test_tariffs_cover_24h():
    farm = create_demo_farm()
    hours_covered = set()
    for t in farm.tariffs:
        for h in range(t.start_hour, t.end_hour):
            hours_covered.add(h)
    assert hours_covered == set(range(24))


def test_seasonal_demand_dry_season_higher():
    base = 1000.0
    dry = generate_seasonal_demand(base, month=1)
    rainy = generate_seasonal_demand(base, month=7)
    assert sum(dry) > sum(rainy)


def test_seasonal_demand_24_hours():
    demand = generate_seasonal_demand(500.0, month=3)
    assert len(demand) == 24
    assert all(d >= 0 for d in demand)


def test_actual_power_includes_age_degradation():
    farm = create_demo_farm(num_pumps=1)
    pump = farm.pumps[0]
    # P1: 45kW, eff=0.75, age=5 -> actual = (45/0.75) * (1 + 5*0.02) = 66.0
    expected = (45.0 / 0.75) * (1 + 5 * 0.02)
    assert abs(pump.actual_power_kw - expected) < 0.01
