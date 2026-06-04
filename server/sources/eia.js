// ============================================================================
// EIA Open Data API v2 — U.S. Energy Information Administration (official, free).
// Register a key: https://www.eia.gov/opendata/register.php
//
// We use the v2 `/seriesid/{ID}` route, which resolves a legacy EIA series ID
// directly without needing its category/facet path. IMPORTANT: the ID must be
// the FULL legacy form `CATEGORY.SERIES.FREQ` (e.g. PET.WCESTUS1.W) — the bare
// series code 404s. Response shape:
//   { response: { data: [ { period: "YYYY-MM-DD", value: <number> }, ... ] } }
//
// Weekly Petroleum Status Report series:
//   PET.WCESTUS1.W            U.S. crude stocks excl. SPR        (Mbbl)
//   PET.WCSSTUS1.W            U.S. crude in Strategic Reserve     (Mbbl)
//   PET.W_EPC0_SAX_YCUOK_MBBL.W  Cushing, OK crude stocks         (Mbbl)
//   PET.WGTSTUS1.W            U.S. total gasoline stocks          (Mbbl)
//   PET.WDISTUS1.W            U.S. distillate fuel oil stocks     (Mbbl)
//   PET.WPULEUS3.W            Refinery % utilization of capacity  (percent)
//   PET.WCESTP{1..5}1.W       Crude stocks by PADD region         (Mbbl)
// Daily spot prices:
//   PET.RWTC.D                WTI Cushing spot                    ($/bbl)
//   PET.RBRTE.D               Brent Europe spot                   ($/bbl)
// EIA reports stocks in thousand barrels; we divide by 1000 to get MMbbl.
// ============================================================================
import { cached, fetchJSON } from "../lib/cache.js";

const KEY = () => process.env.EIA_API_KEY?.trim();
export const eiaEnabled = () => Boolean(KEY());

const BASE = "https://api.eia.gov/v2/seriesid";

// Fetch the latest N points of a series, oldest→newest. Cached 6h (weekly data).
async function series(id, length = 60) {
  if (!eiaEnabled()) return null;
  return cached(`eia:${id}:${length}`, 6 * 60 * 60_000, async () => {
    const url =
      `${BASE}/${id}?api_key=${KEY()}` +
      `&sort[0][column]=period&sort[0][direction]=desc&length=${length}`;
    const json = await fetchJSON(url);
    const rows = json?.response?.data;
    if (!Array.isArray(rows) || rows.length === 0) throw new Error(`EIA: no data for ${id}`);
    return rows
      .map((r) => ({ period: r.period, value: r.value == null ? null : Number(r.value) }))
      .filter((r) => r.value != null)
      .reverse(); // chronological
  });
}

const latest = (arr) => (arr && arr.length ? arr.at(-1).value : null);
const prior = (arr) => (arr && arr.length > 1 ? arr.at(-2).value : null);
const toMM = (kbbl) => (kbbl == null ? null : +(kbbl / 1000).toFixed(1));

// Week-of-year (1..53) for a YYYY-MM-DD period, used to align weekly stock
// readings across calendar years for the 5-year seasonal band.
const weekOfYear = (period) => {
  const d = new Date(`${period}T00:00:00Z`);
  const dayOfYear = Math.floor((d - Date.UTC(d.getUTCFullYear(), 0, 1)) / 86_400_000);
  return Math.floor(dayOfYear / 7) + 1;
};

// Build a week-of-year → {min,max,avg} map from the 5 calendar years preceding
// `curYear` (the current year is excluded so "this year vs history" is honest).
function seasonalBand(rows, curYear) {
  const window = new Set([1, 2, 3, 4, 5].map((n) => curYear - n));
  const byWeek = {};
  for (const r of rows) {
    const mm = toMM(r.value);
    if (mm == null) continue;
    const yr = new Date(`${r.period}T00:00:00Z`).getUTCFullYear();
    if (!window.has(yr)) continue;
    (byWeek[weekOfYear(r.period)] ??= []).push(mm);
  }
  const band = {};
  for (const [w, vals] of Object.entries(byWeek)) {
    band[w] = {
      min: +Math.min(...vals).toFixed(1),
      max: +Math.max(...vals).toFixed(1),
      avg: +(vals.reduce((s, v) => s + v, 0) / vals.length).toFixed(1),
    };
  }
  return band;
}

// ----------------------------------------------------------------------------
// Inventory snapshot: hero tiles, PADD breakdown, 52-week crude history.
// ----------------------------------------------------------------------------
export async function inventories() {
  if (!eiaEnabled()) return null;

  const [crude, spr, cushing, gasoline, distillate, refUtil, p1, p2, p3, p4, p5] =
    await Promise.all([
      // ~5.4 years so the seasonal band has 5 prior years per week-of-year.
      series("PET.WCESTUS1.W", 285),
      series("PET.WCSSTUS1.W", 8),
      series("PET.W_EPC0_SAX_YCUOK_MBBL.W", 8),
      series("PET.WGTSTUS1.W", 8),
      series("PET.WDISTUS1.W", 8),
      series("PET.WPULEUS3.W", 8),
      series("PET.WCESTP11.W", 4),
      series("PET.WCESTP21.W", 4),
      series("PET.WCESTP31.W", 4),
      series("PET.WCESTP41.W", 4),
      series("PET.WCESTP51.W", 4),
    ]);

  const heroCell = (arr, sym, name) => {
    const cur = toMM(latest(arr));
    const prv = toMM(prior(arr));
    const chg = cur != null && prv != null ? +(cur - prv).toFixed(1) : 0;
    const pct = prv ? +((chg / prv) * 100).toFixed(2) : 0;
    return { sym, name, val: cur, chg, pct, unit: "MMbbl" };
  };

  const paddCell = (arr, reg) => {
    const cur = toMM(latest(arr));
    const prv = toMM(prior(arr));
    return { reg, val: cur, chg: cur != null && prv != null ? +(cur - prv).toFixed(1) : 0 };
  };

  // 52W crude history with a REAL 5-year seasonal band: for each week-of-year
  // we take the min/max/avg of the 5 prior calendar years, so the chart shows
  // where current stocks sit inside the normal seasonal envelope.
  const curYear = crude?.length
    ? new Date(`${crude.at(-1).period}T00:00:00Z`).getUTCFullYear()
    : new Date().getUTCFullYear();
  const band = crude ? seasonalBand(crude, curYear) : {};
  const hist = (crude || []).slice(-52).map((r) => {
    const b = band[weekOfYear(r.period)];
    const d = new Date(`${r.period}T00:00:00Z`);
    return {
      w: `${d.getUTCMonth() + 1}/${d.getUTCDate()}`,
      total: toMM(r.value),
      avg5y: b?.avg ?? null,
      min5y: b?.min ?? null,
      max5y: b?.max ?? null,
      // Recharts renders a [low, high] dataKey as a filled range band.
      band: b ? [b.min, b.max] : null,
    };
  });

  return {
    heroes: [
      heroCell(crude, "US CRUDE", "Total Stocks"),
      heroCell(cushing, "CUSHING", "Cushing OK"),
      heroCell(spr, "SPR", "Strategic Reserve"),
      heroCell(gasoline, "GASOLINE", "US Gasoline"),
    ].filter((h) => h.val != null),
    padd: [
      paddCell(p1, "PADD 1"),
      paddCell(p2, "PADD 2"),
      paddCell(p3, "PADD 3"),
      paddCell(p4, "PADD 4"),
      paddCell(p5, "PADD 5"),
    ].filter((p) => p.val != null),
    hist,
    refineryUtil: latest(refUtil),
    distillate: toMM(latest(distillate)),
    asOf: crude?.at(-1)?.period ?? null,
  };
}

// ----------------------------------------------------------------------------
// Weekly crude build/draw: week-over-week change in total crude stocks (MMbbl).
// Negative = draw (bullish), positive = build (bearish). EIA only; the API
// (Amer. Petroleum Inst.) line is members-only — the UI marks it modeled.
// ----------------------------------------------------------------------------
export async function stockFlows() {
  if (!eiaEnabled()) return null;
  const crude = await series("PET.WCESTUS1.W", 24);
  if (!crude) return null;
  const out = [];
  for (let i = 1; i < crude.length; i++) {
    const chg = toMM(crude[i].value) - toMM(crude[i - 1].value);
    const d = new Date(crude[i].period);
    out.push({ w: `${d.getMonth() + 1}/${d.getDate()}`, eia: +chg.toFixed(1), period: crude[i].period });
  }
  return out.slice(-20);
}

// ----------------------------------------------------------------------------
// Official daily spot prices (used as a settlement cross-check vs Yahoo).
// ----------------------------------------------------------------------------
export async function spot() {
  if (!eiaEnabled()) return null;
  const [wti, brent] = await Promise.all([series("PET.RWTC.D", 5), series("PET.RBRTE.D", 5)]);
  return { wti: latest(wti), brent: latest(brent) };
}
