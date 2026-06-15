import { useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from "recharts";
import { ResponsiveContainer } from "../lib/ResponsiveContainer";
import { TrendingUp, Layers, ListChecks, ChevronDown, Circle, Radio } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { Band } from "../components/primitives/Band";
import { SourceTag } from "../components/primitives/SourceTag";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { fmt, fmtSigned } from "../lib/format";
import { useLive } from "../lib/useLive";

const FALLBACK = { summary: { trades: 0 }, byStructure: [], equityCurve: [], trades: [], params: {}, openPositions: [], signalBoard: [], signalLog: [] };

const confColor = (c) => (c >= 75 ? "text-emerald-400" : c >= 55 ? "text-amber-400" : "text-zinc-500");
const confBg = (c) => (c >= 75 ? "bg-emerald-500/70" : c >= 55 ? "bg-amber-500/70" : "bg-zinc-600/70");

const usd = (v, d = 0) => (v == null ? "—" : `${v < 0 ? "-" : ""}$${Math.abs(v).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d })}`);
const fmtT = (iso) => (iso ? iso.slice(5, 16).replace("T", " ") : "");  // "06-12 14:00"
const DIR_COLOR = { LONG: "text-emerald-400", SHORT: "text-sky-400" };

// ----------------------------------------------------------------------------
const MetricTile = ({ label, value, sub, tone = "zinc" }) => {
  const c = tone === "pos" ? "text-emerald-400" : tone === "neg" ? "text-red-400" : tone === "amber" ? "text-amber-400" : "text-zinc-100";
  return (
    <div className="bg-[#0e0f12] p-3">
      <div className="text-[9px] uppercase tracking-[0.14em] text-zinc-600">{label}</div>
      <div className={`font-mono text-xl mt-1 ${c}`}>{value}</div>
      {sub && <div className="text-[9px] text-zinc-600 mt-0.5">{sub}</div>}
    </div>
  );
};

// ----------------------------------------------------------------------------
// Live Now — what the strategy is doing RIGHT NOW: open positions + the current
// dislocation (z) of every structure (|z| >= 1.5 is a live entry signal).
// ----------------------------------------------------------------------------
const ZGauge = ({ s }) => {
  const z = s.z ?? 0;
  const pct = Math.max(3, Math.min(97, 50 + (z / 3) * 50));   // map [-3,3] -> [0,100]
  const hot = s.signal || s.inPosition;
  const col = !hot ? "#52525b" : z < 0 ? "#10b981" : "#f59e0b";
  return (
    <div className="flex items-center gap-2 py-1">
      <span className="text-[10px] font-mono text-zinc-400 w-24 truncate">{s.structure}</span>
      <div className="flex-1 h-3 bg-[#0a0b0e] relative rounded-sm overflow-hidden">
        <div className="absolute inset-y-0 left-1/2 w-px bg-[#3a3b41]" />
        {/* entry threshold marks at ±1.5σ → 25% / 75% */}
        <div className="absolute inset-y-0 w-px bg-amber-500/30" style={{ left: "25%" }} />
        <div className="absolute inset-y-0 w-px bg-amber-500/30" style={{ left: "75%" }} />
        <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-2 h-2 rounded-full"
          style={{ left: `${pct}%`, background: col, boxShadow: hot ? `0 0 6px ${col}` : "none" }} />
      </div>
      <span className="font-mono text-[10px] w-12 text-right" style={{ color: col }}>{fmtSigned(z, 2)}σ</span>
      <span className="w-12 text-[8px] uppercase tracking-wider text-right">
        {s.inPosition ? <span className="text-emerald-400">open</span> : s.signal ? <span className="text-amber-400">signal</span> : <span className="text-zinc-700">—</span>}
      </span>
    </div>
  );
};

const LiveNow = ({ open, board, isLive, lastBar }) => (
  <Card padding={false}>
    <div className="px-4 py-2.5 border-b border-[#1c1d22] flex items-center justify-between">
      <span className="text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase flex items-center gap-2">
        Live now
        {isLive && <span className="flex items-center gap-1 text-[9px] text-emerald-400"><Circle size={5} fill="#10b981" className="animate-pulse" /></span>}
      </span>
      <span className="text-[9px] font-mono text-zinc-600">as of {lastBar ? String(lastBar).slice(5, 16) : "—"}</span>
    </div>
    <div className="grid grid-cols-12">
      {/* Open positions */}
      <div className="col-span-12 md:col-span-6 p-3 border-b md:border-b-0 md:border-r border-[#1c1d22]">
        <div className="text-[9px] uppercase tracking-wider text-zinc-600 mb-2">Open positions ({open.length})</div>
        {open.length ? (
          <div className="space-y-1.5">
            {open.map((o) => {
              const up = (o.unrealized_pnl ?? 0) >= 0;
              return (
                <div key={o.structure} className="flex items-center justify-between text-[11px] py-1 border-b border-[#15161a] last:border-0">
                  <span className="flex items-center gap-2 min-w-0">
                    <span className={`text-[9px] font-semibold uppercase ${DIR_COLOR[o.direction]}`}>{o.direction}</span>
                    <span className="text-zinc-200 font-mono truncate">{o.structure}</span>
                  </span>
                  <span className="flex items-center gap-3 font-mono text-[10px] flex-shrink-0">
                    <span className="text-zinc-600">{String(o.entry_time).slice(11, 16)} · {o.min_held}m</span>
                    <span className="text-zinc-500">z {fmtSigned(o.entry_z, 1)}→{fmtSigned(o.current_z, 1)}</span>
                    <span className={up ? "text-emerald-400" : "text-red-400"}>{usd(o.unrealized_pnl)}</span>
                  </span>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-[11px] text-zinc-600 py-2">Flat — no open positions right now.</div>
        )}
      </div>
      {/* Signal board */}
      <div className="col-span-12 md:col-span-6 p-3">
        <div className="text-[9px] uppercase tracking-wider text-zinc-600 mb-1.5">Dislocation board · |z| ≥ 1.5 fires a trade</div>
        {(board || []).map((s) => <ZGauge key={s.structure} s={s} />)}
      </div>
    </div>
  </Card>
);

// ----------------------------------------------------------------------------
const EquityCurve = ({ data, initial }) => {
  const rows = (data || []).map((p, i) => ({ i, t: fmtT(p.timestamp), equity: p.equity, open: p.open_positions }));
  const last = rows.at(-1)?.equity ?? initial;
  const up = last >= initial;
  return (
    <Card padding={false} className="col-span-12 lg:col-span-8">
      <div className="px-4 py-2.5 border-b border-[#1c1d22] flex items-center justify-between">
        <span className="text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">Equity curve</span>
        <span className={`font-mono text-[12px] ${up ? "text-emerald-400" : "text-red-400"}`}>
          {usd(last)} <span className="text-zinc-600">({fmtSigned(((last - initial) / initial) * 100, 2)}%)</span>
        </span>
      </div>
      <div className="h-64 px-2 py-2">
        <ResponsiveContainer>
          <AreaChart data={rows} margin={{ top: 8, right: 16, bottom: 4, left: 4 }}>
            <defs>
              <linearGradient id="eqFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity={0.25} />
                <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid {...chartProps.grid} />
            <XAxis dataKey="i" {...chartProps.axis} tickFormatter={(i) => rows[i]?.t?.slice(0, 8) ?? ""} minTickGap={60} />
            <YAxis {...chartProps.axis} width={62} domain={["auto", "auto"]} tickFormatter={(v) => `$${Math.round(v / 1000)}k`} />
            <Tooltip content={<ChartTooltip source="backtest" />} />
            <ReferenceLine y={initial} stroke="#3a3b41" strokeDasharray="3 3" label={{ value: "start", fill: "#71717a", fontSize: 9, position: "right" }} />
            <Area type="stepAfter" dataKey="equity" name="Equity" stroke="#10b981" strokeWidth={1.6} fill="url(#eqFill)" isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
const TestSetup = ({ d }) => {
  const p = d.params || {};
  const rows = [
    ["Strategy", d.strategy],
    ["Basis", d.basis],
    ["Regime", d.regime],
    ["Data", `${d.dataBars ?? "—"} bars`],
    ["Span", (d.dataSpan || "").replace(" -> ", " → ")],
    ["Entry / target / stop", `${p.zEntry}σ / ${p.zTarget}σ / ${p.zStop}σ`],
    ["Lookback", `${p.lookback} bars`],
    ["Capital", usd(p.initialCapital)],
  ];
  return (
    <Card padding={false} className="col-span-12 lg:col-span-4">
      <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">Test setup</div>
      <div className="p-3 space-y-1.5">
        {rows.map(([k, v]) => (
          <div key={k} className="flex items-start justify-between gap-3 text-[11px]">
            <span className="text-zinc-600 uppercase tracking-wider text-[9px] mt-0.5 flex-shrink-0">{k}</span>
            <span className="text-zinc-300 text-right font-mono text-[10px] leading-snug">{v}</span>
          </div>
        ))}
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
const PerStructure = ({ rows }) => {
  const traded = (rows || []).filter((r) => r.trades > 0);
  const maxAbs = Math.max(1, ...traded.map((r) => Math.abs(r.netPnl || 0)));
  return (
    <Card padding={false} className="col-span-12 lg:col-span-7">
      <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">Per-structure bifurcation</div>
      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <thead>
            <tr className="text-[9px] uppercase tracking-wider text-zinc-600 border-b border-[#1c1d22]">
              <th className="text-left font-medium px-4 py-2">Structure</th>
              <th className="text-right font-medium px-2">Trades</th>
              <th className="text-right font-medium px-2">Win%</th>
              <th className="text-right font-medium px-2">PF</th>
              <th className="text-right font-medium px-2">Hold</th>
              <th className="text-left font-medium px-3 w-28">Gross PnL</th>
            </tr>
          </thead>
          <tbody>
            {traded.map((r) => {
              const pos = (r.netPnl || 0) >= 0;
              return (
                <tr key={r.structure} className="border-b border-[#15161a] last:border-0 hover:bg-white/[0.015]">
                  <td className="px-4 py-1.5 text-zinc-300 font-mono">{r.structure}</td>
                  <td className="px-2 text-right font-mono text-zinc-400">{r.trades} <span className="text-zinc-600">({r.longs}L/{r.shorts}S)</span></td>
                  <td className="px-2 text-right font-mono text-zinc-400">{r.winRate}%</td>
                  <td className="px-2 text-right font-mono text-zinc-500">{r.profitFactor ?? "—"}</td>
                  <td className="px-2 text-right font-mono text-zinc-600">{Math.round(r.avgHoldMin)}m</td>
                  <td className="px-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-[#15161a] relative overflow-hidden">
                        <div className={`h-full ${pos ? "bg-emerald-500/70" : "bg-red-500/70"}`} style={{ width: `${(Math.abs(r.netPnl) / maxAbs) * 100}%` }} />
                      </div>
                      <span className={`font-mono text-[10px] w-14 text-right ${pos ? "text-emerald-400" : "text-red-400"}`}>{usd(r.netPnl)}</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
const Frequencies = ({ summary }) => {
  const Block = ({ title, obj, color = "#a78bfa" }) => {
    const entries = Object.entries(obj || {});
    const tot = entries.reduce((s, [, v]) => s + v, 0) || 1;
    return (
      <div>
        <div className="text-[9px] uppercase tracking-wider text-zinc-600 mb-1.5">{title}</div>
        <div className="space-y-1">
          {entries.map(([k, v]) => (
            <div key={k} className="flex items-center gap-2">
              <span className="text-[10px] text-zinc-400 w-24 truncate font-mono">{k}</span>
              <div className="flex-1 h-1.5 bg-[#15161a] overflow-hidden">
                <div className="h-full" style={{ width: `${(v / tot) * 100}%`, background: color, opacity: 0.6 }} />
              </div>
              <span className="text-[10px] text-zinc-500 font-mono w-6 text-right">{v}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };
  return (
    <Card padding={false} className="col-span-12 lg:col-span-5">
      <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">Trade frequency</div>
      <div className="p-3 grid grid-cols-2 gap-x-4 gap-y-3">
        <Block title="By exit reason" obj={summary.byExitReason} color="#10b981" />
        <Block title="By direction" obj={summary.byDirection} color="#38bdf8" />
        <Block title="By product" obj={summary.byProduct} color="#f59e0b" />
        <Block title="By structure" obj={summary.byStructure} color="#a78bfa" />
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
const TradeLog = ({ trades }) => {
  const [open, setOpen] = useState(null);
  return (
    <Card padding={false}>
      <div className="px-4 py-2.5 border-b border-[#1c1d22] text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase flex items-center justify-between">
        Full trade log
        <span className="text-[9px] text-zinc-600 normal-case tracking-normal">{(trades || []).length} trades · click a row for the setup</span>
      </div>
      <div className="overflow-x-auto max-h-[460px] overflow-y-auto">
        <table className="w-full text-[11px]">
          <thead className="sticky top-0 bg-[#0e0f12] z-10">
            <tr className="text-[9px] uppercase tracking-wider text-zinc-600 border-b border-[#1c1d22]">
              <th className="text-left font-medium px-4 py-2">#</th>
              <th className="text-left font-medium px-2">Structure</th>
              <th className="text-left font-medium px-2">Dir</th>
              <th className="text-left font-medium px-2">Entry</th>
              <th className="text-left font-medium px-2">Exit</th>
              <th className="text-right font-medium px-2">z in</th>
              <th className="text-right font-medium px-2">z out</th>
              <th className="text-left font-medium px-2">Why</th>
              <th className="text-right font-medium px-2">Hold</th>
              <th className="text-right font-medium px-4">PnL</th>
              <th className="w-5" />
            </tr>
          </thead>
          <tbody>
            {(trades || []).map((t) => {
              const on = open === t.trade_id;
              const pos = (t.net_pnl || 0) >= 0;
              return [
                <tr key={t.trade_id} onClick={() => setOpen(on ? null : t.trade_id)} className="border-b border-[#15161a] hover:bg-white/[0.02] cursor-pointer">
                  <td className="px-4 py-1.5 text-zinc-500 font-mono">{t.trade_id}</td>
                  <td className="px-2 text-zinc-300 font-mono">{t.structure}</td>
                  <td className={`px-2 font-semibold text-[10px] ${DIR_COLOR[t.direction]}`}>{t.direction}</td>
                  <td className="px-2 text-zinc-500 font-mono text-[10px]">{fmtT(t.entry_time)}</td>
                  <td className="px-2 text-zinc-500 font-mono text-[10px]">{fmtT(t.exit_time)}</td>
                  <td className="px-2 text-right font-mono text-zinc-400">{fmtSigned(t.entry_z, 2)}</td>
                  <td className="px-2 text-right font-mono text-zinc-600">{fmtSigned(t.exit_z, 2)}</td>
                  <td className="px-2 text-[9px] uppercase tracking-wider text-zinc-500">{t.exit_reason}</td>
                  <td className="px-2 text-right font-mono text-zinc-600">{t.holding_min}m</td>
                  <td className={`px-4 text-right font-mono ${pos ? "text-emerald-400" : "text-red-400"}`}>{usd(t.net_pnl)}</td>
                  <td className="px-1 text-zinc-600"><ChevronDown size={11} className={`transition-transform ${on ? "rotate-180" : ""}`} /></td>
                </tr>,
                on && (
                  <tr key={t.trade_id + "-d"} className="bg-[#0a0b0e] border-b border-[#15161a]">
                    <td colSpan={11} className="px-4 py-2.5">
                      <p className="text-[11px] text-zinc-400 leading-relaxed">{t.strategy_desc}</p>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-[9px] text-zinc-600 uppercase tracking-wider">
                        <span>legs <span className="text-zinc-400 normal-case font-mono">
                          {[1, 2, 3].map((i) => t[`leg${i}_sym`] ? `${t[`leg${i}_qty`] > 0 ? "+" : ""}${t[`leg${i}_qty`]} ${t[`leg${i}_sym`]} ${fmt(t[`leg${i}_entry`], 3)}→${fmt(t[`leg${i}_exit`], 3)}` : null).filter(Boolean).join(" · ")}
                        </span></span>
                        <span>spread <span className="text-zinc-400 normal-case font-mono">{fmt(t.entry_spread_mid, 3)} → {fmt(t.exit_spread_mid, 3)}</span></span>
                        <span>MAE/MFE <span className="text-zinc-400 normal-case font-mono">{usd(t.mae)} / {usd(t.mfe)}</span></span>
                        <span>equity <span className="text-zinc-400 normal-case font-mono">{usd(t.equity_after)}</span></span>
                      </div>
                    </td>
                  </tr>
                ),
              ];
            })}
            {!(trades || []).length && <tr><td colSpan={11} className="px-4 py-3 text-[10px] text-zinc-600">No backtest yet — run <code className="text-zinc-400">python BackTesting/backtest.py</code>.</td></tr>}
          </tbody>
        </table>
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
// Signal Log — every opportunity the framework has generated, with timestamp,
// regime, instrument, rationale, confidence and subsequent performance.
// ----------------------------------------------------------------------------
const SignalLog = ({ log, isLive }) => {
  const [open, setOpen] = useState(null);
  const [filter, setFilter] = useState("all");
  const all = log || [];
  const rows = [...all].reverse().filter((s) =>
    filter === "all" ? true : filter === "live" ? s.status === "OPEN" : s.status === "CLOSED");
  const liveN = all.filter((s) => s.status === "OPEN").length;

  return (
    <Card padding={false}>
      <div className="px-4 py-2.5 border-b border-[#1c1d22] flex items-center justify-between flex-wrap gap-2">
        <span className="text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase flex items-center gap-2">
          Signal Log
          {isLive && <Circle size={5} fill="#10b981" className="animate-pulse" />}
          <span className="text-[9px] text-zinc-600 normal-case tracking-normal">{all.length} opportunities · {liveN} live</span>
        </span>
        <div className="flex items-center gap-1">
          {["all", "live", "closed"].map((f) => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-2 h-5 text-[9px] uppercase tracking-wider transition-colors ${filter === f ? "bg-amber-500/10 text-amber-400 border border-amber-500/30" : "text-zinc-500 border border-transparent hover:text-zinc-300"}`}>
              {f}
            </button>
          ))}
        </div>
      </div>
      <div className="overflow-x-auto max-h-[480px] overflow-y-auto">
        <table className="w-full text-[11px]">
          <thead className="sticky top-0 bg-[#0e0f12] z-10">
            <tr className="text-[9px] uppercase tracking-wider text-zinc-600 border-b border-[#1c1d22]">
              <th className="text-left font-medium px-4 py-2">Generated</th>
              <th className="text-left font-medium px-2">Regime</th>
              <th className="text-left font-medium px-2">Instrument</th>
              <th className="text-left font-medium px-2">Dir</th>
              <th className="text-left font-medium px-2 w-24">Confidence</th>
              <th className="text-left font-medium px-2">Status</th>
              <th className="text-right font-medium px-2">Performance</th>
              <th className="text-left font-medium px-3">Outcome</th>
              <th className="w-5" />
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => {
              const on = open === s.id;
              const live = s.status === "OPEN";
              const up = (s.pnl ?? 0) >= 0;
              return [
                <tr key={s.id} onClick={() => setOpen(on ? null : s.id)} className="border-b border-[#15161a] hover:bg-white/[0.02] cursor-pointer">
                  <td className="px-4 py-1.5 font-mono text-[10px] text-zinc-400">{String(s.timestamp).slice(5, 16)}</td>
                  <td className="px-2 text-[10px] text-zinc-500">{s.regime}</td>
                  <td className="px-2 font-mono text-zinc-200">{s.instrument}</td>
                  <td className={`px-2 text-[10px] font-semibold ${DIR_COLOR[s.direction]}`}>{s.direction}</td>
                  <td className="px-2">
                    <div className="flex items-center gap-1.5">
                      <div className="flex-1 h-1.5 bg-[#15161a] overflow-hidden"><div className={`h-full ${confBg(s.confidence)}`} style={{ width: `${s.confidence}%` }} /></div>
                      <span className={`font-mono text-[10px] w-6 text-right ${confColor(s.confidence)}`}>{s.confidence}</span>
                    </div>
                  </td>
                  <td className="px-2">
                    {live
                      ? <span className="text-[9px] uppercase tracking-wider text-emerald-400 flex items-center gap-1"><Circle size={4} fill="#10b981" className="animate-pulse" />open</span>
                      : <span className="text-[9px] uppercase tracking-wider text-zinc-600">closed</span>}
                  </td>
                  <td className={`px-2 text-right font-mono ${up ? "text-emerald-400" : "text-red-400"}`}>{usd(s.pnl)}{!s.realized && <span className="text-zinc-600 text-[9px]"> unr.</span>}</td>
                  <td className="px-3 text-[10px] text-zinc-500">{s.outcome}</td>
                  <td className="px-1 text-zinc-600"><ChevronDown size={11} className={`transition-transform ${on ? "rotate-180" : ""}`} /></td>
                </tr>,
                on && (
                  <tr key={s.id + "-d"} className="bg-[#0a0b0e] border-b border-[#15161a]">
                    <td colSpan={9} className="px-4 py-2.5">
                      <p className="text-[11px] text-zinc-400 leading-relaxed">{s.rationale}</p>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-[9px] text-zinc-600 uppercase tracking-wider">
                        <span>entry z <span className="text-zinc-400 font-mono normal-case">{fmtSigned(s.entryZ, 2)}σ</span></span>
                        <span>hist. edge <span className="text-zinc-400 font-mono normal-case">{s.histEdgePct}%</span></span>
                        <span>held <span className="text-zinc-400 font-mono normal-case">{s.heldMin}m</span></span>
                        {s.exitReason && <span>exit <span className="text-zinc-400 normal-case">{s.exitReason} @ {String(s.exitTime).slice(11, 16)}</span></span>}
                      </div>
                    </td>
                  </tr>
                ),
              ];
            })}
            {!rows.length && <tr><td colSpan={9} className="px-4 py-3 text-[10px] text-zinc-600">No signals yet — run <code className="text-zinc-400">python BackTesting/backtest.py --live</code>.</td></tr>}
          </tbody>
        </table>
      </div>
    </Card>
  );
};

// ----------------------------------------------------------------------------
export const PageBackTesting = () => {
  // Poll fast — the backtest is re-run continuously against the live data feed.
  const { data, live, stale } = useLive("/api/backtest", FALLBACK, useLive.REFRESH.fast);
  const s = data.summary || {};
  const hasData = (s.trades ?? 0) > 0;
  const isLive = data.live && !stale;

  return (
    <div className="space-y-3">
      <Band icon={Radio} title="Live Signal Engine" sub="The regime framework running on live market data — every opportunity tracked"
        right={
          <div className="flex items-center gap-2.5">
            {isLive ? (
              <span className="flex items-center gap-1 text-[9px] uppercase tracking-wider text-emerald-400">
                <Circle size={5} fill="#10b981" className="animate-pulse" /> Live
              </span>
            ) : data.mode === "local" ? (
              <span className="text-[9px] uppercase tracking-wider text-zinc-600">Snapshot</span>
            ) : null}
            {data.lastBar && <span className="text-[9px] font-mono text-zinc-500 hidden sm:inline">latest bar {String(data.lastBar).slice(5, 16)}</span>}
            <SourceTag live={live && !stale} stale={stale} source="backtest"
              note={`${data.strategy || "Mean-reversion"} · ${data.basis || "gross"} · ${data.mode === "live" ? "live feed" : "local snapshot"} · ${data.dataBars || 0} bars`} />
          </div>
        } />

      {/* Headline metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-px bg-[#1c1d22]">
        <MetricTile label="Opportunities" value={(data.signalLog || []).length} sub={`${(data.signalLog || []).filter((x) => x.status === "OPEN").length} live now`} tone="amber" />
        <MetricTile label="Win rate" value={hasData ? `${s.winRate}%` : "—"} sub={hasData ? `${s.wins}W / ${s.losses}L` : ""} />
        <MetricTile label="Net PnL (gross)" value={usd(s.netPnl)} tone={(s.netPnl ?? 0) >= 0 ? "pos" : "neg"} />
        <MetricTile label="Profit factor" value={s.profitFactor ?? "—"} />
        <MetricTile label="Expectancy" value={usd(s.expectancyPerTrade)} sub="per closed trade" tone={(s.expectancyPerTrade ?? 0) >= 0 ? "pos" : "neg"} />
        <MetricTile label="Max drawdown" value={hasData ? `${s.maxDrawdownPct}%` : "—"} sub={hasData ? usd(s.maxDrawdown) : ""} tone="neg" />
      </div>

      <Band icon={ListChecks} title="Signal Log" sub="Every opportunity the framework has generated · timestamp · regime · instrument · rationale · confidence · performance" />
      <SignalLog log={data.signalLog} isLive={isLive} />

      <Band icon={Circle} title="Live Now" sub="Open positions & current dislocations at the latest bar" />
      <LiveNow open={data.openPositions || []} board={data.signalBoard || []} isLive={isLive} lastBar={data.lastBar} />

      <Band icon={TrendingUp} title="Equity & Setup" />
      <div className="grid grid-cols-12 gap-3">
        <EquityCurve data={data.equityCurve} initial={data.params?.initialCapital ?? 250000} />
        <TestSetup d={data} />
      </div>

      <Band icon={Layers} title="Historical Validation" sub="Closed-trade performance by structure & type — the edge behind the confidence scores" />
      <div className="grid grid-cols-12 gap-3">
        <PerStructure rows={data.byStructure} />
        <Frequencies summary={s} />
      </div>

      <Card>
        <p className="text-[10px] text-zinc-500 leading-relaxed">
          <span className="text-amber-400/90 font-semibold uppercase tracking-wider">Live engine · gross basis.</span>{" "}
          The framework runs continuously on the live 15-min crude feed, generating and journaling every opportunity with its
          regime, rationale and a confidence score (grounded in the Phase-2 historical reversion edge), then tracking each one's
          performance forward. PnL is gross (costs off) to isolate signal quality; the sample is still small — add more daily data
          and keep <code className="text-zinc-400">BackTesting/backtest.py --live</code> running to build significance.
          Methodology in <code className="text-zinc-400">BackTesting/IDEATION.md</code>.
        </p>
      </Card>
    </div>
  );
};
