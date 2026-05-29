import { useState, useEffect } from "react";
import { Circle, ChevronDown, Globe, Star } from "lucide-react";

export const TopBar = ({ pageTitle }) => {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const utc = time.toISOString().replace("T", " ").slice(0, 19);

  return (
    <header className="h-14 bg-[#0a0b0e] border-b border-[#1c1d22] flex items-center px-4 gap-4 flex-shrink-0">
      <div className="flex items-baseline gap-2 min-w-0">
        <h1 className="text-[13px] font-semibold text-zinc-100 capitalize whitespace-nowrap">{pageTitle}</h1>
        <span className="text-[10px] text-zinc-600 tracking-wider uppercase hidden md:inline">/ Markets / Live</span>
      </div>

      <div className="flex-1" />

      {/* Market status */}
      <div className="hidden lg:flex items-center gap-3 text-[10px] uppercase tracking-wider">
        <div className="flex items-center gap-1.5">
          <Circle size={6} fill="#10b981" className="animate-pulse" />
          <span className="text-zinc-400">NYMEX</span>
          <span className="text-emerald-400 font-mono">OPEN</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Circle size={6} fill="#10b981" className="animate-pulse" />
          <span className="text-zinc-400">ICE</span>
          <span className="text-emerald-400 font-mono">OPEN</span>
        </div>
      </div>

      {/* Watchlist */}
      <button className="hidden md:flex items-center gap-1.5 h-8 px-2.5 bg-[#0e0f12] border border-[#1c1d22] hover:border-[#2a2b31] text-[11px] text-zinc-300 transition-colors">
        <Star size={11} className="text-amber-400" />
        Default
        <ChevronDown size={11} />
      </button>

      {/* UTC clock */}
      <div className="flex items-center gap-1.5 font-mono text-[11px] text-zinc-400 tabular-nums">
        <Globe size={11} className="text-zinc-500" />
        {utc} <span className="text-zinc-600">UTC</span>
      </div>

      {/* Profile */}
      <div className="flex items-center gap-2 pl-3 border-l border-[#1c1d22]">
        <div className="w-7 h-7 bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center text-[11px] font-bold text-zinc-950">
          J
        </div>
        <div className="hidden xl:block">
          <div className="text-[11px] text-zinc-200 font-medium leading-tight">Jammy</div>
          <div className="text-[9px] text-zinc-500 leading-tight">Energy Desk</div>
        </div>
      </div>
    </header>
  );
};
