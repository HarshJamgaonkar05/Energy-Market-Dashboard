import { motion } from "framer-motion";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SourceTag } from "../primitives/SourceTag";
import { INV } from "../../data/mock";
import { fmt, fmtSigned } from "../../lib/format";
import { useLive } from "../../lib/useLive";

// US crude stocks by PADD region — EIA Weekly Petroleum Status Report.
// Falls back to seeded data when no EIA key is configured.
const FALLBACK = {
  padd: INV,
  heroes: [{ sym: "US CRUDE", val: 429.1, chg: -4.2 }],
  hist: [],
};

export const InventorySnap = () => {
  const { data, live } = useLive("/api/inventories", FALLBACK, useLive.REFRESH.hourly);
  const padd = data.padd || INV;
  const crude = (data.heroes || []).find((h) => h.sym === "US CRUDE") || FALLBACK.heroes[0];
  const total = crude.val ?? 429.1;
  const dWeek = crude.chg ?? -4.2;
  const hist = data.hist || [];
  const vs5y = hist.length
    ? ((hist.at(-1).total - hist.at(-1).avg5y) / hist.at(-1).avg5y) * 100
    : 2.8;

  return (
    <Card>
      <SectionTitle sub="EIA Weekly · MMbbl" action={<SourceTag live={live} />}>US Crude Inventory by PADD</SectionTitle>
      <div className="space-y-1.5">
        {padd.map((p) => {
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
          <div className="font-mono text-[13px] text-zinc-100">{fmt(total, 1)}</div>
        </div>
        <div>
          <div className="text-[9px] text-zinc-600 uppercase tracking-wider">Δ Week</div>
          <div className={`font-mono text-[13px] ${dWeek >= 0 ? "text-emerald-400" : "text-red-400"}`}>{fmtSigned(dWeek, 1)}</div>
        </div>
        <div>
          <div className="text-[9px] text-zinc-600 uppercase tracking-wider">vs 5Y</div>
          <div className={`font-mono text-[13px] ${vs5y >= 0 ? "text-emerald-400" : "text-red-400"}`}>{fmtSigned(vs5y, 1)}%</div>
        </div>
      </div>
    </Card>
  );
};
