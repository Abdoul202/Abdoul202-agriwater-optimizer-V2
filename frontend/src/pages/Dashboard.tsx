import { useEffect, useState } from 'react';
import { Zap, Droplets, DollarSign, Gauge, Power, RotateCw } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import { CostComparisonChart, SolarDemandChart, PumpScheduleChart, ReservoirChart } from '../components/Charts';
import { runOptimization, type OptimizeResult } from '../lib/api';
import { fcfa, dec1 } from '../lib/format';

const DEFAULT_PARAMS = {
  area_ha: 30, num_pumps: 3, subscribed_power_kw: 150, penalty_rate_fcfa: 200,
  tariff_peak: 110, tariff_offpeak: 75, peak_start: 7, peak_end: 23,
  solar_capacity_kw: 10, cloud_factor: 0.1, reservoir_m3: 500, et0_mm: null,
};

// Simple solar profile for display
const SOLAR = [0, 0, 0, 0, 0, 0, 0.5, 2, 4.5, 7, 8.8, 9.5, 10, 9.8, 9, 7.5, 5, 2, 0.3, 0, 0, 0, 0, 0];

export default function Dashboard() {
  const [result, setResult] = useState<OptimizeResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    runOptimization(DEFAULT_PARAMS)
      .then(setResult)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center gap-3 text-slate-400">
          <RotateCw className="w-5 h-5 animate-spin" />
          <span>Optimisation en cours...</span>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-6 text-red-400">
        Erreur: {error || 'Pas de resultat'}. Verifiez que le backend est lance (uvicorn api.main:app).
      </div>
    );
  }

  const pumpIds = [...new Set(result.schedule.map(s => s.pump_id))];
  const pumpPower = Array.from({ length: 24 }, (_, h) =>
    result.schedule.filter(s => s.hour === h && s.active).reduce((sum, s) => sum + s.actual_power_kw, 0)
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Tableau de bord</h1>
        <p className="text-sm text-slate-500 mt-1">
          Vue d'ensemble de l'optimisation energetique &middot; Solveur: {result.solver_status} ({dec1(result.solve_time_s)}s)
        </p>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard
          label="Cout optimise"
          value={`${fcfa(result.total_cost_fcfa)} FCFA`}
          sub={`-${dec1(result.savings_pct)}% vs baseline`}
          trend="down"
          icon={<DollarSign className="w-4 h-4" />}
        />
        <MetricCard
          label="Economies"
          value={`${fcfa(result.savings_fcfa)} FCFA/j`}
          sub={`${fcfa(result.savings_fcfa * 30)} FCFA/mois`}
          trend="down"
          icon={<Zap className="w-4 h-4" />}
        />
        <MetricCard
          label="Eau pompee"
          value={`${fcfa(result.total_water_m3)} m3`}
          sub={`Besoin: ${fcfa(result.water_demand_m3)} m3`}
          icon={<Droplets className="w-4 h-4" />}
        />
        <MetricCard
          label="Penalites"
          value={`${fcfa(result.penalty_cost_fcfa)} FCFA`}
          sub={`Baseline: ${fcfa(result.baseline_penalty_fcfa)}`}
          trend="down"
          icon={<Gauge className="w-4 h-4" />}
        />
        <MetricCard label="Energie totale" value={`${fcfa(result.total_energy_kwh)} kWh`} icon={<Power className="w-4 h-4" />} />
        <MetricCard label="Demarrages" value={`${result.num_startups}`} sub={`Cout: ${fcfa(result.startup_cost_fcfa)} FCFA`} />
        <MetricCard label="Puissance max" value={`${dec1(result.peak_power_kw)} kW`} sub="Souscrit: 150 kW" trend={result.peak_power_kw > 150 ? 'up' : 'neutral'} />
        <MetricCard label="Baseline" value={`${fcfa(result.baseline_cost_fcfa)} FCFA`} sub="Cout sans optimisation" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <CostComparisonChart optimized={result.hourly_costs} baseline={result.hourly_baseline} />
        <SolarDemandChart solar={SOLAR} power={pumpPower} />
      </div>

      {/* Pump schedule */}
      <PumpScheduleChart schedule={result.schedule} pumpIds={pumpIds} />

      {/* Reservoir */}
      <ReservoirChart levels={result.reservoir_levels} />
    </div>
  );
}
