import { useMemo } from "react";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { Badge } from "../components/primitives/Badge";
import { Delta } from "../components/primitives/Delta";
import { EconCalendar } from "../components/panels/EconCalendar";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { fmt } from "../lib/format";
import { HERO, genSeries, genSpark } from "../data/mock";
import { HeroCard } from "../components/HeroCard";
import { Heatmap } from "../components/panels/Heatmap";
import { NewsPanel } from "../components/panels/NewsPanel";

export const PageMacro = () => {
  const macroData = useMemo(() => Array.from({ length: 90 }, (_, i) => ({
    t: i,
    dxy: 104 + Math.sin(i / 9) * 1.4 + (Math.random() - 0.5) * 0.4,
    spx: 5200 + i * 4 + Math.sin(i / 5) * 60,
    vix: 14 + Math.cos(i / 7) * 3 + Math.random() * 1.5,
    yield10: 4.2 + Math.sin(i / 11) * 0.3,
  })), []);

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-6 gap-px bg-[#1c1d22]">
        {[
          { sym: "DXY", name: "Dollar Index", val: 104.21, chg: -0.34, pct: -0.33, spark: genSpark(61, 30, -1), unit: "" },
          { sym: "SPX", name: "S&P 500", val: 5284.21, chg: +18.4, pct: +0.35, spark: genSpark(62, 30, 1), unit: "" },
          { sym: "VIX", name: "Volatility", val: 14.32, chg: +0.18, pct: +1.27, spark: genSpark(63, 30, 1), unit: "" },
          { sym: "UST10Y", name: "10Y Yield", val: 4.218, chg: +0.024, pct: +0.57, spark: genSpark(64, 30, 1), unit: "%" },
          { sym: "GOLD", name: "Gold Spot", val: 2148.50, chg: +12.40, pct: +0.58, spark: genSpark(65, 30, 1), unit: "$/oz" },
          { sym: "COPPER", name: "Copper", val: 4.142, chg: +0.038, pct: +0.93, spark: genSpark(66, 30, 1), unit: "$/lb" },
        ].map((d) => <HeroCard key={d.sym} d={d} />)}
      </div>

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-8 space-y-3">
          <Card padding={false}>
            <div className="p-4 pb-2">
              <SectionTitle sub="DXY vs Brent · 90D">Dollar / Commodity Correlation</SectionTitle>
            </div>
            <div className="h-72 px-2 pb-2">
              <ResponsiveContainer>
                <ComposedChart data={macroData}>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis dataKey="t" {...chartProps.axis} />
                  <YAxis yAxisId="L" {...chartProps.axis} orientation="left" width={42} />
                  <YAxis yAxisId="R" {...chartProps.axis} orientation="right" width={42} />
                  <Tooltip content={<ChartTooltip />} />
                  <Line yAxisId="L" type="monotone" dataKey="dxy" stroke="#10b981" strokeWidth={1.4} dot={false} name="DXY" isAnimationActive={false} />
                  <Line yAxisId="R" type="monotone" dataKey="spx" stroke="#f59e0b" strokeWidth={1.4} dot={false} name="SPX" isAnimationActive={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-3">
            <Card padding={false}>
              <div className="p-4 pb-2"><SectionTitle sub="VIX">Risk Indicator</SectionTitle></div>
              <div className="h-44 px-2 pb-2">
                <ResponsiveContainer>
                  <AreaChart data={macroData}>
                    <defs>
                      <linearGradient id="vix" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#ef4444" stopOpacity={0.35} />
                        <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid {...chartProps.grid} />
                    <XAxis dataKey="t" {...chartProps.axis} />
                    <YAxis {...chartProps.axis} width={36} />
                    <Tooltip content={<ChartTooltip />} />
                    <Area type="monotone" dataKey="vix" stroke="#ef4444" strokeWidth={1.4} fill="url(#vix)" isAnimationActive={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </Card>
            <Card padding={false}>
              <div className="p-4 pb-2"><SectionTitle sub="10Y · UST">Yields</SectionTitle></div>
              <div className="h-44 px-2 pb-2">
                <ResponsiveContainer>
                  <LineChart data={macroData}>
                    <CartesianGrid {...chartProps.grid} />
                    <XAxis dataKey="t" {...chartProps.axis} />
                    <YAxis {...chartProps.axis} width={36} domain={["auto", "auto"]} />
                    <Tooltip content={<ChartTooltip unit="%" />} />
                    <Line type="monotone" dataKey="yield10" stroke="#38bdf8" strokeWidth={1.4} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          <EconCalendar />
        </div>

        <div className="col-span-12 lg:col-span-4 space-y-3">
          <Heatmap />
          <NewsPanel compact />
        </div>
      </div>
    </div>
  );
};
