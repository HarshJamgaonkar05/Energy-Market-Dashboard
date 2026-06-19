import { useState, useMemo } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
} from "recharts";
import { ResponsiveContainer } from "../lib/ResponsiveContainer";
import { Gauge, Layers, GitBranch, Activity, Target, ChevronDown } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { Band } from "../components/primitives/Band";
import { SourceTag } from "../components/primitives/SourceTag";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { useLive } from "../lib/useLive";
import { fmt, fmtSigned } from "../lib/format";

// ----------------------------------------------------------------------------
// Labels & colours
// ----------------------------------------------------------------------------
const SPREAD_LABELS = {
  brent_wti: "Brent–WTI", ho_gasoil: "HO–Gas Oil", gasoil_brent: "Gas Oil crack",
  ho_brent: "HO crack · Brent", ho_wti: "HO crack · WTI", rbob_ho: "RBOB–HO",
  crack_321_wti: "3:2:1 crack", wti_m1m2: "WTI M1–M2", wti_fly: "WTI M1·M2·M3 fly",
  brent_m1m2: "Brent M1–M2", gasoil_m1m2: "Gas Oil M1–M2", gasoil_fly: "Gas Oil fly",
};
// Inventory family sets the hue; volatility the shade (light = higher vol).
const REGIME_COLORS = {
  tight_lo: "#0369a1", tight_norm: "#0ea5e9", tight_hi: "#7dd3fc",
  bal_lo: "#6d28d9", bal_norm: "#a78bfa", bal_hi: "#ddd6fe",
  over_lo: "#b45309", over_norm: "#f59e0b", over_hi: "#fcd34d",
};
// Compact, readable labels for the timeline legend (vs the raw ids).
const REGIME_SHORT = {
  tight_lo: "Tight · Lo", tight_norm: "Tight · Norm", tight_hi: "Tight · Hi",
  bal_lo: "Bal · Lo", bal_norm: "Bal · Norm", bal_hi: "Bal · Hi",
  over_lo: "Over · Lo", over_norm: "Over · Norm", over_hi: "Over · Hi",
};
const DIM_STATE_COLOR = {
  Tight: "text-sky-400", Oversupplied: "text-amber-400", Balanced: "text-zinc-300",
  Backwardation: "text-emerald-400", Contango: "text-sky-400", Flat: "text-zinc-300",
  Low: "text-emerald-400", Normal: "text-zinc-300", High: "text-amber-400",
  Up: "text-emerald-400", Down: "text-red-400", Range: "text-zinc-300",
  Heating: "text-orange-400", Driving: "text-emerald-400", Shoulder: "text-zinc-300",
};
const DIM_ORDER = ["inventory", "structure", "volatility", "trend", "season"];
const DIM_TITLE = { inventory: "Inventory", structure: "Term structure", volatility: "Volatility", trend: "Trend", season: "Season" };
const FEATURE_LABELS = {
  crude_z: "Crude stock z", distillate_z: "Distillate z", crude_wow: "Crude WoW",
  distillate_wow: "Distillate WoW", refinery_util: "Refinery util", wti_rvol20: "WTI vol",
  wti_mom20: "Crude momentum", ho_mom20: "Distillate momentum",
  dxy: "Dollar (DXY)", vix: "VIX", ust10y: "10Y yield", month_sin: "Season (sin)", month_cos: "Season (cos)",
};
const CONF_COLOR = { high: "text-emerald-400", medium: "text-zinc-300", low: "text-zinc-600" };
const ROB_COLOR = { high: "text-emerald-400", medium: "text-amber-400", low: "text-zinc-600" };

// Minimal offline fallback so the page renders when the backend is down.
const FALLBACK_CURRENT = {
  asOf: "—",
  current: {
    label: "—", regimeId: "bal_hi", date: "—",
    states: {
      inventory: { state: "—", driver: "Backend offline — start the API to load the regime engine." },
      structure: { state: "—", driver: "" }, volatility: { state: "—", driver: "" },
      trend: { state: "—", driver: "" }, season: { state: "—", driver: "" },
    },
  },
  dimensions: {},
};

// ----------------------------------------------------------------------------
// Current regime hero — the live regime + the drivers behind each dimension
// ----------------------------------------------------------------------------
const CurrentRegime = () => {
  const { data, live, stale } = useLive("/api/regime/current", FALLBACK_CURRENT, useLive.REFRESH.slow);
  const cur = data.current || FALLBACK_CURRENT.current;
  const color = REGIME_COLORS[cur.regimeId] || "#a78bfa";

  return (
    <Card padding={false}>
      <div className="p-4 flex items-start justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-1 h-12 rounded-sm" style={{ background: color }} />
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-500">Current regime</div>
            <div className="text-2xl font-semibold text-zinc-100 leading-tight">{cur.label}</div>
            <div className="text-[10px] text-zinc-600 mt-0.5 font-mono">as of {data.asOf}</div>
          </div>
        </div>
        <SourceTag live={live && !stale} stale={stale} source="regime"
          note="Rule-based regime from inventory, term structure, volatility, trend & season — computed offline from the historical dataset + EIA." />
      </div>

      {/* Dimension chips — each shows the state and the exact driver that set it */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-px bg-[#1c1d22] border-t border-[#1c1d22]">
        {DIM_ORDER.map((dim) => {
          const s = cur.states?.[dim] || {};
          return (
            <div key={dim} className="bg-[#0e0f12] p-3">
              <div className="text-[9px] uppercase tracking-[0.14em] text-zinc-600">{DIM_TITLE[dim]}</div>
              <div className={`text-[15px] font-semibold mt-0.5 ${DIM_STATE_COLOR[s.state] || "text-zinc-200"}`}>
                {s.state ?? "—"}
              </div>
              <div className="text-[10px] text-zinc-500 leading-snug mt-1 min-h-[28px]">{s.driver}</div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
// Regime explorer — pick a regime; see its size/persistence + spread behaviour
// ----------------------------------------------------------------------------
const RegimeExplorer = () => {
  const { data: cat } = useLive("/api/regime/catalog", { catalog: [] }, useLive.REFRESH.slow);
  const { data: hist } = useLive("/api/regime/history", { transitions: {} }, useLive.REFRESH.slow);
  const { data: curData } = useLive("/api/regime/current", FALLBACK_CURRENT, useLive.REFRESH.slow);
  const catalog = cat.catalog || [];
  const currentId = curData.current?.regimeId;

  const [sel, setSel] = useState(null);
  const activeId = sel || currentId || catalog[0]?.regimeId;
  const regime = catalog.find((c) => c.regimeId === activeId);
  const maxN = Math.max(1, ...catalog.map((c) => c.n));
  const trans = (hist.transitions || {})[activeId] || {};
  const nextRegimes = Object.entries(trans).filter(([k]) => k !== activeId).slice(0, 3);

  // Backend not built yet — one clear message instead of a half-empty two-column layout.
  if (!catalog.length) {
    return (
      <Card>
        <div className="py-12 text-center text-[12px] text-zinc-500">
          Regime engine not built yet — run <code className="text-zinc-300">python analytics/run.py</code> to populate the regime catalog.
        </div>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-12 gap-3">
      {/* Catalog list */}
      <Card padding={false} className="col-span-12 lg:col-span-4">
        <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase flex items-center justify-between">
          Regime catalog
          <span className="text-[9px] text-zinc-600 normal-case tracking-normal">Inventory × Volatility · 2021→now</span>
        </div>
        <div className="max-h-[420px] overflow-y-auto">
          {catalog.map((c) => {
            const on = c.regimeId === activeId;
            return (
              <button key={c.regimeId} onClick={() => setSel(c.regimeId)}
                className={`w-full text-left px-3 py-2 border-l-2 transition-colors ${on ? "bg-white/[0.03]" : "border-transparent hover:bg-white/[0.02]"}`}
                style={{ borderLeftColor: on ? REGIME_COLORS[c.regimeId] : "transparent" }}>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-[11px] text-zinc-200">
                    <span className="w-2 h-2 rounded-sm flex-shrink-0" style={{ background: REGIME_COLORS[c.regimeId] }} />
                    {c.label}
                    {c.regimeId === currentId && <span className="text-[8px] uppercase tracking-wider text-emerald-400 border border-emerald-500/30 px-1">now</span>}
                  </span>
                  <span className="font-mono text-[10px] text-zinc-500">{c.n}d</span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 h-1 bg-[#1c1d22] overflow-hidden">
                    <div className="h-full" style={{ width: `${(c.n / maxN) * 100}%`, background: REGIME_COLORS[c.regimeId], opacity: 0.6 }} />
                  </div>
                  <span className="text-[9px] text-zinc-600 font-mono w-8 text-right">{Math.round(c.share * 100)}%</span>
                  {!c.sufficient && <span className="text-[8px] uppercase tracking-wider text-amber-500/80" title="Few observations — treat stats as indicative">thin</span>}
                </div>
              </button>
            );
          })}
          {!catalog.length && <div className="p-4 text-[11px] text-zinc-600">Regime engine not built yet — run <code className="text-zinc-400">python analytics/run.py</code>.</div>}
        </div>
      </Card>

      {/* Selected regime — persistence + how each spread behaves here */}
      <Card padding={false} className="col-span-12 lg:col-span-8">
        {regime ? (
          <>
            <div className="px-4 py-2.5 border-b border-[#1c1d22] flex items-center justify-between flex-wrap gap-2">
              <span className="text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-sm" style={{ background: REGIME_COLORS[regime.regimeId] }} />
                {regime.label}
              </span>
              <span className="text-[10px] text-zinc-500 font-mono flex items-center gap-3">
                <span>{regime.n} days</span>
                <span>{regime.episodes} episodes</span>
                <span>~{regime.avgDurationDays}d avg</span>
              </span>
            </div>

            {/* Transition hint */}
            {nextRegimes.length > 0 && (
              <div className="px-4 py-2 border-b border-[#15161a] text-[10px] text-zinc-500 flex items-center gap-2 flex-wrap">
                <span className="uppercase tracking-wider text-zinc-600">Most likely to shift to</span>
                {nextRegimes.map(([k, p]) => {
                  const lbl = catalog.find((c) => c.regimeId === k)?.label || k;
                  return <span key={k} className="font-mono text-zinc-300">{lbl} <span className="text-zinc-600">{Math.round(p * 100)}%</span></span>;
                })}
              </div>
            )}

            {/* Spread behaviour table */}
            <div className="overflow-x-auto">
              <table className="w-full text-[11px]">
                <thead>
                  <tr className="text-[9px] uppercase tracking-wider text-zinc-600 border-b border-[#1c1d22]">
                    <th className="text-left font-medium px-4 py-2">Spread / Structure</th>
                    <th className="text-right font-medium px-2">Regime avg</th>
                    <th className="text-right font-medium px-2">P10–P90</th>
                    <th className="text-right font-medium px-2">Current</th>
                    <th className="text-right font-medium px-2">z</th>
                    <th className="text-right font-medium px-4">½-life</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(regime.spreads || {}).map(([sp, st]) => {
                    const hot = st.z != null && Math.abs(st.z) >= 1.5;
                    return (
                      <tr key={sp} className="border-b border-[#15161a] last:border-0 hover:bg-white/[0.015]">
                        <td className="px-4 py-1.5 text-zinc-300">{SPREAD_LABELS[sp] || sp}</td>
                        <td className="px-2 text-right font-mono text-zinc-400">{fmt(st.mean)}</td>
                        <td className="px-2 text-right font-mono text-zinc-600">{fmt(st.p10)} … {fmt(st.p90)}</td>
                        <td className="px-2 text-right font-mono text-zinc-200">{fmt(st.current)}</td>
                        <td className={`px-2 text-right font-mono ${hot ? "text-amber-400" : "text-zinc-500"}`}>{fmtSigned(st.z, 1)}σ</td>
                        <td className="px-4 text-right font-mono text-zinc-500">{st.halfLifeDays != null ? `${st.halfLifeDays}d` : "—"}</td>
                      </tr>
                    );
                  })}
                  {!regime.spreads && (
                    <tr><td colSpan={6} className="px-4 py-3 text-[10px] text-zinc-600">Per-spread stats for non-current regimes load from the catalog.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="px-4 py-2 text-[9px] text-zinc-600 leading-snug border-t border-[#1c1d22]">
              z = standardised distance of the latest value from this regime's historical mean. |z| ≥ 1.5σ highlighted —
              a candidate dislocation given the regime. ½-life = AR(1) mean-reversion speed.
            </div>
          </>
        ) : (
          <div className="p-6 text-[11px] text-zinc-600">Select a regime to see its spread behaviour.</div>
        )}
      </Card>
    </div>
  );
};

// ----------------------------------------------------------------------------
// Regime history strip — the timeline of regimes, compressed into runs
// ----------------------------------------------------------------------------
const RegimeHistoryStrip = () => {
  const { data } = useLive("/api/regime/history", { history: [] }, useLive.REFRESH.slow);
  const history = data.history || [];

  // Collapse the daily sequence into consecutive runs for efficient rendering.
  const segments = useMemo(() => {
    const segs = [];
    for (const row of history) {
      const last = segs[segs.length - 1];
      if (last && last.regimeId === row.regimeId) { last.len += 1; last.end = row.date; }
      else segs.push({ regimeId: row.regimeId, label: row.regimeLabel, start: row.date, end: row.date, len: 1 });
    }
    return segs;
  }, [history]);

  const [hover, setHover] = useState(null);

  if (!history.length) return null;
  const first = history[0]?.date, last = history[history.length - 1]?.date;

  return (
    <Card padding={false}>
      <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">
        Regime timeline
      </div>
      <div className="p-4">
        {/* Hover readout — updates to the segment under the cursor */}
        <div className="flex items-center justify-between mb-2 h-5">
          {hover ? (
            <span className="flex items-center gap-2 text-[11px] min-w-0">
              <span className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: REGIME_COLORS[hover.regimeId] || "#3f3f46" }} />
              <span className="text-zinc-200 font-medium truncate">{hover.label}</span>
              <span className="font-mono text-zinc-500 whitespace-nowrap">{hover.start} → {hover.end}</span>
            </span>
          ) : (
            <span className="text-[10px] text-zinc-600">Hover a segment for its regime, dates &amp; duration</span>
          )}
          {hover && <span className="font-mono text-[11px] text-zinc-400 whitespace-nowrap ml-2">{hover.len}d</span>}
        </div>

        <div className="flex h-8 w-full overflow-hidden rounded-sm" onMouseLeave={() => setHover(null)}>
          {segments.map((s, i) => (
            <div key={i}
              onMouseEnter={() => setHover(s)}
              title={`${s.label} · ${s.start} → ${s.end} (${s.len}d)`}
              style={{ flexGrow: s.len, background: REGIME_COLORS[s.regimeId] || "#3f3f46" }}
              className={`h-full first:rounded-l-sm last:rounded-r-sm cursor-pointer transition-opacity duration-150 ${
                hover && hover !== s ? "opacity-35" : "opacity-100"
              }`}
            />
          ))}
        </div>
        <div className="flex justify-between mt-1.5 text-[9px] font-mono text-zinc-600">
          <span>{first}</span><span>{last}</span>
        </div>
        {/* Legend */}
        <div className="flex flex-wrap gap-x-3 gap-y-1 mt-3">
          {Object.entries(REGIME_COLORS).map(([id, c]) => (
            <span key={id} className="flex items-center gap-1 text-[9px] text-zinc-500">
              <span className="w-2 h-2 rounded-sm" style={{ background: c }} />{REGIME_SHORT[id] || id}
            </span>
          ))}
        </div>
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
// Ranked analytical opportunities — spreads dislocated vs regime + fair value
// ----------------------------------------------------------------------------
const SignalsTable = () => {
  const { data, live, stale } = useLive("/api/signals", { opportunities: [], regime: {} }, useLive.REFRESH.slow);
  const opps = data.opportunities || [];
  const [open, setOpen] = useState(null);
  const maxScore = Math.max(0.001, ...opps.map((o) => o.score));

  return (
    <Card padding={false}>
      <div className="px-4 py-2.5 border-b border-[#1c1d22] flex items-center justify-between">
        <span className="text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">
          Ranked opportunities
          <span className="ml-2 text-[9px] text-zinc-600 normal-case tracking-normal">under {data.regime?.label ?? "—"}</span>
        </span>
        <SourceTag live={live && !stale} stale={stale} source="regime"
          note="Spreads ranked by dislocation (regime z + regression residual) × model confidence × robustness." />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <thead>
            <tr className="text-[9px] uppercase tracking-wider text-zinc-600 border-b border-[#1c1d22]">
              <th className="text-left font-medium px-4 py-2">Spread</th>
              <th className="text-left font-medium px-2">Bias</th>
              <th className="text-right font-medium px-2">Current</th>
              <th className="text-right font-medium px-2">Fair value</th>
              <th className="text-right font-medium px-2">z</th>
              <th className="text-right font-medium px-2">Conf.</th>
              <th className="text-right font-medium px-2">Robust</th>
              <th className="text-left font-medium px-3 w-28">Score</th>
              <th className="w-6" />
            </tr>
          </thead>
          <tbody>
            {opps.map((o) => {
              const on = open === o.spread;
              return [
                <tr key={o.spread} onClick={() => setOpen(on ? null : o.spread)}
                  className="border-b border-[#15161a] hover:bg-white/[0.02] cursor-pointer">
                  <td className="px-4 py-2 text-zinc-200">{o.label}</td>
                  <td className="px-2"><span className={`text-[10px] font-semibold uppercase ${o.direction === "rich" ? "text-amber-400" : "text-sky-400"}`}>{o.direction}</span></td>
                  <td className="px-2 text-right font-mono text-zinc-200">{fmt(o.current)}</td>
                  <td className="px-2 text-right font-mono text-zinc-500">{fmt(o.fairValue)}</td>
                  <td className="px-2 text-right font-mono text-zinc-300">{fmtSigned(o.combinedZ, 1)}σ</td>
                  <td className={`px-2 text-right font-mono ${CONF_COLOR[o.confidenceLabel]}`}>{o.confidenceLabel}</td>
                  <td className={`px-2 text-right font-mono ${ROB_COLOR[o.robustness]}`}>{o.robustness}</td>
                  <td className="px-3">
                    <div className="h-1.5 bg-[#1c1d22] overflow-hidden">
                      <div className="h-full bg-amber-500/70" style={{ width: `${(o.score / maxScore) * 100}%` }} />
                    </div>
                  </td>
                  <td className="px-1 text-zinc-600"><ChevronDown size={12} className={`transition-transform ${on ? "rotate-180" : ""}`} /></td>
                </tr>,
                on && (
                  <tr key={o.spread + "-d"} className="bg-[#0a0b0e] border-b border-[#15161a]">
                    <td colSpan={9} className="px-4 py-2.5">
                      <p className="text-[11px] text-zinc-400 leading-relaxed">{o.rationale}</p>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-[9px] text-zinc-600 uppercase tracking-wider">
                        <span>regime z <span className="text-zinc-400 font-mono normal-case">{fmtSigned(o.regimeZ, 1)}σ</span></span>
                        <span>residual z <span className="text-zinc-400 font-mono normal-case">{fmtSigned(o.residualZ, 1)}σ</span></span>
                        <span>model OOS R² <span className="text-zinc-400 font-mono normal-case">{fmt(o.r2_oos)}</span></span>
                        <span>½-life <span className="text-zinc-400 font-mono normal-case">{o.halfLifeDays ?? "—"}d</span></span>
                        {o.backtest && (
                          <span>backtest <span className="text-emerald-400 font-mono normal-case">{Math.round(o.backtest.hitRate * 100)}% revert</span>
                            <span className="text-zinc-600 normal-case"> ({o.backtest.edge >= 0 ? "+" : ""}{Math.round(o.backtest.edge * 100)}pp edge, n={o.backtest.nSignals})</span>
                          </span>
                        )}
                        <span>drivers <span className="text-zinc-400 normal-case">{(o.drivers || []).map((d) => FEATURE_LABELS[d] || d).join(", ")}</span></span>
                      </div>
                    </td>
                  </tr>
                ),
              ];
            })}
            {!opps.length && <tr><td colSpan={9} className="px-4 py-3 text-[10px] text-zinc-600">No signals — run <code className="text-zinc-400">python analytics/run.py</code> to build the model artifacts.</td></tr>}
          </tbody>
        </table>
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
// Fair-value regression panel — actual vs model, drivers, stability, by-regime
// ----------------------------------------------------------------------------
const RegressionPanel = () => {
  const { data: listData } = useLive("/api/regression", { list: [] }, useLive.REFRESH.slow);
  const list = listData.list || [];
  const [sel, setSel] = useState(null);
  const active = sel || list[0]?.spread;
  const { data: model } = useLive(active ? `/api/regression/${active}` : "/api/regression", {}, useLive.REFRESH.slow);

  const series = model.fairValue || [];
  const coef = model.global?.coef || {};
  const coefRows = Object.entries(coef).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 8);
  const maxCoef = Math.max(0.001, ...coefRows.map(([, v]) => Math.abs(v)));
  const byRegime = Object.entries(model.byRegime || {}).sort((a, b) => (b[1].r2 ?? 0) - (a[1].r2 ?? 0));
  const roll = model.rolling;
  const topDriver = model.global?.topDrivers?.[0];
  const rollData = roll && topDriver ? roll.dates.map((d, i) => ({ date: d, beta: roll.betas[topDriver]?.[i] })) : [];

  return (
    <div className="space-y-3">
      {/* Spread selector */}
      <div className="flex items-center gap-1 flex-wrap">
        {list.map((m) => (
          <button key={m.spread} onClick={() => setSel(m.spread)}
            className={`px-2 h-6 text-[10px] font-mono tracking-wider transition-colors border ${
              active === m.spread ? "bg-amber-500/10 text-amber-400 border-amber-500/30" : "text-zinc-500 hover:text-zinc-200 border-transparent"}`}>
            {m.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-12 gap-3">
        {/* Actual vs fair value */}
        <Card padding={false} className="col-span-12 lg:col-span-8">
          <div className="px-4 py-2.5 border-b border-[#1c1d22] flex items-center justify-between flex-wrap gap-2">
            <span className="text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">
              {model.label || active} · actual vs fair value
            </span>
            <span className="text-[10px] font-mono text-zinc-500 flex items-center gap-3">
              <span>R²<sub>in</sub> {fmt(model.global?.r2_in)}</span>
              <span className={model.global?.r2_oos >= 0.2 ? "text-emerald-400" : model.global?.r2_oos >= 0 ? "text-zinc-300" : "text-red-400"}>
                R²<sub>oos</sub> {fmt(model.global?.r2_oos)}
              </span>
            </span>
          </div>
          <div className="h-64 px-2 py-2">
            <ResponsiveContainer>
              <LineChart data={series} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
                <CartesianGrid {...chartProps.grid} />
                <XAxis dataKey="date" {...chartProps.axis} minTickGap={48} tickFormatter={(d) => (d || "").slice(0, 7)} />
                <YAxis {...chartProps.axis} width={46} domain={["auto", "auto"]} />
                <Tooltip content={<ChartTooltip source="regime" />} />
                <Line type="monotone" dataKey="actual" name="Actual" stroke="#e4e4e7" strokeWidth={1.3} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="fv" name="Fair value" stroke="#f59e0b" strokeWidth={1.3} strokeDasharray="4 2" dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="px-4 py-2 border-t border-[#1c1d22] text-[9px] text-zinc-600 leading-snug">
            Fair value is walk-forward (expanding window, refit every 21d) — each point uses only prior data, so the gap
            to actual is an honest residual. R²<sub>oos</sub> is the out-of-sample fit of that walk-forward line.
          </div>
        </Card>

        {/* Driver importance */}
        <Card padding={false} className="col-span-12 lg:col-span-4">
          <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">
            Drivers <span className="text-[9px] text-zinc-600 normal-case tracking-normal">standardized β</span>
          </div>
          <div className="p-3 space-y-1.5">
            {coefRows.map(([f, v]) => (
              <div key={f} className="flex items-center gap-2">
                <span className="text-[10px] text-zinc-400 w-24 truncate">{FEATURE_LABELS[f] || f}</span>
                <div className="flex-1 h-2 bg-[#0a0b0e] relative overflow-hidden">
                  <div className={`h-full absolute top-0 ${v >= 0 ? "left-1/2 bg-emerald-500/70" : "right-1/2 bg-red-500/70"}`}
                    style={{ width: `${(Math.abs(v) / maxCoef) * 50}%` }} />
                  <div className="absolute left-1/2 top-0 bottom-0 w-px bg-[#2a2b31]" />
                </div>
                <span className="font-mono text-[10px] text-zinc-400 w-10 text-right">{fmtSigned(v, 2)}</span>
              </div>
            ))}
            {model.lasso?.selected && (
              <div className="pt-2 mt-1 border-t border-[#1c1d22] text-[9px] text-zinc-600 leading-snug">
                Lasso keeps {model.lasso.selected.length} of {(model.features || []).length} drivers:
                <span className="text-zinc-500"> {model.lasso.selected.map((f) => FEATURE_LABELS[f] || f).join(", ")}</span>
              </div>
            )}
          </div>
        </Card>

        {/* Rolling beta — relationship stability */}
        <Card padding={false} className="col-span-12 lg:col-span-7">
          <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">
            Rolling β · {FEATURE_LABELS[topDriver] || topDriver} <span className="text-[9px] text-zinc-600 normal-case tracking-normal">{roll?.window}d window</span>
          </div>
          <div className="h-40 px-2 py-2">
            {rollData.length ? (
              <ResponsiveContainer>
                <LineChart data={rollData} margin={{ top: 6, right: 16, bottom: 4, left: 0 }}>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis dataKey="date" {...chartProps.axis} minTickGap={48} tickFormatter={(d) => (d || "").slice(0, 7)} />
                  <YAxis {...chartProps.axis} width={42} domain={["auto", "auto"]} />
                  <Tooltip content={<ChartTooltip source="regime" />} />
                  <ReferenceLine y={0} stroke="#3a3b41" />
                  <Line type="monotone" dataKey="beta" name="β" stroke="#a78bfa" strokeWidth={1.3} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-[10px] text-zinc-600">Insufficient data for a rolling fit.</div>
            )}
          </div>
        </Card>

        {/* Fit by regime — compares model performance across conditions */}
        <Card padding={false} className="col-span-12 lg:col-span-5">
          <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">
            Fit by regime <span className="text-[9px] text-zinc-600 normal-case tracking-normal">in-sample R²</span>
          </div>
          <div className="p-3 space-y-1.5 max-h-40 overflow-y-auto">
            {byRegime.map(([rid, r]) => (
              <div key={rid} className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-sm flex-shrink-0" style={{ background: REGIME_COLORS[rid] }} />
                <span className="text-[10px] text-zinc-400 w-20 truncate">{REGIME_SHORT[rid] || rid}</span>
                <div className="flex-1 h-2 bg-[#0a0b0e] overflow-hidden">
                  <div className="h-full bg-sky-500/60" style={{ width: `${Math.max(0, (r.r2 ?? 0)) * 100}%` }} />
                </div>
                <span className="font-mono text-[10px] text-zinc-400 w-8 text-right">{fmt(r.r2)}</span>
                <span className="font-mono text-[9px] text-zinc-600 w-8 text-right">{r.n}d</span>
              </div>
            ))}
            {!byRegime.length && <div className="text-[10px] text-zinc-600">No regime had enough observations for a separate fit.</div>}
          </div>
        </Card>
      </div>
    </div>
  );
};

// ----------------------------------------------------------------------------
export const PageRegime = () => (
  <div className="space-y-3">
    <Band icon={Gauge} title="Current Regime" sub="Live classification across five market dimensions" />
    <CurrentRegime />

    <Band icon={Target} title="Analytical Opportunities" sub="Spreads & butterflies dislocated vs their regime norm and fair value" />
    <SignalsTable />

    <Band icon={GitBranch} title="Fair-Value Models" sub="Regression of each spread on fundamental & macro drivers" />
    <RegressionPanel />

    <Band icon={Layers} title="Regime Explorer" sub="Historical behaviour of spreads & butterflies by regime" />
    <RegimeExplorer />

    <Band icon={Activity} title="Regime Timeline" sub="2021→present · Inventory × Volatility" />
    <RegimeHistoryStrip />
  </div>
);
