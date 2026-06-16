import { motion } from "framer-motion";
import {
  LayoutDashboard, LineChart as LineIcon, Gauge, Globe2, Warehouse, Newspaper,
  ChevronLeft, ChevronRight, Circle, Zap,
} from "lucide-react";

export const NAV = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "analytics", label: "Analytics", icon: LineIcon },
  { id: "regime", label: "Regime & Signals", icon: Gauge },
  { id: "drivers", label: "Market Drivers", icon: Globe2 },
  { id: "inventories", label: "Inventories", icon: Warehouse },
  { id: "news", label: "News", icon: Newspaper },
];

export const Sidebar = ({ active, setActive, collapsed, setCollapsed }) => (
  <motion.aside
    animate={{ width: collapsed ? 56 : 208 }}
    transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
    className="bg-[#0a0b0e] border-r border-[#1c1d22] flex flex-col flex-shrink-0"
  >
    {/* Logo */}
    <div className="h-14 border-b border-[#1c1d22] flex items-center px-3 gap-2">
      <div className="w-7 h-7 bg-amber-500 flex items-center justify-center flex-shrink-0">
        <Zap size={16} className="text-zinc-950" strokeWidth={2.5} />
      </div>
      {!collapsed && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex-1 min-w-0">
          <div className="text-[12px] font-bold tracking-tight text-zinc-100">VOLTAIRE</div>
          <div className="text-[8px] text-zinc-500 tracking-[0.2em] uppercase">Terminal v4.7</div>
        </motion.div>
      )}
    </div>

    {/* Nav */}
    <nav className="flex-1 py-2 overflow-y-auto">
      {NAV.map((item) => {
        const Icon = item.icon;
        const isActive = active === item.id;
        return (
          <button
            key={item.id}
            onClick={() => setActive(item.id)}
            className={`w-full flex items-center gap-3 px-3 h-9 text-[12px] transition-all relative group ${
              isActive
                ? "text-amber-400 bg-amber-500/[0.04]"
                : "text-zinc-500 hover:text-zinc-200 hover:bg-white/[0.02]"
            }`}
          >
            {isActive && <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-amber-500" />}
            <Icon size={15} strokeWidth={1.75} className="flex-shrink-0" />
            {!collapsed && (
              <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="truncate font-medium">
                {item.label}
              </motion.span>
            )}
            {collapsed && (
              <div className="absolute left-full ml-2 px-2 py-1 bg-[#0a0b0e] border border-[#2a2b31] text-[11px] text-zinc-200 opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity">
                {item.label}
              </div>
            )}
          </button>
        );
      })}
    </nav>

    {/* Status footer */}
    <div className="border-t border-[#1c1d22] p-2">
      {!collapsed ? (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-zinc-600 uppercase tracking-wider">Feed</span>
            <span className="flex items-center gap-1 text-emerald-400">
              <Circle size={6} fill="#10b981" className="animate-pulse" />
              Live
            </span>
          </div>
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-zinc-600 uppercase tracking-wider">Latency</span>
            <span className="font-mono text-zinc-300">12ms</span>
          </div>
        </div>
      ) : (
        <div className="flex justify-center">
          <Circle size={6} fill="#10b981" className="text-emerald-500 animate-pulse" />
        </div>
      )}
    </div>

    {/* Collapse toggle */}
    <button
      onClick={() => setCollapsed(!collapsed)}
      className="border-t border-[#1c1d22] h-8 flex items-center justify-center text-zinc-500 hover:text-zinc-200 hover:bg-white/[0.02] transition-colors"
    >
      {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
    </button>
  </motion.aside>
);

