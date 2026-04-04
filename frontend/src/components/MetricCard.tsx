import type { ReactNode } from 'react';

interface Props {
  label: string;
  value: string;
  sub?: string;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
}

export default function MetricCard({ label, value, sub, icon, trend }: Props) {
  const trendColor =
    trend === 'down' ? 'text-emerald-400' :
    trend === 'up' ? 'text-red-400' : 'text-slate-400';

  return (
    <div className="rounded-xl bg-[#111827] border border-[#1e293b] p-4 flex flex-col gap-1 hover:border-[#334155] transition-colors">
      <div className="flex items-center justify-between">
        <span className="text-xs text-slate-400 uppercase tracking-wide">{label}</span>
        {icon && <span className="text-slate-500">{icon}</span>}
      </div>
      <span className="text-2xl font-semibold text-slate-100">{value}</span>
      {sub && <span className={`text-xs ${trendColor}`}>{sub}</span>}
    </div>
  );
}
