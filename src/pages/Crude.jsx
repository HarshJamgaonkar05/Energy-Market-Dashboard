import { useState, useMemo } from "react";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, ComposedChart,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { Filter, Download, BarChart3 } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { Badge } from "../components/primitives/Badge";
import { Delta } from "../components/primitives/Delta";
import { CurveChart } from "../components/panels/CurveChart";
import { MoversPanel } from "../components/panels/MoversPanel";
import { NewsPanel } from "../components/panels/NewsPanel";
import { HeroCard } from "../components/HeroCard";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { fmt, fmtSigned } from "../lib/format";
import { HERO, seededRand, genSeries } from "../data/mock";

const candleData = (() => {
  const r = seededRand(77);
  let p = 80;
  return Array.from({ length: 40 }, (_, i) => {
    const o = p;
    const move = (r() - 0.5) * 3;
    const c = o + move;
    const h = Math.max(o, c) + r() * 1.2;
    const l = Math.min(o, c) - r() * 1.2;
    p = c;
    return { i, o: +o.toFixed(2), h: +h.toFixed(2), l: +l.toFixed(2), c: +c.toFixed(2), v: +(50000 + r() * 50000).toFixed(0) };
  });
})();

const CandlestickChart = ({ data, height = 260 }) => {
  const min = Math.min(...data.map((d) => d.l));
  const max = Math.max(...data.map((d) => d.h));
  const range = max - min;
  const h = height - 30;
  const yScale = (v) => h - ((v - min) / range) * h + 10;

  return (
    <svg width="100%" height={height} className="block">
      {[0.25, 0.5, 0.75].map((p) => (
        <line
          key={p}
          x1="0"
          x2="100%"
          y1={10 + h * p}
          y2={10 + h * p}
          stroke="#1c1d22"
          strokeDasharray="3 4"
        />
      ))}
      {data.map((d, i) => {
        const w = `${100 / data.length}%`;
        const x = `${(i / data.length) * 100 + 50 / data.length}%`;
        const up = d.c >= d.o;
        const color = up ? "#10b981" : "#ef4444";
        const bodyTop = yScale(Math.max(d.o, d.c));
        const bodyH = Math.max(1, Math.abs(yScale(d.o) - yScale(d.c)));
        return (
          <g key={i}>
            <line x1={x} x2={x} y1={yScale(d.h)} y2={yScale(d.l)} stroke={color} strokeWidth="1" />
            <rect
              x={`calc(${(i / data.length) * 100}% + 15%)`}
              y={bodyTop}
              width={`calc(${100 / data.length}% - 30%)`}
              height={bodyH}
              fill={color}
              fillOpacity={up ? 0.5 : 1}
              stroke={color}
            />
          </g>
        );
      })}
    </svg>
  );
};

export const PageCrude = () => {
  const brentSeries = useMemo(() => genSeries(101, 90, 82, 2.4, 0.04), []);
  const wtiSeries = useMemo(() => genSeries(102, 90, 78, 2.2, 0.03), []);
  const spreadData = brentSeries.map((d, i) => ({ t: d.t, spread: +(d.v - wtiSeries[i].v).toFixed(2) }));

  return (
    <div className="space-y-3">
      {/* Sub hero */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[#1c1d22]">
        {HERO.slice(0, 4).map((d) => (
          <HeroCard key={d.sym} d={d} />
        ))}
      </div>

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-9 space-y-3">
          <Card padding={false}>
            <div className="p-4 flex items-center justify-between">
              <div>
                <div className="flex items-baseline gap-3">
                  <h2 className="text-[14px] font-semibold text-zinc-100">BRENT FRONT MONTH</h2>
                  <span className="font-mono text-2xl text-amber-400">$82.47</span>
                  <Delta v={+1.23} pct={+1.51} size="lg" />
                </div>
                <p className="text-[10px] text-zinc-500 mt-0.5">ICE Brent Futures · Continuous</p>
              </div>
              <div className="flex gap-1">
                {["1H", "4H", "1D", "1W", "1M"].map((tf) => (
                  <button key={tf} className={`px-2 h-7 text-[10px] font-mono ${tf === "1D" ? "bg-amber-500/10 text-amber-400 border border-amber-500/30" : "text-zinc-500 border border-transparent hover:text-zinc-200"}`}>
                    {tf}
                  </button>
                ))}
              </div>
            </div>
            <div className="px-4 pb-3">
              <CandlestickChart data={candleData} height={280} />
            </div>
            <div className="border-t border-[#1c1d22] grid grid-cols-6 divide-x divide-[#1c1d22]">
              {[
                { l: "Open", v: "81.24" },
                { l: "High", v: "82.91" },
                { l: "Low", v: "80.88" },
                { l: "Volume", v: "248K" },
                { l: "OI", v: "1.2M" },
                { l: "ATR-14", v: "1.84" },
              ].map((s) => (
                <div key={s.l} className="px-3 py-2">
                  <div className="text-[9px] text-zinc-600 uppercase tracking-wider">{s.l}</div>
                  <div className="font-mono text-[12px] text-zinc-200">{s.v}</div>
                </div>
              ))}
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-3">
            <Card padding={false}>
              <div className="p-4 pb-1">
                <SectionTitle sub="Brent — WTI">Spread</SectionTitle>
              </div>
              <div className="h-44 px-2 pb-2">
                <ResponsiveContainer>
                  <AreaChart data={spreadData}>
                    <defs>
                      <linearGradient id="spr" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.4} />
                        <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid {...chartProps.grid} />
                    <XAxis dataKey="t" {...chartProps.axis} />
                    <YAxis {...chartProps.axis} width={36} />
                    <Tooltip content={<ChartTooltip unit=" $/bbl" />} />
                    <ReferenceLine y={0} stroke="#3a3b41" strokeDasharray="2 2" />
                    <Area type="monotone" dataKey="spread" stroke="#f59e0b" strokeWidth={1.4} fill="url(#spr)" isAnimationActive={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <CurveChart />
          </div>

          <Card>
            <SectionTitle sub="Composite • 30D">Refining Margins</SectionTitle>
            <div className="grid grid-cols-4 gap-3">
              {[
                { reg: "NWE", v: 8.42, c: -0.32 },
                { reg: "USGC", v: 18.74, c: +1.21 },
                { reg: "Singapore", v: 6.18, c: +0.42 },
                { reg: "Med", v: 9.83, c: -0.18 },
              ].map((m) => (
                <div key={m.reg} className="p-3 border border-[#1c1d22]">
                  <div className="text-[10px] text-zinc-500 uppercase tracking-wider">{m.reg}</div>
                  <div className="font-mono text-lg text-zinc-100 mt-1">${fmt(m.v)}</div>
                  <div className="mt-1">
                    <Delta v={m.c} pct={(m.c / m.v) * 100} />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="col-span-12 lg:col-span-3 space-y-3">
          <MoversPanel />
          <NewsPanel compact />
        </div>
      </div>
    </div>
  );
};
