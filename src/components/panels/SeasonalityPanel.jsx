import { useState } from "react";
import { ComposedChart, Bar, Line, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SourceTag } from "../primitives/SourceTag";
import { Sourced } from "../primitives/Sourced";
import { chartProps, ChartTooltip } from "../../lib/chart-theme";
import { fmtSigned } from "../../lib/format";
import { useLive } from "../../lib/useLive";

// Seasonality — typical behaviour by calendar month from ~10y of Yahoo monthly
// closes. PRICE series show average month-over-month return + a hit rate and a
// cumulative "typical path"; CRACK series show the average crack level ($/bbl)
// per month, with the latest value vs its monthly norm. See
// server/compute/seasonality.js.
const M = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const nowM = new Date().getMonth();
const mkPrice = (id, label, amp, phase) => ({
  id, kind: "price", label, unit: "%", currentMonth: nowM, years: 9,
  months: M.map((m, i) => {
    const avgRet = +(Math.sin((i / 12) * 2 * Math.PI + phase) * amp).toFixed(2);
    return { m, avgRet, hit: Math.max(20, Math.min(80, 50 + Math.round(avgRet * 6))), n: 9 };
  }),
});
const mkCrack = (id, label, base, amp) => ({
  id, kind: "crack", label, unit: "$/bbl", currentMonth: nowM, years: 9, current: +(base + amp * 0.4).toFixed(2),
  months: M.map((m, i) => ({ m, avg: +(base + Math.sin((i / 12) * 2 * Math.PI - 1.6) * amp).toFixed(2), n: 9 })),
});
const FALLBACK = {
  series: [
    mkPrice("WTI", "WTI Crude", 3.2, -1.2),
    mkPrice("BRENT", "Brent Crude", 2.9, -1.2),
    mkPrice("RBOB", "RBOB Gasoline", 3.0, -1.6),
    mkPrice("HO", "Heating Oil", 2.4, -2.4),
    mkCrack("RBOB-WTI", "RBOB Crack", 22, 8),
    mkCrack("HO-WTI", "Heating Oil Crack", 26, 6),
    mkCrack("321-WTI", "3:2:1 Crack", 24, 6),
  ],
};

export const SeasonalityPanel = () => {
  const { data, live } = useLive("/api/seasonality", FALLBACK, useLive.REFRESH.slow);
  const series = data.series?.length ? data.series : FALLBACK.series;
  const [id, setId] = useState("321-WTI");
  const s = series.find((x) => x.id === id) || series[0];
  const isPrice = s.kind === "price";
  const cur = s.currentMonth ?? nowM;

  // Build chart rows; compute the cumulative seasonal path for price series.
  const chart = s.months.map((mm, i) => ({ m: mm.m, v: isPrice ? mm.avgRet : mm.avg, hit: mm.hit, cur: i === cur }));
  if (isPrice) {
    let p = 100;
    chart.forEach((c) => { p *= 1 + c.v / 100; c.path = +p.toFixed(1); });
  }
  const cm = s.months[cur] || s.months[0];
  const norm = isPrice ? null : cm.avg;
  const vsNorm = !isPrice && s.current != null ? +(s.current - norm).toFixed(2) : null;

  const priceSeries = series.filter((x) => x.kind === "price");
  const crackSeries = series.filter((x) => x.kind === "crack");

  const Btn = ({ x }) => (
    <button
      onClick={() => setId(x.id)}
      className={`px-2 h-6 text-[10px] font-mono tracking-wider transition-colors ${
        id === x.id ? "bg-amber-500/10 text-amber-400 border border-amber-500/30" : "text-zinc-500 border border-transparent hover:text-zinc-200"
      }`}
    >
      {x.label}
    </button>
  );

  return (
    <Card padding={false}>
      <div className="p-4 pb-2 flex items-start justify-between flex-wrap gap-2">
        <SectionTitle sub={`${s.years}-yr average by calendar month · ${isPrice ? "avg monthly return" : "avg crack ($/bbl)"}`} action={<SourceTag live={live} source="yahoo" note="Average by calendar month over ~10y of Yahoo monthly closes (cracks: product − crude, $/bbl)." />}>Seasonality</SectionTitle>
        <div className="flex flex-col items-end gap-1">
          <div className="flex items-center gap-1 flex-wrap justify-end">{priceSeries.map((x) => <Btn key={x.id} x={x} />)}</div>
          <div className="flex items-center gap-1 flex-wrap justify-end">{crackSeries.map((x) => <Btn key={x.id} x={x} />)}</div>
        </div>
      </div>

      {/* Current-month readout */}
      <div className="px-4 pb-2 flex items-baseline gap-3 flex-wrap">
        <span className="text-[10px] uppercase tracking-wider text-zinc-500">{cm.m} (now)</span>
        {isPrice ? (
          <span className="font-mono text-sm">
            <span className={cm.avgRet >= 0 ? "text-emerald-400" : "text-red-400"}>
              <Sourced source="derived" note={`Average ${cm.m} return over ${s.years} years`} align="start">{fmtSigned(cm.avgRet)}%</Sourced>
            </span>
            <span className="text-zinc-600 text-[11px] ml-2">{cm.hit}% positive</span>
          </span>
        ) : (
          <span className="font-mono text-sm text-zinc-200">
            <Sourced source="derived" note={`Latest ${s.label} value`} align="start">${s.current}</Sourced>
            <span className="text-zinc-600 text-[11px] ml-2">vs {cm.m} norm ${norm}</span>
            {vsNorm != null && <span className={`text-[11px] ml-2 ${vsNorm >= 0 ? "text-emerald-400" : "text-red-400"}`}>{fmtSigned(vsNorm)}</span>}
          </span>
        )}
      </div>

      <div className="h-56 px-2 pb-3">
        <ResponsiveContainer>
          <ComposedChart data={chart} margin={{ top: 6, right: isPrice ? 18 : 12, bottom: 0, left: 0 }}>
            <CartesianGrid {...chartProps.grid} />
            <XAxis dataKey="m" {...chartProps.axis} />
            <YAxis yAxisId="L" {...chartProps.axis} width={40} domain={["auto", "auto"]} />
            {isPrice && <YAxis yAxisId="R" orientation="right" {...chartProps.axis} width={40} domain={["auto", "auto"]} />}
            <Tooltip content={<ChartTooltip unit={isPrice ? " %" : " $/bbl"} source="derived" />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
            <ReferenceLine yAxisId="L" y={0} stroke="#3a3b41" />
            <Bar yAxisId="L" dataKey="v" name={isPrice ? "Avg return" : "Avg crack"} maxBarSize={26} isAnimationActive={false}>
              {chart.map((c, i) => {
                const base = isPrice ? (c.v >= 0 ? "#10b981" : "#ef4444") : "#38bdf8";
                return <Cell key={i} fill={c.cur ? "#f59e0b" : base} fillOpacity={c.cur ? 0.95 : 0.55} />;
              })}
            </Bar>
            {isPrice && <Line yAxisId="R" type="monotone" dataKey="path" name="Typical path" stroke="#a78bfa" strokeWidth={1.4} dot={false} isAnimationActive={false} />}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
