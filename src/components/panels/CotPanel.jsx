import { useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SourceTag } from "../primitives/SourceTag";
import { Sourced } from "../primitives/Sourced";
import { chartProps, ChartTooltip } from "../../lib/chart-theme";
import { useLive } from "../../lib/useLive";

// CFTC Commitments of Traders — Managed Money (speculative funds) net
// positioning. Net = long − short contracts; the percentile places today's net
// inside its own ~3-year range (extremes = crowded positioning, a contrarian
// flag). See server/sources/cftc.js.
const COT_FALLBACK = {
  asOf: "—",
  markets: [
    { id: "WTI", name: "WTI Crude", net: 79924, netChg: -18295, pctile: 35, longShare: 62, netPctOi: 4.0, commNet: -52000, extreme: null, hist: [] },
    { id: "BRENT", name: "Brent Crude", net: 9568, netChg: -3362, pctile: 56, longShare: 75, netPctOi: null, commNet: -12000, extreme: null, hist: [] },
    { id: "RBOB", name: "RBOB Gasoline", net: 67062, netChg: 5388, pctile: 66, longShare: 94, netPctOi: null, commNet: -70000, extreme: null, hist: [] },
    { id: "HO", name: "ULSD / Heating Oil", net: 7689, netChg: -3334, pctile: 61, longShare: 59, netPctOi: null, commNet: -9000, extreme: null, hist: [] },
  ],
};

const fmtK = (n) => (n == null ? "—" : Math.abs(n) >= 1000 ? `${(n / 1000).toFixed(0)}k` : `${Math.round(n)}`);
const signedK = (n) => (n == null ? "—" : `${n >= 0 ? "+" : "−"}${fmtK(Math.abs(n))}`);

// Small 0–100 percentile track with a marker at the current value.
const Pctile = ({ v }) => (
  <div className="relative h-1.5 w-full bg-[#15161a]">
    <div className="absolute inset-y-0 left-0 bg-amber-500/20" style={{ width: `${v}%` }} />
    <div className="absolute inset-y-[-1px] w-px bg-amber-400" style={{ left: `${v}%` }} />
  </div>
);

export const CotPanel = ({ title = "Speculative Positioning" }) => {
  const { data, live } = useLive("/api/cot", COT_FALLBACK, useLive.REFRESH.slow);
  const markets = data.markets?.length ? data.markets : COT_FALLBACK.markets;
  const [id, setId] = useState("WTI");
  const m = markets.find((x) => x.id === id) || markets[0];
  const net = m.net;

  return (
    <Card padding={false}>
      <div className="p-4 pb-2 flex items-center justify-between flex-wrap gap-2">
        <SectionTitle sub={`Managed money · net = long − short · as of ${data.asOf || "—"}`} action={<SourceTag live={live} source="cftc" note="CFTC Commitments of Traders (Disaggregated). Managed Money = speculative funds. Weekly, as of each Tuesday." />}>{title}</SectionTitle>
      </div>

      <div className="grid grid-cols-12">
        {/* Market list with net + 3y percentile */}
        <div className="col-span-12 md:col-span-5 border-b md:border-b-0 md:border-r border-[#1c1d22]">
          {markets.map((x) => {
            const sel = x.id === id;
            return (
              <button
                key={x.id}
                onClick={() => setId(x.id)}
                className={`w-full px-3 py-2 border-l-2 text-left transition-colors ${
                  sel ? "border-amber-500 bg-amber-500/[0.06]" : "border-transparent hover:bg-white/[0.02]"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-[11px] ${sel ? "text-zinc-100" : "text-zinc-300"}`}>{x.name}</span>
                  <span className={`font-mono text-[11px] ${x.net >= 0 ? "text-emerald-400" : "text-red-400"}`}>{signedK(x.net)}</span>
                </div>
                <div className="mt-1.5 flex items-center gap-2">
                  <Pctile v={x.pctile} />
                  <span className="font-mono text-[9px] text-zinc-500 w-7 text-right">{x.pctile}%</span>
                </div>
                {x.extreme && (
                  <div className={`mt-1 text-[9px] uppercase tracking-wider ${x.pctile >= 85 ? "text-red-400" : "text-emerald-400"}`}>{x.extreme}</div>
                )}
              </button>
            );
          })}
        </div>

        {/* Selected market: net history + stats */}
        <div className="col-span-12 md:col-span-7 p-4">
          <div className="flex items-start justify-between mb-2">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-zinc-500">{m.name} · MM Net</div>
              <div className="flex items-baseline gap-2">
                <span className={`font-mono text-2xl ${net >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  <Sourced source="cftc" note="Managed Money net = long − short contracts (CFTC weekly)" align="start">{signedK(net)}</Sourced>
                </span>
                <span className={`font-mono text-[11px] ${m.netChg >= 0 ? "text-emerald-400" : "text-red-400"}`}>{signedK(m.netChg)} w/w</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-[9px] uppercase tracking-wider text-zinc-600">3y percentile</div>
              <div className={`font-mono text-lg ${m.pctile >= 85 ? "text-red-400" : m.pctile <= 15 ? "text-emerald-400" : "text-zinc-200"}`}>{m.pctile}%</div>
            </div>
          </div>

          <div className="h-40">
            <ResponsiveContainer>
              <AreaChart data={m.hist} margin={{ top: 6, right: 8, bottom: 0, left: 0 }}>
                <defs>
                  <linearGradient id="cotFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.28} />
                    <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid {...chartProps.grid} />
                <XAxis dataKey="d" {...chartProps.axis} interval={16} minTickGap={20} />
                <YAxis {...chartProps.axis} width={42} tickFormatter={fmtK} domain={["auto", "auto"]} />
                <Tooltip content={<ChartTooltip source="cftc" />} />
                <ReferenceLine y={0} stroke="#3a3b41" />
                <Area type="monotone" dataKey="net" name="MM net" stroke="#f59e0b" strokeWidth={1.5} fill="url(#cotFill)" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-3 gap-3 mt-3 pt-3 border-t border-[#1c1d22]">
            {[
              { l: "Long share", v: m.longShare != null ? `${m.longShare}%` : "—", note: "Managed-money longs as a share of MM long+short" },
              { l: "Net % OI", v: m.netPctOi != null ? `${m.netPctOi}%` : "—", note: "Net position as a share of total open interest" },
              { l: "Commercials", v: signedK(m.commNet), note: "Producer/Merchant (hedger) net — typically opposite the funds" },
            ].map((s) => (
              <div key={s.l}>
                <div className="text-[9px] text-zinc-600 uppercase tracking-wider">{s.l}</div>
                <div className="font-mono text-[13px] text-zinc-200">
                  <Sourced source="cftc" note={s.note} align="start">{s.v}</Sourced>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
};
