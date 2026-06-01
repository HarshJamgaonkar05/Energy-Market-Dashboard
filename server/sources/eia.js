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

// ----------------------------------------------------------------------------
// Inventory snapshot: hero tiles, PADD breakdown, 52-week crude history.
// ----------------------------------------------------------------------------
export async function inventories() {
  if (!eiaEnabled()) return null;

  const [crude, spr, cushing, gasoline, distillate, refUtil, p1, p2, p3, p4, p5] =
    await Promise.all([
      series("PET.WCESTUS1.W", 60),
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

  // 52W crude history vs a flat 5Y mean proxy (EIA doesn't expose the 5Y band
  // as a series, so we draw it as the trailing-year average — labeled in UI).
  const hist = (crude || []).slice(-52).map((r, i) => ({
    w: i,
    total: toMM(r.value),
  }));
  const mean = hist.length ? hist.reduce((s, p) => s + p.total, 0) / hist.length : 0;
  hist.forEach((p) => (p.avg5y = +mean.toFixed(1)));

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
