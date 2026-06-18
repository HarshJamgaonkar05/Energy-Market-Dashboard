import { useState, useEffect } from "react";
import { Globe } from "lucide-react";
import { AlertBell } from "../alerts/AlertBell";

export const TopBar = ({ pageTitle }) => {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const utc = time.toISOString().replace("T", " ").slice(0, 19);
  const ist = time.toLocaleTimeString("en-GB", { timeZone: "Asia/Kolkata", hour12: false });

  return (
    <header className="no-print h-14 bg-[#0a0b0e] border-b border-[#1c1d22] flex items-center px-4 gap-4 flex-shrink-0">
      <div className="flex items-baseline gap-2 min-w-0">
        <h1 className="text-[13px] font-semibold text-zinc-100 capitalize whitespace-nowrap">{pageTitle}</h1>
      </div>

      <div className="flex-1" />

      {/* Clocks — UTC and IST */}
      <div className="flex items-center gap-3 font-mono text-[11px] text-zinc-400 tabular-nums">
        <div className="flex items-center gap-1.5">
          <Globe size={11} className="text-zinc-500" />
          {utc} <span className="text-zinc-600">UTC</span>
        </div>
        <div className="hidden md:flex items-center gap-1.5">
          {ist} <span className="text-zinc-600">IST</span>
        </div>
      </div>

      {/* Alerts */}
      <div className="pl-3 border-l border-[#1c1d22]">
        <AlertBell />
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
