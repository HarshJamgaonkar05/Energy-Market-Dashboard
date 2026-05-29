import { useMemo } from "react";
import {
  LineChart, Line, AreaChart, Area, Bar, ComposedChart, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { TrendingUp, Anchor, CloudSnow, Wind, Gauge } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { Band } from "../components/primitives/Band";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { Badge } from "../components/primitives/Badge";
import { Delta } from "../components/primitives/Delta";
import { HeroCard } from "../components/HeroCard";
import { ShippingPanel } from "../components/panels/ShippingPanel";
import { WeatherRisk } from "../components/panels/WeatherRisk";
import { EconCalendar } from "../components/panels/EconCalendar";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { fmt, fmtSigned } from "../lib/format";
import { genSpark, OPEC_QUOTAS, OPEC_TOTAL, opecCompliance, RIG_COUNT, STOCK_FLOWS } from "../data/mock";

export const PageDrivers = () => {
  const macro = useMemo(() => Array.from({ length: 90 }, (_, i) => ({
    t: i,
    dxy: 104 + Math.sin(i / 9) * 1.4 + (Math.random() - 0.5) * 0.4,
    spx: 5200 + i * 4 + Math.sin(i / 5) * 60,
    vix: 14 + Math.cos(i / 7) * 3 + Math.random() * 1.5,
  })), []);

  const rates = useMemo(() => Array.from({ length: 60 }, (_, i) => ({
    t: i,
    vlcc: 28000 + Math.sin(i / 8) * 8000 + i * 100,
    suezmax: 38000 + Math.cos(i / 6) * 12000 + i * 80,
    aframax: 42000 + Math.sin(i / 5) * 10000 + i * 60,
  })), []);

  const temp = useMemo(() => Array.from({ length: 14 }, (_, i) => ({
    d: `D+${i}`,
    obs: -2 + Math.sin(i / 3) * 4,
    fc: -2 + Math.sin(i / 3) * 4 + (Math.random() - 0.5) * 2,
  })), []);

  // Aggregate OPEC+ adherence — kept in sync with the per-member table below.
  const opecComp = +((OPEC_TOTAL.quota / OPEC_TOTAL.prod) * 100).toFixed(1);
  const compTone = (c) => (c >= 99.5 ? "#10b981" : c >= 97 ? "#f59e0b" : "#ef4444");

  return (
    <div className="space-y-5">
      {/* ============================ MACRO & RATES ============================ */}
      <section className="space-y-3">
        <Band icon={TrendingUp} title="Macro & Rates" sub="Cross-asset backdrop for energy" />

        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[#1c1d22]">
          {[
            { sym: "DXY", name: "Dollar Index", val: 104.21, chg: -0.34, pct: -0.33, spark: genSpark(61, 30, -1), unit: "" },
            { sym: "SPX", name: "S&P 500", val: 5284.21, chg: +18.4, pct: +0.35, spark: genSpark(62, 30, 1), unit: "" },
            { sym: "VIX", name: "Volatility", val: 14.32, chg: +0.18, pct: +1.27, spark: genSpark(63, 30, 1), unit: "" },
            { sym: "UST10Y", name: "10Y Yield", val: 4.218, chg: +0.024, pct: +0.57, spark: genSpark(64, 30, 1), unit: "%" },
          ].map((d) => <HeroCard key={d.sym} d={d} />)}
        </div>

        <div className="grid grid-cols-12 gap-3">
          <Card padding={false} className="col-span-12 lg:col-span-8">
            <div className="p-4 pb-2"><SectionTitle sub="DXY vs SPX · 90D">Dollar / Equity Backdrop</SectionTitle></div>
            <div className="h-60 px-2 pb-2">
              <ResponsiveContainer>
                <ComposedChart data={macro}>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis dataKey="t" {...chartProps.axis} />
                  <YAxis yAxisId="L" {...chartProps.axis} orientation="left" width={42} domain={["auto", "auto"]} />
                  <YAxis yAxisId="R" {...chartProps.axis} orientation="right" width={46} domain={["auto", "auto"]} />
                  <Tooltip content={<ChartTooltip />} />
                  <Line yAxisId="L" type="monotone" dataKey="dxy" stroke="#10b981" strokeWidth={1.4} dot={false} name="DXY" isAnimationActive={false} />
                  <Line yAxisId="R" type="monotone" dataKey="spx" stroke="#f59e0b" strokeWidth={1.4} dot={false} name="SPX" isAnimationActive={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card padding={false} className="col-span-12 lg:col-span-4">
            <div className="p-4 pb-2"><SectionTitle sub="VIX · 90D">Risk Indicator</SectionTitle></div>
            <div className="h-60 px-2 pb-2">
              <ResponsiveContainer>
                <AreaChart data={macro}>
                  <defs>
                    <linearGradient id="vixFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#ef4444" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis dataKey="t" {...chartProps.axis} />
                  <YAxis {...chartProps.axis} width={32} />
                  <Tooltip content={<ChartTooltip />} />
                  <Area type="monotone" dataKey="vix" stroke="#ef4444" strokeWidth={1.4} fill="url(#vixFill)" name="VIX" isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        <EconCalendar />
      </section>

      {/* ======================== OIL SUPPLY DRIVERS ======================== */}
      <section className="space-y-3">
        <Band icon={Gauge} title="Oil Supply Drivers" sub="OPEC quotas, rig count & inventory flows" />

        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[#1c1d22]">
          {[
            { sym: "OPEC+ COMP", name: "Quota Compliance", val: opecComp, chg: +1.4, pct: +1.4, spark: genSpark(81, 30, 1), unit: "%" },
            { sym: "US OIL RIGS", name: "Baker Hughes", val: 497, chg: -3, pct: -0.60, spark: genSpark(82, 30, -1), unit: "rigs" },
            { sym: "US CRUDE STK", name: "EIA Commercial", val: 429.1, chg: -4.2, pct: -0.97, spark: genSpark(83, 30, -1), unit: "MMbbl" },
            { sym: "OPEC+ SPARE", name: "Spare Capacity", val: 4.21, chg: -0.12, pct: -2.77, spark: genSpark(84, 30, -1), unit: "mb/d" },
          ].map((d) => <HeroCard key={d.sym} d={d} />)}
        </div>

        <div className="grid grid-cols-12 gap-3">
          <Card padding={false} className="col-span-12 lg:col-span-8">
            <div className="p-4 pb-2"><SectionTitle sub="20W · MMbbl · EIA bars / API line · draw bullish">Weekly Crude Builds & Draws</SectionTitle></div>
            <div className="h-60 px-2 pb-2">
              <ResponsiveContainer>
                <ComposedChart data={STOCK_FLOWS}>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis dataKey="w" {...chartProps.axis} interval={2} />
                  <YAxis {...chartProps.axis} width={40} />
                  <Tooltip content={<ChartTooltip unit=" MMbbl" />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                  <ReferenceLine y={0} stroke="#3a3b41" />
                  <Bar dataKey="eia" name="EIA" maxBarSize={16} isAnimationActive={false}>
                    {STOCK_FLOWS.map((d, i) => (
                      <Cell key={i} fill={d.eia >= 0 ? "#ef4444" : "#10b981"} fillOpacity={0.7} />
                    ))}
                  </Bar>
                  <Line type="monotone" dataKey="api" name="API" stroke="#f59e0b" strokeWidth={1.4} strokeDasharray="3 3" dot={false} isAnimationActive={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card padding={false} className="col-span-12 lg:col-span-4">
            <div className="p-4 pb-2"><SectionTitle sub="Baker Hughes · 52W">Rig Count</SectionTitle></div>
            <div className="h-60 px-2 pb-2">
              <ResponsiveContainer>
                <ComposedChart data={RIG_COUNT}>
                  <defs>
                    <linearGradient id="rigFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.32} />
                      <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis dataKey="w" {...chartProps.axis} tick={false} />
                  <YAxis yAxisId="L" {...chartProps.axis} width={34} domain={["auto", "auto"]} />
                  <YAxis yAxisId="R" {...chartProps.axis} orientation="right" width={30} domain={["auto", "auto"]} />
                  <Tooltip content={<ChartTooltip />} />
                  <Area yAxisId="L" type="monotone" dataKey="oil" stroke="#f59e0b" strokeWidth={1.4} fill="url(#rigFill)" name="Oil" isAnimationActive={false} />
                  <Line yAxisId="R" type="monotone" dataKey="gas" stroke="#38bdf8" strokeWidth={1.2} dot={false} name="Gas" isAnimationActive={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        <Card>
          <SectionTitle sub="mb/d · output vs target">OPEC+ Production & Quota Compliance</SectionTitle>
          <div className="grid grid-cols-[1.3fr_repeat(3,0.6fr)_1.4fr] items-center gap-x-3 gap-y-0.5">
            <div className="contents text-[9px] text-zinc-600 uppercase tracking-wider">
              <span>Member</span>
              <span className="text-right">Target</span>
              <span className="text-right">Output</span>
              <span className="text-right">Δ</span>
              <span className="text-right">Compliance</span>
            </div>
            {OPEC_QUOTAS.map((m) => {
              const comp = opecCompliance(m);
              const delta = +(m.prod - m.quota).toFixed(2);
              const c = compTone(comp);
              return (
                <div key={m.member} className="contents">
                  <span className="text-[11px] text-zinc-300 py-1 border-t border-[#15161a] truncate">{m.member}</span>
                  <span className="font-mono text-[11px] text-zinc-400 text-right py-1 border-t border-[#15161a]">{fmt(m.quota)}</span>
                  <span className="font-mono text-[11px] text-zinc-200 text-right py-1 border-t border-[#15161a]">{fmt(m.prod)}</span>
                  <span className={`font-mono text-[11px] text-right py-1 border-t border-[#15161a] ${delta > 0 ? "text-red-400" : "text-emerald-400"}`}>{fmtSigned(delta)}</span>
                  <div className="flex items-center gap-2 py-1 border-t border-[#15161a]">
                    <div className="flex-1 h-1.5 bg-[#15161a]">
                      <div className="h-full" style={{ width: `${Math.min(comp, 100)}%`, background: c, opacity: 0.7 }} />
                    </div>
                    <span className="font-mono text-[10px] w-12 text-right" style={{ color: c }}>{fmt(comp, 1)}%</span>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="grid grid-cols-[1.3fr_repeat(3,0.6fr)_1.4fr] items-center gap-x-3 mt-2 pt-2 border-t border-[#1c1d22]">
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider">OPEC+ Total</span>
            <span className="font-mono text-[11px] text-zinc-300 text-right">{fmt(OPEC_TOTAL.quota)}</span>
            <span className="font-mono text-[11px] text-zinc-100 text-right">{fmt(OPEC_TOTAL.prod)}</span>
            <span className={`font-mono text-[11px] text-right ${OPEC_TOTAL.prod > OPEC_TOTAL.quota ? "text-red-400" : "text-emerald-400"}`}>{fmtSigned(+(OPEC_TOTAL.prod - OPEC_TOTAL.quota).toFixed(2))}</span>
            <span className="font-mono text-[11px] text-right" style={{ color: compTone(opecComp) }}>{fmt(opecComp, 1)}%</span>
          </div>
        </Card>
      </section>

      {/* ========================= FREIGHT & SHIPPING ========================= */}
      <section className="space-y-3">
        <Band icon={Anchor} title="Freight & Shipping" sub="Tanker rates & port congestion" />

        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[#1c1d22]">
          {[
            { sym: "VLCC TD3C", name: "AG–China", val: 38420, chg: +1842, pct: +5.04, spark: genSpark(51, 30, 1), unit: "$/day" },
            { sym: "SUEZMAX", name: "TD20 WAF–UK", val: 51280, chg: +3142, pct: +6.53, spark: genSpark(52, 30, 1), unit: "$/day" },
            { sym: "AFRAMAX", name: "TD25 USGC–UK", val: 48710, chg: -812, pct: -1.64, spark: genSpark(53, 30, -1), unit: "$/day" },
            { sym: "BDI", name: "Baltic Dry", val: 1842, chg: +28, pct: +1.54, spark: genSpark(54, 30, 1), unit: "" },
          ].map((d) => <HeroCard key={d.sym} d={d} />)}
        </div>

        <div className="grid grid-cols-12 gap-3">
          <Card padding={false} className="col-span-12 lg:col-span-8">
            <div className="p-4 pb-2"><SectionTitle sub="$/day · time charter equivalent">Tanker Rates</SectionTitle></div>
            <div className="h-64 px-2 pb-2">
              <ResponsiveContainer>
                <LineChart data={rates}>
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

          <div className="col-span-12 lg:col-span-4 space-y-3">
            <ShippingPanel />
            <Card>
              <SectionTitle sub="$/bbl freight">Route Spreads</SectionTitle>
              {[
                { r: "USGC–NWE", v: 4.82, c: +0.32 },
                { r: "AG–Asia", v: 2.14, c: -0.18 },
                { r: "WAF–Asia", v: 3.41, c: +0.12 },
                { r: "NSEA–USGC", v: 2.86, c: -0.04 },
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
      </section>

      {/* ========================= WEATHER & DEMAND ========================= */}
      <section className="space-y-3">
        <Band icon={CloudSnow} title="Weather & Demand" sub="Heating / cooling demand drivers" />

        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[#1c1d22]">
          {[
            { sym: "US-HDD", name: "Heating Degree Days", val: 142, chg: +18, pct: +14.5, spark: genSpark(71, 30, 1), unit: "vs norm" },
            { sym: "EU-HDD", name: "EU Heating Demand", val: 124, chg: +12, pct: +10.7, spark: genSpark(72, 30, 1), unit: "vs norm" },
            { sym: "ASIA-CDD", name: "Asia Cooling", val: 38, chg: -4, pct: -9.5, spark: genSpark(73, 30, -1), unit: "vs norm" },
            { sym: "ENSO", name: "El Niño Index", val: 1.42, chg: +0.08, pct: +5.9, spark: genSpark(74, 30, 1), unit: "" },
          ].map((d) => <HeroCard key={d.sym} d={d} />)}
        </div>

        <div className="grid grid-cols-12 gap-3">
          <Card padding={false} className="col-span-12 lg:col-span-8">
            <div className="p-4 pb-2"><SectionTitle sub="14-day · NW Europe">Temperature Forecast vs Normal</SectionTitle></div>
            <div className="h-64 px-2 pb-2">
              <ResponsiveContainer>
                <ComposedChart data={temp}>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis dataKey="d" {...chartProps.axis} />
                  <YAxis {...chartProps.axis} width={40} />
                  <Tooltip content={<ChartTooltip unit="°C" />} />
                  <ReferenceLine y={0} stroke="#3a3b41" strokeDasharray="2 2" label={{ value: "Normal", fill: "#71717a", fontSize: 9, position: "right" }} />
                  <Area type="monotone" dataKey="obs" fill="#38bdf8" fillOpacity={0.18} stroke="#38bdf8" strokeWidth={1} name="Observed" isAnimationActive={false} />
                  <Line type="monotone" dataKey="fc" stroke="#f59e0b" strokeWidth={1.6} dot={{ r: 3, fill: "#f59e0b" }} name="Forecast" isAnimationActive={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <div className="col-span-12 lg:col-span-4 space-y-3">
            <Card>
              <SectionTitle sub="Active alerts">Storm Tracker</SectionTitle>
              {[
                { n: "Storm Erika", c: "Atlantic", cat: "Cat 2", risk: "high" },
                { n: "Polar Vortex", c: "N. America", cat: "Severe", risk: "high" },
                { n: "Heatwave Sirius", c: "Europe", cat: "Moderate", risk: "med" },
                { n: "Typhoon Yagi", c: "W. Pacific", cat: "Cat 1", risk: "med" },
              ].map((s) => (
                <div key={s.n} className="flex items-start gap-2 py-2 border-b border-[#15161a] last:border-0">
                  <Wind size={12} className={s.risk === "high" ? "text-red-400" : "text-amber-400"} />
                  <div className="flex-1">
                    <div className="text-[11px] text-zinc-200">{s.n}</div>
                    <div className="text-[9px] text-zinc-500">{s.c} · {s.cat}</div>
                  </div>
                  <Badge tone={s.risk}>{s.risk}</Badge>
                </div>
              ))}
            </Card>
            <WeatherRisk />
          </div>
        </div>
      </section>
    </div>
  );
};
