import {
  Line, Area, ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip,
} from "recharts";
import { ResponsiveContainer } from "../lib/ResponsiveContainer";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { SourceTag } from "../components/primitives/SourceTag";
import { AsOf } from "../components/primitives/AsOf";
import { Sourced } from "../components/primitives/Sourced";
import { InventorySnap } from "../components/panels/InventorySnap";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { fmt, fmtSigned } from "../lib/format";
import { INV_HIST, genSpark } from "../data/mock";
import { HeroCard } from "../components/HeroCard";
import { NewsPanel } from "../components/panels/NewsPanel";
import { useLive } from "../lib/useLive";

// EIA Weekly Petroleum Status Report (server/sources/eia.js). Falls back to the
// seeded snapshot when no EIA key is set.
const INV_FALLBACK = {
  heroes: [
    { sym: "US CRUDE", name: "Total Stocks", val: 429.1, chg: -4.2, pct: -0.97 },
    { sym: "CUSHING", name: "Cushing OK", val: 24.6, chg: -1.1, pct: -4.28 },
    { sym: "SPR", name: "Strategic Reserve", val: 369.8, chg: +0.4, pct: +0.11 },
    { sym: "GASOLINE", name: "US Gasoline", val: 247.2, chg: +2.4, pct: +0.98 },
  ],
  hist: INV_HIST,
  refineryUtil: 91.2,
};

export const PageInventories = () => {
  const { data, live } = useLive("/api/inventories", INV_FALLBACK, useLive.REFRESH.hourly);
  const heroes = data.heroes?.length ? data.heroes : INV_FALLBACK.heroes;
  const hist = data.hist?.length ? data.hist : INV_HIST;
  const refUtil = data.refineryUtil ?? 91.2;

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[#1c1d22]">
        {heroes.map((d, i) => (
          <HeroCard key={d.sym} d={{ ...d, unit: "MMbbl", source: "eia", sourceNote: "EIA Weekly Petroleum Status Report (official, weekly).", spark: genSpark(81 + i, 30, d.chg >= 0 ? 1 : -1) }} />
        ))}
      </div>

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-8 space-y-3">
          <Card padding={false}>
            <div className="p-4 pb-2">
              <SectionTitle sub="52W vs 5-yr seasonal range" action={<div className="flex items-center gap-2"><AsOf date={data.asOf} /><SourceTag live={live} source="eia" note="EIA weekly U.S. crude stocks excl. SPR (WCESTUS1). Shaded band is the min–max across the 5 prior years for each week-of-year; dashed line is the 5-yr average." /></div>}>US Crude Stocks</SectionTitle>
              {/* Legend */}
              <div className="mt-2 flex items-center flex-wrap gap-x-4 gap-y-1 text-[9px] uppercase tracking-wider text-zinc-500">
                <span className="flex items-center gap-1.5"><span className="w-3 h-1.5 bg-sky-500/20 border-y border-sky-500/30" /> 5-yr range</span>
                <span className="flex items-center gap-1.5"><span className="w-3 border-t border-dashed border-zinc-500" /> 5-yr avg</span>
                <span className="flex items-center gap-1.5"><span className="w-3 h-[2px] bg-amber-500" /> Current</span>
              </div>
            </div>
            <div className="h-80 px-2 pb-2">
              <ResponsiveContainer>
                <ComposedChart data={hist}>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis dataKey="w" {...chartProps.axis} interval={5} minTickGap={16} />
                  <YAxis {...chartProps.axis} width={40} domain={["auto", "auto"]} />
                  <Tooltip content={<ChartTooltip unit=" MMbbl" source="eia" />} />
                  {/* Seasonal envelope: Recharts fills a [min,max] dataKey as a band. */}
                  <Area type="monotone" dataKey="band" stroke="none" fill="#38bdf8" fillOpacity={0.12} name="5-yr range" isAnimationActive={false} connectNulls />
                  <Line type="monotone" dataKey="avg5y" stroke="#71717a" strokeWidth={1} strokeDasharray="4 3" dot={false} name="5-yr avg" isAnimationActive={false} connectNulls />
                  <Line type="monotone" dataKey="total" stroke="#f59e0b" strokeWidth={1.6} dot={false} name="Current" isAnimationActive={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-3">
            <InventorySnap />
            <Card>
              <SectionTitle sub="US Refinery Utilization" action={<SourceTag live={live} source="eia" note="EIA refinery % utilization of operable capacity (WPULEUS3), weekly." />}>Refining</SectionTitle>
              <div className="text-center py-3">
                <div className="font-mono text-4xl text-amber-400">
                  <Sourced source="eia" note="EIA refinery % utilization of operable capacity (WPULEUS3)">{fmt(refUtil, 1)}%</Sourced>
                </div>
                <div className="text-[10px] text-zinc-500 mt-1 uppercase tracking-wider">Capacity used</div>
              </div>
              <div className="grid grid-cols-2 gap-3 mt-2 pt-3 border-t border-[#1c1d22]">
                <div>
                  <div className="text-[9px] text-zinc-600 uppercase tracking-wider">Source</div>
                  <div className="font-mono text-[12px] text-zinc-300">EIA WPULEUS3</div>
                </div>
                <div>
                  <div className="text-[9px] text-zinc-600 uppercase tracking-wider">Cadence</div>
                  <div className="font-mono text-[12px] text-zinc-300">Weekly</div>
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <span className="text-[9px] text-zinc-600 uppercase tracking-wider">PADD utilization</span>
                <SourceTag modeled label="No source" source="modeled" note="EIA publishes only the national refinery utilization — no free per-PADD breakdown." />
              </div>
              <div className="mt-1.5 space-y-1.5">
                {[
                  { r: "PADD 1", v: 86 },
                  { r: "PADD 2", v: 94 },
                  { r: "PADD 3", v: 92 },
                  { r: "PADD 5", v: 88 },
                ].map((p) => (
                  <div key={p.r} className="flex items-center gap-2">
                    <span className="text-[10px] text-zinc-400 w-12">{p.r}</span>
                    <div className="flex-1 h-1.5 bg-[#15161a]" />
                    <span className="font-mono text-[10px] text-zinc-300 w-8 text-right">
                      <Sourced source="modeled" note="EIA publishes only the national refinery utilization — no free per-PADD breakdown." align="end" />
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4 space-y-3">
          <Card>
            <SectionTitle sub="Storage utilization" action={<SourceTag modeled label="No source" source="modeled" note="Tank-level storage data (Kpler/Vortexa) is paywalled — no free source." />}>Global Crude Storage</SectionTitle>
            {[
              { r: "OECD", v: 84.2, c: -0.4 },
              { r: "China SPR", v: 71.8, c: +0.8 },
              { r: "Cushing", v: 38.4, c: -2.1 },
              { r: "ARA", v: 68.2, c: +1.2 },
              { r: "Saldanha", v: 92.6, c: -0.2 },
              { r: "Floating", v: 0.84, c: +0.12 },
            ].map((s) => (
              <div key={s.r} className="flex items-center gap-2 py-1.5 border-b border-[#15161a] last:border-0">
                <span className="text-[11px] text-zinc-300 flex-1">{s.r}</span>
                <span className="font-mono text-[11px] text-zinc-200 w-12 text-right">
                  <Sourced source="modeled" note="Commercial tank-level data (Kpler/Vortexa) is paywalled — no free source." align="end" />
                </span>
              </div>
            ))}
          </Card>
          <NewsPanel compact />
        </div>
      </div>
    </div>
  );
};
