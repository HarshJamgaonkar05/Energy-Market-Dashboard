import { useMemo } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { Anchor, AlertTriangle, Circle } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { Badge } from "../components/primitives/Badge";
import { Delta } from "../components/primitives/Delta";
import { ShippingPanel } from "../components/panels/ShippingPanel";
import { HeroCard } from "../components/HeroCard";
import { fmt } from "../lib/format";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { HERO, genSeries, genSpark } from "../data/mock";

export const PageFreight = () => {
  const rateData = useMemo(() => Array.from({ length: 60 }, (_, i) => ({
    t: i,
    vlcc: 28000 + Math.sin(i / 8) * 8000 + i * 100,
    suezmax: 38000 + Math.cos(i / 6) * 12000 + i * 80,
    aframax: 42000 + Math.sin(i / 5) * 10000 + i * 60,
  })), []);

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[#1c1d22]">
        {[
          { sym: "VLCC TD3C", name: "AG-China", val: 38420, chg: +1842, pct: +5.04, spark: genSpark(51, 30, 1), unit: "$/day" },
          { sym: "SUEZMAX", name: "TD20 WAF-UK", val: 51280, chg: +3142, pct: +6.53, spark: genSpark(52, 30, 1), unit: "$/day" },
          { sym: "AFRAMAX", name: "TD25 USGC-UK", val: 48710, chg: -812, pct: -1.64, spark: genSpark(53, 30, -1), unit: "$/day" },
          { sym: "BDI", name: "Baltic Dry", val: 1842, chg: +28, pct: +1.54, spark: genSpark(54, 30, 1), unit: "" },
        ].map((d) => <HeroCard key={d.sym} d={d} />)}
      </div>

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-8 space-y-3">
          <Card padding={false}>
            <div className="p-4 pb-2">
              <SectionTitle sub="$/day · time charter equivalent">Tanker Rates</SectionTitle>
            </div>
            <div className="h-80 px-2 pb-2">
              <ResponsiveContainer>
                <LineChart data={rateData}>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis dataKey="t" {...chartProps.axis} />
                  <YAxis {...chartProps.axis} width={48} />
                  <Tooltip content={<ChartTooltip unit=" $/d" />} />
                  <Line type="monotone" dataKey="vlcc" stroke="#f59e0b" strokeWidth={1.4} dot={false} name="VLCC" isAnimationActive={false} />
                  <Line type="monotone" dataKey="suezmax" stroke="#38bdf8" strokeWidth={1.4} dot={false} name="Suezmax" isAnimationActive={false} />
                  <Line type="monotone" dataKey="aframax" stroke="#10b981" strokeWidth={1.4} dot={false} name="Aframax" isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <SectionTitle sub="Live AIS + AI inference">Route Congestion Map</SectionTitle>
            <div className="aspect-[16/7] bg-gradient-to-br from-[#0a0b0e] to-[#13141a] border border-[#1c1d22] relative overflow-hidden">
              {/* Stylized map representation */}
              <svg viewBox="0 0 800 350" className="absolute inset-0 w-full h-full">
                <defs>
                  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1c1d22" strokeWidth="0.5" />
                  </pattern>
                </defs>
                <rect width="800" height="350" fill="url(#grid)" />
                {/* Continents (abstract) */}
                <path d="M 100 80 Q 200 60, 280 100 L 320 180 Q 280 220, 240 200 L 180 220 Q 120 200, 100 160 Z" fill="#15161a" stroke="#2a2b31" />
                <path d="M 380 70 Q 500 60, 620 120 L 680 200 Q 640 260, 580 240 L 480 280 Q 400 240, 380 180 Z" fill="#15161a" stroke="#2a2b31" />
                {/* Routes */}
                <path d="M 200 150 Q 350 100, 500 180" fill="none" stroke="#f59e0b" strokeWidth="1.4" strokeDasharray="4 3" opacity="0.7" />
                <path d="M 480 220 Q 580 240, 650 200" fill="none" stroke="#10b981" strokeWidth="1.4" strokeDasharray="4 3" opacity="0.7" />
                <path d="M 250 200 Q 350 250, 450 220" fill="none" stroke="#38bdf8" strokeWidth="1.4" strokeDasharray="4 3" opacity="0.7" />
                {/* Ports */}
                {[
                  { x: 220, y: 140, n: "Houston", c: 41 },
                  { x: 340, y: 110, n: "Rotterdam", c: 54 },
                  { x: 510, y: 200, n: "Suez", c: 92 },
                  { x: 600, y: 230, n: "Fujairah", c: 67 },
                  { x: 680, y: 200, n: "Singapore", c: 78 },
                ].map((p) => (
                  <g key={p.n}>
                    <circle cx={p.x} cy={p.y} r={p.c > 75 ? 7 : 5} fill={p.c > 75 ? "#ef4444" : p.c > 55 ? "#f59e0b" : "#10b981"} opacity="0.4" />
                    <circle cx={p.x} cy={p.y} r="2.5" fill={p.c > 75 ? "#ef4444" : p.c > 55 ? "#f59e0b" : "#10b981"} />
                    <text x={p.x + 10} y={p.y - 6} fill="#a1a1aa" fontSize="9" fontFamily="monospace">{p.n}</text>
                    <text x={p.x + 10} y={p.y + 6} fill="#71717a" fontSize="8" fontFamily="monospace">{p.c}%</text>
                  </g>
                ))}
              </svg>
              <div className="absolute bottom-3 left-3 flex items-center gap-3 text-[9px] uppercase tracking-wider">
                <div className="flex items-center gap-1"><Circle size={6} fill="#10b981" /><span className="text-zinc-400">Normal</span></div>
                <div className="flex items-center gap-1"><Circle size={6} fill="#f59e0b" /><span className="text-zinc-400">Elevated</span></div>
                <div className="flex items-center gap-1"><Circle size={6} fill="#ef4444" /><span className="text-zinc-400">Critical</span></div>
              </div>
            </div>
          </Card>
        </div>

        <div className="col-span-12 lg:col-span-4 space-y-3">
          <ShippingPanel />
          <Card>
            <SectionTitle sub="Bps · WTI vs ARA">Freight Spreads</SectionTitle>
            {[
              { r: "USGC-NWE", v: 4.82, c: +0.32 },
              { r: "AG-Asia", v: 2.14, c: -0.18 },
              { r: "WAF-Asia", v: 3.41, c: +0.12 },
              { r: "NSEA-USGC", v: 2.86, c: -0.04 },
            ].map((s) => (
              <div key={s.r} className="flex items-center justify-between py-1.5 border-b border-[#15161a] last:border-0">
                <span className="text-[11px] text-zinc-300">{s.r}</span>
                <span className="font-mono text-[11px] text-zinc-200">${fmt(s.v)}</span>
                <Delta v={s.c} pct={(s.c / s.v) * 100} />
              </div>
            ))}
          </Card>
        </div>
      </div>
    </div>
  );
};
