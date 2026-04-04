import { useEffect, useState } from 'react';
import { RotateCw, Cpu, Droplets } from 'lucide-react';
import { getDemoConfig, type FarmConfig } from '../lib/api';
import { dec1 } from '../lib/format';

export default function Config() {
  const [config, setConfig] = useState<FarmConfig | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDemoConfig()
      .then(setConfig)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RotateCw className="w-5 h-5 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!config) return null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Configuration</h1>
        <p className="text-sm text-slate-500 mt-1">Parametres de la ferme et tarifs SONABEL</p>
      </div>

      {/* Tariffs */}
      <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-5">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Tarifs SONABEL</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {config.tariffs.map((t, i) => (
            <div key={i} className="bg-[#0a0f1a] rounded-lg p-3">
              <p className="text-xs text-slate-500">{t.name}</p>
              <p className="text-lg font-bold text-slate-100">{t.price_fcfa_kwh} <span className="text-xs text-slate-500">FCFA/kWh</span></p>
              <p className="text-[10px] text-slate-600">{t.start_hour}h - {t.end_hour}h</p>
            </div>
          ))}
          <div className="bg-[#0a0f1a] rounded-lg p-3">
            <p className="text-xs text-slate-500">Puissance souscrite</p>
            <p className="text-lg font-bold text-slate-100">{config.subscribed_power_kw} <span className="text-xs text-slate-500">kW</span></p>
          </div>
          <div className="bg-[#0a0f1a] rounded-lg p-3">
            <p className="text-xs text-slate-500">Penalite depassement</p>
            <p className="text-lg font-bold text-slate-100">{config.penalty_rate_fcfa} <span className="text-xs text-slate-500">FCFA/kW</span></p>
          </div>
        </div>
      </div>

      {/* Pumps */}
      <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-5">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Cpu className="w-4 h-4" /> Pompes
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {config.pumps.map(p => (
            <div key={p.id} className="bg-[#0a0f1a] rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-200">{p.name}</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400">{p.pump_type}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div><span className="text-slate-500">Debit:</span> <span className="text-slate-300">{p.capacity_m3h} m3/h</span></div>
                <div><span className="text-slate-500">Puissance:</span> <span className="text-slate-300">{p.power_kw} kW</span></div>
                <div><span className="text-slate-500">Puissance reelle:</span> <span className="text-slate-300">{dec1(p.actual_power_kw)} kW</span></div>
                <div><span className="text-slate-500">Efficacite:</span> <span className="text-slate-300">{p.efficiency}</span></div>
                <div><span className="text-slate-500">Age:</span> <span className="text-slate-300">{p.age_years} ans</span></div>
                <div><span className="text-slate-500">Max demarrages:</span> <span className="text-slate-300">{p.max_startups_per_day}/j</span></div>
                <div className="col-span-2"><span className="text-slate-500">Cout demarrage:</span> <span className="text-slate-300">{p.startup_cost_fcfa} FCFA</span></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Crops */}
      <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-5">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Droplets className="w-4 h-4" /> Cultures
        </h3>
        <table className="w-full text-xs">
          <thead>
            <tr className="text-slate-500 border-b border-[#1e293b]">
              <th className="py-2 text-left">Culture</th>
              <th className="py-2 text-right">Surface (ha)</th>
              <th className="py-2 text-right">Besoin eau (mm/j)</th>
              <th className="py-2 text-right">Kc</th>
              <th className="py-2 text-center">Priorite</th>
            </tr>
          </thead>
          <tbody>
            {config.crops.map((c, i) => (
              <tr key={i} className="border-b border-[#1e293b]/50 text-slate-300">
                <td className="py-2">{c.name}</td>
                <td className="py-2 text-right">{dec1(c.area_ha)}</td>
                <td className="py-2 text-right">{c.water_need_mm_day}</td>
                <td className="py-2 text-right">{c.kc}</td>
                <td className="py-2 text-center">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] ${
                    c.priority === 1 ? 'bg-red-500/10 text-red-400' : 'bg-blue-500/10 text-blue-400'
                  }`}>P{c.priority}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Architecture */}
      <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-5">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Architecture</h3>
        <pre className="text-xs text-slate-400 leading-relaxed font-mono">{`
  Open-Meteo API          →  Previsions + ET0
                                    ↓
  Config ferme (JSON/env) →  FastAPI Backend
                                    ↓
  Tarifs SONABEL          →  Moteur MILP (PuLP/CBC)
  Contraintes demarrages       (startup costs, penalites)
  Efficacite/age pompes             ↓
                             API REST JSON
                                    ↓
                             React + Recharts + Tailwind
        `}</pre>
      </div>

      {/* About */}
      <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-5 space-y-2">
        <h3 className="text-sm font-semibold text-slate-300">AgriWater Dashboard v0.2.0</h3>
        <p className="text-xs text-slate-500 leading-relaxed">
          Systeme d'optimisation energetique pour l'irrigation agricole au Sahel.
          Base sur le moteur agriwater-optimizer original. Optimisation MILP avec
          detection demarrages, degradation pompes, demande dynamique ET0,
          profils saisonniers saheliens, tarifs SONABEL.
        </p>
        <p className="text-xs text-slate-600">Auteur : OUEDRAOGO Abdoulaye</p>
      </div>
    </div>
  );
}
