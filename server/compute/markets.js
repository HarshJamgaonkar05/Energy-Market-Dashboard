// ============================================================================
// Market compute layer — turns raw Yahoo quotes/history into the exact shapes
// the frontend panels render: instruments, ticker, movers, normalized series,
// correlation matrix, crack spreads, forward curves, inter-commodity spreads,
// and the macro block.
// ============================================================================
import { getQuotes } from "../sources/yahoo.js";

const GAL_PER_BBL = 42;
const BBL_PER_MT_GASOIL = 7.45;

// The five instruments. Gas Oil has no free live feed, so it is proxied from
// NYMEX ULSD (HO=F) — both are middle distillates — and flagged `modeled:true`.
const SPEC = [
  { id: "brent",  sym: "BRENT",  name: "Brent Crude",        label: "Brent",       kind: "crude",   color: "#f59e0b", unit: "$/bbl", yahoo: "BZ=F" },
  { id: "wti",    sym: "WTI",    name: "WTI Crude",          label: "WTI",         kind: "crude",   color: "#38bdf8", unit: "$/bbl", yahoo: "CL=F" },
  { id: "ho",     sym: "HO",     name: "Heating Oil · ULSD", label: "Heating Oil", kind: "product", color: "#10b981", unit: "$/gal", yahoo: "HO=F" },
  { id: "rbob",   sym: "RBOB",   name: "RBOB Gasoline",      label: "RBOB",        kind: "product", color: "#a78bfa", unit: "$/gal", yahoo: "RB=F" },
  { id: "gasoil", sym: "GASOIL", name: "ICE Gas Oil",        label: "Gas Oil",     kind: "product", color: "#f472b6", unit: "$/mt",  proxyOf: "ho", modeled: true, source: "derived", sourceNote: "Proxied from live NYMEX ULSD (HO=F), unit-converted to $/mt." },
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

// ----------------------------------------------------------------------------
// Build the live instrument array (HERO / HeroCards / INSTRUMENTS shape).
// ----------------------------------------------------------------------------
export async function instruments() {
  const q = await getQuotes(ENERGY_SYMS);
  const bySym = Object.fromEntries(SPEC.filter((s) => s.yahoo).map((s) => [s.id, q[s.yahoo]]));

  return SPEC.map((s) => {
    if (s.proxyOf) {
      // Gas Oil proxy: ULSD $/gal -> $/bbl (×42) -> $/mt (×7.45 bbl per tonne).
      const galToMt = (gal) => gal * GAL_PER_BBL * BBL_PER_MT_GASOIL;
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
// Normalized 90D series (indexed to 100) + correlation matrix from histories.
// ----------------------------------------------------------------------------
export async function seriesAndCorrelation() {
  const q = await getQuotes(ENERGY_SYMS);
  const keyMap = { brent: "Brent", wti: "WTI", ho: "HO", rbob: "RBOB", gasoil: "Gasoil" };

  // closes per instrument, keyed by date string
  const closesById = {};
  for (const s of SPEC) {
    const src = s.proxyOf ? q[SPEC.find((x) => x.id === s.proxyOf).yahoo] : q[s.yahoo];
    closesById[s.id] = src?.history || [];
  }

  // Align on dates present in every series.
  const wti = closesById.wti;
  const dateOf = (d) => `${d.getMonth() + 1}/${d.getDate()}`;
  const rows = [];
  const aligned = { brent: [], wti: [], ho: [], rbob: [], gasoil: [] };
  for (const point of wti) {
    const dstr = dateOf(point.date);
    const vals = {};
    let ok = true;
    for (const id of Object.keys(closesById)) {
      const match = closesById[id].find((p) => dateOf(p.date) === dstr);
      if (!match) { ok = false; break; }
      vals[id] = match.close;
    }
    if (!ok) continue;
    rows.push({ date: dstr, ...vals });
    for (const id of Object.keys(vals)) aligned[id].push(vals[id]);
  }

  // Normalize each to 100 at window start.
  const series = rows.map((r) => {
    const out = { date: r.date };
    for (const id of Object.keys(keyMap)) {
      const base = rows[0][id];
      out[keyMap[id]] = base ? +((r[id] / base) * 100).toFixed(2) : 100;
    }
    return out;
  });

  const correlation = correlationMatrix(aligned, Object.keys(keyMap).map((k) => keyMap[k]));
  return { series, correlation };
}

function correlationMatrix(aligned, labels) {
  const ids = ["brent", "wti", "ho", "rbob", "gasoil"];
  // daily simple returns, last 30
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
        v: +(front + slope * i).toFixed(s.unit === "$/gal" ? 4 : s.unit === "$/mt" ? 1 : 3),
      })),
    };
  }
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
