// ============================================================================
// Seasonality — average behaviour by calendar month, computed from ~10 years of
// Yahoo monthly closes. Energy is the most seasonal commodity complex, so this
// answers two questions traders ask constantly:
//
//   • PRICE:  what does WTI/Brent/RBOB/HO typically do each month, and where are
//             we vs the "typical" seasonal path? → average month-over-month
//             return per calendar month + a hit rate (% of years positive) + a
//             cumulative seasonal path indexed to 100.
//   • CRACK:  refining margins are strongly seasonal (gasoline crack peaks into
//             summer driving season; heating-oil crack into winter). → average
//             crack LEVEL ($/bbl) per calendar month, from aligned monthly
//             product/crude closes, plus the latest value vs its monthly norm.
//
// This reuses the same "average across prior years per calendar period" idea as
// the EIA 5-year inventory band, extended from weeks to months and to prices.
// Cached 12h (monthly bars move slowly).
// ============================================================================
import { monthlyCloses } from "../sources/yahoo.js";
import { cached } from "../lib/cache.js";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const GAL = 42; // $/gal → $/bbl for the refined products

// Average month-over-month % return per calendar month, with a hit rate and a
// cumulative "typical path" indexed to 100 at the start of the year.
function priceMonths(series) {
  const buckets = Array.from({ length: 12 }, () => []);
  for (let i = 1; i < series.length; i++) {
    const a = series[i - 1].close;
    const b = series[i].close;
    if (!a || !b) continue;
    buckets[series[i].date.getUTCMonth()].push((b / a - 1) * 100);
  }
  const months = buckets.map((arr, m) => {
    const n = arr.length;
    const avgRet = n ? arr.reduce((s, v) => s + v, 0) / n : 0;
    const hit = n ? Math.round((arr.filter((v) => v > 0).length / n) * 100) : 0;
    return { m: MONTHS[m], avgRet: +avgRet.toFixed(2), hit, n };
  });
  let path = 100;
  for (const mm of months) {
    path *= 1 + mm.avgRet / 100;
    mm.path = +path.toFixed(1);
  }
  return months;
}

// Align several monthly series on shared year-month keys.
function align(map) {
  const keys = Object.keys(map);
  const idx = {};
  for (const k of keys) {
    for (const pt of map[k]) {
      const ym = `${pt.date.getUTCFullYear()}-${pt.date.getUTCMonth()}`;
      (idx[ym] ??= { date: pt.date })[k] = pt.close;
    }
  }
  return Object.values(idx)
    .filter((r) => keys.every((k) => r[k] != null))
    .sort((a, b) => a.date - b.date);
}

// Average crack LEVEL ($/bbl) per calendar month from aligned rows.
function crackMonths(rows, fn) {
  const buckets = Array.from({ length: 12 }, () => []);
  for (const r of rows) {
    const c = fn(r);
    if (Number.isFinite(c)) buckets[r.date.getUTCMonth()].push(c);
  }
  const months = buckets.map((arr, m) => {
    const n = arr.length;
    const avg = n ? arr.reduce((s, v) => s + v, 0) / n : 0;
    return { m: MONTHS[m], avg: +avg.toFixed(2), n };
  });
  const last = rows.at(-1);
  return { months, current: last ? +fn(last).toFixed(2) : null };
}

export async function seasonality() {
  return cached("seasonality:all", 12 * 60 * 60_000, async () => {
    const [wti, brent, rbob, ho] = await Promise.all([
      monthlyCloses("CL=F"),
      monthlyCloses("BZ=F"),
      monthlyCloses("RB=F"),
      monthlyCloses("HO=F"),
    ]);
    const nowM = new Date().getUTCMonth();

    const price = (id, label, s) => ({
      id, kind: "price", label, unit: "%",
      months: priceMonths(s), currentMonth: nowM, years: Math.round(s.length / 12),
    });

    // Cracks are vs WTI, products converted $/gal → $/bbl.
    const rows = align({ wti, rbob, ho });
    const crack = (id, label, fn) => ({
      id, kind: "crack", label, unit: "$/bbl",
      ...crackMonths(rows, fn), currentMonth: nowM, years: Math.round(rows.length / 12),
    });

    const series = [
      price("WTI", "WTI Crude", wti),
      price("BRENT", "Brent Crude", brent),
      price("RBOB", "RBOB Gasoline", rbob),
      price("HO", "Heating Oil", ho),
      crack("RBOB-WTI", "RBOB Crack", (r) => r.rbob * GAL - r.wti),
      crack("HO-WTI", "Heating Oil Crack", (r) => r.ho * GAL - r.wti),
      crack("321-WTI", "3:2:1 Crack", (r) => (2 * r.rbob * GAL + r.ho * GAL - 3 * r.wti) / 3),
    ];

    return { series, asOf: rows.at(-1)?.date?.toISOString?.().slice(0, 10) ?? null };
  });
}
