// ============================================================================
// Market compute layer — turns raw Yahoo quotes/history into the exact shapes
// the frontend panels render: instruments, ticker, movers, normalized series,
// correlation matrix, crack spreads, forward curves, inter-commodity spreads,
// and the macro block.
// ============================================================================
import { getQuotes, getFrontPrices, dailyCloses } from "../sources/yahoo.js";
import { cached } from "../lib/cache.js";
import * as history from "../lib/history.js";

const GAL_PER_BBL = 42;
const BBL_PER_MT_GASOIL = 7.45;

// The five instruments. Gas Oil has no free live feed, so it is proxied from
// NYMEX ULSD (HO=F) — both are middle distillates — and flagged `modeled:true`.
const SPEC = [
  { id: "brent",  sym: "BRENT",  name: "Brent Crude",        label: "Brent",       kind: "crude",   color: "#f59e0b", unit: "$/bbl", yahoo: "BZ=F" },
  { id: "wti",    sym: "WTI",    name: "WTI Crude",          label: "WTI",         kind: "crude",   color: "#38bdf8", unit: "$/bbl", yahoo: "CL=F" },
  { id: "ho",     sym: "HO",     name: "Heating Oil · ULSD", label: "Heating Oil", kind: "product", color: "#10b981", unit: "$/gal", yahoo: "HO=F" },
  { id: "rbob",   sym: "RBOB",   name: "RBOB Gasoline",      label: "RBOB",        kind: "product", color: "#a78bfa", unit: "$/gal", yahoo: "RB=F" },
  { id: "gasoil", sym: "GASOIL", name: "ICE Gas Oil",        label: "Gas Oil",     kind: "product", color: "#f472b6", unit: "$/mt",  proxyOf: "ho", modeled: true, source: "derived", sourceNote: "Proxied from live NYMEX ULSD (HO=F), converted to $/mt and calibrated to the dataset's real ULSD↔Gas Oil ratio." },
];

const MACRO_SPEC = [
  { sym: "DXY",    name: "Dollar Index", yahoo: "DX-Y.NYB", unit: "",  dp: 2 },
  { sym: "SPX",    name: "S&P 500",      yahoo: "^GSPC",    unit: "",  dp: 2 },
  { sym: "VIX",    name: "Volatility",   yahoo: "^VIX",     unit: "",  dp: 2 },
  { sym: "UST10Y", name: "10Y Yield",    yahoo: "^TNX",     unit: "%", dp: 3 },
];

// $/bbl normalisation so cracks/spreads are comparable across quote units.
const toBbl = (id, val) => {
  if (val == null) return null;
  if (id === "ho" || id === "rbob") return +(val * GAL_PER_BBL).toFixed(2);
  if (id === "gasoil") return +(val / BBL_PER_MT_GASOIL).toFixed(2);
  return +val.toFixed(2);
};

const ENERGY_SYMS = SPEC.filter((s) => s.yahoo).map((s) => s.yahoo);

// Calibrate the Gas Oil proxy to the dataset's REAL ULSD↔Gas Oil relationship.
// A pure unit-conversion of ULSD ($/gal → $/mt) overstates Gas Oil and collapses
// the HO–Gas Oil spread to ~0; scaling by the last real Gas Oil / converted-HO
// ratio from the dataset restores a realistic distillate spread. Falls back to 1
// (pure conversion) if the dataset is unavailable.
const GASOIL_CAL = (() => {
  const ho = history.dailyCloses("ho").at(-1)?.close;
  const go = history.dailyCloses("gasoil").at(-1)?.close;
  const conv = ho ? ho * GAL_PER_BBL * BBL_PER_MT_GASOIL : 0;
  return conv && go ? go / conv : 1;
})();

// ----------------------------------------------------------------------------
// Build the live instrument array (HERO / HeroCards / INSTRUMENTS shape).
// ----------------------------------------------------------------------------
export async function instruments() {
  const q = await getQuotes(ENERGY_SYMS);
  const bySym = Object.fromEntries(SPEC.filter((s) => s.yahoo).map((s) => [s.id, q[s.yahoo]]));

  return SPEC.map((s) => {
    if (s.proxyOf) {
      // Gas Oil proxy: ULSD $/gal -> $/bbl (×42) -> $/mt (×7.45 bbl per tonne),
      // then calibrated to the dataset's real ULSD↔Gas Oil ratio (GASOIL_CAL).
      const galToMt = (gal) => gal * GAL_PER_BBL * BBL_PER_MT_GASOIL * GASOIL_CAL;
      const base = bySym[s.proxyOf];
      if (!base?.price) return { ...meta(s), val: null };
      const mt = +galToMt(base.price).toFixed(1);
      const prevMt = galToMt(base.prev);
      return {
        ...meta(s),
        val: mt,
        chg: +(mt - prevMt).toFixed(1),
        pct: prevMt ? +(((mt - prevMt) / prevMt) * 100).toFixed(2) : 0,
        bbl: toBbl(s.id, mt),
        spark: base.spark.map((p) => ({ x: p.x, y: +galToMt(p.y).toFixed(1) })),
        volRaw: base.volume,
      };
    }
    const d = bySym[s.id];
    if (!d?.price) return { ...meta(s), val: null };
    return {
      ...meta(s),
      val: +d.price.toFixed(s.unit === "$/gal" ? 4 : 2),
      chg: +d.chg.toFixed(s.unit === "$/gal" ? 4 : 2),
      pct: d.pct,
      bbl: toBbl(s.id, d.price),
      spark: d.spark,
      volRaw: d.volume,
    };
  });
}
const meta = (s) => ({ id: s.id, sym: s.sym, name: s.name, kind: s.kind, color: s.color, unit: s.unit, modeled: !!s.modeled, source: s.source, sourceNote: s.sourceNote });

const byId = (instr, id) => instr.find((i) => i.id === id);

// ----------------------------------------------------------------------------
// Derived headline spreads / cracks (shared by ticker + movers).
// ----------------------------------------------------------------------------
function headlineSpreads(instr) {
  const g = (id) => byId(instr, id) || {};
  const brent = g("brent"), wti = g("wti"), rbob = g("rbob"), ho = g("ho"), gasoil = g("gasoil");
  const safe = (n) => (Number.isFinite(n) ? +n.toFixed(2) : 0);
  return [
    { sym: "BRENT-WTI",   val: safe(brent.val - wti.val) },
    { sym: "3:2:1 CRACK", val: safe((2 * rbob.bbl + ho.bbl - 3 * wti.bbl) / 3) },
    { sym: "GASOIL CRK",  val: safe(gasoil.bbl - brent.bbl) },
    { sym: "RBOB CRK",    val: safe(rbob.bbl - wti.bbl) },
  ];
}

export function ticker(instr) {
  const base = instr.filter((i) => i.val != null).map((i) => ({ sym: i.sym, val: i.val, chg: i.chg, pct: i.pct }));
  const spreads = headlineSpreads(instr).map((s) => ({ ...s, chg: 0, pct: 0 }));
  return [...base, ...spreads];
}

export function movers(instr) {
  const fmtVol = (v) => (v == null ? "—" : v >= 1000 ? `${Math.round(v / 1000)}K` : `${v}`);
  const rows = instr
    .filter((i) => i.val != null)
    .map((i) => ({ sym: i.sym, val: i.val, pct: i.pct, vol: fmtVol(i.volRaw) }));
  // sort by absolute move, biggest first
  return rows.sort((a, b) => Math.abs(b.pct) - Math.abs(a.pct));
}

// ----------------------------------------------------------------------------
// Historical daily price series + correlation matrix — sourced from the
// proprietary dataset (server/data/history.json), NOT Yahoo. Covers the four
// dataset instruments (WTI, Brent, Heating Oil, Gas Oil) over 2021→present at
// daily resolution. The frontend re-indexes each line to 100 over the selected
// window, so we hand back raw daily closes keyed by series name.
// ----------------------------------------------------------------------------
const SERIES_KEY = { brent: "Brent", wti: "WTI", ho: "HO", gasoil: "Gasoil" };
const SERIES_LABEL = { brent: "Brent", wti: "WTI", ho: "HO", gasoil: "Gas Oil" };

export async function seriesAndCorrelation() {
  const ids = history.HISTORY_IDS; // wti, brent, ho, gasoil

  // date(ISO) -> close, per instrument.
  const maps = {};
  for (const id of ids) maps[id] = new Map(history.dailyCloses(id).map((p) => [p.iso, p.close]));

  // Align on the dates present in every series so every line is complete.
  const dates = [...(maps[ids[0]]?.keys() ?? [])]
    .filter((d) => ids.every((id) => maps[id].has(d)))
    .sort();

  const series = dates.map((iso) => {
    const row = { date: iso };
    for (const id of ids) row[SERIES_KEY[id]] = maps[id].get(iso);
    return row;
  });

  const aligned = {};
  for (const id of ids) aligned[id] = dates.map((iso) => maps[id].get(iso));
  const correlation = correlationMatrix(aligned, ids);
  return { series, correlation, asOf: dates.at(-1) ?? null };
}

// 30-day rolling correlation of daily returns across the dataset instruments.
function correlationMatrix(aligned, ids) {
  const rets = {};
  for (const id of ids) {
    const c = aligned[id];
    const r = [];
    for (let i = 1; i < c.length; i++) r.push((c[i] - c[i - 1]) / c[i - 1]);
    rets[id] = r.slice(-30);
  }
  const corr = (a, b) => {
    const n = Math.min(a.length, b.length);
    if (n < 3) return 0;
    const ma = a.slice(-n).reduce((s, x) => s + x, 0) / n;
    const mb = b.slice(-n).reduce((s, x) => s + x, 0) / n;
    let num = 0, da = 0, db = 0;
    for (let i = 0; i < n; i++) {
      const x = a[a.length - n + i] - ma, y = b[b.length - n + i] - mb;
      num += x * y; da += x * x; db += y * y;
    }
    return da && db ? num / Math.sqrt(da * db) : 0;
  };
  const labels = ids.map((id) => SERIES_LABEL[id]);
  const matrix = ids.map((ra) => ids.map((rb) => +corr(rets[ra], rets[rb]).toFixed(2)));
  return { labels, matrix };
}

// ----------------------------------------------------------------------------
// Crack spreads — definitions (formulas) enriched with live $/bbl values.
// ----------------------------------------------------------------------------
const CRACK_DEFS = [
  { id: "rbob-wti",     group: "Product Cracks",   label: "RBOB Crack",        legs: [["rbob", 1]],            crude: "wti",   crudeC: 1, div: 1 },
  { id: "rbob-brent",   group: "Product Cracks",   label: "RBOB Crack",        legs: [["rbob", 1]],            crude: "brent", crudeC: 1, div: 1 },
  { id: "ho-wti",       group: "Product Cracks",   label: "Heating Oil Crack", legs: [["ho", 1]],              crude: "wti",   crudeC: 1, div: 1 },
  { id: "ho-brent",     group: "Product Cracks",   label: "Heating Oil Crack", legs: [["ho", 1]],              crude: "brent", crudeC: 1, div: 1 },
  { id: "gasoil-brent", group: "Product Cracks",   label: "Gas Oil Crack",     legs: [["gasoil", 1]],          crude: "brent", crudeC: 1, div: 1 },
  { id: "gasoil-wti",   group: "Product Cracks",   label: "Gas Oil Crack",     legs: [["gasoil", 1]],          crude: "wti",   crudeC: 1, div: 1 },
  { id: "321-wti",      group: "Refining Margins", label: "3:2:1 Crack",       legs: [["rbob", 2], ["ho", 1]], crude: "wti",   crudeC: 3, div: 3 },
  { id: "321-brent",    group: "Refining Margins", label: "3:2:1 Crack",       legs: [["rbob", 2], ["ho", 1]], crude: "brent", crudeC: 3, div: 3 },
  { id: "211-wti",      group: "Refining Margins", label: "2:1:1 Crack",       legs: [["rbob", 1], ["ho", 1]], crude: "wti",   crudeC: 2, div: 2 },
  { id: "532-wti",      group: "Refining Margins", label: "5:3:2 Crack",       legs: [["rbob", 3], ["ho", 2]], crude: "wti",   crudeC: 5, div: 5 },
];

export function cracks(instr) {
  const bbl = (id) => byId(instr, id)?.bbl ?? null;
  const symOf = (id) => byId(instr, id)?.sym ?? id.toUpperCase();
  return CRACK_DEFS.map((c) => {
    const prod = c.legs.reduce((s, [p, n]) => s + n * (bbl(p) ?? 0), 0);
    const value = +((prod - c.crudeC * (bbl(c.crude) ?? 0)) / c.div).toFixed(2);
    return {
      id: c.id, group: c.group, label: c.label, vs: symOf(c.crude),
      value,
      legsLabel: c.legs.map(([p, n]) => `${n}×${symOf(p)}`).join(" + ") + ` − ${c.crudeC}×${symOf(c.crude)}`,
    };
  });
}

// ----------------------------------------------------------------------------
// REAL daily crack-spread history (replaces the old synthetic 60-day series).
// Builds a $/bbl daily price panel — WTI/Brent/HO/Gas Oil from the dataset, RBOB
// from Yahoo daily (the one instrument not in the dataset) — then evaluates each
// crack formula day by day. Distillate cracks span the full dataset; RBOB-based
// cracks span the dataset∩Yahoo overlap. Returns the last ~1y per crack as
// { [crackId]: { source, points:[{t,v}] } }. Cached 1h.
// ----------------------------------------------------------------------------
const HIST_WINDOW = 252; // ~1 trading year of daily points
export async function crackHistory() {
  return cached("crackhistory:all", 60 * 60_000, async () => {
    // id -> Map(iso -> $/bbl)
    const panel = {};
    const factor = { ho: GAL_PER_BBL, gasoil: 1 / BBL_PER_MT_GASOIL, wti: 1, brent: 1 };
    for (const id of history.HISTORY_IDS) {
      panel[id] = new Map(history.dailyCloses(id).map((p) => [p.iso, +(p.close * factor[id]).toFixed(3)]));
    }
    // RBOB from Yahoo ($/gal → $/bbl); empty map if Yahoo is unavailable.
    try {
      const rb = await dailyCloses("RB=F", "2y");
      panel.rbob = new Map(rb.map((p) => [p.iso, +(p.close * GAL_PER_BBL).toFixed(3)]));
    } catch { panel.rbob = new Map(); }

    const out = {};
    for (const c of CRACK_DEFS) {
      const ids = [...c.legs.map((l) => l[0]), c.crude];
      const base = panel[ids[0]];
      if (!base) continue;
      const usesRbob = ids.includes("rbob");
      const pts = [];
      for (const iso of base.keys()) {
        if (!ids.every((id) => panel[id]?.has(iso))) continue;
        const prod = c.legs.reduce((s, [p, n]) => s + n * panel[p].get(iso), 0);
        pts.push({ t: iso, v: +((prod - c.crudeC * panel[c.crude].get(iso)) / c.div).toFixed(2) });
      }
      pts.sort((a, b) => (a.t < b.t ? -1 : 1));
      if (pts.length >= 20) out[c.id] = { source: usesRbob ? "derived" : "dataset", points: pts.slice(-HIST_WINDOW) };
    }
    return out;
  });
}

// ----------------------------------------------------------------------------
// Forward curves (MODELED). Front month is anchored to the LIVE quote; the
// term structure uses a curated monthly slope (contango/backwardation shape)
// because exchange settlement curves are paywalled. Flagged modeled:true.
// ----------------------------------------------------------------------------
const CURVE_SLOPE = { brent: -0.34, wti: -0.30, ho: -0.012, rbob: 0.009, gasoil: -2.8 };
export function curves(instr) {
  const out = { modeled: true };
  for (const s of SPEC) {
    const inst = byId(instr, s.id);
    if (!inst?.val) continue;
    const front = inst.val;
    const slope = CURVE_SLOPE[s.id] ?? 0;
    out[s.id] = {
      id: s.id, label: s.label,
      color: s.color, unit: s.unit, modeled: !!s.modeled,
      data: Array.from({ length: 12 }, (_, i) => ({
        m: `M${i + 1}`,
        v: +(front + slope * i).toFixed(curveDp(s.unit)),
      })),
    };
  }
  return out;
}

// ----------------------------------------------------------------------------
// Forward curves.
//
//  • WTI / Brent / Heating Oil / Gas Oil — the dataset carries each instrument's
//    genuine M1..M12 settlement curve. We keep that real shape (the month-to-
//    month spreads) and parallel-shift it so M1 sits exactly on the live Yahoo
//    front, so the curve reflects today's price while its structure
//    (contango/backwardation, calendar spreads) is the real observed one.
//  • RBOB — not in the dataset, so its curve is the REAL Yahoo dated-contract
//    term structure (RBN26.NYM, RBQ26.NYM, …): M1..M12 are consecutive live
//    settlements. Falls back to the modeled straight-line only if Yahoo can't
//    resolve a full 12 months, so every curve the API serves is a full M1..M12.
// ----------------------------------------------------------------------------
const curveDp = (unit) => (unit === "$/gal" ? 4 : unit === "$/mt" ? 1 : 3);

// NYMEX/ICE month codes Jan..Dec, for building dated-contract symbols.
const MONTH_CODE = ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"];
const FRESH_LAG = 30 * 3600; // s: an expiring front lags its freshest sibling by a session+

// Next `n` monthly contract symbols from `from`, e.g. RBN26.NYM, RBQ26.NYM, …
function contractSymbols(root, n, from = new Date()) {
  const out = [];
  let y = from.getUTCFullYear();
  let m = from.getUTCMonth();
  for (let i = 0; i < n; i++) {
    out.push(`${root}${MONTH_CODE[m]}${String(y).slice(-2)}.NYM`);
    if (++m > 11) { m = 0; y++; }
  }
  return out;
}

// Real forward curve from individual Yahoo dated contracts. Probes a few extra
// months, skips a STALE expiring front (an expiring contract that stopped
// trading lags its freshest sibling by >FRESH_LAG), then keeps the first 12
// consecutive live settlements. Returns a curve block or null if <12 resolve.
// 10-min cached — dated contracts settle ~daily, so this stays well within
// Yahoo's rate limits no matter how often panels poll.
async function yahooDatedCurve(id, root) {
  const s = SPEC.find((x) => x.id === id);
  const syms = contractSymbols(root, 15);
  const prices = await cached(`curve:${id}`, 10 * 60_000, () => getFrontPrices(syms)).catch(() => ({}));
  const quotes = syms.map((sym) => prices[sym]).filter((q) => q && Number.isFinite(q.price));
  if (!quotes.length) return null;
  const maxTime = quotes.reduce((mx, q) => (q.time && q.time > mx ? q.time : mx), 0);
  let started = false;
  const pts = [];
  for (const sym of syms) {
    const q = prices[sym];
    if (!q || !Number.isFinite(q.price)) continue;
    if (!started && maxTime && q.time && maxTime - q.time > FRESH_LAG) continue; // skip stale front only
    started = true;
    pts.push(q.price);
    if (pts.length === 12) break;
  }
  if (pts.length < 12) return null;
  return {
    id, label: s.label, color: s.color, unit: s.unit, modeled: false,
    source: "yahoo",
    sourceNote: "Live forward curve — individual Yahoo dated-contract settlements (M1–M12), the genuine term structure.",
    data: pts.map((v, i) => ({ m: `M${i + 1}`, v: +v.toFixed(curveDp(s.unit)) })),
  };
}

export async function forwardCurves(instr) {
  const modeled = curves(instr); // straight-line fallback, keyed by id
  const out = { modeled: false };

  // WTI / Brent / HO / Gas Oil — dataset structure carried to the live front.
  for (const s of SPEC) {
    if (s.id === "rbob") continue; // RBOB has no dataset curve → real Yahoo curve below
    const inst = byId(instr, s.id);
    const front = inst?.val;
    const csv = history.latestCurve(s.id); // [{ m, contract, v }] or null
    if (front != null && csv && csv.length >= 2) {
      const base = csv[0].v; // dataset front — shift the whole curve onto the live front
      out[s.id] = {
        id: s.id, label: s.label, color: s.color, unit: s.unit, modeled: false,
        source: "dataset", structureAsOf: history.asOf(s.id),
        sourceNote: "Live front month (Yahoo) carried along the real forward-curve structure from the historical dataset (M1–M12).",
        data: csv.slice(0, 12).map((p, i) => ({ m: `M${i + 1}`, v: +(front + (p.v - base)).toFixed(curveDp(s.unit)) })),
      };
    } else if (modeled[s.id]) {
      out[s.id] = { ...modeled[s.id], modeled: true, source: "modeled" };
    }
  }

  // RBOB — real Yahoo dated-contract forward curve; modeled straight-line only
  // if Yahoo can't resolve a full 12-month strip.
  out.rbob = (await yahooDatedCurve("rbob", "RB")) ?? { ...modeled.rbob, modeled: true, source: "modeled" };

  return out;
}

// Inter-commodity spreads (live, from instruments).
export function interSpreads(instr) {
  const g = (id) => byId(instr, id) || {};
  const b = g("brent"), w = g("wti"), r = g("rbob"), h = g("ho"), go = g("gasoil");
  const s = (n) => (Number.isFinite(n) ? n : 0);
  return [
    { lbl: "Brent – WTI",           v: +s(b.val - w.val).toFixed(2),   unit: "$/bbl", note: "Crude arb" },
    { lbl: "RBOB – Heating Oil",    v: +s(r.val - h.val).toFixed(4),   unit: "$/gal", note: "Gas–Heat" },
    { lbl: "Heating Oil – Gas Oil", v: +s(h.bbl - go.bbl).toFixed(2),  unit: "$/bbl", note: "Distillate" },
    { lbl: "RBOB – Gas Oil",        v: +s(r.bbl - go.bbl).toFixed(2),  unit: "$/bbl", note: "Light prod" },
  ];
}

// ----------------------------------------------------------------------------
// Macro block: DXY / SPX / VIX / UST10Y hero tiles + 90D series for the charts.
// ----------------------------------------------------------------------------
export async function macro() {
  const q = await getQuotes(MACRO_SPEC.map((m) => m.yahoo));
  const heroes = MACRO_SPEC.map((m) => {
    const d = q[m.yahoo];
    if (!d?.price) return { sym: m.sym, name: m.name, val: null, chg: 0, pct: 0, unit: m.unit, spark: [] };
    return { sym: m.sym, name: m.name, val: +d.price.toFixed(m.dp), chg: +d.chg.toFixed(m.dp), pct: d.pct, unit: m.unit, spark: d.spark };
  });

  // Aligned 90D series for the DXY/SPX/VIX chart.
  const hist = (sym) => q[MACRO_SPEC.find((m) => m.sym === sym).yahoo]?.history || [];
  const dxy = hist("DXY"), spx = hist("SPX"), vix = hist("VIX");
  const n = Math.min(dxy.length, spx.length, vix.length);
  const series = Array.from({ length: n }, (_, i) => ({
    t: i,
    dxy: dxy[dxy.length - n + i]?.close ?? null,
    spx: spx[spx.length - n + i]?.close ?? null,
    vix: vix[vix.length - n + i]?.close ?? null,
  }));
  return { heroes, series };
}
