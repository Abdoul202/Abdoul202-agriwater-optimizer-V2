const BASE = '/api';

export interface OptimizeParams {
  area_ha: number;
  num_pumps: number;
  subscribed_power_kw: number;
  penalty_rate_fcfa: number;
  tariff_peak: number;
  tariff_offpeak: number;
  peak_start: number;
  peak_end: number;
  solar_capacity_kw: number;
  cloud_factor: number;
  reservoir_m3: number;
  et0_mm: number | null;
}

export interface HourlySchedule {
  hour: number;
  pump_id: string;
  active: boolean;
  power_kw: number;
  actual_power_kw: number;
  flow_m3h: number;
  cost_fcfa: number;
  tariff_name: string;
  tariff_price: number;
  solar_offset_kw: number;
  is_startup: boolean;
}

export interface OptimizeResult {
  total_cost_fcfa: number;
  baseline_cost_fcfa: number;
  savings_fcfa: number;
  savings_pct: number;
  energy_cost_fcfa: number;
  penalty_cost_fcfa: number;
  startup_cost_fcfa: number;
  baseline_penalty_fcfa: number;
  total_water_m3: number;
  water_demand_m3: number;
  total_energy_kwh: number;
  peak_power_kw: number;
  num_startups: number;
  schedule: HourlySchedule[];
  hourly_costs: number[];
  hourly_power: number[];
  hourly_baseline: number[];
  hourly_demand: number[];
  reservoir_levels: number[];
  solver_status: string;
  solve_time_s: number;
}

export interface Pump {
  id: string;
  name: string;
  capacity_m3h: number;
  power_kw: number;
  actual_power_kw: number;
  efficiency: number;
  age_years: number;
  pump_type: string;
  max_startups_per_day: number;
  startup_cost_fcfa: number;
}

export interface Crop {
  name: string;
  area_ha: number;
  water_need_mm_day: number;
  kc: number;
  priority: number;
}

export interface Tariff {
  name: string;
  start_hour: number;
  end_hour: number;
  price_fcfa_kwh: number;
}

export interface FarmConfig {
  name: string;
  pumps: Pump[];
  crops: Crop[];
  tariffs: Tariff[];
  subscribed_power_kw: number;
  penalty_rate_fcfa: number;
  solar_capacity_kw: number;
  solar_contribution: number;
  reservoir_capacity_m3: number;
}

export interface DayWeather {
  date: string;
  temp_max: number;
  temp_min: number;
  precipitation_mm: number;
  et0_mm: number;
  sunshine_hours: number;
  wind_speed_max: number;
  humidity_mean: number;
}

export interface ForecastResponse {
  days: DayWeather[];
  drought_risk: string;
}

export async function runOptimization(params: OptimizeParams): Promise<OptimizeResult> {
  const res = await fetch(`${BASE}/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Optimization failed: ${res.status}`);
  return res.json();
}

export async function getForecast(days = 7): Promise<ForecastResponse> {
  const res = await fetch(`${BASE}/weather/forecast?days=${days}`);
  if (!res.ok) throw new Error(`Forecast failed: ${res.status}`);
  return res.json();
}

export async function getHistory(daysBack = 30): Promise<{ days: DayWeather[] }> {
  const res = await fetch(`${BASE}/weather/history?days_back=${daysBack}`);
  if (!res.ok) throw new Error(`History failed: ${res.status}`);
  return res.json();
}

export async function getDemoConfig(): Promise<FarmConfig> {
  const res = await fetch(`${BASE}/config/demo`);
  if (!res.ok) throw new Error(`Config failed: ${res.status}`);
  return res.json();
}
