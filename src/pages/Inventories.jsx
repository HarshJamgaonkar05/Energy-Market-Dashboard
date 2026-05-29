import {
  Line, Area, ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { SourceTag } from "../components/primitives/SourceTag";
import { Delta } from "../components/primitives/Delta";
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
          <HeroCard key={d.sym} d={{ ...d, unit: "MMbbl", spark: genSpark(81 + i, 30, d.chg >= 0 ? 1 : -1) }} />
        ))}
      </div>

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-8 space-y-3">
          <Card padding={false}>
            <div className="p-4 pb-2">
              <SectionTitle sub="52W vs trailing avg" action={<SourceTag live={live} />}>US Crude Stocks</SectionTitle>
            </div>
            <div className="h-80 px-2 pb-2">
              <ResponsiveContainer>
                <ComposedChart data={hist}>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis dataKey="w" {...chartProps.axis} />
                  <YAxis {...chartProps.axis} width={40} domain={["auto", "auto"]} />
                  <Tooltip content={<ChartTooltip unit=" MMbbl" />} />
                  <Area type="monotone" dataKey="avg5y" stroke="#3a3b41" strokeWidth={1} fill="#1c1d22" fillOpacity={0.4} name="Avg" isAnimationActive={false} />
                  <Line type="monotone" dataKey="total" stroke="#f59e0b" strokeWidth={1.6} dot={false} name="Current" isAnimationActive={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-3">
            <InventorySnap />
            <Card>
              <SectionTitle sub="US Refinery Utilization" action={<SourceTag live={live} />}>Refining</SectionTitle>
              <div className="text-center py-3">
                <div className="font-mono text-4xl text-amber-400">{fmt(refUtil, 1)}%</div>
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
                <SourceTag modeled label="Illustrative" />
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
                    <div className="flex-1 h-1.5 bg-[#15161a]">
                      <div className="h-full bg-amber-500/70" style={{ width: `${p.v}%` }} />
                    </div>
                    <span className="font-mono text-[10px] text-zinc-300 w-8 text-right">{p.v}%</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4 space-y-3">
          <Card>
            <SectionTitle sub="Storage utilization" action={<SourceTag modeled label="Indicative" />}>Global Crude Storage</SectionTitle>
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
                <span className="font-mono text-[11px] text-zinc-200 w-12 text-right">{s.v}%</span>
                <Delta v={s.c} pct={s.c} />
              </div>
            ))}
          </Card>
          <NewsPanel compact />
        </div>
      </div>
    </div>
  );
};
