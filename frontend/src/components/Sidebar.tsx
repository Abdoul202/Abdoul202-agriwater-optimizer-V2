import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Sliders, Cloud, Settings, Droplets } from 'lucide-react';

const links = [
  { to: '/', label: 'Tableau de bord', icon: LayoutDashboard },
  { to: '/optimizer', label: 'Optimisation', icon: Sliders },
  { to: '/weather', label: 'Meteo', icon: Cloud },
  { to: '/config', label: 'Configuration', icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="w-60 min-h-screen bg-[#111827] border-r border-[#1e293b] flex flex-col fixed left-0 top-0">
      <div className="px-5 py-6 border-b border-[#1e293b]">
        <div className="flex items-center gap-2">
          <Droplets className="w-6 h-6 text-emerald-400" />
          <span className="text-lg font-bold text-slate-100">AgriWater</span>
        </div>
        <p className="text-[10px] text-slate-500 mt-1">Optimisation irrigation Sahel</p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-emerald-500/10 text-emerald-400'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-[#1a2332]'
              }`
            }
          >
            <Icon className="w-4 h-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-5 py-4 border-t border-[#1e293b]">
        <p className="text-[10px] text-slate-600">AgriWater Dashboard v0.2</p>
        <p className="text-[10px] text-slate-600">OUEDRAOGO Abdoulaye</p>
      </div>
    </aside>
  );
}
