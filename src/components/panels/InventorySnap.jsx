import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { motion } from "framer-motion";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { INV, INV_HIST } from "../../data/mock";
import { chartProps, ChartTooltip } from "../../lib/chart-theme";
import { fmt, fmtSigned } from "../../lib/format";

export const InventorySnap = () => (
  <Card>
    <SectionTitle sub="EIA Weekly · MMbbl">US Crude Inventory by PADD</SectionTitle>
    <div className="space-y-1.5">
      {INV.map((p) => {
        const max = 250;
        const w = (p.val / max) * 100;
        const up = p.chg >= 0;
        return (
          <div key={p.reg} className="flex items-center gap-2">
            <span className="text-[10px] text-zinc-400 w-14 font-mono">{p.reg}</span>
            <div className="flex-1 h-4 bg-[#15161a] relative">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${w}%` }}
                transition={{ duration: 0.6 }}
                className="absolute inset-y-0 left-0 bg-gradient-to-r from-amber-600/60 to-amber-500/40"
              />
              <span className="absolute inset-0 flex items-center px-1.5 text-[9px] font-mono text-zinc-100">
                {fmt(p.val, 1)}
              </span>
            </div>
            <span className={`font-mono text-[10px] w-14 text-right ${up ? "text-emerald-400" : "text-red-400"}`}>
              {fmtSigned(p.chg, 1)}
            </span>
          </div>
        );
      })}
    </div>
    <div className="grid grid-cols-3 gap-3 mt-3 pt-3 border-t border-[#1c1d22]">
      <div>
        <div className="text-[9px] text-zinc-600 uppercase tracking-wider">Total</div>
        <div className="font-mono text-[13px] text-zinc-100">429.1</div>
      </div>
      <div>
        <div className="text-[9px] text-zinc-600 uppercase tracking-wider">Δ Week</div>
        <div className="font-mono text-[13px] text-red-400">-4.2</div>
      </div>
      <div>
        <div className="text-[9px] text-zinc-600 uppercase tracking-wider">vs 5Y</div>
        <div className="font-mono text-[13px] text-emerald-400">+2.8%</div>
      </div>
    </div>
  </Card>
);
