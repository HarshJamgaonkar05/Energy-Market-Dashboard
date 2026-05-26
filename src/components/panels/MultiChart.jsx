import { useState } from "react";
import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { MULTI_SERIES } from "../../data/mock";
import { chartProps, ChartTooltip } from "../../lib/chart-theme";

export const MultiChart = () => {
  const [series, setSeries] = useState({ Brent: true, WTI: true, HenryHub: true });
  const [range, setRange] = useState("3M");

  return (
    <Card padding={false} className="overflow-hidden">
      <div className="p-4 pb-2">
        <div className="flex items-center justify-between mb-1">
          <div>
            <h3 className="text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">
              Price Action — Normalized
            </h3>
            <p className="text-[10px] text-zinc-600 mt-0.5">Indexed to 100 at start of window</p>
          </div>
          <div className="flex items-center gap-1">
            {["1D", "1W", "1M", "3M", "6M", "1Y", "5Y"].map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={`px-2 h-6 text-[10px] font-mono tracking-wider transition-colors ${
                  range === r
                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                    : "text-zinc-500 hover:text-zinc-200 border border-transparent"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-3 mt-3">
          {Object.keys(series).map((k) => {
            const colors = { Brent: "#f59e0b", WTI: "#38bdf8", HenryHub: "#10b981" };
            const on = series[k];
            return (
              <button
                key={k}
                onClick={() => setSeries({ ...series, [k]: !series[k] })}
                className="flex items-center gap-1.5 text-[10px] tracking-wider uppercase"
              >
                <div
                  className="w-2.5 h-2.5 border"
                  style={{
                    background: on ? colors[k] : "transparent",
                    borderColor: colors[k],
                  }}
                />
                <span className={on ? "text-zinc-200" : "text-zinc-600"}>{k}</span>
              </button>
            );
          })}
        </div>
      </div>
      <div className="h-64 px-2 pb-2">
        <ResponsiveContainer>
          <LineChart data={MULTI_SERIES} margin={{ top: 8, right: 20, bottom: 6, left: 0 }}>
            <CartesianGrid {...chartProps.grid} />
            <XAxis dataKey="date" {...chartProps.axis} interval={10} />
            <YAxis {...chartProps.axis} domain={["auto", "auto"]} width={40} />
            <Tooltip content={<ChartTooltip />} />
            {series.Brent && (
              <Line type="monotone" dataKey="Brent" stroke="#f59e0b" strokeWidth={1.4} dot={false} isAnimationActive={false} />
            )}
            {series.WTI && (
              <Line type="monotone" dataKey="WTI" stroke="#38bdf8" strokeWidth={1.4} dot={false} isAnimationActive={false} />
            )}
            {series.HenryHub && (
              <Line type="monotone" dataKey="HenryHub" stroke="#10b981" strokeWidth={1.4} dot={false} isAnimationActive={false} />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
