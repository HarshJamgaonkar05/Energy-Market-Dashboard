// ============================================================================
// CFTC Commitments of Traders (COT) — free, official weekly positioning data.
//   Disaggregated Futures-Only report, Socrata API (no key):
//   https://publicreporting.cftc.gov/resource/72hh-3qpy.json
//
// We track "Managed Money" (the speculative funds whose net positioning traders
// watch as a sentiment / crowding gauge) for the four energy contracts that
// match the dashboard's instruments. Contract CODES are stable across the
// market-name renames CFTC has done over the years, so we filter by code:
//
//   067651  WTI-PHYSICAL (NYMEX WTI)        06765T  BRENT LAST DAY (NYMEX)
//   111659  GASOLINE RBOB (NYMEX)           022651  NY HARBOR ULSD (NYMEX)
//
// Released weekly (Friday ~15:30 ET, as of the prior Tuesday). We pull ~3 years
// so we can place the current net position inside its own historical range
// (percentile) — extremes are the contrarian signal. Cached 6h.
// ============================================================================
import { cached, fetchJSON } from "../lib/cache.js";

const BASE = "https://publicreporting.cftc.gov/resource/72hh-3qpy.json";

const MARKETS = [
  { id: "WTI",   code: "067651", name: "WTI Crude" },
  { id: "BRENT", code: "06765T", name: "Brent Crude" },
  { id: "RBOB",  code: "111659", name: "RBOB Gasoline" },
  { id: "HO",    code: "022651", name: "ULSD / Heating Oil" },
];

const SELECT = [
  "report_date_as_yyyy_mm_dd",
  "open_interest_all",
  "m_money_positions_long_all",
  "m_money_positions_short_all",
  "change_in_m_money_long_all",
  "change_in_m_money_short_all",
  "prod_merc_positions_long",
  "prod_merc_positions_short",
].join(",");

// Weekly history for one contract code, chronological (oldest→newest).
async function history(code, weeks = 160) {
  const url =
    `${BASE}?cftc_contract_market_code=${code}` +
    `&$select=${SELECT}` +
    `&$order=report_date_as_yyyy_mm_dd DESC&$limit=${weeks}`;
  const rows = await fetchJSON(encodeURI(url), { timeout: 20_000 });
  return rows
    .map((r) => ({
      date: (r.report_date_as_yyyy_mm_dd || "").slice(0, 10),
      oi: +r.open_interest_all,
      mmLong: +r.m_money_positions_long_all,
      mmShort: +r.m_money_positions_short_all,
      dLong: +r.change_in_m_money_long_all,
      dShort: +r.change_in_m_money_short_all,
      commLong: +r.prod_merc_positions_long,
      commShort: +r.prod_merc_positions_short,
    }))
    .filter((r) => Number.isFinite(r.mmLong) && Number.isFinite(r.mmShort))
    .reverse();
}

export async function cot() {
  return cached("cftc:cot", 6 * 60 * 60_000, async () => {
    const out = await Promise.all(
      MARKETS.map(async (m) => {
        try {
          const h = await history(m.code);
          if (h.length < 2) return null;
          const net = (r) => r.mmLong - r.mmShort;
          const nets = h.map(net);
          const last = h.at(-1);
          const prev = h.at(-2);
          const cur = net(last);
          const min = Math.min(...nets);
          const max = Math.max(...nets);
          // Where does today's net sit in its ~3-year range? (0 = most short
          // ever, 100 = most long ever.) Extremes flag crowded positioning.
          const pctile = max > min ? Math.round(((cur - min) / (max - min)) * 100) : 50;
          const longShort = last.mmLong + last.mmShort;

          return {
            id: m.id,
            name: m.name,
            asOf: last.date,
            oi: last.oi,
            mmLong: last.mmLong,
            mmShort: last.mmShort,
            net: cur,
            netChg: prev ? cur - net(prev) : 0, // week-over-week change in net
            netPctOi: last.oi ? +((cur / last.oi) * 100).toFixed(1) : null,
            longShare: longShort ? Math.round((last.mmLong / longShort) * 100) : 50,
            pctile,
            extreme: pctile >= 85 ? "crowded long" : pctile <= 15 ? "crowded short" : null,
            commNet: last.commLong - last.commShort, // producers/merchants = the hedgers
            // ~2 years of net history for a sparkline-style chart (M/D labels).
            hist: h.slice(-104).map((r) => ({ d: `${r.date.slice(5, 7)}/${r.date.slice(8, 10)}`, net: net(r) })),
          };
        } catch (e) {
          console.warn(`[cftc] ${m.id} failed: ${e.message}`);
          return null;
        }
      })
    );
    const markets = out.filter(Boolean);
    if (!markets.length) throw new Error("CFTC: no markets returned");
    return { markets, asOf: markets[0].asOf };
  });
}
