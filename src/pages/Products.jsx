import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { Badge } from "../components/primitives/Badge";
import { Delta } from "../components/primitives/Delta";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { HERO, genSeries, genSpark } from "../data/mock";
import { HeroCard } from "../components/HeroCard";
import { MoversPanel } from "../components/panels/MoversPanel";
import { NewsPanel } from "../components/panels/NewsPanel";

export const PageProducts = () => (
  <div className="space-y-3">
    <div className="grid grid-cols-2 md:grid-cols-5 gap-px bg-[#1c1d22]">
      {[
        { sym: "GASOIL", name: "ICE Gasoil", val: 742.5, chg: +18.4, pct: +2.54, spark: genSpark(91, 30, 1), unit: "$/t" },
        { sym: "RBOB", name: "NYMEX Gasoline", val: 2.342, chg: +0.041, pct: +1.78, spark: genSpark(92, 30, 1), unit: "$/gal" },
        { sym: "HEATING", name: "Heating Oil", val: 2.512, chg: -0.018, pct: -0.71, spark: genSpark(93, 30, -1), unit: "$/gal" },
        { sym: "JET", name: "Jet/Kero CIF", val: 84.2, chg: +1.42, pct: +1.72, spark: genSpark(94, 30, 1), unit: "$/bbl" },
        { sym: "HSFO", name: "3.5% Fuel Oil", val: 489.2, chg: +4.1, pct: +0.84, spark: genSpark(95, 30, 1), unit: "$/t" },
      ].map((d) => <HeroCard key={d.sym} d={d} />)}
    </div>

    <div className="grid grid-cols-12 gap-3">
      <div className="col-span-12 lg:col-span-8 space-y-3">
        <Card padding={false}>
          <div className="p-4 pb-2"><SectionTitle sub="3-2-1 / NWE / Sing">Crack Spreads</SectionTitle></div>
          <div className="h-72 px-2 pb-2">
            <ResponsiveContainer>
              <LineChart data={Array.from({ length: 60 }, (_, i) => ({
                t: i,
                gulf: 20 + Math.sin(i / 8) * 6 + Math.random() * 2,
                nwe: 16 + Math.cos(i / 6) * 4 + Math.random() * 2,
                sing: 14 + Math.sin(i / 5) * 3 + Math.random() * 1.5,
              }))}>
                <CartesianGrid {...chartProps.grid} />
                <XAxis dataKey="t" {...chartProps.axis} />
                <YAxis {...chartProps.axis} width={36} />
                <Tooltip content={<ChartTooltip unit=" $/bbl" />} />
                <Line type="monotone" dataKey="gulf" stroke="#f59e0b" strokeWidth={1.4} dot={false} name="USGC 3-2-1" isAnimationActive={false} />
                <Line type="monotone" dataKey="nwe" stroke="#38bdf8" strokeWidth={1.4} dot={false} name="NWE" isAnimationActive={false} />
                <Line type="monotone" dataKey="sing" stroke="#10b981" strokeWidth={1.4} dot={false} name="Singapore" isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <MoversPanel />
      </div>
      <div className="col-span-12 lg:col-span-4 space-y-3">
        <NewsPanel compact />
        <Card>
          <SectionTitle sub="Days of forward demand">Product Inventories</SectionTitle>
          {[
            { p: "Gasoline (US)", v: 26.4, c: +0.8 },
            { p: "Distillate (US)", v: 28.2, c: -1.2 },
            { p: "Jet (ARA)", v: 18.6, c: -0.4 },
            { p: "HSFO (Sing)", v: 22.4, c: +0.6 },
          ].map((r) => (
            <div key={r.p} className="flex items-center justify-between py-1.5 border-b border-[#15161a] last:border-0">
              <span className="text-[11px] text-zinc-300">{r.p}</span>
              <div className="flex items-center gap-2">
                <span className="font-mono text-[11px] text-zinc-200">{r.v}d</span>
                <Delta v={r.c} pct={(r.c / r.v) * 100} />
              </div>
            </div>
          ))}
        </Card>
      </div>
    </div>
  </div>
);
