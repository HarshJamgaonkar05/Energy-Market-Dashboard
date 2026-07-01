// ============================================================================
// InventorySignal — the live crude-inventory cross-check engine on the dashboard.
// Reads /api/inventory-signal (written by analytics/inventory_engine.py): the
// pre-release base case for the NEXT EIA crude release, the most recent published
// print scored as a surprise + verdict, and the live market cross-check.
// ============================================================================
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SourceTag } from "../primitives/SourceTag";
import { AsOf } from "../primitives/AsOf";
import { InfoDot } from "../primitives/InfoDot";
import { fmt, fmtSigned } from "../../lib/format";
import { useLive } from "../../lib/useLive";

// Plain-English explanations of the core inventory concepts (subtle hover help).
const INV_EXPL = {
  crude: "Total U.S. commercial crude oil sitting in storage tanks (excludes the government's Strategic Petroleum Reserve), in million barrels.",
  wow: "Week-over-week change. Negative = a DRAW (oil left storage — usually bullish); positive = a BUILD (oil piled up — usually bearish).",
  norm: "How unusual today's stock level is for the time of year, vs the 5-year seasonal norm (in σ). Below normal = tight market = bullish.",
  cushing: "Crude held at Cushing, Oklahoma — the physical delivery point for WTI futures. Draining toward tank lows is very bullish for WTI specifically.",
  refinery: "Share of refining capacity in use. Higher utilization burns more crude, which tends to draw down stocks.",
  regime: "The market backdrop (volatility / season / whether crude & products agree) that decides how much a given inventory surprise actually moves price.",
  verdict: "The framework's lean into the next release: structural bias (bullish/bearish) plus how strong a catalyst the number is likely to be.",
};

const FALLBACK = {
  stage: "pre-release",
  asOf_period: null, next_release_est: null,
  verdict: { direction: "Neutral", confidence: "low",
    headline: "Run analytics/inventory_engine.py to populate the live inventory verdict.",
    factors: [], products: [] },
  current: {}, last_print: null, crosscheck: null, top_spreads: [],
};

const DIR = {
  Bullish: { fg: "text-emerald-400", bg: "bg-emerald-500/10", br: "border-emerald-500/30", dot: "bg-emerald-500" },
  Bearish: { fg: "text-red-400", bg: "bg-red-500/10", br: "border-red-500/30", dot: "bg-red-500" },
  Neutral: { fg: "text-amber-400", bg: "bg-amber-500/10", br: "border-amber-500/30", dot: "bg-amber-500" },
};

const XCHECK = {
  confirmed: { fg: "text-emerald-400", label: "CONFIRMED" },
  contradicted: { fg: "text-red-400", label: "CONTRADICTED" },
  flat: { fg: "text-zinc-400", label: "FLAT" },
  pending: { fg: "text-sky-400", label: "PENDING" },
  "no-price": { fg: "text-zinc-500", label: "NO PRICE" },
};

const Tile = ({ label, value, sub, tone = "text-zinc-100", info }) => (
  <div className="bg-[#0e0f12] p-2.5">
    <div className="text-[9px] uppercase tracking-wider text-zinc-500 flex items-center gap-1">
      {label}{info && <InfoDot text={info} />}
    </div>
    <div className={`font-mono text-base ${tone}`}>{value}</div>
    {sub != null && <div className="text-[9px] text-zinc-600">{sub}</div>}
  </div>
);

export const InventorySignal = () => {
  const { data, live, stale } = useLive("/api/inventory-signal", FALLBACK, useLive.REFRESH.hourly);
  const v = data.verdict || FALLBACK.verdict;
  const c = data.current || {};
  const lp = data.last_print;
  const d = DIR[v.direction] || DIR.Neutral;
  const products = (v.products?.length ? v.products : data.top_spreads) || [];

  const labelSpread = (s) =>
    ({ wti: "WTI", brent: "Brent", brent_wti: "Brent–WTI", wti_m1m2: "WTI M1–M2",
       crack_321_wti: "3-2-1 crack", ho_wti: "HO crack", gasoil_brent: "Gasoil crack" }[s] || s);

  return (
    <Card padding={false}>
      <div className="p-4 pb-2">
        <SectionTitle
          sub="EIA crude release · framework verdict + market cross-check"
          action={<div className="flex items-center gap-2">
            <AsOf date={data.asOf_period} />
            <SourceTag live={live} stale={stale} source="eia"
              note="Live crude-inventory cross-check engine (analytics/inventory_engine.py). Surprise = actual − model-expected (walk-forward seasonal + supply/demand balance + momentum). The verdict is damped by how strongly inventories drive WTI in the current regime; the cross-check compares the post-release call to the live WTI move." />
          </div>}>
          Inventory Release Signal <InfoDot text={INV_EXPL.verdict} />
        </SectionTitle>
      </div>

      {/* Verdict banner */}
      <div className={`mx-4 mb-3 rounded-md border ${d.br} ${d.bg} p-3`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${d.dot}`} />
            <span className={`font-mono text-lg font-semibold ${d.fg}`}>{v.direction}</span>
            <span className="text-[10px] uppercase tracking-wider text-zinc-500">
              {data.stage === "post-release" ? "post-release" : "into next release"} · confidence {v.confidence}
            </span>
          </div>
          {data.next_release_est && (
            <span className="text-[10px] text-zinc-500">next ≈ {data.next_release_est}</span>
          )}
        </div>
        <p className="text-[11px] text-zinc-300 leading-snug mt-1.5">{v.headline}</p>
      </div>

      {/* Current setup tiles */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-px bg-[#1c1d22] border-y border-[#1c1d22]">
        <Tile label="US Crude" info={INV_EXPL.crude} value={`${fmt(c.crude_stock, 1)}`} sub="MMbbl" />
        <Tile label="WoW" info={INV_EXPL.wow} value={fmtSigned(c.crude_wow, 1)}
          tone={c.crude_wow <= 0 ? "text-emerald-400" : "text-red-400"} sub="MMbbl" />
        <Tile label="vs 5y norm" info={INV_EXPL.norm} value={c.crude_z == null ? "—" : `${fmtSigned(c.crude_z, 1)}σ`}
          tone={c.crude_z <= 0 ? "text-emerald-400" : "text-red-400"} sub={c.crude_z <= 0 ? "tight" : "loose"} />
        <Tile label="Cushing" info={INV_EXPL.cushing} value={fmt(c.cushing, 1)} sub={`${fmtSigned(c.cushing_wow, 1)} WoW`} />
        <Tile label="Refinery" info={INV_EXPL.refinery} value={c.refutil == null ? "—" : `${fmt(c.refutil, 1)}%`} sub="utilization" />
        <Tile label="Regime" info={INV_EXPL.regime} value={c.vol_regime || "—"} sub={`${c.season || ""} · ${c.product_alignment || ""}`} />
      </div>

      {/* Last print + cross-check */}
      {lp && (
        <div className="m-4 mt-3 rounded-md border border-[#1c1d22] p-3">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] uppercase tracking-wider text-zinc-500">
              Last print · {lp.period}
            </span>
            {lp.crosscheck && (
              <span className={`font-mono text-[10px] ${(XCHECK[lp.crosscheck.status] || XCHECK.pending).fg}`}>
                {(XCHECK[lp.crosscheck.status] || XCHECK.pending).label}
              </span>
            )}
          </div>
          <div className="grid grid-cols-4 gap-2 text-center">
            <div><div className="text-[9px] text-zinc-600 uppercase">Expected</div>
              <div className="font-mono text-sm text-zinc-300">{fmtSigned(c.expected, 1)}</div></div>
            <div><div className="text-[9px] text-zinc-600 uppercase">Actual</div>
              <div className="font-mono text-sm text-zinc-100">{fmtSigned(c.crude_wow, 1)}</div></div>
            <div><div className="text-[9px] text-zinc-600 uppercase">Surprise</div>
              <div className={`font-mono text-sm ${lp.surprise <= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {fmtSigned(lp.surprise, 1)}</div></div>
            <div><div className="text-[9px] text-zinc-600 uppercase">WTI move</div>
              <div className={`font-mono text-sm ${(lp.crosscheck?.wti_reaction_pct ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {lp.crosscheck ? `${fmtSigned(lp.crosscheck.wti_reaction_pct, 1)}%` : "—"}</div></div>
          </div>
          {lp.crosscheck?.note && (
            <p className="text-[10px] text-zinc-500 leading-snug mt-2">{lp.crosscheck.note}</p>
          )}
        </div>
      )}

      {/* Top drivers + affected spreads */}
      <div className="px-4 pb-4">
        {products.length > 0 && (
          <div className="mb-2.5">
            <span className="text-[9px] uppercase tracking-wider text-zinc-600">Most-affected products / spreads</span>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {products.map((p) => (
                <span key={p} className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[#15161a] text-zinc-300 border border-[#1c1d22]">
                  {labelSpread(p)}
                </span>
              ))}
            </div>
          </div>
        )}
        {v.factors?.length > 0 && (
          <ol className="space-y-1">
            {v.factors.slice(0, 4).map((f, i) => (
              <li key={i} className="text-[11px] text-zinc-400 leading-snug flex gap-1.5">
                <span className="text-zinc-600 font-mono">{i + 1}.</span><span>{f}</span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </Card>
  );
};
