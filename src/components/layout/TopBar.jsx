import { useState, useEffect } from "react";
import {
  Search, Bell, User, Circle, ChevronDown, Wifi, Globe, Star,
} from "lucide-react";

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

      {/* Search */}
      <div className="flex-1 max-w-md ml-4 relative">
        <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-600" />
        <input
          placeholder="Search instruments, news, regions  ⌘K"
          className="w-full bg-[#0e0f12] border border-[#1c1d22] focus:border-[#2a2b31] outline-none pl-8 pr-3 h-8 text-[12px] text-zinc-200 placeholder-zinc-600"
        />
      </div>

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
        <div className="flex items-center gap-1.5">
          <Circle size={6} fill="#6b7280" />
          <span className="text-zinc-400">TOCOM</span>
          <span className="text-zinc-500 font-mono">CLOSED</span>
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

      {/* Notifications */}
      <button className="relative w-8 h-8 flex items-center justify-center border border-[#1c1d22] hover:border-[#2a2b31] text-zinc-400 hover:text-zinc-200 transition-colors">
        <Bell size={13} />
        <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-amber-500 rounded-full" />
      </button>

      {/* Profile */}
      <div className="flex items-center gap-2 pl-3 border-l border-[#1c1d22]">
        <div className="w-7 h-7 bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center text-[10px] font-bold text-zinc-950">
          KM
        </div>
        <div className="hidden xl:block">
          <div className="text-[11px] text-zinc-200 font-medium leading-tight">K. Mehra</div>
          <div className="text-[9px] text-zinc-500 leading-tight">Energy Desk</div>
        </div>
      </div>
    </header>
  );
};

