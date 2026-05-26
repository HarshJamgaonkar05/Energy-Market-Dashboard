import { useMemo } from "react";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { Ship } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { Badge } from "../components/primitives/Badge";
import { Delta } from "../components/primitives/Delta";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { fmt } from "../lib/format";
import { HERO, genSeries, genSpark } from "../data/mock";
import { HeroCard } from "../components/HeroCard";
import { NewsPanel } from "../components/panels/NewsPanel";

export const PageLng = () => {
  const jkmSeries = useMemo(() => genSeries(301, 90, 12, 0.4, 0.01), []);
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[#1c1d22]">
        {[
          { sym: "JKM", name: "Japan Korea Marker", val: 12.84, chg: -0.31, pct: -2.36, spark: genSpark(41, 30, -1), unit: "$/MMBtu" },
          { sym: "DES NWE", name: "NW Europe Delivered", val: 11.42, chg: -0.18, pct: -1.55, spark: genSpark(42, 30, -1), unit: "$/MMBtu" },
          { sym: "JKM-TTF", name: "Asia Premium", val: 0.42, chg: +0.21, pct: +99.0, spark: genSpark(43, 30, 1), unit: "$/MMBtu" },
          { sym: "FOB GC", name: "US Gulf FOB", val: 8.91, chg: +0.12, pct: +1.37, spark: genSpark(44, 30, 1), unit: "$/MMBtu" },
        ].map((d) => <HeroCard key={d.sym} d={d} />)}
      </div>

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-8 space-y-3">
          <Card padding={false}>
            <div className="p-4 pb-2">
              <SectionTitle sub="JKM Platts Spot">LNG Asia Spot Price</SectionTitle>
            </div>
            <div className="h-72 px-2 pb-2">
              <ResponsiveContainer>
                <AreaChart data={jkmSeries}>
                  <defs>
                    <linearGradient id="jkm" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#38bdf8" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis dataKey="t" {...chartProps.axis} />
                  <YAxis {...chartProps.axis} width={36} domain={["auto", "auto"]} />
                  <Tooltip content={<ChartTooltip unit=" $/MMBtu" />} />
                  <Area type="monotone" dataKey="v" stroke="#38bdf8" strokeWidth={1.4} fill="url(#jkm)" isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <SectionTitle sub="Active cargoes · last 24h">LNG Vessel Tracking</SectionTitle>
            <div className="overflow-x-auto -mx-4">
              <table className="w-full text-[11px]">
                <thead>
                  <tr className="text-zinc-500 text-[9px] uppercase tracking-wider border-b border-[#1c1d22]">
                    <th className="text-left px-4 py-2">Vessel</th>
                    <th className="text-left px-2 py-2">Origin</th>
                    <th className="text-left px-2 py-2">Destination</th>
                    <th className="text-right px-2 py-2">Cargo (mcm)</th>
                    <th className="text-right px-2 py-2">ETA</th>
                    <th className="text-right px-4 py-2">Status</th>
                  </tr>
                </thead>
                <tbody className="font-mono">
                  {[
                    { v: "Maran Gas Achilles", o: "Sabine Pass", d: "Zeebrugge", c: 161, eta: "Mar 4", s: "underway", t: "bull" },
                    { v: "Energy Endeavor", o: "Ras Laffan", d: "Futtsu", c: 173, eta: "Mar 2", s: "underway", t: "bull" },
                    { v: "Marvel Glacier", o: "Corpus Christi", d: "Dragon", c: 155, eta: "Mar 6", s: "loading", t: "warn" },
                    { v: "BW Magna", o: "Bonny", d: "Cartagena", c: 138, eta: "Mar 11", s: "underway", t: "bull" },
                    { v: "Diamond Gas Pearl", o: "Cameron", d: "Higashi-Ohgishima", c: 174, eta: "Mar 18", s: "underway", t: "bull" },
                    { v: "Kool Boreas", o: "Yamal", d: "Bilbao", c: 172, eta: "Mar 8", s: "waiting", t: "med" },
                  ].map((row, i) => (
                    <tr key={i} className="border-b border-[#15161a] hover:bg-white/[0.02]">
                      <td className="px-4 py-1.5 text-zinc-200">{row.v}</td>
                      <td className="px-2 py-1.5 text-zinc-400">{row.o}</td>
                      <td className="px-2 py-1.5 text-zinc-400">{row.d}</td>
                      <td className="px-2 py-1.5 text-right text-zinc-300">{row.c}</td>
                      <td className="px-2 py-1.5 text-right text-zinc-400">{row.eta}</td>
                      <td className="px-4 py-1.5 text-right"><Badge tone={row.t}>{row.s}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        <div className="col-span-12 lg:col-span-4 space-y-3">
          <Card>
            <SectionTitle sub="2026 capacity, mtpa">Liquefaction Outlook</SectionTitle>
            {[
              { c: "USA", new: 42, total: 138 },
              { c: "Qatar", new: 16, total: 92 },
              { c: "Australia", new: 0, total: 88 },
              { c: "Russia", new: 6, total: 38 },
              { c: "Malaysia", new: 0, total: 30 },
            ].map((c) => (
              <div key={c.c} className="py-1.5 border-b border-[#15161a] last:border-0">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-zinc-300">{c.c}</span>
                  <span className="font-mono text-[10px] text-zinc-200">{c.total} <span className="text-zinc-500">mtpa</span></span>
                </div>
                {c.new > 0 && <div className="text-[9px] text-emerald-400 mt-0.5">+{c.new} new this year</div>}
              </div>
            ))}
          </Card>
          <NewsPanel compact />
        </div>
      </div>
    </div>
  );
};
