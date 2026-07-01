// ============================================================================
// EIA Release Lab — a LIVE forward engine.
//   • UPCOMING: a leak-free forecast for the NEXT (not-yet-released) crude print —
//     the model's expected build/draw, structural lean, catalyst strength & impact
//     curve. It refreshes itself (on-visit + a scheduled routine) so it always
//     describes the next release, and is graded automatically once it lands.
//   • LAST: the most recent published week, graded (expected vs real, scorecard,
//     cross-check, intraday reaction).
//   • LIVE RECORD: how the engine's own frozen forward calls have actually done.
// Reads /api/release-lab (analytics/release_lab.py). The Run button forces a refresh.
// ============================================================================
import { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ReferenceDot,
  ComposedChart, Area,
} from "recharts";
import { ResponsiveContainer } from "../lib/ResponsiveContainer";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { Band } from "../components/primitives/Band";
import { SourceTag } from "../components/primitives/SourceTag";
import { AsOf } from "../components/primitives/AsOf";
import { InfoDot } from "../components/primitives/InfoDot";
import { fmt, fmtSigned } from "../lib/format";
import { useLive } from "../lib/useLive";
import { chartProps } from "../lib/chart-theme";
import {
  Play, Loader2, CheckCircle2, XCircle, MinusCircle, Radio, CalendarClock, Beaker, History, Target,
} from "lucide-react";

const EMPTY_PRED = {
  expected_wow: null, expected_surprise: 0, lean: "Neutral", confidence: "low",
  factors: [], products: [], scenarios: [], catalyst_r2: null, catalyst_n: null, asof: null,
};
const FALLBACK = {
  status: "awaiting-release",
  track_record: null, live_record: null,
  upcoming: {
    status: "awaiting-release",
    target: { label: "next EIA crude release", period: null, release_date: null, days_until: null },
    current: {}, prediction: EMPTY_PRED, impact_curve: { points: [] }, intraday: null, result: null,
  },
  last: {
    target: { label: "EIA crude release", period: null, release_date: null },
    current: {}, prediction: EMPTY_PRED, impact_curve: { points: [] },
    intraday: null, result: null, comparison: null, scorecard: null,
  },
};

const DIR = {
  Bullish: { fg: "text-emerald-400", bg: "bg-emerald-500/10", br: "border-emerald-500/30", dot: "bg-emerald-500" },
  Bearish: { fg: "text-red-400", bg: "bg-red-500/10", br: "border-red-500/30", dot: "bg-red-500" },
  Neutral: { fg: "text-amber-400", bg: "bg-amber-500/10", br: "border-amber-500/30", dot: "bg-amber-500" },
};
const LIGHT = (ok) =>
  ok === true ? { fg: "text-emerald-400", br: "border-emerald-500/30", bg: "bg-emerald-500/[0.06]", Icon: CheckCircle2 }
  : ok === false ? { fg: "text-red-400", br: "border-red-500/30", bg: "bg-red-500/[0.06]", Icon: XCircle }
  : { fg: "text-amber-400", br: "border-amber-500/30", bg: "bg-amber-500/[0.06]", Icon: MinusCircle };

const SPREAD = { wti: "WTI", brent: "Brent", brent_wti: "Brent–WTI", wti_m1m2: "WTI M1–M2",
  crack_321_wti: "3-2-1 crack", ho_wti: "HO crack", gasoil_brent: "Gasoil crack" };

const EXPL = {
  page: "The lesson here: what the EIA's weekly U.S. crude-inventory number does to the oil price. " +
    "Inventory = how much crude sits in storage tanks. A draw (stocks fall) is usually bullish, a build (stocks rise) bearish — " +
    "but the price only reacts to the SURPRISE vs what was expected, and only when inventories are a strong driver that week.",
  upcoming: "A live forecast for the NEXT crude release, built only from data known before it. It refreshes automatically as new data lands and is graded once the number prints.",
  expected: "Our leak-free estimate of the week's crude build/draw — the stand-in for the market consensus the price is already positioned for. Built only from data known before the release.",
  expSurprise: "Zero by design: the model expects the print to land on its own forecast. Only the miss — the real surprise — moves price.",
  catalyst: "How strongly the crude surprise has driven WTI in conditions like today's (R² of release-day move on the surprise). Near 0 = inventories barely move price right now; other forces rule.",
  actual: "The crude build/draw the EIA actually reported vs last week, in million barrels (MMbbl). Negative = draw, positive = build.",
  realSurprise: "Actual − Expected. A bigger draw than expected is bullish; a bigger build is bearish. Sized in σ — standard deviations, i.e. how unusual the miss is vs a typical week.",
  wtiMove: "How WTI actually moved on the release vs the tiny move the surprise implied. A gap means non-inventory forces drove the day.",
  attrInv: "The part of the day's WTI move explained by the crude inventory surprise.",
  attrMacro: "The part explained by the broad market that day (S&P 500 risk-on/off + the US dollar).",
  attrOther: "Everything left over — OPEC, geopolitics, positioning, oil-specific news. Usually the biggest piece.",
  scorecard: "Did the call work? Three checks: did we forecast the number, did the surprise break our way, and did price actually follow the surprise.",
  curve: "Predicted release-day WTI move = β × surprise. A near-flat line means inventories barely move WTI in this regime — so the gap to the actual dot is the real story.",
  intraday: "How the reaction builds minute-by-minute after the 10:30 ET release: the (near-flat) predicted path vs the live actual path. R² per horizon shows inventories explain almost none of the intraday move.",
  liveRecord: "How the engine's OWN frozen forward calls have done since it went live — forecast accuracy vs the naive seasonal guess, and how often the pre-release lean called the surprise. Distinct from the backtest below.",
  trSurprise: "Among sizeable surprises in history, how often WTI moved the way the surprise implied. 50% = coin-flip; higher = a real edge.",
  trLean: "How often our pre-release bias (lean) called the direction of the surprise.",
  trMae: "Average miss of our expected build/draw vs a naive 'just use the seasonal average' guess (million barrels; lower is better). Shows the forecast has genuine skill.",
};

const drawWord = (v) => (v == null ? "—" : v < 0 ? "draw" : "build");
const pct = (v, d = 2) => (v == null ? "—" : `${fmtSigned(v, d)}%`);
const toneFor = (v, bullishWhenNeg = true) =>
  v == null ? "text-zinc-300" : (bullishWhenNeg ? v <= 0 : v >= 0) ? "text-emerald-400" : "text-red-400";

const Tile = ({ label, value, sub, tone = "text-zinc-100", info }) => (
  <div className="bg-[#0e0f12] p-3">
    <div className="text-[9px] uppercase tracking-wider text-zinc-500 flex items-center gap-1">
      {label}{info && <InfoDot text={info} />}
    </div>
    <div className={`font-mono text-2xl ${tone}`}>{value}</div>
    {sub != null && <div className="text-[9px] text-zinc-600 leading-tight mt-0.5">{sub}</div>}
  </div>
);

// ---- Shared "Expected" (prediction) content -------------------------------
const ExpectedBody = ({ p }) => {
  const leanColor = DIR[p.lean] || DIR.Neutral;
  return (
    <>
      <div className={`mx-4 mb-3 rounded-md border ${leanColor.br} ${leanColor.bg} px-3 py-2 flex items-center gap-2`}>
        <span className={`w-2.5 h-2.5 rounded-full ${leanColor.dot}`} />
        <span className={`font-mono text-sm font-semibold ${leanColor.fg}`}>{p.lean}</span>
        <span className="text-[10px] uppercase tracking-wider text-zinc-500">lean · conf {p.confidence}</span>
      </div>
      <div className="grid grid-cols-3 gap-px bg-[#1c1d22] border-y border-[#1c1d22]">
        <Tile label="Expected" info={EXPL.expected} value={fmtSigned(p.expected_wow, 1)} tone={toneFor(p.expected_wow)} sub={`MMbbl ${drawWord(p.expected_wow)}`} />
        <Tile label="Exp. surprise" info={EXPL.expSurprise} value={fmtSigned(p.expected_surprise, 1)} tone="text-zinc-300" sub="≈0 (consensus)" />
        <Tile label="Catalyst" info={EXPL.catalyst} value={p.catalyst_r2 == null ? "—" : `R² ${fmt(p.catalyst_r2, 2)}`}
          tone={(p.catalyst_r2 ?? 0) >= 0.05 ? "text-emerald-400" : "text-amber-400"}
          sub={`${(p.catalyst_r2 ?? 0) >= 0.05 ? "drives" : "weak"} · n=${p.catalyst_n ?? "—"}`} />
      </div>
      {p.scenarios?.length > 0 && (
        <div className="px-4 pt-3">
          <div className="text-[9px] uppercase tracking-wider text-zinc-600 mb-1.5">Scenarios · predicted WTI move</div>
          <div className="grid grid-cols-3 gap-2">
            {p.scenarios.map((s, i) => (
              <div key={i} className="rounded-md border border-[#1c1d22] bg-[#0e0f12] p-2 text-center">
                <div className="text-[9px] text-zinc-500 leading-tight h-7">{s.label}</div>
                <div className={`font-mono text-sm ${toneFor(s.pred_move_pct, false)}`}>{pct(s.pred_move_pct)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      {p.factors?.length > 0 && (
        <ol className="px-4 py-3 space-y-1">
          {p.factors.slice(0, 3).map((f, i) => (
            <li key={i} className="text-[11px] text-zinc-400 leading-snug flex gap-1.5">
              <span className="text-zinc-600 font-mono">{i + 1}.</span><span>{f}</span>
            </li>
          ))}
        </ol>
      )}
    </>
  );
};

// ---- Real (post-release result) content -----------------------------------
const RealBody = ({ r }) => {
  const verdictColor = DIR[r.verdict?.direction] || DIR.Neutral;
  return (
    <>
      <div className={`mx-4 mb-3 rounded-md border ${verdictColor.br} ${verdictColor.bg} px-3 py-2 flex items-center gap-2`}>
        <span className={`w-2.5 h-2.5 rounded-full ${verdictColor.dot}`} />
        <span className={`font-mono text-sm font-semibold ${verdictColor.fg}`}>{r.verdict?.direction}</span>
        <span className="text-[10px] uppercase tracking-wider text-zinc-500">verdict · conf {r.verdict?.confidence}</span>
      </div>
      <div className="grid grid-cols-3 gap-px bg-[#1c1d22] border-y border-[#1c1d22]">
        <Tile label="Actual" info={EXPL.actual} value={fmtSigned(r.actual_wow, 1)} tone={toneFor(r.actual_wow)} sub={`MMbbl ${drawWord(r.actual_wow)}`} />
        <Tile label="Real surprise" info={EXPL.realSurprise} value={fmtSigned(r.real_surprise, 1)} tone={toneFor(r.real_surprise)} sub={`${fmtSigned(r.real_surprise_z, 1)}σ · ${r.real_surprise_dir}`} />
        <Tile label="WTI on print" info={EXPL.wtiMove} value={pct(r.actual_move_pct, 1)} tone={toneFor(r.actual_move_pct, false)} sub={`pred ${pct(r.pred_move_pct)}`} />
      </div>
      {r.attribution && (
        <div className="px-4 pt-3 pb-1">
          <div className="text-[9px] uppercase tracking-wider text-zinc-600 mb-1.5 flex items-center gap-1">
            Move attribution · what drove it <InfoDot text="The day's WTI move split into the part from the inventory surprise, the part from the broad market, and everything else." />
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="rounded-md border border-[#1c1d22] bg-[#0e0f12] p-2">
              <div className="text-[9px] text-zinc-500 flex items-center justify-center gap-1">Inventory <InfoDot text={EXPL.attrInv} /></div>
              <div className="font-mono text-sm text-sky-400">{pct(r.attribution.inventory_pct)}</div>
            </div>
            <div className="rounded-md border border-[#1c1d22] bg-[#0e0f12] p-2">
              <div className="text-[9px] text-zinc-500 flex items-center justify-center gap-1">Macro <InfoDot text={EXPL.attrMacro} /></div>
              <div className="font-mono text-sm text-zinc-300">{r.attribution.macro_pct == null ? "—" : pct(r.attribution.macro_pct)}</div>
            </div>
            <div className="rounded-md border border-[#1c1d22] bg-[#0e0f12] p-2">
              <div className="text-[9px] text-zinc-500 flex items-center justify-center gap-1">Other <InfoDot text={EXPL.attrOther} /></div>
              <div className={`font-mono text-sm ${toneFor(r.attribution.residual_pct, false)}`}>{pct(r.attribution.residual_pct)}</div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// ---- Countdown pill --------------------------------------------------------
const Countdown = ({ days }) => {
  if (days == null) return null;
  const soon = days <= 2;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono border ${
      soon ? "text-emerald-300 border-emerald-500/30 bg-emerald-500/10" : "text-zinc-400 border-[#2a2b31] bg-[#0e0f12]"}`}>
      <CalendarClock size={11} />
      {days <= 0 ? "due now" : days === 1 ? "in 1 day" : `in ${days} days`}
    </span>
  );
};

// ---- Scorecard -------------------------------------------------------------
const Scorecard = ({ scorecard }) => (
  <Card>
    <SectionTitle sub="last print · prediction vs reality">Scorecard <InfoDot text={EXPL.scorecard} /></SectionTitle>
    {!scorecard ? (
      <div className="text-[11px] text-zinc-500 py-2">Awaiting the print to grade the call.</div>
    ) : (
      <>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {scorecard.lights.map((l) => {
            const c = LIGHT(l.ok);
            return (
              <div key={l.key} className={`rounded-lg border ${c.br} ${c.bg} p-3`}>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase tracking-wider text-zinc-400">{l.label}</span>
                  <c.Icon size={15} className={c.fg} />
                </div>
                <div className={`font-mono text-xl font-semibold mt-1 ${c.fg}`}>{l.grade}</div>
                <div className="text-[10px] text-zinc-500 leading-tight mt-0.5">{l.detail}</div>
              </div>
            );
          })}
        </div>
        <p className="text-[12px] text-zinc-300 leading-snug mt-3">{scorecard.net}</p>
      </>
    )}
  </Card>
);

// ---- Track record ----------------------------------------------------------
const hitTone = (v) => (v == null ? "text-zinc-300" : v >= 0.55 ? "text-emerald-400" : v >= 0.45 ? "text-amber-400" : "text-red-400");
const Row = ({ label, value, sub, tone = "text-zinc-100", info }) => (
  <div className="flex items-center justify-between gap-2">
    <span className="text-[11px] text-zinc-400 flex items-center gap-1">{label}{info && <InfoDot text={info} />}</span>
    <div className="text-right">
      <span className={`font-mono text-[13px] ${tone}`}>{value}</span>
      {sub && <span className="text-[9px] text-zinc-600 ml-1.5">{sub}</span>}
    </div>
  </div>
);
const TrackRecord = ({ track }) => {
  if (!track) return null;
  const Col = ({ w, title }) => (
    <div className="flex-1">
      <div className="text-[9px] uppercase tracking-wider text-zinc-600 mb-2 text-center">{title}</div>
      <div className="space-y-2">
        <Row label="Surprise → price" info={EXPL.trSurprise} value={w.surprise_hit_rate == null ? "—" : `${(w.surprise_hit_rate * 100).toFixed(0)}%`}
          tone={hitTone(w.surprise_hit_rate)} sub={w.surprise_hit_n ? `n=${w.surprise_hit_n}` : ""} />
        <Row label="Lean called it" info={EXPL.trLean} value={w.lean?.hit_rate == null ? "—" : `${(w.lean.hit_rate * 100).toFixed(0)}%`}
          tone={hitTone(w.lean?.hit_rate)} sub={w.lean?.n ? `n=${w.lean.n}` : ""} />
        <Row label="Model / seasonal MAE" info={EXPL.trMae} value={w.mae ? `${fmt(w.mae.model, 1)} / ${fmt(w.mae.seasonal, 1)}` : "—"}
          tone={w.mae && w.mae.model < w.mae.seasonal ? "text-emerald-400" : "text-amber-400"} />
        <Row label="Avg favorable move" value={w.avg_fav_move_pct == null ? "—" : pct(w.avg_fav_move_pct)}
          tone={toneFor(w.avg_fav_move_pct, false)} />
      </div>
    </div>
  );
  return (
    <Card>
      <SectionTitle sub="backtested" action={<SourceTag source="derived" note={track.note} />}>Track record</SectionTitle>
      <div className="flex gap-6">
        <Col w={track.recent} title="Last 52" />
        <div className="w-px bg-[#1c1d22]" />
        <Col w={track.all} title="All history" />
      </div>
    </Card>
  );
};

// ---- Live record (the engine's OWN forward calls) --------------------------
const LiveRecord = ({ live }) => {
  if (!live) return null;
  const graded = live.n || 0;
  const skill = live.mae != null && live.mae_seasonal != null ? live.mae < live.mae_seasonal : null;
  return (
    <Card>
      <SectionTitle sub="frozen forward calls, graded" action={<SourceTag source="derived"
        note="Every pre-release forecast is frozen to disk, then graded when the week prints — an honest, growing out-of-sample record of the live engine (separate from the backtest)." />}>
        Live record <InfoDot text={EXPL.liveRecord} />
      </SectionTitle>
      {graded < 3 ? (
        <div className="text-[11px] text-zinc-500 py-1 leading-snug">
          <span className="font-mono text-zinc-300">{graded}</span> graded · <span className="font-mono text-zinc-300">{live.pending || 0}</span> pending.
          The live track record starts filling as each frozen forecast prints — check back after a few releases.
        </div>
      ) : (
        <div className="space-y-2">
          <Row label="Forward calls graded" value={`${graded}`} sub={live.pending ? `${live.pending} pending` : ""} tone="text-zinc-200" />
          <Row label="Forecast MAE vs seasonal" value={`${fmt(live.mae, 1)} / ${fmt(live.mae_seasonal, 1)}`}
            tone={skill ? "text-emerald-400" : "text-amber-400"} sub="MMbbl" />
          <Row label="Lean called the surprise" value={live.lean_hit_rate == null ? "—" : `${(live.lean_hit_rate * 100).toFixed(0)}%`}
            tone={hitTone(live.lean_hit_rate)} />
          {live.recent?.length > 0 && (
            <div className="pt-1 border-t border-[#1c1d22] space-y-1">
              {live.recent.slice(-4).map((e) => (
                <div key={e.period} className="flex items-center justify-between text-[10px] font-mono">
                  <span className="text-zinc-600">{e.period}</span>
                  <span className="text-zinc-500">exp {fmtSigned(e.expected_wow, 1)} · act {fmtSigned(e.actual_wow, 1)}</span>
                  <span className={e.lean_hit === true ? "text-emerald-400" : e.lean_hit === false ? "text-red-400" : "text-zinc-600"}>
                    {e.lean} {e.lean_hit === true ? "✓" : e.lean_hit === false ? "✗" : ""}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </Card>
  );
};

// ---- Impact curve ----------------------------------------------------------
const ImpactCurve = ({ curve, result }) => {
  const data = (curve?.points || []).map((p) => ({ surprise: p.surprise, regime: p.regime_pct, overall: p.overall_pct }));
  if (!data.length) return null;
  const rp = result?.realized_point;
  return (
    <>
      <div className="flex items-center flex-wrap gap-x-4 gap-y-1 text-[9px] uppercase tracking-wider text-zinc-500 mb-1 px-1">
        <span className="flex items-center gap-1.5"><span className="w-3 h-[2px] bg-sky-500" /> This regime</span>
        <span className="flex items-center gap-1.5"><span className="w-3 border-t border-dashed border-zinc-500" /> All-history</span>
        {rp?.actual_pct != null && <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-400" /> Actual</span>}
        {rp?.pred_regime_pct != null && <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-sky-400" /> Predicted</span>}
      </div>
      <div className="h-60">
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 8, right: 12, bottom: 16, left: 4 }}>
            <CartesianGrid {...chartProps.grid} />
            <XAxis type="number" dataKey="surprise" {...chartProps.axis} domain={["dataMin", "dataMax"]}
              tickFormatter={(v) => v.toFixed(0)}
              label={{ value: "surprise (MMbbl) · draw ← → build", position: "bottom", offset: 2, fill: "#6b6d75", fontSize: 9 }} />
            <YAxis {...chartProps.axis} width={42} tickFormatter={(v) => `${v}%`} />
            <Tooltip contentStyle={{ background: "#0a0b0e", border: "1px solid #2a2b31", fontSize: 11 }}
              labelFormatter={(v) => `surprise ${fmtSigned(v, 1)} MMbbl`}
              formatter={(val, name) => [`${Number(val).toFixed(2)}%`, name === "regime" ? "This regime" : "All-history"]} />
            <ReferenceLine x={0} stroke="#52525b" strokeDasharray="3 3"
              label={{ value: "in line", position: "top", fill: "#71717a", fontSize: 8 }} />
            <ReferenceLine y={0} stroke="#3a3b41" />
            <Line type="monotone" dataKey="overall" stroke="#71717a" strokeWidth={1} strokeDasharray="4 3" dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="regime" stroke="#38bdf8" strokeWidth={1.8} dot={false} isAnimationActive={false} />
            {rp && <ReferenceLine x={rp.surprise} stroke="#f59e0b" strokeDasharray="2 3"
              label={{ value: "real", position: "top", fill: "#f59e0b", fontSize: 8 }} />}
            {rp?.pred_regime_pct != null && <ReferenceDot x={rp.surprise} y={rp.pred_regime_pct} r={4} fill="#38bdf8" stroke="#0a0b0e" />}
            {rp?.actual_pct != null && <ReferenceDot x={rp.surprise} y={rp.actual_pct} r={5} fill="#f59e0b" stroke="#0a0b0e" />}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </>
  );
};

// ---- Intraday reaction -----------------------------------------------------
const r2Tone = (v) => (v == null ? "text-zinc-400" : v >= 0.1 ? "text-emerald-400" : v >= 0.03 ? "text-amber-400" : "text-zinc-500");
const IntradayReaction = ({ intraday }) => {
  if (!intraday) return null;
  const rows = intraday.horizons || [];
  const featured = (intraday.headline_min || [5, 30, 60]).map((m) => rows.find((r) => r.min === m)).filter(Boolean);
  const pred = intraday.path?.predicted || [];
  const act = intraday.path?.actual || [];
  const byMin = {};
  pred.forEach((p) => { byMin[p.min] = { ...(byMin[p.min] || { min: p.min }), pred: p.pct, lo: p.lo, hi: p.hi }; });
  act.forEach((a) => { byMin[a.min] = { ...(byMin[a.min] || { min: a.min }), actual: a.pct }; });
  const data = Object.values(byMin).sort((a, b) => a.min - b.min)
    .map((d) => ({ ...d, band: d.lo != null && d.hi != null ? [d.lo, d.hi] : undefined }));
  const hasPath = data.some((d) => d.actual != null) || pred.length > 1;

  return (
    <Card padding={false}>
      <div className="p-4 pb-1">
        <SectionTitle sub={`reaction by horizon · ${intraday.vol_regime_used} vol`}
          action={<SourceTag source="derived"
            note={`Per-horizon OLS of WTI cumulative return on the surprise, ${intraday.model_n} historical releases on the 1-min tape. Predicted = β×surprise ±RMSE; actual = live Yahoo 5-min path.`} />}>
          Intraday reaction <InfoDot text={EXPL.intraday} />
        </SectionTitle>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 px-4 pt-2">
        {featured.map((r) => {
          const has = r.actual_pct != null;
          const c = r.hit == null ? LIGHT(null) : LIGHT(r.hit);
          return (
            <div key={r.min} className={`rounded-lg border p-3 ${has ? c.br + " " + c.bg : "border-[#1c1d22] bg-[#0e0f12]"}`}>
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase tracking-wider text-zinc-400">+{r.min} min</span>
                {has && <c.Icon size={14} className={c.fg} />}
              </div>
              <div className={`font-mono text-2xl mt-1 ${has ? toneFor(r.actual_pct, false) : "text-zinc-600"}`}>{has ? pct(r.actual_pct) : "—"}</div>
              <div className="text-[9px] text-zinc-600 leading-tight mt-0.5">
                {r.predicted_pct != null ? <>pred {pct(r.predicted_pct)} · </> : ""}<span className={r2Tone(r.r2)}>R² {fmt(r.r2, 2)}</span>
              </div>
            </div>
          );
        })}
      </div>
      <div className="px-3 pt-3 pb-4">
        {hasPath ? (
          <>
            <div className="flex items-center flex-wrap gap-x-4 gap-y-1 text-[9px] uppercase tracking-wider text-zinc-500 mb-1 px-1">
              <span className="flex items-center gap-1.5"><span className="w-3 h-[2px] bg-amber-400" /> Actual</span>
              <span className="flex items-center gap-1.5"><span className="w-3 border-t border-dashed border-sky-500" /> Predicted</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-2 bg-sky-500/20" /> ±1σ</span>
            </div>
            <div className="h-56">
              <ResponsiveContainer>
                <ComposedChart data={data} margin={{ top: 8, right: 12, bottom: 16, left: 4 }}>
                  <CartesianGrid {...chartProps.grid} />
                  <XAxis type="number" dataKey="min" {...chartProps.axis} domain={[0, "dataMax"]}
                    ticks={[0, 5, 15, 30, 60, 120]} tickFormatter={(v) => `${v}m`}
                    label={{ value: "minutes after 10:30 ET release", position: "bottom", offset: 2, fill: "#6b6d75", fontSize: 9 }} />
                  <YAxis {...chartProps.axis} width={44} tickFormatter={(v) => `${v}%`} />
                  <Tooltip contentStyle={{ background: "#0a0b0e", border: "1px solid #2a2b31", fontSize: 11 }}
                    labelFormatter={(v) => `+${v} min`}
                    formatter={(val, name) => (name === "band" || val == null) ? [null, null] : [`${Number(val).toFixed(2)}%`, name === "actual" ? "Actual" : "Predicted"]} />
                  <ReferenceLine y={0} stroke="#3a3b41" />
                  <Area dataKey="band" stroke="none" fill="#38bdf8" fillOpacity={0.12} connectNulls isAnimationActive={false} />
                  <Line dataKey="pred" stroke="#38bdf8" strokeWidth={1.2} strokeDasharray="4 3" dot={false} connectNulls isAnimationActive={false} />
                  <Line dataKey="actual" stroke="#f59e0b" strokeWidth={1.8} dot={false} connectNulls isAnimationActive={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </>
        ) : (
          <div className="rounded-md border border-dashed border-[#2a2b31] p-5 text-center text-[11px] text-zinc-500">
            The live reaction path appears once the release prints.
          </div>
        )}
      </div>
    </Card>
  );
};

// ===========================================================================
export const PageReleaseLab = () => {
  const { data, live } = useLive("/api/release-lab", FALLBACK, useLive.REFRESH.hourly);
  const [override, setOverride] = useState(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);

  const view = override || data;
  const up = view.upcoming || FALLBACK.upcoming;
  const last = view.last || FALLBACK.last;
  const ut = up.target || FALLBACK.upcoming.target;
  const lt = last.target || FALLBACK.last.target;
  const r = last.result;

  const runPipeline = async () => {
    setRunning(true); setError(null);
    try {
      const res = await fetch("/api/release-lab/run", { method: "POST", headers: { Accept: "application/json" } });
      const json = await res.json();
      if (!res.ok || json.error) throw new Error(json.error || `HTTP ${res.status}`);
      setOverride(json);
    } catch (e) {
      setError(e.message || "run failed");
    } finally { setRunning(false); }
  };

  const RunBtn = (
    <button onClick={runPipeline} disabled={running}
      className={`flex items-center gap-2 px-3.5 h-9 rounded-md font-semibold text-[11px] tracking-wide transition-all ${
        running ? "bg-zinc-800 text-zinc-400 cursor-wait" : "bg-amber-500 text-zinc-950 hover:bg-amber-400 active:scale-[0.98]"}`}>
      {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={13} fill="currentColor" />}
      {running ? "Refreshing…" : "Refresh now"}
    </button>
  );

  return (
    <div className="space-y-3">
      {/* Header */}
      <Card>
        <SectionTitle sub="live forward engine · crude inventories → WTI" action={RunBtn}>
          EIA Release Lab <InfoDot text={EXPL.page} title="What this teaches" />
        </SectionTitle>
        <div className="flex items-center gap-2 flex-wrap text-[11px] text-zinc-500">
          <span className="inline-flex items-center gap-1 text-emerald-400">
            <Radio size={12} className="animate-pulse" /> auto-updating
          </span>
          <span className="text-zinc-600">·</span>
          <span>Forecasts the next release and grades itself when it prints — no button needed.</span>
          {view.generatedAtET && <span className="text-zinc-600 font-mono ml-auto">refreshed {view.generatedAtET}</span>}
        </div>
        {error && (
          <div className="mt-2 rounded-md border border-red-500/30 bg-red-500/10 p-2 text-[11px] text-red-300">
            Refresh failed: <span className="font-mono">{error}</span>
          </div>
        )}
      </Card>

      {/* ============ UPCOMING — the live forward forecast ============ */}
      <Band icon={Target} title="Upcoming release · live forecast"
        sub={ut.label} right={<Countdown days={ut.days_until} />} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Card padding={false}>
          <div className="p-4 pb-2">
            <SectionTitle sub={`forecast · updates automatically · frozen ${up.prediction?.asof || "—"}`}
              action={<SourceTag live={live} source="eia"
                note="One-step-ahead, leak-free forecast for the next release: the model's expected build/draw, structural lean, catalyst strength & impact curve. Refreshes on-visit and on a schedule; graded once the number prints." />}>
              <span className="text-sky-400">Expected</span> <InfoDot text={EXPL.upcoming} />
            </SectionTitle>
          </div>
          <ExpectedBody p={up.prediction || EMPTY_PRED} />
        </Card>

        <Card padding={false}>
          <div className="p-4 pb-1">
            <SectionTitle sub="predicted WTI move = β × surprise">Impact curve <InfoDot text={EXPL.curve} /></SectionTitle>
          </div>
          <div className="px-3 pb-4"><ImpactCurve curve={up.impact_curve} result={null} /></div>
        </Card>
      </div>

      {/* ============ LAST — the graded print ============ */}
      <Band icon={History} title="Last release · graded"
        sub={lt.label} right={r ? <AsOf date={lt.release_date} /> : <span className="text-[10px] text-zinc-600">awaiting print</span>} />
      <Scorecard scorecard={last.scorecard} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Card padding={false}>
          <div className="p-4 pb-2">
            <SectionTitle sub={`frozen ${last.prediction?.asof || "—"}`}><span className="text-sky-400">Expected</span></SectionTitle>
          </div>
          <ExpectedBody p={last.prediction || EMPTY_PRED} />
        </Card>

        <Card padding={false}>
          <div className="p-4 pb-2">
            <SectionTitle sub={r ? `post-release · ${lt.release_date}` : "awaiting print"}><span className="text-amber-400">Real</span></SectionTitle>
          </div>
          {!r ? (
            <div className="m-4 mt-2 rounded-md border border-dashed border-[#2a2b31] p-8 text-center text-[11px] text-zinc-500">
              The actual print, real surprise and graded call appear automatically once the EIA releases.
            </div>
          ) : <RealBody r={r} />}
        </Card>
      </div>

      {/* Impact curve with realized dot + intraday reaction for the graded print */}
      <Card padding={false}>
        <div className="p-4 pb-1">
          <SectionTitle sub="WTI move = β × surprise · with realized point" action={<AsOf date={lt.release_date} />}>
            Impact curve · last print <InfoDot text={EXPL.curve} />
          </SectionTitle>
        </div>
        <div className="px-3 pb-4"><ImpactCurve curve={last.impact_curve} result={r} /></div>
      </Card>

      <IntradayReaction intraday={last.intraday} />

      {/* Records + affected products */}
      <Band icon={Beaker} title="How the engine is doing" sub="live calls + backtest" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <LiveRecord live={view.live_record} />
        <div className="lg:col-span-2"><TrackRecord track={view.track_record} /></div>
      </div>
      <Card>
        <SectionTitle sub="by sensitivity">Affected products</SectionTitle>
        <div className="flex flex-wrap gap-1.5">
          {(up.prediction?.products || []).map((s) => (
            <span key={s} className="font-mono text-[11px] px-2 py-1 rounded bg-[#15161a] text-zinc-300 border border-[#1c1d22]">
              {SPREAD[s] || s}
            </span>
          ))}
        </div>
      </Card>
    </div>
  );
};
