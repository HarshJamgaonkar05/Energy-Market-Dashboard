import { motion } from "framer-motion";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SourceTag } from "../primitives/SourceTag";
import { Sourced } from "../primitives/Sourced";
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
  const { data, live, stale } = useLive("/api/inventories", FALLBACK, useLive.REFRESH.hourly);
  const padd = data.padd || INV;
  const crude = (data.heroes || []).find((h) => h.sym === "US CRUDE") || FALLBACK.heroes[0];
  const total = crude.val ?? 429.1;
  const dWeek = crude.chg ?? -4.2;
  const hist = data.hist || [];
  // Only compute a "vs average" figure when we actually have history — no magic
  // constant masquerading as a derived stat.
  const vs5y = hist.length
    ? ((hist.at(-1).total - hist.at(-1).avg5y) / hist.at(-1).avg5y) * 100
    : null;
  // Convention (matches InventorySignal / Release Lab): a DRAW (stocks fall) is
  // bullish → green; a BUILD (stocks rise) is bearish → red.
  const flowTone = (chg) => (chg == null ? "text-zinc-400" : chg < 0 ? "text-emerald-400" : chg > 0 ? "text-red-400" : "text-zinc-400");

  return (
    <Card>
      <SectionTitle sub="EIA Weekly · MMbbl" action={<SourceTag live={live} stale={stale} source="eia" note="EIA Weekly Petroleum Status Report — crude stocks by PADD (WCESTP1..5)." />}>US Crude Inventory by PADD</SectionTitle>
      <div className="space-y-1.5">
        {padd.map((p) => {
          const max = 250;
          const w = (p.val / max) * 100;
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
                  <Sourced source="eia" note={`${p.reg} crude stocks · EIA Weekly Petroleum Status Report`} align="start">{fmt(p.val, 1)}</Sourced>
                </span>
              </div>
              <span className={`font-mono text-[10px] w-14 text-right ${flowTone(p.chg)}`}>
                <Sourced source="eia" note="Week-over-week change · EIA · draw (−) is bullish" align="end">{fmtSigned(p.chg, 1)}</Sourced>
              </span>
            </div>
          );
        })}
      </div>
      <div className="grid grid-cols-3 gap-3 mt-3 pt-3 border-t border-[#1c1d22]">
        <div>
          <div className="text-[9px] text-zinc-600 uppercase tracking-wider">Total</div>
          <div className="font-mono text-[13px] text-zinc-100">
            <Sourced source="eia" note="U.S. commercial crude stocks excl. SPR (WCESTUS1) · EIA" align="start">{fmt(total, 1)}</Sourced>
          </div>
        </div>
        <div>
          <div className="text-[9px] text-zinc-600 uppercase tracking-wider">Δ Week</div>
          <div className={`font-mono text-[13px] ${flowTone(dWeek)}`}>
            <Sourced source="eia" note="Week-over-week build/draw · EIA · draw (−) is bullish" align="start">{fmtSigned(dWeek, 1)}</Sourced>
          </div>
        </div>
        <div>
          <div className="text-[9px] text-zinc-600 uppercase tracking-wider">vs avg</div>
          <div className={`font-mono text-[13px] ${vs5y == null ? "text-zinc-500" : vs5y < 0 ? "text-emerald-400" : "text-red-400"}`}>
            <Sourced source="derived" note="Latest crude stocks vs trailing-year average (proxy for the 5-year band) · derived from EIA · below-average (−) is tight/bullish" align="end">{vs5y == null ? "—" : `${fmtSigned(vs5y, 1)}%`}</Sourced>
          </div>
        </div>
      </div>
    </Card>
  );
};
