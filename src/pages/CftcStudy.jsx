import { useMemo } from "react";
import {
  BarChart, Bar, Cell, LineChart, Line, ComposedChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Legend,
} from "recharts";
import {
  Sigma, GitCompareArrows, Layers, FlaskConical, ExternalLink, ScrollText, ShieldAlert,
} from "lucide-react";
import { ResponsiveContainer } from "../lib/ResponsiveContainer";
import { Card } from "../components/primitives/Card";
import { Band } from "../components/primitives/Band";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import S from "../data/cftcStudy.json";

// ============================================================================
// CFTC Managed-Money positioning vs WTI — self-contained quantitative study.
// All numbers come from src/data/cftcStudy.json, distilled by
// CFTC_Analysis/05_export_dashboard.py from the analysis pipeline, so the
// in-app figures never drift from 02_analysis.py / 04_deep_analysis.py.
// ============================================================================
const C = { amber: "#f59e0b", emer: "#10b981", red: "#ef4444", sky: "#38bdf8", violet: "#a78bfa", mut: "#a1a1aa" };
const pct1 = (x) => `${x >= 0 ? "+" : ""}${(x * 100).toFixed(1)}%`;
const pct2 = (x) => `${x >= 0 ? "+" : ""}${(x * 100).toFixed(2)}%`;
const num = (x, d = 2) => (x == null ? "—" : `${x >= 0 ? "+" : ""}${x.toFixed(d)}`);
const yr = (d) => (d || "").slice(0, 4);

// Small stat tile matching the dashboard's KPI look.
const Stat = ({ big, lbl, tone = "text-zinc-100", sub }) => (
  <div className="bg-[#0e0f12] border border-[#1c1d22] rounded-lg p-3">
    <div className={`text-xl font-bold tracking-tight ${tone}`}>{big}</div>
    <div className="text-[10px] text-zinc-500 leading-snug mt-1">{lbl}</div>
    {sub && <div className="text-[9px] text-zinc-600 mt-1 font-mono">{sub}</div>}
  </div>
);

const PanelHead = ({ children, right }) => (
  <div className="px-4 py-2.5 border-b border-[#1c1d22] flex items-center justify-between gap-2">
    <span className="text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">{children}</span>
    {right && <span className="text-[10px] text-zinc-600 font-mono">{right}</span>}
  </div>
);

// ----------------------------------------------------------------------------
// Overview — headline + honest data-source note + link to the full deck
// ----------------------------------------------------------------------------
const Overview = () => (
  <Card padding={false}>
    <div className="p-4 flex items-start justify-between flex-wrap gap-3">
      <div className="flex items-center gap-3">
        <div className="w-1 h-12 rounded-sm bg-amber-500" />
        <div>
          <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-500">Quantitative study</div>
          <div className="text-2xl font-semibold text-zinc-100 leading-tight">Does CFTC positioning predict WTI?</div>
          <div className="text-[10px] text-zinc-600 mt-0.5 font-mono">
            Managed-Money net vs WTI spot · {S.meta.start} → {S.meta.end} · {S.meta.weeks} weeks
          </div>
        </div>
      </div>
      <a href="/cftc/presentation.html" target="_blank" rel="noreferrer"
        className="flex items-center gap-1.5 px-3 h-8 text-[11px] font-medium text-amber-400 border border-amber-500/30 bg-amber-500/[0.06] hover:bg-amber-500/10 transition-colors rounded">
        <ScrollText size={13} /> Open 8-slide deck <ExternalLink size={11} />
      </a>
    </div>

    <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-[#1c1d22] border-t border-[#1c1d22]">
      <div className="bg-[#0e0f12] p-3">
        <div className="text-xl font-bold text-sky-400">{num(S.relationship.chg_ret_mm)}</div>
        <div className="text-[10px] text-zinc-500 mt-1 leading-snug">Δposition vs same-week return → <b className="text-zinc-300">coincident</b>, not leading</div>
      </div>
      <div className="bg-[#0e0f12] p-3">
        <div className="text-xl font-bold text-amber-400">~0</div>
        <div className="text-[10px] text-zinc-500 mt-1 leading-snug">predictive corr. of positioning with 1–4wk returns (all HAC p&gt;0.29)</div>
      </div>
      <div className="bg-[#0e0f12] p-3">
        <div className="text-xl font-bold text-emerald-400">{pct1(S.extremes_decile.extreme_short["4w"].median)}</div>
        <div className="text-[10px] text-zinc-500 mt-1 leading-snug">median 4wk return after extreme net-short (vs {pct1(S.baseline["4w"].median)} base)</div>
      </div>
      <div className="bg-[#0e0f12] p-3">
        <div className="text-xl font-bold text-red-400">{S.backtest.perf.long_only.sharpe.toFixed(2)}</div>
        <div className="text-[10px] text-zinc-500 mt-1 leading-snug">yet OOS Sharpe &lt; {S.backtest.perf.buy_hold.sharpe.toFixed(2)} buy-hold — no tradeable edge</div>
      </div>
    </div>

    <div className="m-4 mt-3 bg-amber-500/[0.05] border border-amber-500/25 border-l-2 border-l-amber-500 rounded p-3 flex gap-2.5">
      <ShieldAlert size={15} className="text-amber-400 flex-shrink-0 mt-0.5" />
      <p className="text-[11px] text-zinc-400 leading-relaxed">
        <b className="text-zinc-200">Data note:</b> {S.meta.note}
      </p>
    </div>
  </Card>
);

// ----------------------------------------------------------------------------
// 1 · Relationship — cross-correlation + predictive slope table
// ----------------------------------------------------------------------------
const Relationship = () => {
  const ccf = useMemo(() => S.ccf.lags.map((lag, i) => ({ lag, corr: S.ccf.corr[i] })), []);
  const sigLabels = { z_roll52: "Rolling-52w z (tradeable)", z_full: "Full-sample z" };
  return (
    <div className="grid grid-cols-12 gap-3">
      <Card padding={false} className="col-span-12 lg:col-span-7">
        <PanelHead right={`Bartlett band ±${S.ccf.band.toFixed(2)}`}>Cross-correlation · Δposition vs return</PanelHead>
        <div className="h-60 px-2 py-2">
          <ResponsiveContainer>
            <BarChart data={ccf} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
              <CartesianGrid {...chartProps.grid} />
              <XAxis dataKey="lag" {...chartProps.axis} />
              <YAxis {...chartProps.axis} width={40} />
              <Tooltip content={<ChartTooltip />} cursor={{ fill: "#ffffff08" }} />
              <ReferenceLine y={S.ccf.band} stroke={C.mut} strokeDasharray="4 3" />
              <ReferenceLine y={-S.ccf.band} stroke={C.mut} strokeDasharray="4 3" />
              <ReferenceLine y={0} stroke="#3a3b41" />
              <Bar dataKey="corr" name="corr" isAnimationActive={false}>
                {ccf.map((d) => (
                  <Cell key={d.lag} fill={d.lag === 0 ? C.amber : d.lag < 0 ? C.sky : C.emer} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="px-4 py-2 border-t border-[#1c1d22] text-[9px] text-zinc-600 leading-snug">
          k&lt;0: return leads · k=0: same week · k&gt;0: position change leads. All correlation mass sits at lag 0
          (r={num(S.ccf.corr[S.ccf.lags.indexOf(0)])}); no lead bar clears the band → coincident, not predictive.
        </div>
      </Card>

      <Card padding={false} className="col-span-12 lg:col-span-5">
        <PanelHead right="Newey-West HAC p">Predictive slope · positioning → forward return</PanelHead>
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead>
              <tr className="text-[9px] uppercase tracking-wider text-zinc-600 border-b border-[#1c1d22]">
                <th className="text-left font-medium px-4 py-2">Signal</th>
                <th className="text-right font-medium px-2">1w</th>
                <th className="text-right font-medium px-2">2w</th>
                <th className="text-right font-medium px-4">4w</th>
              </tr>
            </thead>
            <tbody>
              {["z_roll52", "z_full"].map((sig) => (
                <tr key={sig} className="border-b border-[#15161a]">
                  <td className="px-4 py-2 text-zinc-300">{sigLabels[sig]}</td>
                  {["1w", "2w", "4w"].map((h) => {
                    const c = S.relationship.predictive[sig][h];
                    return (
                      <td key={h} className={`px-2 text-right font-mono ${h === "4w" ? "pr-4" : ""}`}>
                        <span className="text-zinc-300">{num(c.r)}</span>
                        <span className="text-zinc-600"> [{c.p.toFixed(2)}]</span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-3 border-t border-[#1c1d22] space-y-2">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-zinc-500">Granger Δposition → return</span>
            <span className="font-mono text-amber-400">p={S.granger.dpos_ret_p.toFixed(2)} <span className="text-zinc-600">(lag {S.granger.dpos_ret_lag})</span></span>
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-zinc-500">Granger return → Δposition</span>
            <span className="font-mono text-amber-400">p={S.granger.ret_dpos_p.toFixed(2)} <span className="text-zinc-600">(lag {S.granger.ret_dpos_lag})</span></span>
          </div>
          <p className="text-[9px] text-zinc-600 leading-snug pt-1">
            r [p] = Pearson correlation and its overlap-adjusted HAC p-value. Every slope is insignificant; neither
            Granger direction is causal — the relationship is contemporaneous comovement.
          </p>
        </div>
      </Card>
    </div>
  );
};

// ----------------------------------------------------------------------------
// 2 · Extremes — decile median returns + event-study path + bucket table
// ----------------------------------------------------------------------------
const Extremes = () => {
  const deciles = useMemo(() => Object.entries(S.decile_median).map(([d, v]) => ({
    d: +d, w1: v["1w"] * 100, w2: v["2w"] * 100, w4: v["4w"] * 100,
  })).sort((a, b) => a.d - b.d), []);
  const ev = useMemo(() => {
    const n = S.event_study.mid.mean.length;
    return Array.from({ length: n }, (_, k) => ({
      k,
      short: S.event_study.extreme_short?.mean?.[k],
      mid: S.event_study.mid?.mean?.[k],
      long: S.event_study.extreme_long?.mean?.[k],
    }));
  }, []);
  const buckets = [
    ["Decile top/bottom 10%", "extremes_decile"],
    ["Rolling-52w z > |1.5|", "extremes_rollz"],
  ];
  return (
    <div className="grid grid-cols-12 gap-3">
      <Card padding={false} className="col-span-12 lg:col-span-6">
        <PanelHead right="median %">Forward return by positioning decile</PanelHead>
        <div className="h-56 px-2 py-2">
          <ResponsiveContainer>
            <BarChart data={deciles} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
              <CartesianGrid {...chartProps.grid} />
              <XAxis dataKey="d" {...chartProps.axis} />
              <YAxis {...chartProps.axis} width={40} unit="%" />
              <Tooltip content={<ChartTooltip unit="%" />} cursor={{ fill: "#ffffff08" }} />
              <ReferenceLine y={0} stroke="#3a3b41" />
              <Bar dataKey="w1" name="1w" fill={C.sky} isAnimationActive={false} />
              <Bar dataKey="w2" name="2w" fill={C.amber} isAnimationActive={false} />
              <Bar dataKey="w4" name="4w" fill={C.emer} isAnimationActive={false} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="px-4 py-2 border-t border-[#1c1d22] text-[9px] text-zinc-600 leading-snug">
          Decile 1 = most net-short → 10 = most net-long. The relationship is non-monotonic — no clean "more long → worse" gradient.
        </div>
      </Card>

      <Card padding={false} className="col-span-12 lg:col-span-6">
        <PanelHead right="cumulative %">Event study · WTI path after an extreme</PanelHead>
        <div className="h-56 px-2 py-2">
          <ResponsiveContainer>
            <LineChart data={ev} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
              <CartesianGrid {...chartProps.grid} />
              <XAxis dataKey="k" {...chartProps.axis} unit="w" />
              <YAxis {...chartProps.axis} width={40} unit="%" />
              <Tooltip content={<ChartTooltip unit="%" />} />
              <ReferenceLine y={0} stroke="#3a3b41" />
              <Line type="monotone" dataKey="short" name="extreme short" stroke={C.emer} strokeWidth={2} dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="mid" name="baseline" stroke={C.mut} strokeWidth={1.4} dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="long" name="extreme long" stroke={C.red} strokeWidth={1.4} dot={false} isAnimationActive={false} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="px-4 py-2 border-t border-[#1c1d22] text-[9px] text-zinc-600 leading-snug">
          Mean cumulative path, weeks after the CFTC release. Washed-out shorts outpace baseline — but the mean is skewed by the 2016/2020 rebounds.
        </div>
      </Card>

      <Card padding={false} className="col-span-12">
        <PanelHead right="median % | mean % | hit | 95% boot-CI(mean) | Mann-Whitney p">Forward performance after extreme positioning · 4-week</PanelHead>
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead>
              <tr className="text-[9px] uppercase tracking-wider text-zinc-600 border-b border-[#1c1d22]">
                <th className="text-left font-medium px-4 py-2">Definition</th>
                <th className="text-left font-medium px-2">Bucket</th>
                <th className="text-right font-medium px-2">n</th>
                <th className="text-right font-medium px-2">median</th>
                <th className="text-right font-medium px-2">mean</th>
                <th className="text-right font-medium px-2">hit</th>
                <th className="text-right font-medium px-2">95% CI (mean)</th>
                <th className="text-right font-medium px-4">p</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-[#15161a] text-zinc-500">
                <td className="px-4 py-1.5">Baseline (all weeks)</td><td className="px-2">—</td><td className="px-2 text-right font-mono">{S.meta.weeks}</td>
                <td className="px-2 text-right font-mono">{pct2(S.baseline["4w"].median)}</td>
                <td className="px-2 text-right font-mono">{pct2(S.baseline["4w"].mean)}</td>
                <td className="px-2 text-right font-mono">{(S.baseline["4w"].hit * 100).toFixed(0)}%</td>
                <td className="px-2 text-right font-mono">—</td><td className="px-4 text-right font-mono">—</td>
              </tr>
              {buckets.map(([label, key]) =>
                ["extreme_short", "extreme_long"].map((bk) => {
                  const d = S[key][bk]["4w"];
                  const tone = bk === "extreme_short" ? "text-emerald-400" : "text-zinc-300";
                  return (
                    <tr key={key + bk} className="border-b border-[#15161a] hover:bg-white/[0.015]">
                      <td className="px-4 py-1.5 text-zinc-400">{label}</td>
                      <td className={`px-2 font-medium ${tone}`}>{bk.replace("extreme_", "")}</td>
                      <td className="px-2 text-right font-mono text-zinc-500">{S[key][bk].n}</td>
                      <td className={`px-2 text-right font-mono ${tone}`}>{pct2(d.median)}</td>
                      <td className="px-2 text-right font-mono text-zinc-400">{pct2(d.mean)}</td>
                      <td className="px-2 text-right font-mono text-zinc-400">{(d.hit * 100).toFixed(0)}%</td>
                      <td className="px-2 text-right font-mono text-zinc-500">[{pct1(d.ci_lo)}, {pct1(d.ci_hi)}]</td>
                      <td className={`px-4 text-right font-mono ${d.p != null && d.p < 0.1 ? "text-amber-400" : "text-zinc-500"}`}>{d.p != null ? d.p.toFixed(2) : "—"}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

// ----------------------------------------------------------------------------
// 3 · Deep-dive — OOS backtest, half-life, quantile reg, FDR, verdict
// ----------------------------------------------------------------------------
const DeepDive = () => {
  const eq = useMemo(() => S.backtest.dates.map((date, i) => ({
    date, bh: S.backtest.buy_hold[i], lo: S.backtest.long_only[i], ls: S.backtest.long_short[i],
  })), []);
  const acf = useMemo(() => S.half_life.acf.map((v, k) => ({ k, v })), []);
  const qr = useMemo(() => S.quantile.taus.map((tau, i) => ({
    tau, slope: S.quantile.slope[i], band: [S.quantile.lo[i], S.quantile.hi[i]],
  })), []);
  const p = S.backtest.perf;
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-12 gap-3">
        <Card padding={false} className="col-span-12 lg:col-span-8">
          <PanelHead right="growth of $1 · weekly non-overlap">Out-of-sample backtest of the one candidate edge</PanelHead>
          <div className="h-64 px-2 py-2">
            <ResponsiveContainer>
              <LineChart data={eq} margin={{ top: 8, right: 14, bottom: 4, left: 0 }}>
                <CartesianGrid {...chartProps.grid} />
                <XAxis dataKey="date" {...chartProps.axis} minTickGap={48} tickFormatter={yr} />
                <YAxis {...chartProps.axis} width={40} domain={["auto", "auto"]} />
                <Tooltip content={<ChartTooltip />} />
                <ReferenceLine y={1} stroke="#3a3b41" />
                <Line type="monotone" dataKey="bh" name="Buy & hold" stroke={C.mut} strokeWidth={1.5} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="lo" name="Contrarian long-only (z≤−1)" stroke={C.emer} strokeWidth={1.9} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="ls" name="Long-short" stroke={C.amber} strokeWidth={1.3} dot={false} isAnimationActive={false} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-3 gap-px bg-[#1c1d22] border-t border-[#1c1d22] text-center">
            {[
              ["Long-only", p.long_only.sharpe.toFixed(2), `ann ${pct1(p.long_only.ann)} · DD ${(p.long_only.dd * 100).toFixed(0)}%`, "text-emerald-400"],
              ["Buy & hold", p.buy_hold.sharpe.toFixed(2), `ann ${pct1(p.buy_hold.ann)} · DD ${(p.buy_hold.dd * 100).toFixed(0)}%`, "text-zinc-300"],
              ["Long-short", p.long_short.sharpe.toFixed(2), `ann ${pct1(p.long_short.ann)} · DD ${(p.long_short.dd * 100).toFixed(0)}%`, "text-red-400"],
            ].map(([l, sh, sub, tone]) => (
              <div key={l} className="bg-[#0e0f12] py-2.5">
                <div className="text-[9px] uppercase tracking-wider text-zinc-600">{l} · Sharpe</div>
                <div className={`text-lg font-bold ${tone}`}>{sh}</div>
                <div className="text-[9px] text-zinc-600 font-mono">{sub}</div>
              </div>
            ))}
          </div>
          <div className="px-4 py-2 border-t border-[#1c1d22] text-[9px] text-zinc-600 leading-snug">
            Point-in-time rolling-z signal, fixed a-priori thresholds (pseudo-OOS). The contrarian rule trails buy-and-hold;
            its Sharpe is indistinguishable from zero (block-bootstrap p(Sharpe≤0)={p.long_only.boot_p.toFixed(2)}), and unchanged net of 5 bps costs ({p.long_only.sharpe_5bps.toFixed(2)}).
          </div>
        </Card>

        <div className="col-span-12 lg:col-span-4 grid grid-cols-2 lg:grid-cols-1 gap-3">
          <Stat big={`≈${S.half_life.wks.toFixed(0)} wks`} tone="text-sky-400"
            lbl={<>Positioning mean-reversion <b className="text-zinc-300">half-life</b> — AR(1) ρ={S.half_life.rho.toFixed(2)}. A slow-moving context state.</>}
            sub={`ADF p=${S.half_life.adf_p.toFixed(3)} (stationary)`} />
          <Stat big={`AUC ${S.logit.auc.toFixed(2)}`} tone="text-amber-400"
            lbl={<>Logistic direction model on the z-score — a <b className="text-zinc-300">coin flip</b> (β={S.logit.beta.toFixed(2)}, p={S.logit.p.toFixed(2)}).</>}
            sub={`pseudo-R² ${S.logit.pseudo_r2.toFixed(3)}`} />
          <Stat big={`${S.fdr.n_survivors} / ${S.fdr.m}`} tone="text-red-400"
            lbl={<>bucket tests survive <b className="text-zinc-300">Benjamini-Hochberg</b> FDR at q={S.fdr.q}. The "edge" is look-where-you-looked noise.</>} />
        </div>
      </div>

      <div className="grid grid-cols-12 gap-3">
        <Card padding={false} className="col-span-12 lg:col-span-5">
          <PanelHead right={`AR(1) ρ=${S.half_life.rho.toFixed(2)}`}>Positioning autocorrelation (persistence)</PanelHead>
          <div className="h-48 px-2 py-2">
            <ResponsiveContainer>
              <BarChart data={acf} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
                <CartesianGrid {...chartProps.grid} />
                <XAxis dataKey="k" {...chartProps.axis} unit="w" interval={3} />
                <YAxis {...chartProps.axis} width={36} />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: "#ffffff08" }} />
                <ReferenceLine y={0.5} stroke={C.emer} strokeDasharray="4 3" />
                <ReferenceLine y={0} stroke="#3a3b41" />
                <Bar dataKey="v" name="autocorr" fill={C.sky} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="px-4 py-2 border-t border-[#1c1d22] text-[9px] text-zinc-600 leading-snug">
            Autocorrelation of MM net crosses 0.5 (green) near the {S.half_life.wks.toFixed(0)}-week half-life — crowding persists for months.
          </div>
        </Card>

        <Card padding={false} className="col-span-12 lg:col-span-7">
          <PanelHead right="4-week · %/σ">Quantile regression · positioning barely moves the tails</PanelHead>
          <div className="h-48 px-2 py-2">
            <ResponsiveContainer>
              <ComposedChart data={qr} margin={{ top: 8, right: 14, bottom: 4, left: 0 }}>
                <CartesianGrid {...chartProps.grid} />
                <XAxis dataKey="tau" {...chartProps.axis} />
                <YAxis {...chartProps.axis} width={40} />
                <Tooltip content={<ChartTooltip />} />
                <ReferenceLine y={0} stroke="#3a3b41" />
                <Area dataKey="band" name="95% CI" stroke="none" fill={C.amber} fillOpacity={0.14} isAnimationActive={false} />
                <Line type="monotone" dataKey="slope" name="slope" stroke={C.amber} strokeWidth={2} dot={{ r: 3, fill: C.amber }} isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <div className="px-4 py-2 border-t border-[#1c1d22] text-[9px] text-zinc-600 leading-snug">
            Slope of the 4-week return on the positioning z-score, across return quantiles τ. Small, sign-flipping, every CI straddles zero.
          </div>
        </Card>
      </div>

      {/* Verdict */}
      <Card>
        <div className="flex items-start gap-3">
          <div className="w-1 self-stretch rounded-sm bg-amber-500" />
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-amber-400 mb-1">Verdict</div>
            <p className="text-[14px] text-zinc-200 leading-relaxed font-medium">
              CFTC Managed-Money positioning is a <b>contemporaneous crowding / sentiment gauge</b> for WTI — <b>not</b> a standalone timing signal.
            </p>
            <ul className="mt-2 space-y-1.5 text-[12px] text-zinc-400 leading-relaxed list-disc pl-4">
              <li><b className="text-zinc-300">Coincident, not causal.</b> All cross-correlation mass sits at lag 0; neither Granger direction is significant (p={S.granger.dpos_ret_p.toFixed(2)} / {S.granger.ret_dpos_p.toFixed(2)}).</li>
              <li><b className="text-zinc-300">Persistent state.</b> ~{S.half_life.wks.toFixed(0)}-week mean-reversion half-life — a context regime, not a crisp entry trigger.</li>
              <li><b className="text-zinc-300">No robust edge.</b> The lone net-short bounce ({pct1(S.extremes_decile.extreme_short["4w"].median)} median) fails out-of-sample (Sharpe {p.long_only.sharpe.toFixed(2)} &lt; {p.buy_hold.sharpe.toFixed(2)}) and dies under multiple-testing correction ({S.fdr.n_survivors}/{S.fdr.m}).</li>
              <li><b className="text-zinc-300">Use it as context</b> — combine with inventories &amp; term structure rather than trading it alone.</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};

// ----------------------------------------------------------------------------
export const PageCftcStudy = () => (
  <div className="space-y-3">
    <Band icon={Sigma} title="CFTC Positioning Study" sub="Managed-Money net vs WTI — does speculative positioning predict price?" />
    <Overview />

    <Band icon={GitCompareArrows} title="1 · Relationship" sub="Coincident momentum vs leading indicator" />
    <Relationship />

    <Band icon={Layers} title="2 · Extremes & forward returns" sub="Decile buckets, event study, robustness" />
    <Extremes />

    <Band icon={FlaskConical} title="3 · Mathematical deep-dive" sub="Causality, dynamics, out-of-sample tradeability & multiple testing" />
    <DeepDive />
  </div>
);
