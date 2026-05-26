import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { Warehouse } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { Badge } from "../components/primitives/Badge";
import { Delta } from "../components/primitives/Delta";
import { InventorySnap } from "../components/panels/InventorySnap";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { fmt, fmtSigned } from "../lib/format";
import { HERO, INV, INV_HIST, genSpark } from "../data/mock";
import { HeroCard } from "../components/HeroCard";
import { NewsPanel } from "../components/panels/NewsPanel";

export const PageInventories = () => (
  <div className="space-y-3">
    <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[#1c1d22]">
      {[
        { sym: "US CRUDE", name: "Total Stocks", val: 429.1, chg: -4.2, pct: -0.97, spark: genSpark(81, 30, -1), unit: "MMbbl" },
        { sym: "CUSHING", name: "Cushing OK", val: 24.6, chg: -1.1, pct: -4.28, spark: genSpark(82, 30, -1), unit: "MMbbl" },
        { sym: "SPR", name: "Strategic Reserve", val: 369.8, chg: +0.4, pct: +0.11, spark: genSpark(83, 30, 1), unit: "MMbbl" },
        { sym: "GASOLINE", name: "US Gasoline", val: 247.2, chg: +2.4, pct: +0.98, spark: genSpark(84, 30, 1), unit: "MMbbl" },
      ].map((d) => <HeroCard key={d.sym} d={d} />)}
    </div>

    <div className="grid grid-cols-12 gap-3">
      <div className="col-span-12 lg:col-span-8 space-y-3">
        <Card padding={false}>
          <div className="p-4 pb-2">
            <SectionTitle sub="52W vs 5Y average">US Crude Stocks</SectionTitle>
          </div>
          <div className="h-80 px-2 pb-2">
            <ResponsiveContainer>
              <ComposedChart data={INV_HIST}>
                <CartesianGrid {...chartProps.grid} />
                <XAxis dataKey="w" {...chartProps.axis} />
                <YAxis {...chartProps.axis} width={40} domain={["auto", "auto"]} />
                <Tooltip content={<ChartTooltip unit=" MMbbl" />} />
                <Area type="monotone" dataKey="avg5y" stroke="#3a3b41" strokeWidth={1} fill="#1c1d22" fillOpacity={0.4} name="5Y Avg" isAnimationActive={false} />
                <Line type="monotone" dataKey="total" stroke="#f59e0b" strokeWidth={1.6} dot={false} name="Current" isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <div className="grid grid-cols-2 gap-3">
          <InventorySnap />
          <Card>
            <SectionTitle sub="US Refinery Utilization">Refining</SectionTitle>
            <div className="text-center py-3">
              <div className="font-mono text-4xl text-amber-400">91.2%</div>
              <div className="text-[10px] text-zinc-500 mt-1 uppercase tracking-wider">Capacity used</div>
            </div>
            <div className="grid grid-cols-2 gap-3 mt-2 pt-3 border-t border-[#1c1d22]">
              <div>
                <div className="text-[9px] text-zinc-600 uppercase tracking-wider">Δ Week</div>
                <div className="font-mono text-[12px] text-emerald-400">+1.4 pp</div>
              </div>
              <div>
                <div className="text-[9px] text-zinc-600 uppercase tracking-wider">vs 5Y</div>
                <div className="font-mono text-[12px] text-emerald-400">+2.1 pp</div>
              </div>
            </div>
            <div className="mt-3 space-y-1.5">
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
          <SectionTitle sub="Storage utilization">Global Crude Storage</SectionTitle>
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
