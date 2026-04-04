"""
MILP Optimizer - Minimize irrigation energy costs.

Based on the original agriwater-optimizer by Abdoulaye Ouedraogo.
Uses PuLP/CBC to schedule pump operations with:
- Startup detection and costs (5000 FCFA per startup)
- Max startups per day per pump (8)
- Subscribed power penalty (200 FCFA/kW exceeded)
- Age-based pump efficiency degradation (2%/year)
- ET0-driven dynamic water demand
- Reservoir level tracking
- Solar offset support
"""

from __future__ import annotations

import logging
import time

import pulp

from agriwater.optimizer.models import (
    FarmConfig,
    HourlySchedule,
    OptimizationResult,
)

logger = logging.getLogger(__name__)

HOURS = list(range(24))


class IrrigationOptimizer:
    """MILP-based pump scheduling optimizer aligned with original agriwater."""

    def __init__(self, config: FarmConfig) -> None:
        self.config = config
        self._tariff_map = self._build_tariff_map()

    def _build_tariff_map(self) -> dict[int, tuple[str, float]]:
        """Map each hour to its tariff name and price."""
        tariff_map: dict[int, tuple[str, float]] = {}
        for h in HOURS:
            for t in self.config.tariffs:
                if t.start_hour <= h < t.end_hour:
                    tariff_map[h] = (t.name, t.price_fcfa_kwh)
                    break
            if h not in tariff_map:
                cheapest = min(self.config.tariffs, key=lambda t: t.price_fcfa_kwh)
                tariff_map[h] = (cheapest.name, cheapest.price_fcfa_kwh)
        return tariff_map

    def optimize(
        self,
        solar_profile: list[float] | None = None,
        hourly_demand_m3: list[float] | None = None,
        et0_mm: float | None = None,
    ) -> OptimizationResult:
        """
        Run MILP optimization for a single day (24h).

        Args:
            solar_profile: 24 values of solar power available (kW per hour).
            hourly_demand_m3: 24 values of water demand (m3/h). If None,
                computed from crop data (optionally using ET0).
            et0_mm: Evapotranspiration in mm/day. Used to compute dynamic
                crop water demand when hourly_demand_m3 is not provided.

        Returns:
            OptimizationResult with schedule and cost comparison.
        """
        if solar_profile is None:
            solar_profile = [0.0] * 24

        config = self.config
        pumps = config.pumps

        # --- Water demand ---
        if hourly_demand_m3 is not None:
            demand_per_hour = hourly_demand_m3[:24]
            # Pad if shorter
            while len(demand_per_hour) < 24:
                demand_per_hour.append(0.0)
            water_demand = sum(demand_per_hour)
        else:
            # Compute from crops, using ET0 if available
            water_demand = sum(c.daily_demand_m3(et0_mm) for c in config.crops)
            # Distribute demand across a realistic irrigation profile
            demand_per_hour = self._distribute_demand(water_demand)

        # --- Build MILP problem ---
        t0 = time.monotonic()
        prob = pulp.LpProblem("AgriWater_Irrigation_Scheduling", pulp.LpMinimize)

        # Decision variables: pump_status[p][h] = 1 if pump p active at hour h
        pump_status: dict[str, dict[int, pulp.LpVariable]] = {}
        for pump in pumps:
            pump_status[pump.id] = {}
            for h in HOURS:
                pump_status[pump.id][h] = pulp.LpVariable(
                    f"pump_{pump.id}_h{h}", cat=pulp.LpBinary,
                )

        # Startup detection: startup[p][h] = 1 if pump p starts at hour h
        startup: dict[str, dict[int, pulp.LpVariable]] = {}
        for pump in pumps:
            startup[pump.id] = {}
            for h in HOURS:
                startup[pump.id][h] = pulp.LpVariable(
                    f"startup_{pump.id}_h{h}", cat=pulp.LpBinary,
                )

        # Total power per hour
        total_power: dict[int, pulp.LpVariable] = {}
        for h in HOURS:
            total_power[h] = pulp.LpVariable(f"total_power_h{h}", lowBound=0)

        # Penalty per hour (power exceedance)
        penalty: dict[int, pulp.LpVariable] = {}
        for h in HOURS:
            penalty[h] = pulp.LpVariable(f"penalty_h{h}", lowBound=0)

        # --- Objective function ---
        # Minimize: energy cost + penalty cost + startup cost - solar savings
        solar_contrib = config.solar_contribution

        objective = pulp.lpSum([
            # Energy cost (using actual power adjusted for efficiency/age)
            total_power[h] * self._tariff_map[h][1]
            # Penalty for exceeding subscribed power
            + penalty[h]
            # Startup costs
            + pulp.lpSum([
                startup[pump.id][h] * pump.startup_cost_fcfa
                for pump in pumps
            ])
            # Solar offset savings (negative cost)
            - pulp.lpSum([
                pump_status[pump.id][h]
                * min(solar_profile[h] * solar_contrib, pump.actual_power_kw)
                * self._tariff_map[h][1]
                for pump in pumps
            ]) if solar_profile[h] > 0 else 0
            for h in HOURS
        ])
        prob += objective

        # --- Constraints ---

        # 1. Satisfy hourly water demand
        for h in HOURS:
            prob += (
                pulp.lpSum([
                    pump_status[pump.id][h] * pump.capacity_m3h
                    for pump in pumps
                ]) >= demand_per_hour[h],
                f"demand_h{h}",
            )

        # 2. Total power calculation (using actual power with efficiency/age)
        for h in HOURS:
            prob += (
                total_power[h] == pulp.lpSum([
                    pump_status[pump.id][h] * pump.actual_power_kw
                    for pump in pumps
                ]),
                f"total_power_calc_h{h}",
            )

        # 3. Penalty calculation (if exceeding subscribed power)
        for h in HOURS:
            prob += (
                penalty[h] >= config.penalty_rate_fcfa * (
                    total_power[h] - config.subscribed_power_kw
                ),
                f"penalty_calc_h{h}",
            )

        # 4. Startup detection: startup[p][h] >= status[p][h] - status[p][h-1]
        for pump in pumps:
            # Hour 0: startup if pump is on
            prob += (
                startup[pump.id][0] >= pump_status[pump.id][0],
                f"startup_detect_{pump.id}_h0",
            )
            for h in range(1, 24):
                prob += (
                    startup[pump.id][h] >=
                    pump_status[pump.id][h] - pump_status[pump.id][h - 1],
                    f"startup_detect_{pump.id}_h{h}",
                )

        # 5. Max startups per day per pump
        for pump in pumps:
            prob += (
                pulp.lpSum([startup[pump.id][h] for h in HOURS])
                <= pump.max_startups_per_day,
                f"max_startups_{pump.id}",
            )

        # 6. Max hours per pump per day
        for pump in pumps:
            prob += (
                pulp.lpSum([pump_status[pump.id][h] for h in HOURS])
                <= pump.max_hours_per_day,
                f"max_hours_{pump.id}",
            )

        # --- Solve ---
        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=60)
        prob.solve(solver)
        solve_time = time.monotonic() - t0

        status = pulp.LpStatus[prob.status]
        logger.info("Solver status: %s (%.2fs)", status, solve_time)

        # --- Extract results ---
        schedule: list[HourlySchedule] = []
        hourly_costs = [0.0] * 24
        hourly_power = [0.0] * 24
        hourly_demand_out = list(demand_per_hour)
        reservoir_levels = [config.reservoir_initial_m3]
        total_energy_kwh = 0.0
        total_penalty = 0.0
        total_startup_cost = 0.0
        total_energy_cost = 0.0
        num_startups = 0
        peak_power = 0.0
        total_water_pumped = 0.0

        reservoir_level = config.reservoir_initial_m3

        for h in HOURS:
            hour_power = 0.0
            hour_flow = 0.0
            hour_cost = 0.0
            pen_val = pulp.value(penalty[h]) or 0.0

            for pump in pumps:
                active = (pulp.value(pump_status[pump.id][h]) or 0) > 0.5
                is_start = (pulp.value(startup[pump.id][h]) or 0) > 0.5

                if active:
                    tariff_name, price = self._tariff_map[h]
                    solar_kw = min(
                        solar_profile[h] * solar_contrib, pump.actual_power_kw,
                    )
                    net_power = pump.actual_power_kw - solar_kw
                    cost = net_power * price
                    start_cost = pump.startup_cost_fcfa if is_start else 0.0

                    hour_power += pump.actual_power_kw
                    hour_flow += pump.capacity_m3h
                    hour_cost += cost + start_cost
                    total_energy_cost += cost
                    total_startup_cost += start_cost
                    total_energy_kwh += pump.actual_power_kw
                    total_water_pumped += pump.capacity_m3h

                    if is_start:
                        num_startups += 1

                    schedule.append(HourlySchedule(
                        hour=h,
                        pump_id=pump.id,
                        active=True,
                        power_kw=pump.power_kw,
                        actual_power_kw=pump.actual_power_kw,
                        flow_m3h=pump.capacity_m3h,
                        cost_fcfa=cost + start_cost,
                        tariff_name=tariff_name,
                        tariff_price=price,
                        solar_offset_kw=solar_kw,
                        is_startup=is_start,
                    ))

            total_penalty += pen_val
            hour_cost += pen_val
            hourly_costs[h] = hour_cost
            hourly_power[h] = hour_power
            peak_power = max(peak_power, hour_power)

            # Reservoir tracking
            reservoir_level = min(
                config.reservoir_capacity_m3,
                max(0, reservoir_level + hour_flow - demand_per_hour[h]),
            )
            reservoir_levels.append(reservoir_level)

        total_cost = total_energy_cost + total_penalty + total_startup_cost

        # --- Baseline comparison ---
        baseline_cost, baseline_penalty, hourly_baseline = self._compute_baseline(
            demand_per_hour, solar_profile,
        )

        savings = baseline_cost - total_cost
        savings_pct = (savings / baseline_cost * 100) if baseline_cost > 0 else 0

        return OptimizationResult(
            total_cost_fcfa=total_cost,
            baseline_cost_fcfa=baseline_cost,
            savings_fcfa=savings,
            savings_pct=savings_pct,
            energy_cost_fcfa=total_energy_cost,
            penalty_cost_fcfa=total_penalty,
            startup_cost_fcfa=total_startup_cost,
            baseline_penalty_fcfa=baseline_penalty,
            total_water_m3=total_water_pumped,
            water_demand_m3=water_demand,
            total_energy_kwh=total_energy_kwh,
            peak_power_kw=peak_power,
            num_startups=num_startups,
            schedule=schedule,
            hourly_costs=hourly_costs,
            hourly_power=hourly_power,
            hourly_baseline=hourly_baseline,
            hourly_demand=hourly_demand_out,
            reservoir_levels=reservoir_levels,
            solver_status=status,
            solve_time_s=solve_time,
        )

    def _distribute_demand(self, daily_total_m3: float) -> list[float]:
        """
        Distribute daily water demand across 24 hours using a realistic
        Sahelian irrigation profile (morning + evening peaks, minimal midday).

        Caps hourly demand to not exceed total pump capacity so the MILP
        remains feasible; excess is redistributed to lighter hours.
        """
        # Weights from original data_generator demand pattern
        weights = [
            0.02, 0.02, 0.02, 0.02, 0.02,  # 00-04: night minimal
            0.08, 0.10, 0.10, 0.08,          # 05-08: morning peak
            0.04, 0.03, 0.02, 0.02, 0.02, 0.02, 0.03,  # 09-15: midday low
            0.04, 0.05,                        # 16-17: pre-evening
            0.08, 0.08, 0.07, 0.06,           # 18-21: evening peak
            0.04, 0.03,                        # 22-23: night
        ]
        total_w = sum(weights)
        demand = [daily_total_m3 * (w / total_w) for w in weights]

        # Cap at total pump capacity to keep MILP feasible
        max_cap = self.config.total_pump_capacity_m3h()
        if max_cap > 0:
            excess = 0.0
            for i in range(24):
                if demand[i] > max_cap * 0.95:
                    excess += demand[i] - max_cap * 0.95
                    demand[i] = max_cap * 0.95
            # Redistribute excess to lighter hours
            if excess > 0:
                light_hours = [i for i in range(24) if demand[i] < max_cap * 0.5]
                if light_hours:
                    per_hour = excess / len(light_hours)
                    for i in light_hours:
                        demand[i] += per_hour

        return demand

    def _compute_baseline(
        self,
        demand_per_hour: list[float],
        solar_profile: list[float],
    ) -> tuple[float, float, list[float]]:
        """
        Compute naive baseline: sequential pump activation (like original).

        The baseline activates pumps fully (binary on/off) in order P1→P2→P3
        whenever there is demand, without time-shifting to cheaper tariff
        periods. This mirrors the original agriwater-optimizer behaviour and
        provides a fair comparison against the MILP binary decisions.
        """
        config = self.config
        pumps = config.pumps
        solar_contrib = config.solar_contribution

        hourly_baseline = [0.0] * 24
        total_cost = 0.0
        total_penalty = 0.0

        prev_active: set[str] = set()

        for h in HOURS:
            dem = demand_per_hour[h]
            if dem <= 0:
                continue

            remaining = dem
            hour_power = 0.0
            curr_active: set[str] = set()

            # Activate pumps sequentially (binary on/off, like original)
            for pump in pumps:
                if remaining <= 0:
                    break
                # Full activation (binary)
                actual_pw = pump.actual_power_kw
                solar_kw = min(solar_profile[h] * solar_contrib, actual_pw)
                net_kw = actual_pw - solar_kw

                _, price = self._tariff_map[h]
                cost = net_kw * price

                # Startup cost if pump was off previous hour
                if pump.id not in prev_active:
                    cost += pump.startup_cost_fcfa

                hourly_baseline[h] += cost
                total_cost += cost
                hour_power += actual_pw
                remaining -= pump.capacity_m3h
                curr_active.add(pump.id)

            # Penalty
            if hour_power > config.subscribed_power_kw:
                excess = hour_power - config.subscribed_power_kw
                pen = excess * config.penalty_rate_fcfa
                hourly_baseline[h] += pen
                total_cost += pen
                total_penalty += pen

            prev_active = curr_active

        return total_cost, total_penalty, hourly_baseline
