import { motion } from "framer-motion";
import { AreaChart, Area } from "recharts";
import { ResponsiveContainer } from "../lib/ResponsiveContainer";
import { Circle, BellPlus } from "lucide-react";
import { Delta } from "./primitives/Delta";
import { Sourced } from "./primitives/Sourced";
import { sourceOf } from "../lib/sources";
import { useAlerts } from "../lib/alerts";
import { fmt } from "../lib/format";

export const HeroCard = ({ d }) => {
  const up = d.chg >= 0;
  const gid = `g-${d.sym.replace(/[^a-zA-Z0-9]/g, "")}`;
  // Quick-add a price alert straight from the tile (only where an alertable
  // metric exists for this instrument — i.e. the energy futures, not macro tiles).
  const alerts = useAlerts();
  const alertMetricId = `px:${d.sym}`;
  const canAlert = !!alerts?.metricMap?.[alertMetricId];
  // Each tile carries its provenance: explicit `d.source`, else modeled tiles
  // fall back to "modeled" and everything else to the live Yahoo quote.
  const source = d.source || (d.modeled ? "modeled" : "yahoo");
  // "modeled" = no free/open source → we show "—" (and no fabricated sparkline)
  // instead of an assumed value.
  const unavailable = sourceOf(source).kind === "modeled";

  return (
    <motion.div
      whileHover={{ y: -1 }}
      className="relative bg-[#0e0f12] border border-[#1c1d22] p-3 hover:border-[#2a2b31] transition-colors cursor-pointer group overflow-hidden"
    >
      {canAlert && (
        <button
          onClick={(e) => { e.stopPropagation(); alerts.openComposer(alertMetricId); }}
          aria-label={`Set a price alert for ${d.sym}`}
          title="Set price alert"
          className="absolute bottom-1.5 right-1.5 z-10 w-5 h-5 flex items-center justify-center bg-[#0a0b0e]/90 border border-[#2a2b31] text-zinc-400 opacity-0 group-hover:opacity-100 hover:text-amber-400 hover:border-amber-500/40 transition-all"
        >
          <BellPlus size={11} />
        </button>
      )}
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-bold tracking-wider text-zinc-400">{d.sym}</span>
          {unavailable ? (
            <Circle size={5} fill="#52525b" className="text-zinc-600" />
          ) : up ? (
            <Circle size={5} fill="#10b981" className="text-emerald-500 animate-pulse" />
          ) : (
            <Circle size={5} fill="#ef4444" className="text-red-500 animate-pulse" />
          )}
        </div>
        <span className="text-[9px] text-zinc-600 uppercase tracking-wider flex items-center gap-1">
          {d.modeled && <span className="text-amber-500/70" title="No free live feed for this value">~</span>}
          {d.unit}
        </span>
      </div>
      <div className="text-[10px] text-zinc-500 mb-2 truncate">{d.name}</div>
      <div className="flex items-end justify-between gap-2">
        {unavailable ? (
          <Sourced source={source} note={d.sourceNote} align="start" className="font-mono text-xl" />
        ) : (
          <>
            <Sourced source={source} note={d.sourceNote} align="start">
              <div>
                <div className="font-mono text-xl font-medium tracking-tight text-zinc-100">
                  {fmt(d.val, d.val < 10 ? 3 : 2)}
                </div>
                <div className="mt-1">
                  <Delta v={d.chg} pct={d.pct} />
                </div>
              </div>
            </Sourced>
            <div className="w-20 h-10 -mb-1">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={d.spark}>
                  <defs>
                    <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={up ? "#10b981" : "#ef4444"} stopOpacity={0.5} />
                      <stop offset="100%" stopColor={up ? "#10b981" : "#ef4444"} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area
                    type="monotone"
                    dataKey="y"
                    stroke={up ? "#10b981" : "#ef4444"}
                    strokeWidth={1.2}
                    fill={`url(#${gid})`}
                    dot={false}
                    isAnimationActive={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </div>
      {!unavailable && (
        <div className={`absolute inset-x-0 bottom-0 h-px ${up ? "bg-emerald-500/40" : "bg-red-500/40"}`} />
      )}
    </motion.div>
  );
};
