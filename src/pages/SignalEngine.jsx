import { useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from "recharts";
import { ResponsiveContainer } from "../lib/ResponsiveContainer";
import { TrendingUp, Layers, ListChecks, ChevronDown, Circle, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { Band } from "../components/primitives/Band";
import { SourceTag } from "../components/primitives/SourceTag";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { useLive } from "../lib/useLive";
import { fmt, fmtSigned } from "../lib/format";

// ----------------------------------------------------------------------------
// Strategy Backtest — the Phase-2 relative-value mean-reversion strategy run
// over the provided 15-min crude data. The trade log is the centrepiece: every
// trade, its gross PnL (slippage 0), and full detail.
// ----------------------------------------------------------------------------

const FALLBACK = {
  generatedAt: "—", mode: "local", live: false, firstBar: "—", lastBar: "—", bars: 0,
  regime: "—", strategy: { name: "Regime-conditioned RV mean-reversion", params: {} },
  summary: { trades: 0, grossPnl: 0, winRate: 0, avgWin: 0, avgLoss: 0, profitFactor: null,
    expectancy: 0, avgHoldMin: 0, maxDrawdown: 0, endingEquity: 250000, initialCapital: 250000,
    byExitReason: {}, byDirection: {} },
  byStructure: {}, equityCurve: [], trades: [], openPositions: [], openCount: 0,
};

const regimeText = (r) => (typeof r === "string" ? r : r?.label ?? "—");
const dirColor = (d) => (d === "LONG" ? "text-emerald-400" : "text-red-400");
const pnlColor = (n) => (n > 0 ? "text-emerald-400" : n < 0 ? "text-red-400" : "text-zinc-400");

// ----------------------------------------------------------------------------
// Hero scoreboard
// ----------------------------------------------------------------------------
const Hero = ({ d, live, stale }) => {
  const s = d.summary;
  const stats = [
    { k: "Trades", v: s.trades, sub: `${d.openCount} still open` },
    { k: "Gross P&L", v: fmtSigned(s.grossPnl, 0), sub: `exp ${fmtSigned(s.expectancy, 0)}/trade`, color: pnlColor(s.grossPnl) },
    { k: "Win rate", v: `${(s.winRate * 100).toFixed(0)}%`, sub: `+${fmt(s.avgWin, 0)} / ${fmt(s.avgLoss, 0)} avg` },
    { k: "Profit factor", v: s.profitFactor ?? "∞", sub: `max DD ${fmtSigned(s.maxDrawdown, 0)}` },
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
              {d.bars} bars · {d.firstBar} → {d.lastBar} · {d.mode === "live" ? "LIVE feed" : "provided data"} · gross, slippage 0
            </div>
          </div>
        </div>
        <SourceTag live={live && !stale} stale={stale} source="signalEngine"
          note="The Phase-2 mean-reversion strategy backtested over the provided 15-min crude bars. Trade log + equity are computed here." />
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 divide-x divide-[#1c1d22]">
        {stats.map((m) => (
          <div key={m.k} className="p-4">
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
        <span className="text-[10px] text-zinc-600">gross · slippage 0 · 1,000 bbl/contract</span>
      </div>
      <div className="overflow-x-auto max-h-[560px] overflow-y-auto">
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
                    <td className="px-2 py-2 text-right font-mono text-zinc-400 tabular-nums">{fmtSigned(t.entryZ, 2)}</td>
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
                          <span className="text-zinc-300">{t.strategy}</span> · regime {regimeText(t.regime)} · historical edge {(t.histHitRate * 100).toFixed(0)}% · confidence {t.confidence}/100
                        </div>
                        <div className="flex flex-wrap gap-x-5 gap-y-1 text-[10px] font-mono text-zinc-500">
                          <span>spread {t.entrySpread} → {t.exitSpread}</span>
                          <span>z {fmtSigned(t.entryZ, 2)} → {fmtSigned(t.exitZ, 2)}</span>
                          <span>held {t.holdBars} bars ({t.holdMin}m)</span>
                          <span>MAE/MFE {fmtSigned(t.mae, 0)} / {fmtSigned(t.mfe, 0)}</span>
                          <span>contracts {t.contracts}</span>
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
                  <td className="px-2 py-2 text-right font-mono text-zinc-400 tabular-nums">{(s.winRate * 100).toFixed(0)}%</td>
                  <td className={`px-2 py-2 text-right font-mono tabular-nums ${pnlColor(s.pnl)}`}>{fmtSigned(s.pnl, 0)}</td>
                  <td className="px-2 py-2 text-right font-mono text-zinc-400 tabular-nums">{s.profitFactor ?? "∞"}</td>
                  <td className="px-3 py-2 text-right font-mono text-emerald-400/70 tabular-nums">{(s.histHitRate * 100).toFixed(0)}%</td>
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

// ============================================================================
// PAGE
// ============================================================================
export const PageSignalEngine = () => {
  const { data, live, stale } = useLive("/api/signal-engine", FALLBACK, useLive.REFRESH.fast);
  const d = data || FALLBACK;
  return (
    <div className="space-y-4">
      <Hero d={d} live={live} stale={stale} />
      <Equity curve={d.equityCurve} initial={d.summary?.initialCapital || 250000} />
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
