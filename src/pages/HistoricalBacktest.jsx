import { useState } from "react";
import { AreaChart, Area, ComposedChart, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from "recharts";
import { ResponsiveContainer } from "../lib/ResponsiveContainer";
import { History, Layers, Gauge, ChevronDown, ArrowUpRight, ArrowDownRight, Download, Shield, Zap, Activity } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { Band } from "../components/primitives/Band";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { useLive } from "../lib/useLive";
import { fmt, fmtSigned } from "../lib/format";

// Compact $ (e.g. -$133k, +$1.2M) for risk figures.
const usdK = (n) => {
  if (n == null || Number.isNaN(Number(n))) return "—";
  const a = Math.abs(n), s = n < 0 ? "-" : "";
  if (a >= 1e6) return `${s}$${(a / 1e6).toFixed(2)}M`;
  if (a >= 1e3) return `${s}$${Math.round(a / 1e3)}k`;
  return `${s}$${Math.round(a)}`;
};
const pctOf = (n, d = 1) => (n == null || Number.isNaN(Number(n)) ? "—" : `${(n * 100).toFixed(d)}%`);
const num = (n, d = 2) => (n == null || Number.isNaN(Number(n)) ? "—" : Number(n).toFixed(d));

// ----------------------------------------------------------------------------
// Historical Backtest — the Phase-2 FUNDAMENTAL fair value, traded as a daily
// mean-reversion simulation over 2021-2026. This is the model's proper home: on
// daily data with the fundamental drivers present, the regression fair value is
// meaningful, and 5+ years is a statistically real sample. Walk-forward (no
// look-ahead), fixed 1 unit/trade, gross.
// ----------------------------------------------------------------------------

const FALLBACK = {
  generatedAt: "—", span: { first: "—", last: "—" }, years: 0, days: 0,
  strategy: { name: "Regime-driven RV mean-reversion", desc: "", params: {} },
  summary: { trades: 0, grossPnl: 0, netPnl: 0, costs: 0, winRate: 0, avgWin: 0, avgLoss: 0,
    profitFactor: null, expectancy: 0, netExpectancy: 0, avgNetWin: 0, avgNetLoss: 0,
    perTradeSharpe: 0, avgHoldDays: 0, tradesPerYear: 0, avgSize: 1,
    sharpe: 0, calmar: null, cagr: 0, maxDrawdownPct: 0, cvar5: 0, volAnn: 0, pctTimeInMarket: 0,
    maxDrawdown: 0, endingEquity: 250000, initialCapital: 250000, byExitReason: {}, byDirection: {} },
  blind: { summary: {}, equityCurve: [] }, comparison: {}, byVolState: {},
  byStructure: {}, byRegime: {}, equityCurve: [], equityCurveBlind: [], sizingSeries: [],
  trades: [], openPositions: [], openCount: 0,
};

const dirColor = (d) => (d === "LONG" ? "text-emerald-400" : "text-red-400");
const pnlColor = (n) => (n > 0 ? "text-emerald-400" : n < 0 ? "text-red-400" : "text-zinc-400");
const pct = (n) => (n == null || Number.isNaN(Number(n)) ? "—" : `${(n * 100).toFixed(0)}%`);
// Profit factor: gross wins ÷ gross losses. null (no trades) → "—"; no losing trades → "Inf".
const pf = (n) => (n == null ? "—" : !Number.isFinite(n) ? "Inf" : fmt(n, 2));
// Tone: weak (1–1.5) amber, losing (<1) red, strong (≥1.5) neutral; missing → neutral.
const pfTone = (n) => (n == null ? "text-zinc-400" : n < 1 ? "text-red-400/80" : n < 1.5 ? "text-amber-400" : "text-zinc-400");
const PF_TITLE = "Profit factor = gross profit ÷ gross loss. >1 is profitable; higher is better. “Inf” means no losing trades.";

// ----------------------------------------------------------------------------
// Hero scoreboard
// ----------------------------------------------------------------------------
const ModeToggle = ({ mode, setMode }) => (
  <div className="no-print inline-flex rounded-md border border-[#26272e] overflow-hidden text-[11px] font-medium">
    {[["daily", "Daily · fundamental"], ["intraday", "Intraday · rolling"]].map(([m, lbl]) => (
      <button key={m} onClick={() => setMode(m)}
        className={`px-3 h-8 transition-colors ${mode === m ? "bg-sky-500/15 text-sky-300" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.02]"}`}>
        {lbl}
      </button>
    ))}
  </div>
);

const Hero = ({ d, mode, setMode }) => {
  const s = d.summary;
  const hasCost = (s.costs || 0) > 0;
  const intraday = d.mode === "intraday";
  const obs = intraday ? `${fmt(d.bars || 0, 0)} 15-min bars` : `${d.days || 0} trading days`;
  const fvText = intraday
    ? "regime-adaptive fair value (EWMA · span set by the regime's half-life)"
    : "Phase-2 fundamentals regression · walk-forward (out-of-sample)";
  // Lead with RISK (the mentor's mandate); gross P&L is the by-product, shown last.
  const stats = [
    { k: "Sharpe", v: num(s.sharpe, 2), sub: `Calmar ${s.calmar == null ? "—" : num(s.calmar, 2)}`, big: true },
    { k: "Max drawdown", v: usdK(s.maxDrawdown), sub: `${pctOf(s.maxDrawdownPct)} · MTM` },
    { k: "Tail risk · CVaR 5%", v: usdK(s.cvar5), sub: `${pctOf(s.pctTimeInMarket, 0)} time in market` },
    { k: "Net P&L", v: usdK(s.netPnl), sub: `${fmt(s.trades, 0)} trades · ${pct(s.winRate)} win`, color: pnlColor(s.netPnl) },
  ];
  return (
    <Card padding={false}>
      <div className="p-4 border-b border-[#1c1d22] flex items-start justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-1 h-12 rounded-sm bg-sky-500" />
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-500">Historical Backtest · WTI &amp; Brent · regime-driven</div>
            <div className="text-2xl font-semibold text-zinc-100 leading-tight">{d.years}-year {intraday ? "intraday" : "daily"} simulation <span className="text-zinc-600 text-base">2021–2026</span></div>
            <div className="text-[10px] text-zinc-600 mt-0.5 font-mono">
              {obs} · {d.span?.first} → {d.span?.last} · {fvText} · vol-target sizing · {hasCost ? "net of cost" : "gross"}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <ModeToggle mode={mode} setMode={setMode} />
          <button
            onClick={() => window.print()}
            className="no-print inline-flex items-center gap-1.5 h-8 px-3 rounded-md bg-sky-500/10 border border-sky-500/30 text-[11px] font-medium text-sky-300 hover:bg-sky-500/15 hover:border-sky-500/50 transition-colors"
            title="Export this page as a PDF (opens the print dialog → Save as PDF)"
          >
            <Download size={13} /> Export PDF
          </button>
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
// Equity curve (5-year)
// ----------------------------------------------------------------------------
const Equity = ({ curve, blindCurve, initial }) => {
  if (!curve || curve.length < 2) return null;
  const blindByT = new Map((blindCurve || []).map((p) => [p.t, p.equity]));
  const data = curve.map((p, i) => ({ ...p, i, blind: blindByT.get(p.t) }));
  const hasBlind = (blindCurve || []).length > 1;
  return (
    <Card padding={false}>
      <div className="px-4 py-2.5 border-b border-[#1c1d22] flex items-center justify-between flex-wrap gap-2">
        <span className="text-[11px] uppercase tracking-[0.14em] text-zinc-400">
          Equity curve <span className="text-zinc-600 normal-case tracking-normal">· mark-to-market, gross · {curve[0].t} → {curve[curve.length - 1].t}</span>
        </span>
        {hasBlind && (
          <span className="flex items-center gap-3 text-[10px]">
            <span className="flex items-center gap-1.5 text-sky-300"><span className="w-3 h-0.5 bg-sky-400 inline-block" /> Regime-aware</span>
            <span className="flex items-center gap-1.5 text-zinc-500"><span className="w-3 h-0 border-t border-dashed border-zinc-500 inline-block" /> Regime-blind</span>
          </span>
        )}
      </div>
      <div className="h-56 p-2">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
            <defs>
              <linearGradient id="heq" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.22} />
                <stop offset="100%" stopColor="#38bdf8" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid {...chartProps.grid} />
            <XAxis dataKey="i" {...chartProps.axis} tick={false} />
            <YAxis {...chartProps.axis} width={64} domain={["auto", "auto"]}
              tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
            <ReferenceLine y={initial} stroke="#3f3f46" strokeDasharray="3 3" />
            <Tooltip content={<ChartTooltip formatter={(v) => `$${fmt(v, 0)}`} />} />
            <Area type="monotone" name="Regime-aware" dataKey="equity" stroke="#38bdf8" strokeWidth={1.5} fill="url(#heq)" />
            {hasBlind && <Line type="monotone" name="Regime-blind" dataKey="blind" stroke="#71717a" strokeWidth={1.2} strokeDasharray="4 3" dot={false} />}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
// Verdict scorecard — the ONE digestible takeaway: regime-aware vs an identical
// regime-blind baseline (same fair value & universe), isolating the regime model's
// contribution. Three risk tiles + a plain-English headline.
// ----------------------------------------------------------------------------
const DeltaBadge = ({ good, text }) => (
  <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${good ? "bg-emerald-500/15 text-emerald-400" : "bg-zinc-600/20 text-zinc-400"}`}>{text}</span>
);

const Verdict = ({ s, cmp, intraday }) => {
  if (!cmp || !cmp.sharpe) return null;
  const a = (k) => cmp[k]?.aware, b = (k) => cmp[k]?.blind;
  const reduction = (x, y) => (y && x != null ? 1 - Math.abs(x) / Math.abs(y) : null);
  const sa = a("sharpe"), sb = b("sharpe");
  const ddRed = reduction(a("maxDrawdown"), b("maxDrawdown"));
  const cvRed = reduction(a("cvar5"), b("cvar5"));
  const shX = sb ? sa / sb : null;
  const tiles = [
    { k: "Sharpe", hint: "risk-adjusted return", aware: num(sa, 2), blind: num(sb, 2),
      good: sa >= sb, delta: shX == null ? "—" : sa >= sb ? `${num(shX, 1)}× higher` : `${num(shX, 2)}×` },
    { k: "Max drawdown", hint: "peak-to-trough, incl. open risk", aware: usdK(a("maxDrawdown")), blind: usdK(b("maxDrawdown")),
      good: ddRed != null && ddRed >= 0, delta: ddRed == null ? "—" : `${(ddRed * 100).toFixed(0)}% smaller` },
    { k: "Tail risk · CVaR 5%", hint: "worst-5%-of-days loss", aware: usdK(a("cvar5")), blind: usdK(b("cvar5")),
      good: cvRed != null && cvRed >= 0, delta: cvRed == null ? "—" : `${(cvRed * 100).toFixed(0)}% smaller` },
  ];
  const sentence = intraday
    ? "Intraday the naive baseline is already strong, so the regime model holds the edge while cutting drawdown and tail risk to a fraction — risk reduction, not extra return."
    : "The regime model nearly doubles the Sharpe and cuts drawdown and tail risk by a third to a half — a better risk-adjusted book, not just a bigger one.";
  return (
    <Card padding={false}>
      <div className="px-4 py-2.5 border-b border-[#1c1d22] flex items-center gap-2">
        <Shield size={13} className="text-sky-400" />
        <span className="text-[11px] uppercase tracking-[0.14em] text-zinc-200">Regime model vs blind baseline</span>
        <span className="text-[10px] text-zinc-600 normal-case hidden sm:inline">· same fair value &amp; universe — isolates the regime layer</span>
      </div>
      <div className="px-4 py-3 text-[12px] text-zinc-300 leading-snug border-b border-[#1c1d22]">{sentence}</div>
      <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-[#1c1d22]">
        {tiles.map((t) => (
          <div key={t.k} className="p-4" title={t.hint}>
            <div className="flex items-center justify-between">
              <span className="text-[9px] uppercase tracking-[0.16em] text-zinc-500">{t.k}</span>
              <DeltaBadge good={t.good} text={t.delta} />
            </div>
            <div className="text-2xl font-semibold tabular-nums mt-1 text-sky-300">{t.aware}</div>
            <div className="text-[10px] text-zinc-600 mt-0.5">vs <span className="text-zinc-400 tabular-nums">{t.blind}</span> blind</div>
          </div>
        ))}
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
// Sizing / shock series — the vol-target + shock layer DE-LEVERING over time.
// ----------------------------------------------------------------------------
const SizingChart = ({ series }) => {
  if (!series || series.length < 2) return null;
  const data = series.map((p, i) => ({ ...p, i }));
  return (
    <Card padding={false}>
      <div className="px-4 py-2.5 border-b border-[#1c1d22] flex items-center gap-2">
        <Activity size={13} className="text-amber-400" />
        <span className="text-[11px] uppercase tracking-[0.14em] text-zinc-400">Vol-target &amp; shock sizing</span>
        <span className="text-[10px] text-zinc-600 normal-case">· book size shrinks as shock severity rises</span>
      </div>
      <div className="h-40 p-2">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
            <defs>
              <linearGradient id="hsev" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f43f5e" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#f43f5e" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid {...chartProps.grid} />
            <XAxis dataKey="i" {...chartProps.axis} tick={false} />
            <YAxis yAxisId="sz" {...chartProps.axis} width={40} domain={[0, "auto"]} tickFormatter={(v) => `${v.toFixed(1)}x`} />
            <YAxis yAxisId="sv" orientation="right" {...chartProps.axis} width={36} domain={[0, 1]} tickFormatter={(v) => v.toFixed(1)} />
            <Tooltip content={<ChartTooltip />} />
            <Area yAxisId="sv" type="monotone" name="shock severity" dataKey="severity" stroke="#f43f5e" strokeWidth={1} fill="url(#hsev)" />
            <Line yAxisId="sz" type="monotone" name="avg size (units)" dataKey="size" stroke="#fbbf24" strokeWidth={1.4} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
// Trade log
// ----------------------------------------------------------------------------
const TradeLog = ({ trades, total }) => {
  const [open, setOpen] = useState(null);
  const capped = total && total > trades.length;
  return (
    <Card padding={false}>
      <div className="px-4 py-2.5 border-b border-[#1c1d22] flex items-center justify-between">
        <span className="text-[11px] uppercase tracking-[0.14em] text-zinc-400">
          {capped ? `${trades.length} of ${fmt(total, 0)} trades` : `${trades.length} trades`}
        </span>
        <span className="text-[10px] text-zinc-600">1 unit/trade · {capped ? "most recent shown · " : ""}tap a row for detail</span>
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
              <th className="text-left font-medium px-2 py-2">Regime</th>
              <th className="text-left font-medium px-2 py-2">Exit</th>
              <th className="text-right font-medium px-2 py-2">PnL</th>
              <th className="w-6"></th>
            </tr>
          </thead>
          <tbody>
            {trades.length === 0 && <tr><td colSpan={9} className="px-3 py-8 text-center text-zinc-600">No trades — run the backtest to populate the log.</td></tr>}
            {trades.map((t, i) => {
              const id = t.structure + t.entryDate + i;
              const isOpen = open === id;
              return (
                <>
                  <tr key={id} onClick={() => setOpen(isOpen ? null : id)}
                    className="border-b border-[#141519] hover:bg-white/[0.02] cursor-pointer">
                    <td className="px-3 py-2 font-mono text-zinc-400 whitespace-nowrap">{t.entryDate}</td>
                    <td className="px-2 py-2 text-zinc-200 whitespace-nowrap">{t.label}</td>
                    <td className={`px-2 py-2 font-semibold ${dirColor(t.direction)}`}>
                      <span className="inline-flex items-center gap-1">
                        {t.direction === "LONG" ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}{t.direction}
                      </span>
                    </td>
                    <td className="px-2 py-2 text-right font-mono text-zinc-400 tabular-nums">{fmtSigned(t.entryZ, 2)}σ</td>
                    <td className="px-2 py-2 text-right font-mono text-zinc-500 tabular-nums">{t.holdLabel || `${t.holdDays}d`}</td>
                    <td className="px-2 py-2 text-zinc-500 whitespace-nowrap">{t.regime || "—"}</td>
                    <td className="px-2 py-2 text-zinc-500 whitespace-nowrap">{t.exitReason}</td>
                    <td className={`px-2 py-2 text-right font-mono tabular-nums font-medium ${pnlColor(t.pnl)}`}>{fmtSigned(t.pnl, 0)}</td>
                    <td className="px-2 py-2 text-zinc-600"><ChevronDown size={12} className={`transition-transform ${isOpen ? "rotate-180" : ""}`} /></td>
                  </tr>
                  {isOpen && (
                    <tr key={id + "-d"} className="bg-[#0a0b0e] border-b border-[#141519]">
                      <td colSpan={9} className="px-4 py-3 space-y-2">
                        <div className="text-[10px] text-zinc-500">
                          Faded a {Math.abs(t.entryZ)}σ {t.direction === "LONG" ? "cheap" : "rich"} dislocation from the fundamental fair value · regime {t.regime || "—"}
                          {t.histHitRate != null && <> · Phase-2 reversion edge {pct(t.histHitRate)}</>}
                        </div>
                        <div className="flex flex-wrap gap-x-5 gap-y-1 text-[10px] font-mono text-zinc-500">
                          <span>spread {t.entrySpread} → {t.exitSpread}</span>
                          <span>fair value {t.fairValue}</span>
                          <span>z {fmtSigned(t.entryZ, 2)}σ → {fmtSigned(t.exitZ, 2)}σ</span>
                          <span>held {t.holdLabel || `${t.holdDays} days`}</span>
                          <span>MAE/MFE {fmtSigned(t.mae, 0)} / {fmtSigned(t.mfe, 0)}</span>
                          {t.cost > 0 && <span>cost {fmt(t.cost, 0)} · net {fmtSigned(t.netPnl, 0)}</span>}
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
// By structure + by regime
// ----------------------------------------------------------------------------
const Breakdown = ({ byStructure, byRegime, byVolState = {} }) => {
  const rows = Object.entries(byStructure);
  const regimes = Object.entries(byRegime);
  const volStates = Object.entries(byVolState);
  return (
    <div className="grid grid-cols-12 gap-3">
      <Card className="col-span-12 lg:col-span-7" padding={false}>
        <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] uppercase tracking-[0.14em] text-zinc-400">
          By structure <span className="text-zinc-600 normal-case tracking-normal">· result vs Phase-2 historical edge</span>
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
                  <td className={`px-2 py-2 text-right font-mono tabular-nums ${pfTone(s.profitFactor)}`} title={PF_TITLE}>{pf(s.profitFactor)}</td>
                  <td className="px-3 py-2 text-right font-mono text-emerald-400/70 tabular-nums">{s.histHitRate != null ? pct(s.histHitRate) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="col-span-12 lg:col-span-5" padding={false}>
        <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] uppercase tracking-[0.14em] text-zinc-400">
          By regime <span className="text-zinc-600 normal-case tracking-normal">· does the edge hold across market states?</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead className="text-zinc-600 text-[9px] uppercase tracking-wider">
              <tr className="border-b border-[#1c1d22]">
                <th className="text-left font-medium px-3 py-2">Regime</th>
                <th className="text-right font-medium px-2 py-2">Trades</th>
                <th className="text-right font-medium px-2 py-2">Win</th>
                <th className="text-right font-medium px-2 py-2">PnL</th>
                <th className="text-right font-medium px-3 py-2">PF</th>
              </tr>
            </thead>
            <tbody>
              {regimes.length === 0 && <tr><td colSpan={5} className="px-3 py-6 text-center text-zinc-600">No data.</td></tr>}
              {regimes.map(([k, s]) => (
                <tr key={k} className="border-b border-[#141519]">
                  <td className="px-3 py-2 text-zinc-200 whitespace-nowrap">{k}</td>
                  <td className="px-2 py-2 text-right font-mono text-zinc-400 tabular-nums">{s.trades}</td>
                  <td className="px-2 py-2 text-right font-mono text-zinc-400 tabular-nums">{pct(s.winRate)}</td>
                  <td className={`px-2 py-2 text-right font-mono tabular-nums ${pnlColor(s.pnl)}`}>{fmtSigned(s.pnl, 0)}</td>
                  <td className={`px-3 py-2 text-right font-mono tabular-nums ${pfTone(s.profitFactor)}`} title={PF_TITLE}>{pf(s.profitFactor)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {volStates.length > 0 && (
          <div className="border-t border-[#1c1d22]">
            <div className="px-4 py-2 text-[10px] uppercase tracking-[0.14em] text-zinc-500">By vol-state <span className="normal-case text-zinc-600">· avg size shows the vol-target de-risking</span></div>
            <div className="flex divide-x divide-[#1c1d22]">
              {volStates.map(([k, s]) => (
                <div key={k} className="flex-1 px-3 py-2">
                  <div className="text-[10px] text-zinc-400">{k} vol</div>
                  <div className={`text-[13px] font-mono tabular-nums ${pnlColor(s.pnl)}`}>{fmtSigned(s.pnl, 0)}</div>
                  <div className="text-[9px] text-zinc-600 font-mono">{s.trades} tr · {pct(s.winRate)} · {fmt(s.avgSize, 2)}× size</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

// ----------------------------------------------------------------------------
// Shock-absorption study (server/data/shock_analysis.json) — the primary axis:
// per-shock-window drawdown head-to-head + the synthetic vol-stress curve where
// the blind book's drawdown explodes and the regime book stays contained.
// ----------------------------------------------------------------------------
const ShockSection = () => {
  const { data } = useLive("/api/shock-analysis", null, useLive.REFRESH.slow);
  if (!data) return null;
  const ws = data.windowSummary || {};
  const stress = (data.stress || []).map((r) => ({
    factor: r.factor, aware: Math.abs(r.aware?.maxDrawdown ?? 0), blind: Math.abs(r.blind?.maxDrawdown ?? 0),
  }));
  const worst = [...(data.windows || [])].sort((a, b) => Math.abs(b.blind?.drawdown ?? 0) - Math.abs(a.blind?.drawdown ?? 0)).slice(0, 8);
  return (
    <div className="space-y-2">
      <Band icon={Zap} title="Shock Absorption" sub="regime-aware vs blind through vol/regime shocks (5-year daily)" />
      <Card padding={false}>
        <div className="px-4 py-3 border-b border-[#1c1d22] flex flex-wrap items-center gap-x-6 gap-y-1">
          <div>
            <div className="text-[9px] uppercase tracking-[0.16em] text-zinc-500">Shock windows</div>
            <div className="text-lg font-semibold text-zinc-100 tabular-nums">{ws.count ?? 0}</div>
          </div>
          <div>
            <div className="text-[9px] uppercase tracking-[0.16em] text-zinc-500">Aware shallower DD</div>
            <div className="text-lg font-semibold text-emerald-400 tabular-nums">{pctOf(ws.awareShallowerPct, 0)}</div>
          </div>
          <div>
            <div className="text-[9px] uppercase tracking-[0.16em] text-zinc-500">Avg DD · aware</div>
            <div className="text-lg font-semibold text-sky-300 tabular-nums">{usdK(ws.avgAwareDD)}</div>
          </div>
          <div>
            <div className="text-[9px] uppercase tracking-[0.16em] text-zinc-500">Avg DD · blind</div>
            <div className="text-lg font-semibold text-red-400 tabular-nums">{usdK(ws.avgBlindDD)}</div>
          </div>
        </div>
        <div className="grid grid-cols-12 gap-0 divide-x divide-[#1c1d22]">
          {/* synthetic stress curve */}
          <div className="col-span-12 lg:col-span-5 p-3">
            <div className="text-[10px] uppercase tracking-[0.14em] text-zinc-500 mb-1">Synthetic stress · max drawdown vs vol shock</div>
            <div className="h-44">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={stress} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis dataKey="factor" {...chartProps.axis} tickFormatter={(v) => `${v}x`} />
                  <YAxis {...chartProps.axis} width={48} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                  <Tooltip content={<ChartTooltip formatter={(v) => `$${fmt(v, 0)}`} />} />
                  <Line type="monotone" name="Regime-blind" dataKey="blind" stroke="#f43f5e" strokeWidth={1.6} dot={{ r: 2 }} />
                  <Line type="monotone" name="Regime-aware" dataKey="aware" stroke="#38bdf8" strokeWidth={1.6} dot={{ r: 2 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="text-[10px] text-zinc-600 mt-1">
              Blind drawdown grows ~linearly with the shock; the regime book de-levers and stands aside, so its drawdown saturates.
            </div>
          </div>
          {/* worst shock windows */}
          <div className="col-span-12 lg:col-span-7 overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead className="text-zinc-600 text-[9px] uppercase tracking-wider">
                <tr className="border-b border-[#1c1d22]">
                  <th className="text-left font-medium px-3 py-2">Shock date</th>
                  <th className="text-left font-medium px-2 py-2">Trigger</th>
                  <th className="text-right font-medium px-2 py-2">Aware DD</th>
                  <th className="text-right font-medium px-2 py-2">Blind DD</th>
                  <th className="text-right font-medium px-2 py-2">DD avoided</th>
                  <th className="text-right font-medium px-3 py-2">Recover</th>
                </tr>
              </thead>
              <tbody>
                {worst.map((w) => (
                  <tr key={w.start} className="border-b border-[#141519]">
                    <td className="px-3 py-2 font-mono text-zinc-400 whitespace-nowrap">{w.start}</td>
                    <td className="px-2 py-2 text-zinc-500 whitespace-nowrap">{w.kind === "regime_to_high" ? "→ High-vol regime" : "Vol jump"}</td>
                    <td className="px-2 py-2 text-right font-mono tabular-nums text-sky-300">{usdK(w.aware?.drawdown)}</td>
                    <td className="px-2 py-2 text-right font-mono tabular-nums text-red-400">{usdK(w.blind?.drawdown)}</td>
                    <td className="px-2 py-2 text-right font-mono tabular-nums text-emerald-400">{usdK(w.awareDeeperDDavoided)}</td>
                    <td className="px-3 py-2 text-right font-mono tabular-nums text-zinc-500">{w.aware?.recoveredDays == null ? "—" : `${w.aware.recoveredDays}d`}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Card>
    </div>
  );
};

// ============================================================================
// PAGE
// ============================================================================
export const PageHistoricalBacktest = () => {
  const [mode, setMode] = useState("daily");
  const ep = mode === "intraday" ? "/api/historical-intraday" : "/api/historical-backtest";
  const { data } = useLive(ep, FALLBACK, useLive.REFRESH.slow);
  const d = data || FALLBACK;
  const intraday = d.mode === "intraday";
  return (
    <div className="space-y-4">
      {/* Print-only masthead */}
      <div className="hidden print:flex items-baseline justify-between pb-2 mb-1 border-b border-[#1c1d22]">
        <div className="flex items-baseline gap-2">
          <span className="text-base font-bold tracking-tight text-sky-400">VOLTAIRE</span>
          <span className="text-sm font-semibold text-zinc-100">Historical Backtest · WTI &amp; Brent · {intraday ? "Intraday" : "Daily"} · 2021–2026</span>
        </div>
        <div className="text-[10px] font-mono text-zinc-500">Exported {d.generatedAt}</div>
      </div>

      <Hero d={d} mode={mode} setMode={setMode} />
      <Verdict s={d.summary || {}} cmp={d.comparison || {}} intraday={intraday} />
      <Equity curve={d.equityCurve} blindCurve={d.equityCurveBlind} initial={d.summary?.initialCapital || 250000} />
      <SizingChart series={d.sizingSeries} />
      <ShockSection />
      <div className="space-y-2">
        <Band icon={History} title="Trade Log" sub={`every ${intraday ? "intraday" : "daily"} trade · full detail · gross PnL`} />
        <TradeLog trades={d.trades || []} total={d.summary?.trades} />
      </div>
      <div className="space-y-2">
        <Band icon={Gauge} title="Breakdown" sub="per structure, regime & vol-state" />
        <Breakdown byStructure={d.byStructure || {}} byRegime={d.byRegime || {}} byVolState={d.byVolState || {}} />
      </div>
    </div>
  );
};
