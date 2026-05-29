// ============================================================================
// Deterministic helpers
// ============================================================================
export const seededRand = (seed) => {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
};

export const genSeries = (seed, n = 60, base = 80, vol = 1.5, trend = 0.02) => {
  const r = seededRand(seed);
  const out = [];
  let v = base;
  for (let i = 0; i < n; i++) {
    v += (r() - 0.5) * vol + trend;
    out.push({ t: i, v: +v.toFixed(2), o: +(v - r() * vol).toFixed(2), h: +(v + r() * vol).toFixed(2), l: +(v - r() * vol).toFixed(2) });
  }
  return out;
};

export const genSpark = (seed, n = 24, dir = 1) => {
  const r = seededRand(seed);
  let v = 50;
  return Array.from({ length: n }, (_, i) => {
    v += (r() - 0.5) * 6 + dir * 0.4;
    return { x: i, y: +v.toFixed(2) };
  });
};

// Mean-reverting series pinned to `center` at the latest point.
// Used for crack / spread history so the chart's last value matches the live print.
export const genAround = (seed, n, center, amp) => {
  const r = seededRand(seed);
  let v = center;
  const out = [];
  for (let i = 0; i < n; i++) {
    v += (r() - 0.5) * amp - (v - center) * 0.12;
    out.push({ t: i, v: +v.toFixed(2) });
  }
  out[out.length - 1].v = +center.toFixed(2);
  return out;
};

// ============================================================================
// The five instruments this terminal covers
// Brent · WTI · Heating Oil (ULSD) · RBOB Gasoline · ICE Gas Oil
// `bbl` normalises every quote to $/bbl so cracks & spreads are comparable.
// ============================================================================
const GAL_PER_BBL = 42;        // RBOB & Heating Oil quoted in $/gal
const BBL_PER_MT_GASOIL = 7.45; // ICE Gas Oil quoted in $/metric tonne

export const INSTRUMENTS = [
  { id: "brent",  sym: "BRENT",  name: "Brent Crude",        kind: "crude",   color: "#f59e0b", unit: "$/bbl", val: 82.47, chg: +1.23,  pct: +1.51, bbl: 82.47,                            spark: genSpark(1, 30, 1) },
  { id: "wti",    sym: "WTI",    name: "WTI Crude",          kind: "crude",   color: "#38bdf8", unit: "$/bbl", val: 78.92, chg: +0.86,  pct: +1.10, bbl: 78.92,                            spark: genSpark(2, 30, 1) },
  { id: "ho",     sym: "HO",     name: "Heating Oil · ULSD", kind: "product", color: "#10b981", unit: "$/gal", val: 2.512, chg: -0.031, pct: -1.22, bbl: +(2.512 * GAL_PER_BBL).toFixed(2), spark: genSpark(3, 30, -1) },
  { id: "rbob",   sym: "RBOB",   name: "RBOB Gasoline",      kind: "product", color: "#a78bfa", unit: "$/gal", val: 2.342, chg: +0.066, pct: +2.90, bbl: +(2.342 * GAL_PER_BBL).toFixed(2), spark: genSpark(4, 30, 1) },
  { id: "gasoil", sym: "GASOIL", name: "ICE Gas Oil",        kind: "product", color: "#f472b6", unit: "$/mt",  val: 742.5, chg: +23.10, pct: +3.21, bbl: +(742.5 / BBL_PER_MT_GASOIL).toFixed(2), spark: genSpark(5, 30, 1) },
];

export const byId = (id) => INSTRUMENTS.find((i) => i.id === id);

// Hero cards (dashboard) use the instruments directly.
export const HERO = INSTRUMENTS;

// Scrolling ticker strip = instruments + the headline derived spreads/cracks.
export const TICKER = [
  ...INSTRUMENTS.map((i) => ({ sym: i.sym, val: i.val, chg: i.chg, pct: i.pct })),
  { sym: "BRENT-WTI",   val: 3.55,  chg: +0.37, pct: +11.6 },
  { sym: "3:2:1 CRACK", val: 21.82, chg: -0.42, pct: -1.89 },
  { sym: "GASOIL CRK",  val: 17.19, chg: +0.61, pct: +3.68 },
  { sym: "RBOB CRK",    val: 19.44, chg: +0.88, pct: +4.74 },
];

// ============================================================================
// Normalized price action — all five indexed to 100 at window start
// ============================================================================
export const MULTI_SERIES = (() => {
  const days = 90;
  const cfg = [
    { k: "Brent",  seed: 11, vol: 1.7, drift: +0.05 },
    { k: "WTI",    seed: 22, vol: 1.9, drift: +0.04 },
    { k: "HO",     seed: 33, vol: 2.1, drift: -0.03 },
    { k: "RBOB",   seed: 44, vol: 2.4, drift: +0.10 },
    { k: "Gasoil", seed: 55, vol: 2.0, drift: +0.02 },
  ].map((c) => ({ ...c, r: seededRand(c.seed), v: 100 }));
  const out = [];
  for (let i = 0; i < days; i++) {
    const d = new Date(2026, 1, 1 + i);
    const row = { date: `${d.getMonth() + 1}/${d.getDate()}` };
    cfg.forEach((c) => {
      c.v += (c.r() - 0.5) * c.vol + c.drift;
      row[c.k] = +c.v.toFixed(2);
    });
    out.push(row);
  }
  return out;
})();

// ============================================================================
// Forward curves (M1..M12) for all five instruments
// ============================================================================
const genCurve = (front, monthlySlope, seed, jitter) => {
  const r = seededRand(seed);
  return Array.from({ length: 12 }, (_, i) => ({
    m: `M${i + 1}`,
    v: +(front + monthlySlope * i + (r() - 0.5) * jitter).toFixed(3),
  }));
};

export const FWD_CURVES = {
  brent:  { id: "brent",  label: "Brent",       color: "#f59e0b", unit: "$/bbl", data: genCurve(82.47, -0.34, 201, 0.18) },
  wti:    { id: "wti",    label: "WTI",         color: "#38bdf8", unit: "$/bbl", data: genCurve(78.92, -0.30, 202, 0.18) },
  ho:     { id: "ho",     label: "Heating Oil", color: "#10b981", unit: "$/gal", data: genCurve(2.512, -0.012, 203, 0.012) },
  rbob:   { id: "rbob",   label: "RBOB",        color: "#a78bfa", unit: "$/gal", data: genCurve(2.342, +0.009, 204, 0.012) },
  gasoil: { id: "gasoil", label: "Gas Oil",     color: "#f472b6", unit: "$/mt",  data: genCurve(742.5, -2.80, 205, 1.6) },
};

// ============================================================================
// Crack-spread definitions for the five instruments.
// value = ( Σ leg.c · product$/bbl − crudeC · crude$/bbl ) / div   →  $/bbl
// ============================================================================
export const CRACKS = [
  // ---- Single-product cracks ----
  { id: "rbob-wti",    group: "Product Cracks",   label: "RBOB Crack",        legs: [{ p: "rbob", c: 1 }],               crude: "wti",   div: 1 },
  { id: "rbob-brent",  group: "Product Cracks",   label: "RBOB Crack",        legs: [{ p: "rbob", c: 1 }],               crude: "brent", div: 1 },
  { id: "ho-wti",      group: "Product Cracks",   label: "Heating Oil Crack", legs: [{ p: "ho", c: 1 }],                 crude: "wti",   div: 1 },
  { id: "ho-brent",    group: "Product Cracks",   label: "Heating Oil Crack", legs: [{ p: "ho", c: 1 }],                 crude: "brent", div: 1 },
  { id: "gasoil-brent",group: "Product Cracks",   label: "Gas Oil Crack",     legs: [{ p: "gasoil", c: 1 }],             crude: "brent", div: 1 },
  { id: "gasoil-wti",  group: "Product Cracks",   label: "Gas Oil Crack",     legs: [{ p: "gasoil", c: 1 }],             crude: "wti",   div: 1 },
  // ---- Blended refining margins ----
  { id: "321-wti",     group: "Refining Margins", label: "3:2:1 Crack",       legs: [{ p: "rbob", c: 2 }, { p: "ho", c: 1 }], crude: "wti",   crudeC: 3, div: 3 },
  { id: "321-brent",   group: "Refining Margins", label: "3:2:1 Crack",       legs: [{ p: "rbob", c: 2 }, { p: "ho", c: 1 }], crude: "brent", crudeC: 3, div: 3 },
  { id: "211-wti",     group: "Refining Margins", label: "2:1:1 Crack",       legs: [{ p: "rbob", c: 1 }, { p: "ho", c: 1 }], crude: "wti",   crudeC: 2, div: 2 },
  { id: "532-wti",     group: "Refining Margins", label: "5:3:2 Crack",       legs: [{ p: "rbob", c: 3 }, { p: "ho", c: 2 }], crude: "wti",   crudeC: 5, div: 5 },
];

export const crackValue = (c) => {
  const prod = c.legs.reduce((s, l) => s + l.c * byId(l.p).bbl, 0);
  const crudeC = c.crudeC ?? 1;
  return (prod - crudeC * byId(c.crude).bbl) / c.div;
};

// Suffix used in the UI to show which crude the crack is struck against.
export const crackVs = (c) => byId(c.crude).sym;

// ============================================================================
// Correlation matrix — 30D rolling, the five instruments
// (crudes track tightly; middle distillates HO/Gas Oil are the strongest pair;
//  RBOB is the loosest fit as a light/seasonal product)
// ============================================================================
export const CORR_LABELS = ["Brent", "WTI", "HO", "RBOB", "Gasoil"];
export const CORR_MATRIX = [
  [1.00, 0.97, 0.88, 0.82, 0.93],
  [0.97, 1.00, 0.86, 0.84, 0.89],
  [0.88, 0.86, 1.00, 0.79, 0.95],
  [0.82, 0.84, 0.79, 1.00, 0.76],
  [0.93, 0.89, 0.95, 0.76, 1.00],
];

// ============================================================================
// Market movers — the five plus their headline spreads/cracks
// ============================================================================
export const MOVERS = [
  { sym: "GASOIL",       val: 742.50, pct: +3.21,  vol: "184K" },
  { sym: "RBOB",         val: 2.342,  pct: +2.90,  vol: "92K" },
  { sym: "BRENT",        val: 82.47,  pct: +1.51,  vol: "312K" },
  { sym: "WTI",          val: 78.92,  pct: +1.10,  vol: "284K" },
  { sym: "HEATING OIL",  val: 2.512,  pct: -1.22,  vol: "78K" },
  { sym: "BRENT-WTI",    val: 3.55,   pct: +11.60, vol: "—" },
  { sym: "3:2:1 CRACK",  val: 21.82,  pct: -1.89,  vol: "—" },
  { sym: "GASOIL CRACK", val: 17.19,  pct: +3.68,  vol: "—" },
];

// ============================================================================
// News feed
// ============================================================================
export const NEWS = [
  { t: "02:14", sev: "high", src: "REUTERS",      txt: "OPEC+ signals possible production cut extension into Q3 2026 amid demand uncertainty", tag: "OPEC" },
  { t: "02:02", sev: "high", src: "BLOOMBERG",    txt: "Strait of Hormuz tensions flare after tanker seizure; crude risk premium rebuilds", tag: "GEOPOLITICS" },
  { t: "01:42", sev: "high", src: "PLATTS",       txt: "Red Sea transit volumes drop 38% YoY; tanker rates surge to multi-month highs", tag: "FREIGHT" },
  { t: "01:31", sev: "med",  src: "ENERGY INTEL", txt: "JMMC flags Kazakhstan and Iraq overproduction; compensation cuts demanded", tag: "OPEC" },
  { t: "01:23", sev: "low",  src: "EIA",          txt: "Weekly crude inventories drew 4.2 MMbbl vs +1.1 expected; gasoline +2.4 MMbbl", tag: "STOCKS" },
  { t: "01:05", sev: "med",  src: "ARGUS",        txt: "ICE gas oil crack widens to 6-week high as European diesel demand firms", tag: "PRODUCTS" },
  { t: "00:48", sev: "high", src: "REUTERS",      txt: "Drone strikes hit Black Sea export terminal; Urals loadings disrupted", tag: "GEOPOLITICS" },
  { t: "00:34", sev: "low",  src: "ICIS",         txt: "US Gulf refinery utilization rises to 91.2%, highest since November", tag: "PRODUCTS" },
  { t: "00:21", sev: "med",  src: "OPIS",         txt: "RBOB crack rallies into driving-season restocking; 3:2:1 margin tests $22/bbl", tag: "PRODUCTS" },
  { t: "00:12", sev: "high", src: "WSJ",          txt: "Fed minutes signal extended hold; dollar strengthens against major commodity currencies", tag: "MACRO" },
];

// ============================================================================
// Economic calendar
// ============================================================================
export const ECON = [
  { t: "14:30", evt: "US Crude Stocks", imp: "high", fc: "-2.1M", prev: "-4.2M" },
  { t: "15:00", evt: "EIA Distillate",  imp: "high", fc: "+1.4M", prev: "-0.8M" },
  { t: "16:30", evt: "FOMC Minutes",    imp: "high", fc: "—",     prev: "—" },
  { t: "21:00", evt: "API Stocks",      imp: "med",  fc: "—",     prev: "+1.8M" },
];

// ============================================================================
// Inventories (US crude / products)
// ============================================================================
export const INV = [
  { reg: "PADD 1", val: 8.4, chg: -0.3 },
  { reg: "PADD 2", val: 102.7, chg: +1.2 },
  { reg: "PADD 3", val: 248.6, chg: -2.8 },
  { reg: "PADD 4", val: 22.1, chg: +0.1 },
  { reg: "PADD 5", val: 47.3, chg: -0.4 },
];

export const INV_HIST = (() => {
  const r = seededRand(99);
  let v = 460;
  return Array.from({ length: 52 }, (_, i) => {
    v += (r() - 0.5) * 8;
    return { w: i, total: +v.toFixed(1), avg5y: 465 + Math.sin(i / 8) * 12 };
  });
})();

// ============================================================================
// Freight (combined into Market Drivers)
// ============================================================================
export const SHIPPING = [
  { port: "Singapore", congestion: 78, vessels: 142, delay: "3.2d" },
  { port: "Rotterdam", congestion: 54, vessels: 89, delay: "1.8d" },
  { port: "Fujairah", congestion: 67, vessels: 71, delay: "2.4d" },
  { port: "Houston", congestion: 41, vessels: 58, delay: "1.2d" },
  { port: "Suez", congestion: 92, vessels: 38, delay: "5.8d" },
  { port: "Shanghai", congestion: 61, vessels: 124, delay: "2.1d" },
];

// ============================================================================
// Weather (combined into Market Drivers)
// ============================================================================
export const WEATHER = [
  { reg: "US Northeast", temp: -4, anom: -3.2, hdd: 142, severity: "high" },
  { reg: "US Midwest", temp: -8, anom: -5.1, hdd: 168, severity: "high" },
  { reg: "US Gulf Coast", temp: 12, anom: +1.8, hdd: 62, severity: "low" },
  { reg: "NW Europe", temp: 3, anom: -1.4, hdd: 124, severity: "med" },
  { reg: "Northeast Asia", temp: -2, anom: -2.8, hdd: 134, severity: "high" },
  { reg: "S. Europe", temp: 11, anom: +2.1, hdd: 68, severity: "low" },
];

// ============================================================================
// Oil-specific supply drivers (Drivers › Oil Supply Drivers)
// OPEC+ quota compliance · Baker Hughes rig count · EIA/API weekly stock flows
// ============================================================================

// OPEC+ production vs agreed target (mb/d). compliance = quota / output:
//  ≥100% → producing at/below target (deeper cut, supportive of price)
//  <100% → overproducing the quota (bearish, weak adherence)
export const OPEC_QUOTAS = [
  { member: "Saudi Arabia", quota: 9.00, prod: 8.97 },
  { member: "Russia",       quota: 9.00, prod: 9.18 },
  { member: "Iraq",         quota: 4.00, prod: 4.22 },
  { member: "UAE",          quota: 2.91, prod: 2.92 },
  { member: "Kuwait",       quota: 2.41, prod: 2.39 },
  { member: "Kazakhstan",   quota: 1.47, prod: 1.65 },
  { member: "Nigeria",      quota: 1.50, prod: 1.38 },
  { member: "Algeria",      quota: 0.91, prod: 0.90 },
];

export const opecCompliance = (m) => +((m.quota / m.prod) * 100).toFixed(1);

export const OPEC_TOTAL = OPEC_QUOTAS.reduce(
  (a, m) => ({ quota: +(a.quota + m.quota).toFixed(2), prod: +(a.prod + m.prod).toFixed(2) }),
  { quota: 0, prod: 0 }
);

// Baker Hughes weekly US rig count — drilling activity = future shale supply.
// Last point pinned to the live print used on the hero cards.
export const RIG_COUNT = (() => {
  const r = seededRand(77);
  let oil = 515, gas = 101;
  const out = Array.from({ length: 52 }, (_, i) => {
    oil += (r() - 0.5) * 7 - 0.32;
    gas += (r() - 0.5) * 3 - 0.04;
    return { w: i, oil: Math.round(oil), gas: Math.round(gas) };
  });
  out[out.length - 1].oil = 497;
  out[out.length - 1].gas = 98;
  return out;
})();

// EIA / API weekly crude inventory change (MMbbl) — the build/draw time series.
// Negative = draw (bullish), positive = build (bearish). Last EIA bar pinned to
// the -4.2 MMbbl print shown in NEWS and InventorySnap so the panels agree.
export const STOCK_FLOWS = (() => {
  const r = seededRand(88);
  const out = Array.from({ length: 20 }, (_, i) => {
    const base = Math.sin(i / 3.2) * 3.4 + (r() - 0.5) * 3.2;
    const eia = +base.toFixed(1);
    const api = +(base + (r() - 0.5) * 2.4).toFixed(1);
    const d = new Date(2026, 0, 8 + i * 7);
    return { w: `${d.getMonth() + 1}/${d.getDate()}`, eia, api };
  });
  const last = out[out.length - 1];
  last.eia = -4.2;
  last.api = -3.1;
  return out;
})();
