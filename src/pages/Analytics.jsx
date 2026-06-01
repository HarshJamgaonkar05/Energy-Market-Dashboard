import { useState, useMemo } from "react";
import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { GitBranch, Layers, Grid3x3 } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { Band } from "../components/primitives/Band";
import { SourceTag } from "../components/primitives/SourceTag";
import { Sourced } from "../components/primitives/Sourced";
import { Heatmap } from "../components/panels/Heatmap";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { fmt, fmtSigned } from "../lib/format";
import { useLive } from "../lib/useLive";
import {
  byId, CRACKS, crackValue, crackVs, FWD_CURVES, genAround,
  CORR_LABELS, CORR_MATRIX,
} from "../data/mock";

// Fallbacks shaped exactly like the live endpoints, derived from the seeded mock.
const CRACKS_FALLBACK = CRACKS.map((c) => ({
  id: c.id, group: c.group, label: c.label, vs: crackVs(c), value: +crackValue(c).toFixed(2),
  legsLabel: c.legs.map((l) => `${l.c}×${byId(l.p).sym}`).join(" + ") + ` − ${c.crudeC ?? 1}×${crackVs(c)}`,
}));
const INTER_FALLBACK = [
  { lbl: "Brent – WTI",           v: byId("brent").val - byId("wti").val,  unit: "$/bbl", note: "Crude arb" },
  { lbl: "RBOB – Heating Oil",    v: byId("rbob").val - byId("ho").val,    unit: "$/gal", note: "Gas–Heat" },
  { lbl: "Heating Oil – Gas Oil", v: byId("ho").bbl - byId("gasoil").bbl,  unit: "$/bbl", note: "Distillate" },
  { lbl: "RBOB – Gas Oil",        v: byId("rbob").bbl - byId("gasoil").bbl, unit: "$/bbl", note: "Light prod" },
];
const CURVES_FALLBACK = { ...FWD_CURVES, inter: INTER_FALLBACK, modeled: false };

// ----------------------------------------------------------------------------
// Crack spreads — pick any of the cracks available across the five instruments
// ----------------------------------------------------------------------------
const CrackSpreads = () => {
  const [id, setId] = useState("321-wti");
  const { data: cracks, live } = useLive("/api/cracks", CRACKS_FALLBACK);

  const crack = cracks.find((c) => c.id === id) || cracks[0];
  const idx = cracks.findIndex((c) => c.id === id);
  const value = crack.value;

  const hist = useMemo(
    () => genAround(900 + idx, 60, value, Math.max(1, Math.abs(value) * 0.07)),
    [id, value]
  );

  const first = hist[0].v;
  const chg = value - first;
  const pct = (chg / Math.abs(first)) * 100;
  const lo = Math.min(...hist.map((p) => p.v));
  const hi = Math.max(...hist.map((p) => p.v));
  const avg = hist.reduce((s, p) => s + p.v, 0) / hist.length;
  const up = chg >= 0;

  const groups = ["Product Cracks", "Refining Margins"];

  return (
    <Card padding={false}>
      <div className="grid grid-cols-12">
        {/* Selector — every possible crack for the five instruments */}
        <div className="col-span-12 md:col-span-4 border-b md:border-b-0 md:border-r border-[#1c1d22] max-h-[360px] overflow-y-auto">
          {groups.map((g) => (
            <div key={g}>
              <div className="px-3 py-1.5 text-[9px] uppercase tracking-[0.16em] text-zinc-600 bg-[#0a0b0e] sticky top-0 flex items-center justify-between">
                {g}
                {g === groups[0] && <SourceTag live={live} source="derived" note="Crack value = product − crude, in $/bbl, from live Yahoo quotes." />}
              </div>
              {cracks.filter((c) => c.group === g).map((c) => {
                const v = c.value;
                const sel = c.id === id;
                return (
                  <button
                    key={c.id}
                    onClick={() => setId(c.id)}
                    className={`w-full flex items-center justify-between px-3 h-9 text-[11px] border-l-2 transition-colors ${
                      sel
                        ? "border-amber-500 bg-amber-500/[0.06] text-zinc-100"
                        : "border-transparent text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.02]"
                    }`}
                  >
                    <span className="flex items-center gap-1.5 truncate">
                      <span className="truncate">{c.label}</span>
                      <span className="text-[9px] font-mono text-zinc-600">vs {c.vs}</span>
                    </span>
                    <span className="font-mono text-[11px] text-zinc-300">
                      <Sourced source="derived" note={`${c.legsLabel} · $/bbl, from live Yahoo quotes`} align="end">{fmt(v)}</Sourced>
                    </span>
                  </button>
                );
              })}
            </div>
          ))}
        </div>

        {/* Selected crack chart + stats */}
        <div className="col-span-12 md:col-span-8 p-4">
          <div className="flex items-start justify-between mb-3">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-zinc-500">
                {crack.label} · vs {crack.vs}
              </div>
              <div className="flex items-baseline gap-2 mt-0.5">
                <span className="font-mono text-2xl text-zinc-100">
                  $<Sourced source="derived" note={`${crack.legsLabel} · live crack value ($/bbl) from Yahoo quotes`} align="start">{fmt(value)}</Sourced>
                </span>
                <span className="text-[10px] text-zinc-600">/bbl</span>
                <span className="font-mono text-[11px] text-zinc-600">
                  <Sourced source="modeled" note="No free intraday crack-history source for the 60-day change." align="start" /> · 60d
                </span>
              </div>
            </div>
            <span className="text-[9px] font-mono text-zinc-600 hidden sm:block">
              {crack.legsLabel}
            </span>
          </div>

          <div className="h-52">
            <ResponsiveContainer>
              <AreaChart data={hist} margin={{ top: 6, right: 12, bottom: 4, left: 0 }}>
                <defs>
                  <linearGradient id="crackFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid {...chartProps.grid} />
                <XAxis dataKey="t" {...chartProps.axis} />
                <YAxis {...chartProps.axis} width={40} domain={["auto", "auto"]} />
                <Tooltip content={<ChartTooltip unit=" $/bbl" />} />
                <ReferenceLine y={avg} stroke="#3a3b41" strokeDasharray="3 3" label={{ value: "avg", fill: "#71717a", fontSize: 9, position: "right" }} />
                <Area type="monotone" dataKey="v" name={crack.label} stroke="#f59e0b" strokeWidth={1.5} fill="url(#crackFill)" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-3 gap-3 mt-3 pt-3 border-t border-[#1c1d22]">
            {[
              { l: "60d Low", v: `$${fmt(lo)}` },
              { l: "60d Avg", v: `$${fmt(avg)}` },
              { l: "60d High", v: `$${fmt(hi)}` },
            ].map((s) => (
              <div key={s.l}>
                <div className="text-[9px] text-zinc-600 uppercase tracking-wider">{s.l}</div>
                <div className="font-mono text-[13px] text-zinc-200">
                  <Sourced source="modeled" note="60-day range is modeled around the live crack print" align="start">{s.v}</Sourced>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
// Futures spreads — forward curves, calendar spreads, inter-commodity spreads
// ----------------------------------------------------------------------------
const FuturesSpreads = () => {
  const [id, setId] = useState("brent");
  const { data: curves } = useLive("/api/curves", CURVES_FALLBACK, useLive.REFRESH.slow);
  const curveMap = { brent: curves.brent, wti: curves.wti, ho: curves.ho, rbob: curves.rbob, gasoil: curves.gasoil };
  const curve = curveMap[id] || CURVES_FALLBACK[id];
  const d = curve.data;
  const inter = curves.inter || INTER_FALLBACK;

  const cal = [
    { lbl: "M1–M2", v: d[0].v - d[1].v },
    { lbl: "M2–M3", v: d[1].v - d[2].v },
    { lbl: "M1–M6", v: d[0].v - d[5].v },
    { lbl: "M1–M12", v: d[0].v - d[11].v },
  ];
  const structure = d[0].v >= d[11].v ? "Backwardation" : "Contango";

  return (
    <div className="grid grid-cols-12 gap-3">
      {/* Forward curve */}
      <Card padding={false} className="col-span-12 lg:col-span-7">
        <div className="p-4 pb-2 flex items-center justify-between flex-wrap gap-2">
          <div>
            <div className="text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase inline-flex items-center gap-2">
              Forward Curve <SourceTag modeled label="Modeled curve" source="modeled" note="Front month anchored to the live Yahoo quote; term structure uses a curated slope (settlement curves are paywalled)." />
            </div>
            <div className="text-[10px] text-zinc-600 mt-0.5">{curve.label} · M1–M12 · {curve.unit}</div>
          </div>
          <div className="flex items-center gap-1">
            {Object.values(curveMap).filter(Boolean).map((c) => (
              <button
                key={c.id}
                onClick={() => setId(c.id)}
                className={`px-2 h-6 text-[10px] font-mono tracking-wider transition-colors ${
                  id === c.id
                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                    : "text-zinc-500 hover:text-zinc-200 border border-transparent"
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
        </div>
        <div className="h-60 px-2 pb-2">
          <ResponsiveContainer>
            <LineChart data={d} margin={{ top: 8, right: 18, bottom: 4, left: 0 }}>
              <CartesianGrid {...chartProps.grid} />
              <XAxis dataKey="m" {...chartProps.axis} />
              <YAxis {...chartProps.axis} width={48} domain={["auto", "auto"]} />
              <Tooltip content={<ChartTooltip source="modeled" />} />
              <Line type="monotone" dataKey="v" name={curve.label} stroke={curve.color} strokeWidth={1.6} dot={{ r: 2.5, fill: curve.color }} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="px-4 py-2.5 border-t border-[#1c1d22] flex items-center gap-2 text-[10px]">
          <span className="text-zinc-600 uppercase tracking-wider">Term structure</span>
          <span className={`font-mono ${structure === "Backwardation" ? "text-emerald-400" : "text-sky-400"}`}>{structure}</span>
        </div>
      </Card>

      {/* Spread tables */}
      <div className="col-span-12 lg:col-span-5 space-y-3">
        <Card padding={false}>
          <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">
            Calendar Spreads · {curve.label}
          </div>
          {cal.map((s) => (
            <div key={s.lbl} className="flex items-center justify-between px-4 py-2 border-b border-[#15161a] last:border-0">
              <span className="text-[11px] text-zinc-300 font-mono">{s.lbl}</span>
              <div className="flex items-center gap-2">
                <span className={`font-mono text-[11px] ${s.v >= 0 ? "text-emerald-400" : "text-sky-400"}`}>
                  <Sourced source="modeled" note="Calendar spread off the modeled forward curve" align="end">{fmtSigned(s.v, curve.unit === "$/gal" ? 4 : 3)}</Sourced>
                </span>
                <span className="text-[9px] uppercase tracking-wider text-zinc-600 w-16 text-right">{s.v >= 0 ? "Backwrd" : "Contango"}</span>
              </div>
            </div>
          ))}
        </Card>

        <Card padding={false}>
          <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">
            Inter-Commodity Spreads
          </div>
          {inter.map((s) => (
            <div key={s.lbl} className="flex items-center justify-between px-4 py-2 border-b border-[#15161a] last:border-0">
              <div className="min-w-0">
                <div className="text-[11px] text-zinc-300 truncate">{s.lbl}</div>
                <div className="text-[9px] text-zinc-600 uppercase tracking-wider">{s.note}</div>
              </div>
              <span className="font-mono text-[12px] text-zinc-100 whitespace-nowrap">
                <Sourced source="derived" note={`${s.lbl} · live inter-commodity spread from Yahoo quotes`} align="end">{fmtSigned(s.v, s.unit === "$/gal" ? 4 : 2)}</Sourced> <span className="text-[9px] text-zinc-600">{s.unit}</span>
              </span>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
};

// ----------------------------------------------------------------------------
// Correlation insight — strongest / weakest pair pulled from the matrix
// ----------------------------------------------------------------------------
const CorrelationInsight = () => {
  const { data } = useLive("/api/correlation", { labels: CORR_LABELS, matrix: CORR_MATRIX }, useLive.REFRESH.slow);
  const labels = data.labels || CORR_LABELS;
  const matrix = data.matrix || CORR_MATRIX;
  const pairs = [];
  for (let i = 0; i < labels.length; i++) {
    for (let j = i + 1; j < labels.length; j++) {
      pairs.push({ a: labels[i], b: labels[j], v: matrix[i][j] });
    }
  }
  const sorted = [...pairs].sort((x, y) => y.v - x.v);
  const strongest = sorted[0];
  const weakest = sorted[sorted.length - 1];

  return (
    <Card className="col-span-12 lg:col-span-4">
      <div className="text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase mb-3">Read</div>
      <div className="space-y-3">
        <div>
          <div className="text-[9px] text-zinc-600 uppercase tracking-wider">Tightest pair</div>
          <div className="flex items-baseline justify-between">
            <span className="text-[12px] text-zinc-200">{strongest.a} · {strongest.b}</span>
            <span className="font-mono text-[13px] text-emerald-400">
              <Sourced source="derived" note="Highest 30D return correlation in the matrix (Yahoo closes)" align="end">{strongest.v.toFixed(2)}</Sourced>
            </span>
          </div>
        </div>
        <div>
          <div className="text-[9px] text-zinc-600 uppercase tracking-wider">Loosest pair</div>
          <div className="flex items-baseline justify-between">
            <span className="text-[12px] text-zinc-200">{weakest.a} · {weakest.b}</span>
            <span className="font-mono text-[13px] text-amber-400">
              <Sourced source="derived" note="Lowest 30D return correlation in the matrix (Yahoo closes)" align="end">{weakest.v.toFixed(2)}</Sourced>
            </span>
          </div>
        </div>
        <p className="text-[10px] text-zinc-500 leading-relaxed pt-2 border-t border-[#1c1d22]">
          Crudes move near-lockstep; the two middle distillates (Heating Oil &amp; Gas Oil)
          are the most correlated product pair. RBOB is the loosest fit — a light,
          seasonally-driven product whose crack swings independently.
        </p>
        <div className="flex items-center gap-3 pt-1 text-[9px] uppercase tracking-wider">
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 bg-emerald-500/70" /> <span className="text-zinc-400">Positive</span></span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 bg-red-500/70" /> <span className="text-zinc-400">Negative</span></span>
        </div>
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
export const PageAnalytics = () => (
  <div className="space-y-3">
    <Band icon={Layers} title="Crack Spreads" sub="Refining margins across the five instruments" />
    <CrackSpreads />

    <Band icon={GitBranch} title="Futures Spreads" sub="Forward curves · calendar & inter-commodity" />
    <FuturesSpreads />

    <Band icon={Grid3x3} title="Correlation Matrix" sub="30D rolling · Brent · WTI · HO · RBOB · Gas Oil" />
    <div className="grid grid-cols-12 gap-3">
      <div className="col-span-12 lg:col-span-8">
        <Heatmap title={null} />
      </div>
      <CorrelationInsight />
    </div>
  </div>
);
