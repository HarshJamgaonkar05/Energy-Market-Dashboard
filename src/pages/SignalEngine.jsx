import { useState } from "react";
import { AreaChart, Area, ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from "recharts";
import { ResponsiveContainer } from "../lib/ResponsiveContainer";
import { TrendingUp, Layers, ListChecks, ChevronDown, Circle, ArrowUpRight, ArrowDownRight, Download, Award, Shield, Activity } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { Band } from "../components/primitives/Band";
import { SourceTag } from "../components/primitives/SourceTag";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { useLive } from "../lib/useLive";
import { fmt, fmtSigned } from "../lib/format";

const usdK = (n) => {
  if (n == null || Number.isNaN(Number(n))) return "—";
  const a = Math.abs(n), s = n < 0 ? "-" : "";
  if (a >= 1e6) return `${s}$${(a / 1e6).toFixed(2)}M`;
  if (a >= 1e3) return `${s}$${Math.round(a / 1e3)}k`;
  return `${s}$${Math.round(a)}`;
};
const num = (n, d = 2) => (n == null || Number.isNaN(Number(n)) ? "—" : Number(n).toFixed(d));
const pctOf = (n, d = 0) => (n == null || Number.isNaN(Number(n)) ? "—" : `${(n * 100).toFixed(d)}%`);

// ----------------------------------------------------------------------------
// Strategy Backtest — the Phase-2 relative-value mean-reversion strategy run
// over the provided 15-min crude data. The trade log is the centrepiece: every
// trade, its gross PnL (slippage 0), and full detail.
// ----------------------------------------------------------------------------

const FALLBACK = {
  generatedAt: "—", mode: "local", live: false, firstBar: "—", lastBar: "—", bars: 0,
  regime: "—", strategy: { name: "Regime-driven RV mean-reversion", params: {} },
  summary: { trades: 0, grossPnl: 0, netPnl: 0, costs: 0, winRate: 0, avgWin: 0, avgLoss: 0,
    profitFactor: null, expectancy: 0, netExpectancy: 0, avgNetWin: 0, avgNetLoss: 0,
    perTradeSharpe: 0, avgHoldMin: 0, maxDrawdown: 0, sharpe: 0, calmar: null, cvar5: 0,
    maxDrawdownPct: 0, pctTimeInMarket: 0, avgSize: 1,
    endingEquity: 250000, initialCapital: 250000, byExitReason: {}, byDirection: {} },
  blind: { summary: {}, equityCurve: [] }, comparison: {}, sizingSeries: [],
  byStructure: {}, equityCurve: [], equityCurveBlind: [], trades: [], openPositions: [], openCount: 0,
};

const regimeText = (r) => (typeof r === "string" ? r : r?.label ?? "—");
const pct = (n) => (n == null || Number.isNaN(Number(n)) ? "—" : `${(n * 100).toFixed(0)}%`);
// Profit factor: gross wins ÷ gross losses. null/undefined (no trades) → "—";
// no losing trades makes it infinite → "Inf".
const pf = (n) => (n == null ? "—" : !Number.isFinite(n) ? "Inf" : fmt(n, 2));
const PF_TITLE = "Profit factor = gross profit ÷ gross loss. >1 is profitable; higher is better. “Inf” means no losing trades.";
const dirColor = (d) => (d === "LONG" ? "text-emerald-400" : "text-red-400");
const pnlColor = (n) => (n > 0 ? "text-emerald-400" : n < 0 ? "text-red-400" : "text-zinc-400");
const compactUsd = (n) => {
  const a = Math.abs(n);
  if (a >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (a >= 1e3) return `$${Math.round(n / 1e3)}k`;
  return `$${Math.round(n)}`;
};

// ----------------------------------------------------------------------------
// Proven-track-record strip — the live panel is only a few days; this anchors it
// to the same strategy's 5-year, cost-validated result (the Historical BT panel),
// so the short live sample isn't read in a vacuum.
// ----------------------------------------------------------------------------
const ProvenStrip = ({ ctx }) => {
  const s = ctx?.summary;
  if (!s || !s.trades) return null;
  const net = s.refNet ?? s.netPnl ?? s.grossPnl;
  const keep = s.refKeepPct != null ? `${Math.round(s.refKeepPct * 100)}%` : null;
  return (
    <Card padding={false}>
      <div className="px-4 py-2.5 flex items-center gap-x-3 gap-y-1 flex-wrap">
        <Award size={15} className="text-sky-400 shrink-0" />
        <span className="text-[11px] text-zinc-400">
          A <span className="text-zinc-200 font-medium">few-day demo</span> on the real feed — the{" "}
          <span className="text-zinc-200 font-medium">same strategy</span>, proven over{" "}
          <span className="text-zinc-200 font-medium">{ctx.years} years</span> (Historical BT):
        </span>
        <span className="flex items-center gap-2.5 font-mono text-[11px] ml-auto">
          <span className="text-emerald-400">net {compactUsd(net)}</span>
          <span className="text-zinc-700">·</span>
          <span className="text-zinc-200" title={PF_TITLE}>PF {pf(s.profitFactor)}</span>
          {keep && (<><span className="text-zinc-700">·</span><span className="text-zinc-300">{keep} kept after costs</span></>)}
          <span className="text-zinc-700">·</span>
          <span className="text-zinc-400">{fmt(s.trades, 0)} trades</span>
        </span>
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
// Hero scoreboard
// ----------------------------------------------------------------------------
const Hero = ({ d, live, stale }) => {
  const s = d.summary;
  const hasCost = (s.costs || 0) > 0;
  // Risk-led (gross is the by-product). NB the live window is a few days — the 5-year proven
  // strip below carries the statistical weight; these are a small live demo.
  const stats = [
    { k: "Sharpe", v: num(s.sharpe, 2), sub: `${fmt(s.trades, 0)} trades · ${d.openCount} open` },
    { k: "Max drawdown", v: usdK(s.maxDrawdown), sub: `${pctOf(s.maxDrawdownPct)} · MTM` },
    { k: "Tail · CVaR 5%", v: usdK(s.cvar5), sub: `${pct(s.winRate)} win` },
    { k: "Net P&L", v: usdK(s.netPnl), sub: "few-day live demo", color: pnlColor(s.netPnl) },
  ];
  return (
    <Card padding={false}>
      <div className="p-4 border-b border-[#1c1d22] flex items-start justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-1 h-12 rounded-sm bg-amber-500" />
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-500">Strategy Backtest · {d.strategy?.name}</div>
            <div className="text-2xl font-semibold text-zinc-100 leading-tight">{regimeText(d.regime)} <span className="text-zinc-600 text-base">regime</span></div>
            <div className="text-[10px] text-zinc-600 mt-0.5 font-mono">
              {d.bars} bars · {d.firstBar} → {d.lastBar} · {d.mode === "live" ? "LIVE feed" : "provided data"}
              {" · "}1 unit/trade · {hasCost ? "net of slippage" : "gross"}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => window.print()}
            className="no-print inline-flex items-center gap-1.5 h-8 px-3 rounded-md bg-amber-500/10 border border-amber-500/30 text-[11px] font-medium text-amber-300 hover:bg-amber-500/15 hover:border-amber-500/50 transition-colors"
            title="Export this page as a PDF (opens the print dialog → Save as PDF)"
          >
            <Download size={13} /> Export PDF
          </button>
          <SourceTag live={live && !stale} stale={stale} source="signalEngine"
            note="The Phase-2 mean-reversion strategy backtested over the provided 15-min crude bars. Trade log + equity are computed here." />
        </div>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 divide-x divide-[#1c1d22]">
        {stats.map((m) => (
          <div key={m.k} className="p-4" title={m.title}>
            <div className="text-[9px] uppercase tracking-[0.16em] text-zinc-500">{m.k}</div>
            <div className={`text-2xl font-semibold tabular-nums mt-1 ${m.color || "text-zinc-100"}`}>{m.v}</div>
            <div className="text-[10px] text-zinc-600 mt-0.5">{m.sub}</div>
          </div>
        ))}
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
// Equity curve
// ----------------------------------------------------------------------------
const Equity = ({ curve, initial }) => {
  if (!curve || curve.length < 2) return null;
  const data = curve.map((p, i) => ({ ...p, i }));
  return (
    <Card padding={false}>
      <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] uppercase tracking-[0.14em] text-zinc-400">
        Equity curve <span className="text-zinc-600 normal-case tracking-normal">· realised, gross</span>
      </div>
      <div className="h-44 p-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
            <defs>
              <linearGradient id="eq" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity={0.22} />
                <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid {...chartProps.grid} />
            <XAxis dataKey="i" {...chartProps.axis} tick={false} />
            <YAxis {...chartProps.axis} width={64} domain={["dataMin - 100", "dataMax + 100"]}
              tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`} />
            <ReferenceLine y={initial} stroke="#3f3f46" strokeDasharray="3 3" />
            <Tooltip content={<ChartTooltip formatter={(v) => `$${fmt(v, 0)}`} />} />
            <Area type="monotone" dataKey="equity" stroke="#10b981" strokeWidth={1.5} fill="url(#eq)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
// Trade Log — the centrepiece
// ----------------------------------------------------------------------------
const TradeLog = ({ trades }) => {
  const [open, setOpen] = useState(null);
  return (
    <Card padding={false}>
      <div className="px-4 py-2.5 border-b border-[#1c1d22] flex items-center justify-between">
        <span className="text-[11px] uppercase tracking-[0.14em] text-zinc-400">{trades.length} trades</span>
        <span className="text-[10px] text-zinc-600">1 unit/trade · 1,000 bbl/contract · tap a row for detail</span>
      </div>
      <div className="overflow-x-auto max-h-[560px] overflow-y-auto print-expand">
        <table className="w-full text-[11px]">
          <thead className="sticky top-0 bg-[#0e0f12] text-zinc-600 text-[9px] uppercase tracking-wider">
            <tr className="border-b border-[#1c1d22]">
              <th className="text-left font-medium px-3 py-2">Entry</th>
              <th className="text-left font-medium px-2 py-2">Instrument</th>
              <th className="text-left font-medium px-2 py-2">Dir</th>
              <th className="text-right font-medium px-2 py-2">Entry z</th>
              <th className="text-right font-medium px-2 py-2">Held</th>
              <th className="text-left font-medium px-2 py-2">Exit</th>
              <th className="text-right font-medium px-2 py-2">Conf</th>
              <th className="text-right font-medium px-2 py-2">PnL</th>
              <th className="w-6"></th>
            </tr>
          </thead>
          <tbody>
            {trades.length === 0 && <tr><td colSpan={9} className="px-3 py-8 text-center text-zinc-600">No trades — run the backtest to populate the log.</td></tr>}
            {trades.map((t, i) => {
              const id = t.structure + t.entryTime + i;
              const isOpen = open === id;
              return (
                <>
                  <tr key={id} onClick={() => setOpen(isOpen ? null : id)}
                    className="border-b border-[#141519] hover:bg-white/[0.02] cursor-pointer">
                    <td className="px-3 py-2 font-mono text-zinc-400 whitespace-nowrap">{t.entryTime}</td>
                    <td className="px-2 py-2 text-zinc-200 whitespace-nowrap">{t.label}</td>
                    <td className={`px-2 py-2 font-semibold ${dirColor(t.direction)}`}>
                      <span className="inline-flex items-center gap-1">
                        {t.direction === "LONG" ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}{t.direction}
                      </span>
                    </td>
                    <td className="px-2 py-2 text-right font-mono text-zinc-400 tabular-nums">{fmtSigned(t.entryZ, 2)}σ</td>
                    <td className="px-2 py-2 text-right font-mono text-zinc-500 tabular-nums">{t.holdMin}m</td>
                    <td className="px-2 py-2 text-zinc-500 whitespace-nowrap">{t.exitReason}</td>
                    <td className="px-2 py-2 text-right font-mono text-zinc-500 tabular-nums">{t.confidence}</td>
                    <td className={`px-2 py-2 text-right font-mono tabular-nums font-medium ${pnlColor(t.pnl)}`}>{fmtSigned(t.pnl, 0)}</td>
                    <td className="px-2 py-2 text-zinc-600"><ChevronDown size={12} className={`transition-transform ${isOpen ? "rotate-180" : ""}`} /></td>
                  </tr>
                  {isOpen && (
                    <tr key={id + "-d"} className="bg-[#0a0b0e] border-b border-[#141519]">
                      <td colSpan={9} className="px-4 py-3 space-y-2">
                        <div className="text-[10px] text-zinc-500">
                          <span className="text-zinc-300">{t.strategy}</span> · regime {regimeText(t.regime)} · historical edge {pct(t.histHitRate)} · confidence {t.confidence}/100
                        </div>
                        <div className="flex flex-wrap gap-x-5 gap-y-1 text-[10px] font-mono text-zinc-500">
                          <span>spread {t.entrySpread} → {t.exitSpread}</span>
                          <span>z {fmtSigned(t.entryZ, 2)}σ → {fmtSigned(t.exitZ, 2)}σ</span>
                          <span>held {t.holdBars} bars ({t.holdMin}m)</span>
                          <span>MAE/MFE {fmtSigned(t.mae, 0)} / {fmtSigned(t.mfe, 0)}</span>
                          <span>contracts {t.contracts}</span>
                          {t.cost > 0 && <span>cost {fmt(t.cost, 0)} · net {fmtSigned(t.netPnl, 0)}</span>}
                        </div>
                        <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] font-mono text-zinc-600">
                          {Object.entries(t.entryLegs || {}).map(([leg, px]) => (
                            <span key={leg}>{leg}: {px} → {t.exitLegs?.[leg]}</span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
// Per-structure + open positions
// ----------------------------------------------------------------------------
const Bottom = ({ byStructure, openPositions }) => {
  const rows = Object.entries(byStructure);
  return (
    <div className="grid grid-cols-12 gap-3">
      <Card className="col-span-12 lg:col-span-7" padding={false}>
        <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] uppercase tracking-[0.14em] text-zinc-400">
          By structure <span className="text-zinc-600 normal-case tracking-normal">· result vs historical edge</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead className="text-zinc-600 text-[9px] uppercase tracking-wider">
              <tr className="border-b border-[#1c1d22]">
                <th className="text-left font-medium px-3 py-2">Structure</th>
                <th className="text-right font-medium px-2 py-2">Trades</th>
                <th className="text-right font-medium px-2 py-2">Win</th>
                <th className="text-right font-medium px-2 py-2">PnL</th>
                <th className="text-right font-medium px-2 py-2">PF</th>
                <th className="text-right font-medium px-3 py-2">Hist edge</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && <tr><td colSpan={6} className="px-3 py-6 text-center text-zinc-600">No trades.</td></tr>}
              {rows.map(([k, s]) => (
                <tr key={k} className="border-b border-[#141519]">
                  <td className="px-3 py-2 text-zinc-200">{s.label}</td>
                  <td className="px-2 py-2 text-right font-mono text-zinc-400 tabular-nums">{s.trades}</td>
                  <td className="px-2 py-2 text-right font-mono text-zinc-400 tabular-nums">{pct(s.winRate)}</td>
                  <td className={`px-2 py-2 text-right font-mono tabular-nums ${pnlColor(s.pnl)}`}>{fmtSigned(s.pnl, 0)}</td>
                  <td className="px-2 py-2 text-right font-mono text-zinc-400 tabular-nums">{pf(s.profitFactor)}</td>
                  <td className="px-3 py-2 text-right font-mono text-emerald-400/70 tabular-nums">{pct(s.histHitRate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="col-span-12 lg:col-span-5" padding={false}>
        <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] uppercase tracking-[0.14em] text-zinc-400">
          Open at last bar ({openPositions.length})
        </div>
        <div className="divide-y divide-[#141519]">
          {openPositions.length === 0 && <div className="px-4 py-6 text-center text-[11px] text-zinc-600">Flat — no positions open at the last bar.</div>}
          {openPositions.map((p) => (
            <div key={p.structure + p.entryTime} className="px-4 py-2.5 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <div className="text-[12px] text-zinc-200 font-medium truncate">
                  {p.label} <span className={`ml-1 text-[10px] font-semibold ${dirColor(p.direction)}`}>{p.direction}</span>
                </div>
                <div className="text-[10px] text-zinc-600 font-mono">in {p.entryTime} @ {p.entrySpread} · z {fmtSigned(p.entryZ, 2)}→{fmtSigned(p.curZ, 2)} · {p.holdBars} bars</div>
              </div>
              <div className={`font-mono text-[13px] tabular-nums ${pnlColor(p.unrealizedPnl)}`}>{fmtSigned(p.unrealizedPnl, 0)}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

// ----------------------------------------------------------------------------
// Risk strip — lead with risk + the regime-aware vs regime-blind head-to-head.
// ----------------------------------------------------------------------------
const RiskStrip = ({ s, cmp }) => {
  const has = cmp && Object.keys(cmp).length > 0;
  const stats = [
    { k: "Sharpe", v: num(s.sharpe, 2) },
    { k: "Max DD", v: usdK(s.maxDrawdown), sub: s.maxDrawdownPct ? `${(s.maxDrawdownPct * 100).toFixed(1)}%` : null },
    { k: "CVaR 5%", v: usdK(s.cvar5) },
    { k: "Time in mkt", v: pctOf(s.pctTimeInMarket) },
    { k: "Avg size", v: `${num(s.avgSize, 2)}×` },
  ];
  const cmpRows = [["Sharpe", "sharpe", (v) => num(v, 2), true], ["Max DD", "maxDrawdown", usdK, true],
    ["CVaR 5%", "cvar5", usdK, true], ["Net P&L", "netPnl", usdK, null]];
  return (
    <Card padding={false}>
      <div className="px-4 py-2.5 border-b border-[#1c1d22] flex items-center gap-2">
        <Shield size={13} className="text-amber-400" />
        <span className="text-[11px] uppercase tracking-[0.14em] text-zinc-300">Risk profile</span>
        <span className="text-[10px] text-zinc-600 normal-case">· this few-day live window — the 5-year backtest above is the proven result</span>
      </div>
      <div className="grid grid-cols-3 md:grid-cols-5 divide-x divide-[#1c1d22]">
        {stats.map((m) => (
          <div key={m.k} className="p-3">
            <div className="text-[9px] uppercase tracking-[0.16em] text-zinc-500">{m.k}</div>
            <div className="text-lg font-semibold tabular-nums mt-0.5 text-zinc-100">{m.v}</div>
            {m.sub && <div className="text-[10px] text-zinc-600">{m.sub}</div>}
          </div>
        ))}
      </div>
      {has && (
        <div className="border-t border-[#1c1d22] flex flex-wrap divide-x divide-[#1c1d22]">
          {cmpRows.map(([label, key, f, betterHigher]) => {
            const a = cmp[key]?.aware, b = cmp[key]?.blind;
            const win = betterHigher && a != null && b != null ? a > b : null;
            return (
              <div key={key} className="flex-1 min-w-[140px] px-3 py-2">
                <div className="text-[9px] uppercase tracking-[0.14em] text-zinc-500">{label} · aware vs blind</div>
                <div className="text-[12px] font-mono tabular-nums">
                  <span className={win === true ? "text-emerald-400" : "text-zinc-200"}>{f(a)}</span>
                  <span className="text-zinc-600"> / </span>
                  <span className={win === false ? "text-emerald-400" : "text-zinc-500"}>{f(b)}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
};

const SizingChart = ({ series }) => {
  if (!series || series.length < 2) return null;
  const data = series.map((p, i) => ({ ...p, i }));
  return (
    <Card padding={false}>
      <div className="px-4 py-2.5 border-b border-[#1c1d22] flex items-center gap-2">
        <Activity size={13} className="text-amber-400" />
        <span className="text-[11px] uppercase tracking-[0.14em] text-zinc-400">Vol-target &amp; shock sizing</span>
        <span className="text-[10px] text-zinc-600 normal-case">· size de-levers as shock severity rises</span>
      </div>
      <div className="h-36 p-2">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
            <defs>
              <linearGradient id="ssev" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f43f5e" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#f43f5e" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid {...chartProps.grid} />
            <XAxis dataKey="i" {...chartProps.axis} tick={false} />
            <YAxis yAxisId="sz" {...chartProps.axis} width={40} domain={[0, "auto"]} tickFormatter={(v) => `${v.toFixed(1)}x`} />
            <YAxis yAxisId="sv" orientation="right" {...chartProps.axis} width={32} domain={[0, 1]} tickFormatter={(v) => v.toFixed(1)} />
            <Tooltip content={<ChartTooltip />} />
            <Area yAxisId="sv" type="monotone" name="shock severity" dataKey="severity" stroke="#f43f5e" strokeWidth={1} fill="url(#ssev)" />
            <Line yAxisId="sz" type="monotone" name="avg size" dataKey="size" stroke="#fbbf24" strokeWidth={1.4} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

// ============================================================================
// PAGE
// ============================================================================
export const PageSignalEngine = () => {
  const { data, live, stale } = useLive("/api/signal-engine", FALLBACK, useLive.REFRESH.fast);
  const { data: ctx } = useLive("/api/historical-intraday", null, useLive.REFRESH.slow);
  const d = data || FALLBACK;
  return (
    <div className="space-y-4">
      {/* Print-only report masthead — replaces the (hidden) app top bar in the PDF */}
      <div className="hidden print:flex items-baseline justify-between pb-2 mb-1 border-b border-[#1c1d22]">
        <div className="flex items-baseline gap-2">
          <span className="text-base font-bold tracking-tight text-amber-400">VOLTAIRE</span>
          <span className="text-sm font-semibold text-zinc-100">Strategy Backtest</span>
        </div>
        <div className="text-[10px] font-mono text-zinc-500">Exported {d.generatedAt} · {d.mode === "live" ? "live feed" : "provided data"}</div>
      </div>
      <Hero d={d} live={live} stale={stale} />
      <ProvenStrip ctx={ctx} />
      <RiskStrip s={d.summary || {}} cmp={d.comparison || {}} />
      <Equity curve={d.equityCurve} initial={d.summary?.initialCapital || 250000} />
      <SizingChart series={d.sizingSeries} />
      <div className="space-y-2">
        <Band icon={TrendingUp} title="Trade Log" sub="every trade · full detail · gross PnL" />
        <TradeLog trades={d.trades || []} />
      </div>
      <div className="space-y-2">
        <Band icon={Layers} title="Breakdown" sub="per structure & open positions" />
        <Bottom byStructure={d.byStructure || {}} openPositions={d.openPositions || []} />
      </div>
    </div>
  );
};
