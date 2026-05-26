import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell, ReferenceLine,
} from "recharts";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { Badge } from "../components/primitives/Badge";
import { Delta } from "../components/primitives/Delta";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { fmt } from "../lib/format";
import { HERO, genSeries, genSpark } from "../data/mock";
import { HeroCard } from "../components/HeroCard";
import { NewsPanel } from "../components/panels/NewsPanel";
import { WeatherRisk } from "../components/panels/WeatherRisk";

export const PageGas = () => {
  const hhSeries = useMemo(() => genSeries(201, 90, 3.1, 0.14, 0.005), []);
  const ttfSeries = useMemo(() => genSeries(202, 90, 38, 1.6, 0.05), []);

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-px bg-[#1c1d22]">
        {[
          { sym: "HENRY HUB", name: "Front Month", val: 3.142, chg: -0.087, pct: -2.69, spark: genSpark(31, 30, -1), unit: "$/MMBtu" },
          { sym: "TTF", name: "Dutch TTF", val: 38.65, chg: +0.42, pct: +1.10, spark: genSpark(32, 30, 1), unit: "€/MWh" },
          { sym: "NBP", name: "UK NBP", val: 88.21, chg: +1.84, pct: +2.13, spark: genSpark(33, 30, 1), unit: "p/th" },
          { sym: "ALGONQUIN", name: "Northeast Basis", val: 4.18, chg: +0.32, pct: +8.32, spark: genSpark(34, 30, 1), unit: "$" },
          { sym: "WAHA", name: "Permian Basis", val: -1.42, chg: -0.21, pct: -17.4, spark: genSpark(35, 30, -1), unit: "$" },
        ].map((d) => <HeroCard key={d.sym} d={d} />)}
      </div>

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-8 space-y-3">
          <Card padding={false}>
            <div className="p-4 pb-2">
              <SectionTitle sub="USD/MMBtu — Front Month">Henry Hub Futures</SectionTitle>
            </div>
            <div className="h-72 px-2 pb-2">
              <ResponsiveContainer>
                <AreaChart data={hhSeries}>
                  <defs>
                    <linearGradient id="hh" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#10b981" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis dataKey="t" {...chartProps.axis} />
                  <YAxis {...chartProps.axis} width={36} domain={["auto", "auto"]} />
                  <Tooltip content={<ChartTooltip unit=" $/MMBtu" />} />
                  <Area type="monotone" dataKey="v" stroke="#10b981" strokeWidth={1.4} fill="url(#hh)" isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-3">
            <Card padding={false}>
              <div className="p-4 pb-2">
                <SectionTitle sub="EUR/MWh">TTF Front Month</SectionTitle>
              </div>
              <div className="h-44 px-2 pb-2">
                <ResponsiveContainer>
                  <LineChart data={ttfSeries}>
                    <CartesianGrid {...chartProps.grid} />
                    <XAxis dataKey="t" {...chartProps.axis} />
                    <YAxis {...chartProps.axis} width={36} />
                    <Tooltip content={<ChartTooltip unit=" €" />} />
                    <Line type="monotone" dataKey="v" stroke="#f59e0b" strokeWidth={1.4} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card>
              <SectionTitle sub="EU regions, % full">Storage Levels</SectionTitle>
              {[
                { c: "Germany", v: 71 },
                { c: "Netherlands", v: 68 },
                { c: "Italy", v: 82 },
                { c: "France", v: 75 },
                { c: "Austria", v: 89 },
              ].map((r) => (
                <div key={r.c} className="flex items-center gap-2 py-1">
                  <span className="text-[11px] text-zinc-300 w-24">{r.c}</span>
                  <div className="flex-1 h-2 bg-[#15161a]">
                    <motion.div initial={{ width: 0 }} animate={{ width: `${r.v}%` }} transition={{ duration: 0.6 }} className="h-full bg-sky-500/70" />
                  </div>
                  <span className="font-mono text-[10px] text-zinc-300 w-9 text-right">{r.v}%</span>
                </div>
              ))}
            </Card>
          </div>

          <Card padding={false}>
            <div className="p-4 pb-2">
              <SectionTitle sub="Bcf weekly change">EIA Storage Report</SectionTitle>
            </div>
            <div className="h-44 px-2 pb-2">
              <ResponsiveContainer>
                <BarChart data={Array.from({ length: 26 }, (_, i) => ({ w: `W${i + 1}`, v: Math.round((Math.sin(i / 4) + (i / 26 - 0.5)) * 80) }))}>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis dataKey="w" {...chartProps.axis} interval={3} />
                  <YAxis {...chartProps.axis} width={40} />
                  <Tooltip content={<ChartTooltip unit=" Bcf" />} />
                  <ReferenceLine y={0} stroke="#3a3b41" />
                  <Bar dataKey="v" isAnimationActive={false}>
                    {Array.from({ length: 26 }).map((_, i) => {
                      const v = Math.round((Math.sin(i / 4) + (i / 26 - 0.5)) * 80);
                      return <Cell key={i} fill={v >= 0 ? "#10b981" : "#ef4444"} fillOpacity={0.7} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        <div className="col-span-12 lg:col-span-4 space-y-3">
          <WeatherRisk />
          <NewsPanel compact />
        </div>
      </div>
    </div>
  );
};
