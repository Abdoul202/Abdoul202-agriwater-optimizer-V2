"""Tests for the MILP optimization engine."""

from agriwater.data.generator import create_demo_farm, generate_solar_profile
from agriwater.optimizer.engine import IrrigationOptimizer


def test_optimization_finds_solution():
    farm = create_demo_farm(area_ha=10)
    optimizer = IrrigationOptimizer(farm)
    result = optimizer.optimize()

    assert result.solver_status == "Optimal"
    assert result.total_water_m3 >= result.water_demand_m3
    assert result.total_cost_fcfa > 0


def test_optimization_saves_vs_baseline():
    # Use 30ha where pumps have slack to shift load to cheaper hours
    farm = create_demo_farm(area_ha=30)
    optimizer = IrrigationOptimizer(farm)
    result = optimizer.optimize()

    assert result.savings_fcfa >= 0
    assert result.total_cost_fcfa <= result.baseline_cost_fcfa


def test_solar_reduces_cost():
    farm = create_demo_farm(area_ha=20)
    optimizer = IrrigationOptimizer(farm)

    result_no_solar = optimizer.optimize(solar_profile=[0.0] * 24)
    solar = generate_solar_profile(10.0, cloud_factor=0.0)
    result_solar = optimizer.optimize(solar_profile=solar)

    assert result_solar.total_cost_fcfa <= result_no_solar.total_cost_fcfa


def test_schedule_not_empty():
    farm = create_demo_farm(area_ha=10)
    optimizer = IrrigationOptimizer(farm)
    result = optimizer.optimize()

    assert len(result.schedule) > 0
    assert all(s.active for s in result.schedule)


def test_penalty_decreases_with_optimization():
    farm = create_demo_farm(area_ha=30)
    optimizer = IrrigationOptimizer(farm)
    result = optimizer.optimize()

    assert result.penalty_cost_fcfa <= result.baseline_penalty_fcfa


def test_startup_tracking():
    farm = create_demo_farm(area_ha=10)
    optimizer = IrrigationOptimizer(farm)
    result = optimizer.optimize()

    assert result.num_startups >= 0
    assert result.startup_cost_fcfa >= 0
    # Each startup costs 5000 FCFA
    assert result.startup_cost_fcfa == result.num_startups * 5000.0


def test_et0_driven_demand():
    farm = create_demo_farm(area_ha=20)
    optimizer = IrrigationOptimizer(farm)

    # Higher ET0 means more water demand
    result_low = optimizer.optimize(et0_mm=3.0)
    result_high = optimizer.optimize(et0_mm=8.0)

    assert result_high.water_demand_m3 > result_low.water_demand_m3


def test_hourly_demand_input():
    farm = create_demo_farm(area_ha=10)
    optimizer = IrrigationOptimizer(farm)

    # Provide explicit hourly demand
    demand = [30.0] * 6 + [60.0] * 4 + [20.0] * 8 + [50.0] * 6
    result = optimizer.optimize(hourly_demand_m3=demand)

    assert result.solver_status == "Optimal"
    assert result.water_demand_m3 > 0


def test_reservoir_levels_tracked():
    farm = create_demo_farm(area_ha=10)
    optimizer = IrrigationOptimizer(farm)
    result = optimizer.optimize()

    # 25 levels: initial + 24 hours
    assert len(result.reservoir_levels) == 25
    assert result.reservoir_levels[0] == farm.reservoir_initial_m3


def test_solve_time_recorded():
    farm = create_demo_farm(area_ha=10)
    optimizer = IrrigationOptimizer(farm)
    result = optimizer.optimize()

    assert result.solve_time_s > 0
