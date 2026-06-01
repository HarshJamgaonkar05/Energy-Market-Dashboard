import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SourceTag } from "../primitives/SourceTag";
import { Sourced } from "../primitives/Sourced";
import { MOVERS } from "../../data/mock";
import { fmt, fmtSigned } from "../../lib/format";
import { useLive } from "../../lib/useLive";

// Live movers — instruments ranked by absolute daily move (Yahoo Finance).
export const MoversPanel = () => {
  const { data: movers, live } = useLive("/api/movers", MOVERS);
  return (
    <Card>
      <SectionTitle sub="Last 24h" action={<SourceTag live={live} source="yahoo" />}>Market Movers</SectionTitle>
      <div className="-mx-1">
        <div className="grid grid-cols-12 px-2 py-1 text-[9px] text-zinc-600 uppercase tracking-wider border-b border-[#1c1d22]">
          <div className="col-span-4">Symbol</div>
          <div className="col-span-3 text-right">Last</div>
          <div className="col-span-3 text-right">Δ%</div>
          <div className="col-span-2 text-right">Vol</div>
        </div>
        {movers.map((m, i) => {
          const spread = /CRACK|CRK|-/.test(m.sym);
          const src = spread ? "derived" : "yahoo";
          const note = spread ? "Derived spread — computed from live Yahoo Finance quotes" : undefined;
          return (
            <div
              key={i}
              className="grid grid-cols-12 px-2 py-1.5 text-[11px] font-mono border-b border-[#15161a] last:border-0 hover:bg-white/[0.02] cursor-pointer"
            >
              <div className="col-span-4 text-zinc-300 truncate">{m.sym}</div>
              <div className="col-span-3 text-right text-zinc-200">
                <Sourced source={src} note={note} align="end">{fmt(m.val, m.val < 10 ? 3 : 2)}</Sourced>
              </div>
              <div className={`col-span-3 text-right ${m.pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                <Sourced source={src} note={note} align="end">{fmtSigned(m.pct)}%</Sourced>
              </div>
              <div className="col-span-2 text-right text-zinc-500">{m.vol}</div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
