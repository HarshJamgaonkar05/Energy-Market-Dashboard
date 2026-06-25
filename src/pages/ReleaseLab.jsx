// ============================================================================
// EIA Release Lab — the "expected surprise vs real surprise" experiment for ONE
// crude release. Reads /api/release-lab (written by analytics/release_lab.py):
//   • PREDICTION  — frozen from data BEFORE the release: expected build/draw
//                   (consensus proxy), the structural lean, and the impact curve.
//   • RESULT      — filled in when you press "Run the latest EIA release": the
//                   actual print, the REAL surprise, the verdict, the cross-check,
//                   a 3-light SCORECARD and the realized point on the curve.
//   • TRACK RECORD— the framework backtested on history, so one experiment isn't
//                   read as luck.
// The big button POSTs /api/release-lab/run, which spawns the Python pipeline.
// ============================================================================
import { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ReferenceDot,
} from "recharts";
import { ResponsiveContainer } from "../lib/ResponsiveContainer";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { SourceTag } from "../components/primitives/SourceTag";
import { AsOf } from "../components/primitives/AsOf";
import { fmt, fmtSigned } from "../lib/format";
import { useLive } from "../lib/useLive";
import { chartProps } from "../lib/chart-theme";
import { FlaskConical, Play, Loader2, CheckCircle2, XCircle, MinusCircle } from "lucide-react";

const FALLBACK = {
  status: "awaiting-release",
  target: { label: "EIA crude release", period: null, release_date: null },
  current: {},
  prediction: {
    expected_wow: null, expected_surprise: 0, lean: "Neutral", confidence: "low",
    headline: "Run analytics/release_lab.py to build the prediction.",
    factors: [], products: [], scenarios: [], catalyst_r2: null, catalyst_n: null,
    beta_pct_per_mmbbl: null, beta_overall_pct_per_mmbbl: null, sigma_mmbbl: null, narrative: "",
  },
  impact_curve: { points: [] },
  track_record: null, result: null, comparison: null, scorecard: null,
};

const DIR = {
  Bullish: { fg: "text-emerald-400", bg: "bg-emerald-500/10", br: "border-emerald-500/30", dot: "bg-emerald-500" },
  Bearish: { fg: "text-red-400", bg: "bg-red-500/10", br: "border-red-500/30", dot: "bg-red-500" },
  Neutral: { fg: "text-amber-400", bg: "bg-amber-500/10", br: "border-amber-500/30", dot: "bg-amber-500" },
};

// tri-state light: true -> green, false -> red, null/undefined -> amber
const LIGHT = (ok) =>
  ok === true ? { fg: "text-emerald-400", br: "border-emerald-500/30", bg: "bg-emerald-500/[0.06]", Icon: CheckCircle2 }
  : ok === false ? { fg: "text-red-400", br: "border-red-500/30", bg: "bg-red-500/[0.06]", Icon: XCircle }
  : { fg: "text-amber-400", br: "border-amber-500/30", bg: "bg-amber-500/[0.06]", Icon: MinusCircle };

const SPREAD = { wti: "WTI", brent: "Brent", brent_wti: "Brent–WTI", wti_m1m2: "WTI M1–M2",
  crack_321_wti: "3-2-1 crack", ho_wti: "HO crack", gasoil_brent: "Gasoil crack" };

const drawWord = (v) => (v == null ? "—" : v < 0 ? "draw" : "build");
const pct = (v, d = 2) => (v == null ? "—" : `${fmtSigned(v, d)}%`);
const toneFor = (v, bullishWhenNeg = true) =>
  v == null ? "text-zinc-300" : (bullishWhenNeg ? v <= 0 : v >= 0) ? "text-emerald-400" : "text-red-400";

const Stat = ({ label, value, sub, tone = "text-zinc-100", big = false }) => (
  <div>
    <div className="text-[9px] uppercase tracking-wider text-zinc-500">{label}</div>
    <div className={`font-mono ${big ? "text-2xl" : "text-base"} ${tone}`}>{value}</div>
    {sub != null && <div className="text-[9px] text-zinc-600 leading-tight mt-0.5">{sub}</div>}
  </div>
);

// ===========================================================================
// SCORECARD — the at-a-glance "did it work?" (3 traffic lights + net verdict).
// ===========================================================================
const Scorecard = ({ scorecard, comparison }) => {
  if (!scorecard) {
    return (
      <Card>
        <SectionTitle sub="run to grade the call">Scorecard</SectionTitle>
        <div className="flex items-center gap-3 text-zinc-500 text-[12px] py-4 justify-center">
          <FlaskConical size={18} className="text-zinc-700" />
          Press <span className="text-amber-400 font-semibold">Run the latest EIA release</span> to grade the prediction against reality.
        </div>
      </Card>
    );
  }
  return (
    <Card>
      <SectionTitle sub="prediction graded against reality">Scorecard — did it work?</SectionTitle>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {scorecard.lights.map((l) => {
          const c = LIGHT(l.ok);
          return (
            <div key={l.key} className={`rounded-lg border ${c.br} ${c.bg} p-3`}>
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase tracking-wider text-zinc-400">{l.label}</span>
                <c.Icon size={16} className={c.fg} />
              </div>
              <div className={`font-mono text-xl font-semibold mt-1 ${c.fg}`}>{l.grade}</div>
              <div className="text-[10px] text-zinc-500 leading-tight mt-0.5">{l.detail}</div>
            </div>
          );
        })}
      </div>
      <div className="mt-3 rounded-md border border-[#1c1d22] bg-[#0e0f12] p-3">
        <div className="text-[9px] uppercase tracking-wider text-zinc-600 mb-1">Net verdict</div>
        <p className="text-[12px] text-zinc-200 leading-relaxed">{scorecard.net}</p>
        {comparison?.narrative && (
          <p className="text-[11px] text-zinc-500 leading-relaxed mt-2">{comparison.narrative}</p>
        )}
      </div>
    </Card>
  );
};

// ===========================================================================
// TRACK RECORD — the framework backtested over history (last 52 + all releases).
// ===========================================================================
const hitTone = (v) => (v == null ? "text-zinc-300" : v >= 0.55 ? "text-emerald-400" : v >= 0.45 ? "text-amber-400" : "text-red-400");

const TrackRecord = ({ track }) => {
  if (!track) return null;
  const Col = ({ w, title }) => (
    <div className="flex-1">
      <div className="text-[9px] uppercase tracking-wider text-zinc-600 mb-2 text-center">{title}</div>
      <div className="space-y-2">
        <Row label="Surprise → price"
          value={w.surprise_hit_rate == null ? "—" : `${(w.surprise_hit_rate * 100).toFixed(0)}%`}
          tone={hitTone(w.surprise_hit_rate)} sub={w.surprise_hit_n ? `n=${w.surprise_hit_n}` : ""} />
        <Row label="Lean called surprise"
          value={w.lean?.hit_rate == null ? "—" : `${(w.lean.hit_rate * 100).toFixed(0)}%`}
          tone={hitTone(w.lean?.hit_rate)} sub={w.lean?.n ? `n=${w.lean.n}` : "n<6"} />
        <Row label="Model vs seasonal (MAE)"
          value={w.mae ? `${fmt(w.mae.model, 1)} / ${fmt(w.mae.seasonal, 1)}` : "—"}
          tone={w.mae && w.mae.model < w.mae.seasonal ? "text-emerald-400" : "text-amber-400"}
          sub={w.mae ? (w.mae.model < w.mae.seasonal ? "model better" : "no edge") : ""} />
        <Row label="Avg favorable move"
          value={w.avg_fav_move_pct == null ? "—" : pct(w.avg_fav_move_pct)}
          tone={toneFor(w.avg_fav_move_pct, false)} sub="signed return" />
      </div>
    </div>
  );
  return (
    <Card>
      <SectionTitle sub="the framework backtested — so this isn't read as luck"
        action={<SourceTag source="derived" note={track.note} />}>
        Framework track record
      </SectionTitle>
      <div className="flex gap-6">
        <Col w={track.recent} title="Last 52 releases" />
        <div className="w-px bg-[#1c1d22]" />
        <Col w={track.all} title="All history" />
      </div>
      <p className="text-[10px] text-zinc-600 leading-snug mt-3">
        Read: hit-rates near 50% = coin-flip; the edge is real but modest and concentrates in specific
        regimes. The model beats the naive seasonal guess on forecast error — but inventories are a weak
        same-day price driver, which is the framework's whole point.
      </p>
    </Card>
  );
};

const Row = ({ label, value, sub, tone = "text-zinc-100" }) => (
  <div className="flex items-center justify-between gap-2">
    <span className="text-[11px] text-zinc-400">{label}</span>
    <div className="text-right">
      <span className={`font-mono text-[13px] ${tone}`}>{value}</span>
      {sub && <span className="text-[9px] text-zinc-600 ml-1.5">{sub}</span>}
    </div>
  </div>
);

// ===========================================================================
// IMPACT CURVE — predicted release-day WTI move = beta × surprise + realized dot.
// ===========================================================================
const ImpactCurve = ({ curve, result }) => {
  const data = (curve.points || []).map((p) => ({ surprise: p.surprise, regime: p.regime_pct, overall: p.overall_pct }));
  if (!data.length) return null;
  const rp = result?.realized_point;
  return (
    <div>
      <div className="flex items-center flex-wrap gap-x-4 gap-y-1 text-[9px] uppercase tracking-wider text-zinc-500 mb-1 px-1">
        <span className="flex items-center gap-1.5"><span className="w-3 h-[2px] bg-sky-500" /> This regime</span>
        <span className="flex items-center gap-1.5"><span className="w-3 border-t border-dashed border-zinc-500" /> All-history</span>
        {rp?.actual_pct != null && <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-400" /> Actual move</span>}
        {rp?.pred_regime_pct != null && <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-sky-400" /> Predicted</span>}
      </div>
      <div className="h-64">
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 8, right: 12, bottom: 16, left: 4 }}>
            <CartesianGrid {...chartProps.grid} />
            <XAxis type="number" dataKey="surprise" {...chartProps.axis} domain={["dataMin", "dataMax"]}
              tickFormatter={(v) => v.toFixed(0)}
              label={{ value: "Surprise (MMbbl)  ← bigger draw · bigger build →", position: "bottom", offset: 2, fill: "#6b6d75", fontSize: 9 }} />
            <YAxis {...chartProps.axis} width={42} tickFormatter={(v) => `${v}%`}
              label={{ value: "WTI move", angle: -90, position: "insideLeft", fill: "#6b6d75", fontSize: 9 }} />
            <Tooltip contentStyle={{ background: "#0a0b0e", border: "1px solid #2a2b31", fontSize: 11 }}
              labelFormatter={(v) => `surprise ${fmtSigned(v, 1)} MMbbl`}
              formatter={(val, name) => [`${Number(val).toFixed(2)}%`, name === "regime" ? "This regime" : "All-history"]} />
            <ReferenceLine x={0} stroke="#52525b" strokeDasharray="3 3"
              label={{ value: "in line", position: "top", fill: "#71717a", fontSize: 8 }} />
            <ReferenceLine y={0} stroke="#3a3b41" />
            <Line type="monotone" dataKey="overall" stroke="#71717a" strokeWidth={1} strokeDasharray="4 3" dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="regime" stroke="#38bdf8" strokeWidth={1.8} dot={false} isAnimationActive={false} />
            {rp && <ReferenceLine x={rp.surprise} stroke="#f59e0b" strokeDasharray="2 3"
              label={{ value: "real surprise", position: "top", fill: "#f59e0b", fontSize: 8 }} />}
            {rp?.pred_regime_pct != null && <ReferenceDot x={rp.surprise} y={rp.pred_regime_pct} r={4} fill="#38bdf8" stroke="#0a0b0e" />}
            {rp?.actual_pct != null && <ReferenceDot x={rp.surprise} y={rp.actual_pct} r={5} fill="#f59e0b" stroke="#0a0b0e" />}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="text-[10px] text-zinc-500 leading-snug px-1 mt-1">
        The line is how much WTI moves per MMbbl of surprise. A flat line means inventories barely drive
        price in this regime — so the gap between the <span className="text-amber-400">actual move</span> and
        the <span className="text-sky-400">predicted</span> dot is the whole story.
      </p>
    </div>
  );
};

// ===========================================================================
export const PageReleaseLab = () => {
  const { data, live } = useLive("/api/release-lab", FALLBACK, useLive.REFRESH.hourly);
  const [override, setOverride] = useState(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);

  const view = override || data;
  const p = view.prediction || FALLBACK.prediction;
  const r = view.result;
  const cur = view.current || {};
  const t = view.target || FALLBACK.target;
  const leanColor = DIR[p.lean] || DIR.Neutral;
  const verdictColor = r ? (DIR[r.verdict?.direction] || DIR.Neutral) : null;

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

  return (
    <div className="space-y-3">
      {/* ---- Hero: title + run button ----------------------------------- */}
      <Card padding={false}>
        <div className="p-4 flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center flex-shrink-0">
              <FlaskConical size={18} className="text-amber-400" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-zinc-100 tracking-tight">EIA Release Lab</h2>
              <p className="text-[11px] text-zinc-500 leading-snug mt-0.5 max-w-xl">
                One experiment around the <span className="text-zinc-300">{t.label}</span>. We froze the
                model on everything known <span className="text-zinc-300">before</span> the print, then the
                button runs the full pipeline on the actual number to show{" "}
                <span className="text-sky-400">expected</span> vs <span className="text-amber-400">real</span>{" "}
                surprise — and grades the call.
              </p>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1.5">
            <button onClick={runPipeline} disabled={running}
              className={`flex items-center gap-2 px-4 h-10 rounded-lg font-semibold text-[12px] tracking-wide transition-all ${
                running ? "bg-zinc-800 text-zinc-400 cursor-wait" : "bg-amber-500 text-zinc-950 hover:bg-amber-400 active:scale-[0.98]"}`}>
              {running ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} fill="currentColor" />}
              {running ? "Running pipeline…" : r ? "Re-run on latest release" : "Run the latest EIA release"}
            </button>
            <span className="text-[9px] text-zinc-600">
              {running ? "fetching EIA + Yahoo, scoring surprise…" : r ? `last run ${r.ran_at_et || ""}` : "spawns analytics/release_lab.py"}
            </span>
          </div>
        </div>
        {error && (
          <div className="mx-4 mb-4 rounded-md border border-red-500/30 bg-red-500/10 p-2.5 text-[11px] text-red-300">
            Run failed: <span className="font-mono">{error}</span>
          </div>
        )}
      </Card>

      {/* ---- Scorecard (the headline outcome) --------------------------- */}
      <Scorecard scorecard={view.scorecard} comparison={view.comparison} />

      {/* ---- EXPECTED vs REAL, side by side ----------------------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* EXPECTED (prediction) */}
        <Card padding={false}>
          <div className="p-4 pb-2">
            <SectionTitle sub={`frozen as of ${p.asof || "—"} · pre-release`}
              action={<SourceTag live={live} source="eia"
                note="The prediction is built only from data strictly before the target week. EXPECTED build/draw is the walk-forward consensus proxy; the lean comes from stocks vs seasonal norm, momentum, Cushing and product alignment." />}>
              <span className="text-sky-400">Expected</span> — the call before the print
            </SectionTitle>
          </div>
          <div className={`mx-4 mb-3 rounded-md border ${leanColor.br} ${leanColor.bg} p-3`}>
            <div className="flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${leanColor.dot}`} />
              <span className={`font-mono text-base font-semibold ${leanColor.fg}`}>{p.lean}</span>
              <span className="text-[10px] uppercase tracking-wider text-zinc-500">structural lean · conf {p.confidence}</span>
            </div>
            <p className="text-[11px] text-zinc-300 leading-snug mt-1.5">{p.narrative}</p>
          </div>
          <div className="grid grid-cols-3 gap-px bg-[#1c1d22] border-y border-[#1c1d22]">
            <div className="bg-[#0e0f12] p-3"><Stat label="Expected change" big value={fmtSigned(p.expected_wow, 1)}
              tone={toneFor(p.expected_wow)} sub={`MMbbl ${drawWord(p.expected_wow)} (consensus)`} /></div>
            <div className="bg-[#0e0f12] p-3"><Stat label="Expected surprise" big value={fmtSigned(p.expected_surprise, 1)}
              tone="text-zinc-300" sub="≈0 — model expects to be right" /></div>
            <div className="bg-[#0e0f12] p-3"><Stat label="Catalyst strength"
              value={p.catalyst_r2 == null ? "—" : `R² ${fmt(p.catalyst_r2, 2)}`}
              tone={(p.catalyst_r2 ?? 0) >= 0.05 ? "text-emerald-400" : "text-amber-400"}
              sub={`${(p.catalyst_r2 ?? 0) >= 0.05 ? "drives price" : "weak driver"} · n=${p.catalyst_n ?? "—"}`} /></div>
          </div>
          {p.scenarios?.length > 0 && (
            <div className="px-4 pt-3">
              <div className="text-[9px] uppercase tracking-wider text-zinc-600 mb-1.5">If the print comes in… (predicted WTI move on the surprise alone)</div>
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
              {p.factors.slice(0, 6).map((f, i) => (
                <li key={i} className="text-[11px] text-zinc-400 leading-snug flex gap-1.5">
                  <span className="text-zinc-600 font-mono">{i + 1}.</span><span>{f}</span>
                </li>
              ))}
            </ol>
          )}
        </Card>

        {/* REAL (result) */}
        <Card padding={false}>
          <div className="p-4 pb-2">
            <SectionTitle sub={r ? `released ${t.release_date} · post-release` : "press the button"}>
              <span className="text-amber-400">Real</span> — what actually printed
            </SectionTitle>
          </div>
          {!r ? (
            <div className="m-4 mt-2 rounded-md border border-dashed border-[#2a2b31] p-8 text-center">
              <FlaskConical size={26} className="text-zinc-700 mx-auto mb-2" />
              <p className="text-[12px] text-zinc-400">The result is hidden until you run the pipeline.</p>
              <p className="text-[10px] text-zinc-600 mt-1 max-w-xs mx-auto">
                Press <span className="text-amber-400 font-semibold">Run the latest EIA release</span> above — it
                fetches the actual print, computes the real surprise and grades the call against the market.
              </p>
            </div>
          ) : (
            <>
              <div className={`mx-4 mb-3 rounded-md border ${verdictColor.br} ${verdictColor.bg} p-3`}>
                <div className="flex items-center gap-2">
                  <span className={`w-2.5 h-2.5 rounded-full ${verdictColor.dot}`} />
                  <span className={`font-mono text-base font-semibold ${verdictColor.fg}`}>{r.verdict?.direction}</span>
                  <span className="text-[10px] uppercase tracking-wider text-zinc-500">regime-aware verdict · conf {r.verdict?.confidence}</span>
                </div>
                <p className="text-[11px] text-zinc-300 leading-snug mt-1.5">{r.verdict?.headline}</p>
              </div>
              <div className="grid grid-cols-3 gap-px bg-[#1c1d22] border-y border-[#1c1d22]">
                <div className="bg-[#0e0f12] p-3"><Stat label="Actual change" big value={fmtSigned(r.actual_wow, 1)}
                  tone={toneFor(r.actual_wow)} sub={`MMbbl ${drawWord(r.actual_wow)} · ${fmt(r.actual_stock, 0)} total`} /></div>
                <div className="bg-[#0e0f12] p-3"><Stat label="Real surprise" big value={fmtSigned(r.real_surprise, 1)}
                  tone={toneFor(r.real_surprise)} sub={`${fmtSigned(r.real_surprise_z, 1)}σ · ${r.real_surprise_dir} beat`} /></div>
                <div className="bg-[#0e0f12] p-3"><Stat label="WTI move on print" big value={pct(r.actual_move_pct, 1)}
                  tone={toneFor(r.actual_move_pct, false)} sub={`vs predicted ${pct(r.pred_move_pct)}`} /></div>
              </div>
              {r.crosscheck?.note && <p className="text-[11px] text-zinc-400 leading-snug px-4 py-3">{r.crosscheck.note}</p>}
            </>
          )}
        </Card>
      </div>

      {/* ---- Impact curve ----------------------------------------------- */}
      <Card padding={false}>
        <div className="p-4 pb-1">
          <SectionTitle sub="predicted WTI move = β × surprise" action={<AsOf date={t.release_date} />}>
            Impact curve — how much should the surprise move WTI?
          </SectionTitle>
        </div>
        <div className="px-3 pb-4">
          <ImpactCurve curve={view.impact_curve || FALLBACK.impact_curve} result={r} />
        </div>
      </Card>

      {/* ---- Track record + affected products --------------------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <div className="lg:col-span-2"><TrackRecord track={view.track_record} /></div>
        <Card>
          <SectionTitle sub="ranked by sensitivity">Affected products</SectionTitle>
          <div className="flex flex-wrap gap-1.5">
            {(p.products || []).map((s) => (
              <span key={s} className="font-mono text-[11px] px-2 py-1 rounded bg-[#15161a] text-zinc-300 border border-[#1c1d22]">
                {SPREAD[s] || s}
              </span>
            ))}
          </div>
          <p className="text-[10px] text-zinc-600 leading-snug mt-3">
            The instruments whose release-day move correlates most with the crude surprise — where any
            inventory-driven reaction should show up first.
          </p>
        </Card>
      </div>
    </div>
  );
};
