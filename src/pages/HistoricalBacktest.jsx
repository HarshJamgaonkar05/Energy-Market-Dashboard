import { useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from "recharts";
import { ResponsiveContainer } from "../lib/ResponsiveContainer";
import { History, Layers, Gauge, ChevronDown, ArrowUpRight, ArrowDownRight, Download } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { Band } from "../components/primitives/Band";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { useLive } from "../lib/useLive";
import { fmt, fmtSigned } from "../lib/format";

// ----------------------------------------------------------------------------
// Historical Backtest — the Phase-2 FUNDAMENTAL fair value, traded as a daily
// mean-reversion simulation over 2021-2026. This is the model's proper home: on
// daily data with the fundamental drivers present, the regression fair value is
// meaningful, and 5+ years is a statistically real sample. Walk-forward (no
// look-ahead), fixed 1 unit/trade, gross.
// ----------------------------------------------------------------------------

const FALLBACK = {
  generatedAt: "—", span: { first: "—", last: "—" }, years: 0, days: 0,
  strategy: { name: "Phase-2 fundamental RV mean-reversion", desc: "", params: {} },
  summary: { trades: 0, grossPnl: 0, netPnl: 0, costs: 0, winRate: 0, avgWin: 0, avgLoss: 0,
    profitFactor: null, expectancy: 0, netExpectancy: 0, avgNetWin: 0, avgNetLoss: 0,
    perTradeSharpe: 0, avgHoldDays: 0, tradesPerYear: 0,
    maxDrawdown: 0, endingEquity: 250000, initialCapital: 250000, byExitReason: {}, byDirection: {} },
  byStructure: {}, byRegime: {}, equityCurve: [], trades: [], openPositions: [], openCount: 0,
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
  const fvText = intraday ? "rolling-mean fair value (price-derived)" : "Phase-2 fundamental fair value · walk-forward (out-of-sample)";
  const stats = [
    { k: "Trades", v: fmt(s.trades, 0), sub: `${fmt(s.tradesPerYear || 0, 0)}/yr` },
    { k: "Gross P&L", v: fmtSigned(s.grossPnl, 0),
      sub: hasCost ? `net ${fmtSigned(s.netPnl, 0)} after costs` : `exp ${fmtSigned(s.expectancy, 0)}/trade`,
      color: pnlColor(s.grossPnl) },
    { k: "Win rate", v: pct(s.winRate),
      sub: hasCost ? `+${fmt(s.avgNetWin, 0)} / ${fmt(s.avgNetLoss, 0)} avg · net`
                   : `+${fmt(s.avgWin, 0)} / ${fmt(s.avgLoss, 0)} avg` },
    { k: "Profit factor", v: pf(s.profitFactor), title: PF_TITLE, sub: `Sharpe ${s.perTradeSharpe} · DD ${fmtSigned(s.maxDrawdown, 0)}` },
  ];
  return (
    <Card padding={false}>
      <div className="p-4 border-b border-[#1c1d22] flex items-start justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-1 h-12 rounded-sm bg-sky-500" />
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-500">Historical Backtest · WTI &amp; Brent · {fvText.split(" ·")[0]}</div>
            <div className="text-2xl font-semibold text-zinc-100 leading-tight">{d.years}-year {intraday ? "intraday" : "daily"} simulation <span className="text-zinc-600 text-base">2021–2026</span></div>
            <div className="text-[10px] text-zinc-600 mt-0.5 font-mono">
              {obs} · {d.span?.first} → {d.span?.last} · {fvText} · 1 unit/trade · {hasCost ? "net of cost" : "gross"}
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
const Equity = ({ curve, initial }) => {
  if (!curve || curve.length < 2) return null;
  const data = curve.map((p, i) => ({ ...p, i }));
  return (
    <Card padding={false}>
      <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] uppercase tracking-[0.14em] text-zinc-400">
        Equity curve <span className="text-zinc-600 normal-case tracking-normal">· realised, gross · {curve[0].t} → {curve[curve.length - 1].t}</span>
      </div>
      <div className="h-56 p-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
            <defs>
              <linearGradient id="heq" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.22} />
                <stop offset="100%" stopColor="#38bdf8" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid {...chartProps.grid} />
            <XAxis dataKey="i" {...chartProps.axis} tick={false} />
            <YAxis {...chartProps.axis} width={64} domain={["dataMin - 5000", "dataMax + 5000"]}
              tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
            <ReferenceLine y={initial} stroke="#3f3f46" strokeDasharray="3 3" />
            <Tooltip content={<ChartTooltip formatter={(v) => `$${fmt(v, 0)}`} />} />
            <Area type="monotone" dataKey="equity" stroke="#38bdf8" strokeWidth={1.5} fill="url(#heq)" />
          </AreaChart>
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
const Breakdown = ({ byStructure, byRegime }) => {
  const rows = Object.entries(byStructure);
  const regimes = Object.entries(byRegime);
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
      <Equity curve={d.equityCurve} initial={d.summary?.initialCapital || 250000} />
      <div className="space-y-2">
        <Band icon={History} title="Trade Log" sub={`every ${intraday ? "intraday" : "daily"} trade · full detail · gross PnL`} />
        <TradeLog trades={d.trades || []} total={d.summary?.trades} />
      </div>
      <div className="space-y-2">
        <Band icon={Gauge} title="Breakdown" sub="per structure & per regime" />
        <Breakdown byStructure={d.byStructure || {}} byRegime={d.byRegime || {}} />
      </div>
    </div>
  );
};
