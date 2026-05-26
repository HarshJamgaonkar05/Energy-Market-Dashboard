import { motion } from "framer-motion";
import { AreaChart, Area, ResponsiveContainer } from "recharts";
import { Circle } from "lucide-react";
import { Delta } from "./primitives/Delta";
import { fmt } from "../lib/format";

export const HeroCard = ({ d }) => {
  const up = d.chg >= 0;
  return (
    <motion.div
      whileHover={{ y: -1 }}
      className="relative bg-[#0e0f12] border border-[#1c1d22] p-3 hover:border-[#2a2b31] transition-colors cursor-pointer group overflow-hidden"
    >
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-bold tracking-wider text-zinc-400">{d.sym}</span>
          {up ? (
            <Circle size={5} fill="#10b981" className="text-emerald-500 animate-pulse" />
          ) : (
            <Circle size={5} fill="#ef4444" className="text-red-500 animate-pulse" />
          )}
        </div>
        <span className="text-[9px] text-zinc-600 uppercase tracking-wider">{d.unit}</span>
      </div>
      <div className="text-[10px] text-zinc-500 mb-2 truncate">{d.name}</div>
      <div className="flex items-end justify-between gap-2">
        <div>
          <div className="font-mono text-xl font-medium tracking-tight text-zinc-100">
            {fmt(d.val, d.val < 10 ? 3 : 2)}
          </div>
          <div className="mt-1">
            <Delta v={d.chg} pct={d.pct} />
          </div>
        </div>
        <div className="w-20 h-10 -mb-1">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={d.spark}>
              <defs>
                <linearGradient id={`g-${d.sym}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={up ? "#10b981" : "#ef4444"} stopOpacity={0.5} />
                  <stop offset="100%" stopColor={up ? "#10b981" : "#ef4444"} stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area
                type="monotone"
                dataKey="y"
                stroke={up ? "#10b981" : "#ef4444"}
                strokeWidth={1.2}
                fill={`url(#g-${d.sym})`}
                dot={false}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className={`absolute inset-x-0 bottom-0 h-px ${up ? "bg-emerald-500/40" : "bg-red-500/40"}`} />
    </motion.div>
  );
};
