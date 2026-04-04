import {
  BarChart, Bar, ComposedChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from 'recharts';

const COLORS = {
  green: '#10b981',
  red: '#ef4444',
  blue: '#3b82f6',
  yellow: '#f59e0b',
  purple: '#8b5cf6',
  slate: '#475569',
};

const tooltipStyle = {
  contentStyle: { background: '#1e293b', border: '1px solid #334155', borderRadius: 8 },
  labelStyle: { color: '#94a3b8' },
};

// --- Cost Comparison ---
interface CostData { hour: string; optimise: number; baseline: number }

export function CostComparisonChart({ optimized, baseline }: { optimized: number[]; baseline: number[] }) {
  const data: CostData[] = optimized.map((v, i) => ({
    hour: `${i}h`,
    optimise: Math.round(v),
    baseline: Math.round(baseline[i] || 0),
  }));

  return (
    <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-4">
      <h3 className="text-sm font-medium text-slate-300 mb-3">Cout horaire : Optimise vs Baseline</h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip {...tooltipStyle} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="baseline" name="Baseline" fill={COLORS.red} opacity={0.4} radius={[2, 2, 0, 0]} />
          <Bar dataKey="optimise" name="Optimise" fill={COLORS.green} radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// --- Solar vs Demand ---
export function SolarDemandChart({ solar, power }: { solar: number[]; power: number[] }) {
  const data = solar.map((s, i) => ({ hour: `${i}h`, solaire: s, demande: Math.round(power[i] || 0) }));

  return (
    <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-4">
      <h3 className="text-sm font-medium text-slate-300 mb-3">Solaire vs Demande energetique</h3>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip {...tooltipStyle} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Area type="monotone" dataKey="solaire" name="Solaire (kW)" stroke={COLORS.yellow} fill={COLORS.yellow} fillOpacity={0.2} />
          <Area type="monotone" dataKey="demande" name="Demande (kW)" stroke={COLORS.blue} fill={COLORS.blue} fillOpacity={0.15} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// --- Pump Schedule Heatmap ---
export function PumpScheduleChart({ schedule, pumpIds }: { schedule: { hour: number; pump_id: string; active: boolean }[]; pumpIds: string[] }) {
  const hours = Array.from({ length: 24 }, (_, i) => i);

  return (
    <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-4">
      <h3 className="text-sm font-medium text-slate-300 mb-3">Planning des pompes (24h)</h3>
      <div className="overflow-x-auto">
        <div className="flex gap-2 mb-2">
          <div className="w-12" />
          {hours.map(h => (
            <div key={h} className="w-8 text-center text-[10px] text-slate-500">{h}h</div>
          ))}
        </div>
        {pumpIds.map(pid => (
          <div key={pid} className="flex gap-2 mb-1 items-center">
            <div className="w-12 text-xs text-slate-400 font-mono">{pid}</div>
            {hours.map(h => {
              const active = schedule.some(s => s.hour === h && s.pump_id === pid && s.active);
              return (
                <div
                  key={h}
                  className={`w-8 h-6 rounded-sm transition-colors ${
                    active ? 'bg-emerald-500' : 'bg-[#1a2332]'
                  }`}
                  title={`${pid} ${h}h: ${active ? 'ON' : 'OFF'}`}
                />
              );
            })}
          </div>
        ))}
        <div className="flex gap-3 mt-3 ml-12">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-sm bg-emerald-500" />
            <span className="text-[10px] text-slate-500">Actif</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-sm bg-[#1a2332]" />
            <span className="text-[10px] text-slate-500">Inactif</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- Reservoir Level ---
export function ReservoirChart({ levels }: { levels: number[] }) {
  const data = levels.map((v, i) => ({ hour: `${i}h`, niveau: Math.round(v) }));

  return (
    <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-4">
      <h3 className="text-sm font-medium text-slate-300 mb-3">Niveau du reservoir</h3>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip {...tooltipStyle} />
          <Area type="monotone" dataKey="niveau" name="Reservoir (m3)" stroke={COLORS.blue} fill={COLORS.blue} fillOpacity={0.2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// --- Weather Forecast ---
export function WeatherChart({ days }: { days: { date: string; temp_max: number; temp_min: number; precipitation_mm: number }[] }) {
  return (
    <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-4">
      <h3 className="text-sm font-medium text-slate-300 mb-3">Previsions meteo (7 jours)</h3>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={days}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis yAxisId="temp" tick={{ fontSize: 11 }} />
          <YAxis yAxisId="rain" orientation="right" tick={{ fontSize: 11 }} />
          <Tooltip {...tooltipStyle} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar yAxisId="rain" dataKey="precipitation_mm" name="Pluie (mm)" fill={COLORS.blue} opacity={0.5} radius={[2, 2, 0, 0]} />
          <Line yAxisId="temp" type="monotone" dataKey="temp_max" name="Temp max" stroke={COLORS.red} strokeWidth={2} dot={{ r: 3 }} />
          <Line yAxisId="temp" type="monotone" dataKey="temp_min" name="Temp min" stroke={COLORS.blue} strokeWidth={2} dot={{ r: 3 }} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

// --- ET0 Chart ---
export function ET0Chart({ days }: { days: { date: string; et0_mm: number; precipitation_mm: number }[] }) {
  return (
    <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-4">
      <h3 className="text-sm font-medium text-slate-300 mb-3">Evapotranspiration vs Precipitation</h3>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={days}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip {...tooltipStyle} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Area type="monotone" dataKey="et0_mm" name="ET0 (mm)" stroke={COLORS.red} fill={COLORS.red} fillOpacity={0.15} />
          <Bar dataKey="precipitation_mm" name="Pluie (mm)" fill={COLORS.blue} opacity={0.5} radius={[2, 2, 0, 0]} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
