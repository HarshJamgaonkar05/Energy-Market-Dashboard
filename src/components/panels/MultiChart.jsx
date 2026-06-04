import { useState, useRef, useEffect } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { ChevronDown, Check } from "lucide-react";
import { Card } from "../primitives/Card";
import { SourceTag } from "../primitives/SourceTag";
import { MULTI_SERIES } from "../../data/mock";
import { useLive } from "../../lib/useLive";
import { chartProps, ChartTooltip } from "../../lib/chart-theme";

const SERIES = [
  { k: "Brent", name: "Brent Crude", c: "#f59e0b" },
  { k: "WTI", name: "WTI Crude", c: "#38bdf8" },
  { k: "HO", name: "Heating Oil", c: "#10b981" },
  { k: "RBOB", name: "RBOB Gasoline", c: "#a78bfa" },
  { k: "Gasoil", name: "ICE Gas Oil", c: "#f472b6" },
];

// Dropdown options: compare all five, or isolate a single instrument.
const VIEWS = [
  { v: "all", label: "Compare All 5", c: null },
  ...SERIES.map((s) => ({ v: s.k, label: s.name, c: s.c })),
];

// Trailing window per range. The series is daily; the backend only carries
// ~90 days (3M) of history, so 3M shows the whole window.
const RANGE_POINTS = { "1W": 7, "1M": 30, "3M": Infinity };

export const MultiChart = () => {
  const [view, setView] = useState("all");
  const [on, setOn] = useState({ Brent: true, WTI: true, HO: true, RBOB: true, Gasoil: true });
  const [range, setRange] = useState("3M");
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);
  // Live normalized price action (Yahoo daily closes, indexed to 100).
  const { data: series, live } = useLive("/api/series", MULTI_SERIES, useLive.REFRESH.slow);

  // Close the dropdown when clicking outside of it.
  useEffect(() => {
    const onClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const current = VIEWS.find((x) => x.v === view);
  // "all" honours the per-series toggle chips; a single view isolates one line.
  const visible = view === "all" ? SERIES.filter((s) => on[s.k]) : SERIES.filter((s) => s.k === view);

  // Slice the series to the selected range, then re-index every line to 100 at
  // the first visible point so the chart stays true to "indexed to 100 at start
  // of window" regardless of which range is active.
  const n = RANGE_POINTS[range] ?? Infinity;
  const slice = series.slice(Math.max(0, series.length - n));
  const base = slice[0];
  const windowed = base
    ? slice.map((row) => {
        const out = { date: row.date };
        for (const { k } of SERIES) out[k] = base[k] ? +((row[k] / base[k]) * 100).toFixed(2) : 100;
        return out;
      })
    : slice;
  // Aim for ~8 date labels regardless of how many points are in view.
  const tickInterval = Math.max(0, Math.floor(windowed.length / 8));

  return (
    <Card padding={false} className="overflow-hidden">
      <div className="p-4 pb-2">
        <div className="flex items-center justify-between mb-1">
          <div>
            <h3 className="text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase inline-flex items-center gap-2">
              Price Action — Normalized
              <SourceTag live={live} source="yahoo" note="Yahoo Finance daily closes, indexed to 100 at the start of the window." />
            </h3>
            <p className="text-[10px] text-zinc-600 mt-0.5">Indexed to 100 at start of window</p>
          </div>
          <div className="flex items-center gap-1">
            {["1W", "1M", "3M"].map((r) => (
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

        <div className="flex items-center flex-wrap gap-3 mt-3">
          {/* Instrument selector — single instrument or compare all five */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setOpen((o) => !o)}
              className="flex items-center gap-1.5 h-6 px-2 bg-[#0e0f12] border border-[#1c1d22] hover:border-[#2a2b31] text-[10px] tracking-wider uppercase text-zinc-300 transition-colors"
            >
              {current.c && <span className="w-2 h-2" style={{ background: current.c }} />}
              {current.label}
              <ChevronDown size={11} className={`text-zinc-500 transition-transform ${open ? "rotate-180" : ""}`} />
            </button>
            {open && (
              <div className="absolute z-20 left-0 mt-1 w-44 bg-[#0a0b0e] border border-[#2a2b31] shadow-xl py-1">
                {VIEWS.map((item) => {
                  const sel = item.v === view;
                  return (
                    <button
                      key={item.v}
                      onClick={() => { setView(item.v); setOpen(false); }}
                      className={`w-full flex items-center gap-2 px-2.5 h-7 text-[10px] tracking-wider uppercase text-left transition-colors ${
                        sel ? "bg-amber-500/[0.08] text-amber-400" : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.03]"
                      }`}
                    >
                      {item.c
                        ? <span className="w-2 h-2 flex-shrink-0" style={{ background: item.c }} />
                        : <span className="w-2 h-2 flex-shrink-0 border border-zinc-600" />}
                      <span className="flex-1">{item.label}</span>
                      {sel && <Check size={11} className="flex-shrink-0" />}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Per-series toggles — only meaningful when comparing all five */}
          {view === "all" && (
            <div className="flex items-center flex-wrap gap-x-3 gap-y-1">
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
          )}
        </div>
      </div>
      <div className="h-64 px-2 pb-2">
        <ResponsiveContainer>
          <LineChart data={windowed} margin={{ top: 8, right: 20, bottom: 6, left: 0 }}>
            <CartesianGrid {...chartProps.grid} />
            <XAxis dataKey="date" {...chartProps.axis} interval={tickInterval} />
            <YAxis {...chartProps.axis} domain={["auto", "auto"]} width={40} />
            <Tooltip content={<ChartTooltip source="yahoo" />} />
            {visible.map(({ k, c }) => (
              <Line key={k} type="monotone" dataKey={k} stroke={c} strokeWidth={1.4} dot={false} isAnimationActive={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
