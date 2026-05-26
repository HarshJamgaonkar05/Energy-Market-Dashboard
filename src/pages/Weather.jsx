import { useMemo } from "react";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { Thermometer, Wind, CloudSnow, AlertTriangle } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { Badge } from "../components/primitives/Badge";
import { WeatherRisk } from "../components/panels/WeatherRisk";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { HERO, WEATHER, genSeries, genSpark } from "../data/mock";
import { HeroCard } from "../components/HeroCard";

export const PageWeather = () => {
  const tempData = useMemo(() => Array.from({ length: 14 }, (_, i) => ({
    d: `D+${i}`,
    obs: -2 + Math.sin(i / 3) * 4,
    fc: -2 + Math.sin(i / 3) * 4 + (Math.random() - 0.5) * 2,
    norm: 0,
  })), []);

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[#1c1d22]">
        {[
          { sym: "US-HDD", name: "Heating Degree Days", val: 142, chg: +18, pct: +14.5, spark: genSpark(71, 30, 1), unit: "vs norm" },
          { sym: "EU-HDD", name: "EU Heating Demand", val: 124, chg: +12, pct: +10.7, spark: genSpark(72, 30, 1), unit: "vs norm" },
          { sym: "ASIA-CDD", name: "Asia Cooling", val: 38, chg: -4, pct: -9.5, spark: genSpark(73, 30, -1), unit: "vs norm" },
          { sym: "ENSO", name: "El Niño Index", val: 1.42, chg: +0.08, pct: +5.9, spark: genSpark(74, 30, 1), unit: "" },
        ].map((d) => <HeroCard key={d.sym} d={d} />)}
      </div>

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-8 space-y-3">
          <Card padding={false}>
            <div className="p-4 pb-2">
              <SectionTitle sub="14-day · NW Europe">Temperature Forecast vs Normal</SectionTitle>
            </div>
            <div className="h-72 px-2 pb-2">
              <ResponsiveContainer>
                <ComposedChart data={tempData}>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis dataKey="d" {...chartProps.axis} />
                  <YAxis {...chartProps.axis} width={40} />
                  <Tooltip content={<ChartTooltip unit="°C" />} />
                  <ReferenceLine y={0} stroke="#3a3b41" strokeDasharray="2 2" label={{ value: "Normal", fill: "#71717a", fontSize: 9, position: "right" }} />
                  <Bar dataKey="obs" fill="#38bdf8" fillOpacity={0.5} name="Observed" isAnimationActive={false} />
                  <Line type="monotone" dataKey="fc" stroke="#f59e0b" strokeWidth={1.6} dot={{ r: 3, fill: "#f59e0b" }} name="Forecast" isAnimationActive={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <SectionTitle sub="By region · σ from 30Y normal">Anomaly Heatmap</SectionTitle>
            <div className="grid grid-cols-7 gap-px">
              <div />
              {Array.from({ length: 14 }, (_, i) => i % 2 === 0 && (
                <div key={i} className="text-[9px] text-zinc-600 text-center">D+{i}</div>
              )).filter(Boolean)}
              {["US NE", "US MW", "US GC", "NW Europe", "S Europe", "NE Asia"].map((reg, ri) => (
                <>
                  <div key={`l-${reg}`} className="text-[10px] text-zinc-400 pr-2 py-2 text-right">{reg}</div>
                  {Array.from({ length: 7 }, (_, i) => {
                    const v = ((ri + i) % 5) - 2;
                    const intensity = Math.abs(v) / 2;
                    const color = v < 0 ? `rgba(56, 189, 248, ${intensity * 0.8})` : `rgba(245, 158, 11, ${intensity * 0.8})`;
                    return (
                      <div
                        key={`${reg}-${i}`}
                        className="aspect-square flex items-center justify-center text-[9px] font-mono"
                        style={{ background: color }}
                      >
                        {v > 0 ? `+${v}` : v}
                      </div>
                    );
                  })}
                </>
              ))}
            </div>
          </Card>
        </div>

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
    </div>
  );
};
