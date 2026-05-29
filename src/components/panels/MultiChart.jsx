import { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { Card } from "../primitives/Card";
import { MULTI_SERIES } from "../../data/mock";
import { chartProps, ChartTooltip } from "../../lib/chart-theme";

const SERIES = [
  { k: "Brent", c: "#f59e0b" },
  { k: "WTI", c: "#38bdf8" },
  { k: "HO", c: "#10b981" },
  { k: "RBOB", c: "#a78bfa" },
  { k: "Gasoil", c: "#f472b6" },
];

export const MultiChart = () => {
  const [on, setOn] = useState({ Brent: true, WTI: true, HO: true, RBOB: true, Gasoil: true });
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
            {["1W", "1M", "3M", "6M", "1Y"].map((r) => (
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
        <div className="flex items-center flex-wrap gap-x-3 gap-y-1 mt-3">
          {SERIES.map(({ k, c }) => (
            <button
              key={k}
              onClick={() => setOn({ ...on, [k]: !on[k] })}
              className="flex items-center gap-1.5 text-[10px] tracking-wider uppercase"
            >
              <div className="w-2.5 h-2.5 border" style={{ background: on[k] ? c : "transparent", borderColor: c }} />
              <span className={on[k] ? "text-zinc-200" : "text-zinc-600"}>{k}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="h-64 px-2 pb-2">
        <ResponsiveContainer>
          <LineChart data={MULTI_SERIES} margin={{ top: 8, right: 20, bottom: 6, left: 0 }}>
            <CartesianGrid {...chartProps.grid} />
            <XAxis dataKey="date" {...chartProps.axis} interval={10} />
            <YAxis {...chartProps.axis} domain={["auto", "auto"]} width={40} />
            <Tooltip content={<ChartTooltip />} />
            {SERIES.map(({ k, c }) =>
              on[k] ? (
                <Line key={k} type="monotone" dataKey={k} stroke={c} strokeWidth={1.4} dot={false} isAnimationActive={false} />
              ) : null
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
