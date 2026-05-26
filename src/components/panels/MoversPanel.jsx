import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { MOVERS } from "../../data/mock";
import { fmt, fmtSigned } from "../../lib/format";

export const MoversPanel = () => (
  <Card>
    <SectionTitle sub="Last 24h">Market Movers</SectionTitle>
    <div className="-mx-1">
      <div className="grid grid-cols-12 px-2 py-1 text-[9px] text-zinc-600 uppercase tracking-wider border-b border-[#1c1d22]">
        <div className="col-span-4">Symbol</div>
        <div className="col-span-3 text-right">Last</div>
        <div className="col-span-3 text-right">Δ%</div>
        <div className="col-span-2 text-right">Vol</div>
      </div>
      {MOVERS.map((m, i) => (
        <div
          key={i}
          className="grid grid-cols-12 px-2 py-1.5 text-[11px] font-mono border-b border-[#15161a] last:border-0 hover:bg-white/[0.02] cursor-pointer"
        >
          <div className="col-span-4 text-zinc-300 truncate">{m.sym}</div>
          <div className="col-span-3 text-right text-zinc-200">{fmt(m.val, m.val < 10 ? 3 : 2)}</div>
          <div className={`col-span-3 text-right ${m.pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            {fmtSigned(m.pct)}%
          </div>
          <div className="col-span-2 text-right text-zinc-500">{m.vol}</div>
        </div>
      ))}
    </div>
  </Card>
);
