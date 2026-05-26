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

// Hero ticker data
export const HERO = [
  { sym: "BRENT", name: "Brent Crude", val: 82.47, chg: +1.23, pct: +1.51, spark: genSpark(1, 30, 1), unit: "$/bbl" },
  { sym: "WTI", name: "WTI Crude", val: 78.92, chg: +0.86, pct: +1.10, spark: genSpark(2, 30, 1), unit: "$/bbl" },
  { sym: "HENRY", name: "Henry Hub", val: 3.142, chg: -0.087, pct: -2.69, spark: genSpark(3, 30, -1), unit: "$/MMBtu" },
  { sym: "TTF", name: "Dutch TTF", val: 38.65, chg: +0.42, pct: +1.10, spark: genSpark(4, 30, 1), unit: "€/MWh" },
  { sym: "JKM", name: "LNG JKM", val: 12.84, chg: -0.31, pct: -2.36, spark: genSpark(5, 30, -1), unit: "$/MMBtu" },
  { sym: "VIX", name: "VIX Index", val: 14.32, chg: +0.18, pct: +1.27, spark: genSpark(6, 30, 1), unit: "" },
  { sym: "DXY", name: "Dollar Index", val: 104.21, chg: -0.34, pct: -0.33, spark: genSpark(7, 30, -1), unit: "" },
];

// Multi-commodity comparison
export const MULTI_SERIES = (() => {
  const days = 90;
  const r1 = seededRand(11), r2 = seededRand(22), r3 = seededRand(33);
  let b = 100, w = 100, h = 100;
  const out = [];
  for (let i = 0; i < days; i++) {
    b += (r1() - 0.48) * 1.8;
    w += (r2() - 0.49) * 2.1;
    h += (r3() - 0.52) * 2.4;
    const d = new Date(2026, 1, 1 + i);
    out.push({
      date: `${d.getMonth() + 1}/${d.getDate()}`,
      Brent: +b.toFixed(2),
      WTI: +w.toFixed(2),
      HenryHub: +h.toFixed(2),
    });
  }
  return out;
})();

// Forward curve
export const FWD_CURVE = [
  { m: "M1", brent: 82.47, wti: 78.92 },
  { m: "M2", brent: 82.12, wti: 78.61 },
  { m: "M3", brent: 81.78, wti: 78.24 },
  { m: "M4", brent: 81.36, wti: 77.81 },
  { m: "M5", brent: 80.92, wti: 77.42 },
  { m: "M6", brent: 80.51, wti: 77.05 },
  { m: "M7", brent: 80.18, wti: 76.72 },
  { m: "M8", brent: 79.85, wti: 76.41 },
  { m: "M9", brent: 79.52, wti: 76.13 },
  { m: "M10", brent: 79.21, wti: 75.86 },
  { m: "M11", brent: 78.93, wti: 75.62 },
  { m: "M12", brent: 78.67, wti: 75.40 },
];

// Correlation matrix
export const CORR_LABELS = ["Brent", "WTI", "HH", "TTF", "JKM", "DXY", "SPX", "VIX"];
export const CORR_MATRIX = [
  [1.00, 0.94, 0.31, 0.62, 0.58, -0.42, 0.51, -0.38],
  [0.94, 1.00, 0.34, 0.58, 0.55, -0.39, 0.49, -0.36],
  [0.31, 0.34, 1.00, 0.71, 0.68, -0.18, 0.22, -0.15],
  [0.62, 0.58, 0.71, 1.00, 0.86, -0.28, 0.31, -0.24],
  [0.58, 0.55, 0.68, 0.86, 1.00, -0.31, 0.34, -0.21],
  [-0.42, -0.39, -0.18, -0.28, -0.31, 1.00, -0.32, 0.18],
  [0.51, 0.49, 0.22, 0.31, 0.34, -0.32, 1.00, -0.78],
  [-0.38, -0.36, -0.15, -0.24, -0.21, 0.18, -0.78, 1.00],
];

// Movers
export const MOVERS = [
  { sym: "GASOIL", val: 742.50, pct: +3.21, vol: "184K" },
  { sym: "RBOB", val: 2.342, pct: +2.86, vol: "92K" },
  { sym: "WTI-BRENT", val: -3.55, pct: -2.14, vol: "—" },
  { sym: "TTF-NBP", val: 1.82, pct: +1.92, vol: "—" },
  { sym: "JKM-TTF", val: -0.34, pct: -1.43, vol: "—" },
  { sym: "CRACK 321", val: 24.86, pct: -0.92, vol: "—" },
  { sym: "DIESEL", val: 2.512, pct: -1.21, vol: "78K" },
  { sym: "FUEL OIL", val: 489.20, pct: +0.84, vol: "31K" },
];

// News feed
export const NEWS = [
  { t: "02:14", sev: "high", src: "REUTERS", txt: "OPEC+ signals possible production cut extension into Q3 2026 amid demand uncertainty", tag: "CRUDE" },
  { t: "01:58", sev: "med", src: "BLOOMBERG", txt: "European gas storage at 64% capacity, above 5-year average ahead of summer injection", tag: "GAS" },
  { t: "01:42", sev: "high", src: "PLATTS", txt: "Red Sea transit volumes drop 38% YoY; tanker rates surge to multi-month highs", tag: "FREIGHT" },
  { t: "01:23", sev: "low", src: "EIA", txt: "Weekly crude inventories drew 4.2 MMbbl vs +1.1 expected; gasoline +2.4 MMbbl", tag: "STOCKS" },
  { t: "00:51", sev: "med", src: "ARGUS", txt: "Asian LNG buyers ramp up term contracting; JKM curve steepens through winter strip", tag: "LNG" },
  { t: "00:34", sev: "low", src: "ICIS", txt: "US Gulf refinery utilization rises to 91.2%, highest since November", tag: "PRODUCTS" },
  { t: "00:12", sev: "high", src: "WSJ", txt: "Fed minutes signal extended hold; dollar strengthens against major commodity currencies", tag: "MACRO" },
];

// Economic calendar
export const ECON = [
  { t: "14:30", evt: "US Crude Stocks", imp: "high", fc: "-2.1M", prev: "-4.2M" },
  { t: "15:00", evt: "EIA Gas Storage", imp: "high", fc: "+82B", prev: "+76B" },
  { t: "16:30", evt: "FOMC Minutes", imp: "high", fc: "—", prev: "—" },
  { t: "21:00", evt: "API Stocks", imp: "med", fc: "—", prev: "+1.8M" },
];

// Inventory data
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

// Shipping congestion
export const SHIPPING = [
  { port: "Singapore", congestion: 78, vessels: 142, delay: "3.2d" },
  { port: "Rotterdam", congestion: 54, vessels: 89, delay: "1.8d" },
  { port: "Fujairah", congestion: 67, vessels: 71, delay: "2.4d" },
  { port: "Houston", congestion: 41, vessels: 58, delay: "1.2d" },
  { port: "Suez", congestion: 92, vessels: 38, delay: "5.8d" },
  { port: "Shanghai", congestion: 61, vessels: 124, delay: "2.1d" },
];

// Weather regions
export const WEATHER = [
  { reg: "US Northeast", temp: -4, anom: -3.2, hdd: 142, severity: "high" },
  { reg: "US Midwest", temp: -8, anom: -5.1, hdd: 168, severity: "high" },
  { reg: "US Gulf Coast", temp: 12, anom: +1.8, hdd: 62, severity: "low" },
  { reg: "NW Europe", temp: 3, anom: -1.4, hdd: 124, severity: "med" },
  { reg: "Northeast Asia", temp: -2, anom: -2.8, hdd: 134, severity: "high" },
  { reg: "S. Europe", temp: 11, anom: +2.1, hdd: 68, severity: "low" },
];

// Alerts
export const ALERTS = [
  { id: 1, sev: "high", t: "02:14", sym: "BRENT", msg: "Crossed above 82.00 resistance", act: true },
  { id: 2, sev: "med", t: "01:48", sym: "TTF", msg: "Volatility 30D > 45%", act: true },
  { id: 3, sev: "high", t: "01:23", sym: "WTI-BRENT", msg: "Spread widened beyond -$4.00", act: true },
  { id: 4, sev: "low", t: "00:54", sym: "JKM", msg: "Backwardation steepening detected", act: false },
  { id: 5, sev: "med", t: "00:31", sym: "DXY", msg: "Below 200D MA", act: false },
];
