import { useState } from 'react';
import { Play, RotateCw } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import { CostComparisonChart, SolarDemandChart, PumpScheduleChart, ReservoirChart } from '../components/Charts';
import { runOptimization, type OptimizeParams, type OptimizeResult } from '../lib/api';
import { fcfa, dec1 } from '../lib/format';

const SOLAR_CURVE = [0, 0, 0, 0, 0, 0, 0.05, 0.2, 0.45, 0.7, 0.88, 0.95, 1, 0.98, 0.9, 0.75, 0.5, 0.2, 0.03, 0, 0, 0, 0, 0];

function Slider({ label, value, onChange, min, max, step = 1, unit = '' }: {
  label: string; value: number; onChange: (v: number) => void;
  min: number; max: number; step?: number; unit?: string;
}) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-300 font-mono">{value}{unit}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none bg-[#1e293b] accent-emerald-500 cursor-pointer"
      />
    </div>
  );
}

export default function Optimizer() {
  const [params, setParams] = useState<OptimizeParams>({
    area_ha: 30, num_pumps: 3, subscribed_power_kw: 150, penalty_rate_fcfa: 200,
    tariff_peak: 110, tariff_offpeak: 75, peak_start: 7, peak_end: 23,
    solar_capacity_kw: 10, cloud_factor: 0.1, reservoir_m3: 500, et0_mm: null,
  });
  const [et0Enabled, setEt0Enabled] = useState(false);
  const [et0Value, setEt0Value] = useState(5);
  const [result, setResult] = useState<OptimizeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const set = (key: keyof OptimizeParams, value: number) =>
    setParams(p => ({ ...p, [key]: value }));

  const handleOptimize = async () => {
    setLoading(true);
    setError('');
    try {
      const finalParams = { ...params, et0_mm: et0Enabled ? et0Value : null };
      const res = await runOptimization(finalParams);
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  };

  const pumpIds = result ? [...new Set(result.schedule.map(s => s.pump_id))] : [];
  const pumpPower = result
    ? Array.from({ length: 24 }, (_, h) =>
        result.schedule.filter(s => s.hour === h && s.active).reduce((sum, s) => sum + s.actual_power_kw, 0))
    : [];
  const solar = SOLAR_CURVE.map(s => s * params.solar_capacity_kw * (1 - params.cloud_factor));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Optimisation interactive</h1>
        <p className="text-sm text-slate-500 mt-1">Ajustez les parametres et lancez l'optimisation MILP</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Controls panel */}
        <div className="lg:col-span-1 space-y-5 rounded-xl bg-[#111827] border border-[#1e293b] p-5">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Parametres</h3>

          <div className="space-y-4">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider">Ferme</p>
            <Slider label="Surface (ha)" value={params.area_ha} onChange={v => set('area_ha', v)} min={5} max={100} unit=" ha" />
            <Slider label="Pompes" value={params.num_pumps} onChange={v => set('num_pumps', v)} min={1} max={5} />
            <Slider label="Puissance souscrite" value={params.subscribed_power_kw} onChange={v => set('subscribed_power_kw', v)} min={50} max={300} step={10} unit=" kW" />
            <Slider label="Reservoir" value={params.reservoir_m3} onChange={v => set('reservoir_m3', v)} min={0} max={2000} step={50} unit=" m3" />
          </div>

          <div className="space-y-4">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider">Tarifs SONABEL</p>
            <Slider label="Heures pleines" value={params.tariff_peak} onChange={v => set('tariff_peak', v)} min={50} max={200} unit=" FCFA" />
            <Slider label="Heures creuses" value={params.tariff_offpeak} onChange={v => set('tariff_offpeak', v)} min={30} max={150} unit=" FCFA" />
            <Slider label="Penalite" value={params.penalty_rate_fcfa} onChange={v => set('penalty_rate_fcfa', v)} min={50} max={500} step={10} unit=" FCFA/kW" />
          </div>

          <div className="space-y-4">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider">Solaire & Meteo</p>
            <Slider label="Capacite solaire" value={params.solar_capacity_kw} onChange={v => set('solar_capacity_kw', v)} min={0} max={50} unit=" kW" />
            <Slider label="Couverture nuageuse" value={Math.round(params.cloud_factor * 100)} onChange={v => set('cloud_factor', v / 100)} min={0} max={100} unit="%" />
          </div>

          <div className="space-y-3">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider">ET0 dynamique</p>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={et0Enabled} onChange={e => setEt0Enabled(e.target.checked)}
                className="rounded accent-emerald-500" />
              <span className="text-xs text-slate-400">Utiliser ET0</span>
            </label>
            {et0Enabled && (
              <Slider label="ET0 (mm/jour)" value={et0Value} onChange={setEt0Value} min={1} max={12} step={0.5} unit=" mm" />
            )}
          </div>

          <button
            onClick={handleOptimize}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
          >
            {loading ? <RotateCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {loading ? 'Optimisation...' : "Lancer l'optimisation"}
          </button>
        </div>

        {/* Results panel */}
        <div className="lg:col-span-3 space-y-4">
          {error && (
            <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-red-400 text-sm">{error}</div>
          )}

          {!result && !error && (
            <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-12 text-center text-slate-500">
              Ajustez les parametres puis cliquez sur &laquo; Lancer l'optimisation &raquo;
            </div>
          )}

          {result && (
            <>
              <div className="flex items-center gap-2 text-xs text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                {result.solver_status} en {dec1(result.solve_time_s)}s
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <MetricCard label="Cout optimise" value={`${fcfa(result.total_cost_fcfa)} FCFA`} sub={`-${dec1(result.savings_pct)}%`} trend="down" />
                <MetricCard label="Baseline" value={`${fcfa(result.baseline_cost_fcfa)} FCFA`} />
                <MetricCard label="Economies" value={`${fcfa(result.savings_fcfa)} FCFA`} sub={`${fcfa(result.savings_fcfa * 30)}/mois`} trend="down" />
                <MetricCard label="Eau pompee" value={`${fcfa(result.total_water_m3)} m3`} sub={`Besoin: ${fcfa(result.water_demand_m3)}`} />
                <MetricCard label="Energie" value={`${fcfa(result.total_energy_kwh)} kWh`} />
                <MetricCard label="Demarrages" value={`${result.num_startups}`} sub={`${fcfa(result.startup_cost_fcfa)} FCFA`} />
                <MetricCard label="Penalites" value={`${fcfa(result.penalty_cost_fcfa)} FCFA`} />
                <MetricCard label="Puissance max" value={`${dec1(result.peak_power_kw)} kW`} trend={result.peak_power_kw > params.subscribed_power_kw ? 'up' : 'neutral'} />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <CostComparisonChart optimized={result.hourly_costs} baseline={result.hourly_baseline} />
                <SolarDemandChart solar={solar} power={pumpPower} />
              </div>

              <PumpScheduleChart schedule={result.schedule} pumpIds={pumpIds} />
              <ReservoirChart levels={result.reservoir_levels} />

              {/* Projections */}
              <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-4">
                <h3 className="text-sm font-medium text-slate-300 mb-3">Projections</h3>
                <div className="grid grid-cols-3 gap-4">
                  <MetricCard label="Economies / mois" value={`${fcfa(result.savings_fcfa * 30)} FCFA`} />
                  <MetricCard label="Economies / an" value={`${fcfa(result.savings_fcfa * 365)} FCFA`} />
                  <MetricCard label="ROI solaire"
                    value={params.solar_capacity_kw > 0 && result.savings_fcfa > 0
                      ? `${dec1(params.solar_capacity_kw * 350000 / (result.savings_fcfa * 365))} ans`
                      : 'N/A'} />
                </div>
              </div>

              {/* Schedule table */}
              <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-4 overflow-x-auto">
                <h3 className="text-sm font-medium text-slate-300 mb-3">Planning detaille</h3>
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-slate-500 border-b border-[#1e293b]">
                      <th className="py-2 text-left">Heure</th>
                      <th className="py-2 text-left">Pompe</th>
                      <th className="py-2 text-right">Puissance</th>
                      <th className="py-2 text-right">Debit</th>
                      <th className="py-2 text-left">Tarif</th>
                      <th className="py-2 text-right">Solaire</th>
                      <th className="py-2 text-center">Demarrage</th>
                      <th className="py-2 text-right">Cout</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.schedule.filter(s => s.active).map((s, i) => (
                      <tr key={i} className="border-b border-[#1e293b]/50 text-slate-300">
                        <td className="py-1.5">{String(s.hour).padStart(2, '0')}:00</td>
                        <td className="py-1.5 font-mono">{s.pump_id}</td>
                        <td className="py-1.5 text-right">{dec1(s.actual_power_kw)} kW</td>
                        <td className="py-1.5 text-right">{s.flow_m3h} m3/h</td>
                        <td className="py-1.5">{s.tariff_name}</td>
                        <td className="py-1.5 text-right">{dec1(s.solar_offset_kw)} kW</td>
                        <td className="py-1.5 text-center">{s.is_startup ? <span className="text-yellow-400">Oui</span> : ''}</td>
                        <td className="py-1.5 text-right">{fcfa(s.cost_fcfa)} FCFA</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
