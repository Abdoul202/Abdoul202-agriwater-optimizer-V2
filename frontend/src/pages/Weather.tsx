import { useEffect, useState } from 'react';
import { RotateCw, CloudRain, Thermometer, Droplets, Wind } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import { WeatherChart, ET0Chart } from '../components/Charts';
import { getForecast, getHistory, type DayWeather } from '../lib/api';
import { dec1 } from '../lib/format';

const RISK_STYLE: Record<string, { color: string; bg: string; label: string }> = {
  low: { color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30', label: 'Faible' },
  moderate: { color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/30', label: 'Modere' },
  high: { color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/30', label: 'Eleve' },
  severe: { color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/30', label: 'Severe' },
  unknown: { color: 'text-slate-400', bg: 'bg-slate-500/10 border-slate-500/30', label: 'Inconnu' },
};

export default function Weather() {
  const [forecast, setForecast] = useState<{ days: DayWeather[]; drought_risk: string } | null>(null);
  const [history, setHistory] = useState<DayWeather[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getForecast(7).catch(() => null),
      getHistory(30).catch(() => ({ days: [] })),
    ]).then(([fc, hist]) => {
      if (fc) setForecast(fc);
      else setError('Impossible de charger les previsions meteo');
      setHistory(hist.days);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center gap-3 text-slate-400">
          <RotateCw className="w-5 h-5 animate-spin" />
          <span>Chargement meteo...</span>
        </div>
      </div>
    );
  }

  if (error || !forecast) {
    return (
      <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-6 text-red-400">
        {error || 'Erreur de chargement'}. Verifiez que le backend est lance.
      </div>
    );
  }

  const risk = RISK_STYLE[forecast.drought_risk] || RISK_STYLE.unknown;
  const totalRain = forecast.days.reduce((s, d) => s + d.precipitation_mm, 0);
  const totalET0 = forecast.days.reduce((s, d) => s + d.et0_mm, 0);
  const avgTemp = forecast.days.reduce((s, d) => s + d.temp_max, 0) / forecast.days.length;
  const avgHumidity = forecast.days.reduce((s, d) => s + d.humidity_mean, 0) / forecast.days.length;

  const waterBalance = totalRain - totalET0;
  const histRain = history.reduce((s, d) => s + d.precipitation_mm, 0);
  const histET0 = history.reduce((s, d) => s + d.et0_mm, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Meteo & Risque de secheresse</h1>
        <p className="text-sm text-slate-500 mt-1">Donnees Open-Meteo pour Ouagadougou (12.37, -1.52)</p>
      </div>

      {/* Drought risk banner */}
      <div className={`rounded-xl border p-4 ${risk.bg}`}>
        <span className={`text-sm font-semibold ${risk.color}`}>
          Risque de secheresse : {risk.label.toUpperCase()}
        </span>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard label="Precipitation (7j)" value={`${dec1(totalRain)} mm`} icon={<CloudRain className="w-4 h-4" />} />
        <MetricCard label="ET0 totale (7j)" value={`${dec1(totalET0)} mm`} icon={<Droplets className="w-4 h-4" />} />
        <MetricCard label="Temp moy max" value={`${dec1(avgTemp)} C`} icon={<Thermometer className="w-4 h-4" />} />
        <MetricCard label="Humidite moy" value={`${Math.round(avgHumidity)}%`} icon={<Wind className="w-4 h-4" />} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <WeatherChart days={forecast.days} />
        <ET0Chart days={forecast.days} />
      </div>

      {/* Irrigation recommendation */}
      <div className={`rounded-xl border p-5 ${waterBalance >= 0
        ? 'bg-emerald-500/10 border-emerald-500/30'
        : 'bg-yellow-500/10 border-yellow-500/30'
      }`}>
        <h3 className="text-sm font-semibold text-slate-200 mb-2">Recommandation irrigation</h3>
        {waterBalance >= 0 ? (
          <p className="text-sm text-emerald-300">
            Les precipitations prevues ({dec1(totalRain)} mm) couvrent l'evapotranspiration ({dec1(totalET0)} mm). Reduire l'irrigation cette semaine.
          </p>
        ) : (
          <p className="text-sm text-yellow-300">
            Deficit hydrique prevu : <strong>{dec1(Math.abs(waterBalance))} mm</strong> sur 7 jours.
            Pour 50 ha, cela represente environ <strong>{Math.round(Math.abs(waterBalance) * 50 * 10).toLocaleString('fr-FR')} m3</strong> d'eau a compenser.
          </p>
        )}
      </div>

      {/* Daily details */}
      <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-4 overflow-x-auto">
        <h3 className="text-sm font-medium text-slate-300 mb-3">Details par jour</h3>
        <table className="w-full text-xs">
          <thead>
            <tr className="text-slate-500 border-b border-[#1e293b]">
              <th className="py-2 text-left">Date</th>
              <th className="py-2 text-right">Temp max</th>
              <th className="py-2 text-right">Temp min</th>
              <th className="py-2 text-right">Pluie</th>
              <th className="py-2 text-right">ET0</th>
              <th className="py-2 text-right">Soleil</th>
              <th className="py-2 text-right">Vent max</th>
              <th className="py-2 text-right">Humidite</th>
            </tr>
          </thead>
          <tbody>
            {forecast.days.map((d, i) => (
              <tr key={i} className="border-b border-[#1e293b]/50 text-slate-300">
                <td className="py-1.5">{d.date}</td>
                <td className="py-1.5 text-right">{dec1(d.temp_max)} C</td>
                <td className="py-1.5 text-right">{dec1(d.temp_min)} C</td>
                <td className="py-1.5 text-right">{dec1(d.precipitation_mm)} mm</td>
                <td className="py-1.5 text-right">{dec1(d.et0_mm)} mm</td>
                <td className="py-1.5 text-right">{dec1(d.sunshine_hours)} h</td>
                <td className="py-1.5 text-right">{dec1(d.wind_speed_max)} km/h</td>
                <td className="py-1.5 text-right">{Math.round(d.humidity_mean)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* History */}
      {history.length > 0 && (
        <>
          <h2 className="text-lg font-semibold text-slate-200">Historique (30 jours)</h2>
          <div className="grid grid-cols-3 gap-3">
            <MetricCard label="Pluie cumulee (30j)" value={`${dec1(histRain)} mm`} />
            <MetricCard label="ET0 cumulee (30j)" value={`${dec1(histET0)} mm`} />
            <MetricCard label="Bilan hydrique" value={`${dec1(histRain - histET0)} mm`} trend={histRain >= histET0 ? 'down' : 'up'} />
          </div>
          <ET0Chart days={history} />
        </>
      )}
    </div>
  );
}
