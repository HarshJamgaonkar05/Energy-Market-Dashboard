// ============================================================================
// Yahoo Finance — public chart endpoint (no key, unofficial but stable).
//   GET /v8/finance/chart/{symbol}?range=&interval=
// One call returns BOTH the live quote (meta.regularMarketPrice) and the
// historical close series, so a single fetch powers price, %chg, sparkline,
// the normalized multi-series chart, and the correlation matrix.
//
// Symbols we use:
//   CL=F Crude WTI · BZ=F Brent · HO=F Heating Oil · RB=F RBOB · NG=F Nat Gas
//   ^GSPC S&P500 · ^VIX Volatility · ^TNX 10Y yield · DX-Y.NYB Dollar Index
// ============================================================================
import { cached, fetchJSON } from "../lib/cache.js";

const BASE = "https://query1.finance.yahoo.com/v8/finance/chart";

// Raw chart fetch, cached ~45s. Prices are intraday-live; 45s keeps us well
// inside Yahoo's tolerance while the dashboard polls every 30–60s.
async function rawChart(symbol, range = "3mo", interval = "1d") {
  const key = `yahoo:${symbol}:${range}:${interval}`;
  return cached(key, 45_000, async () => {
    const url = `${BASE}/${encodeURIComponent(symbol)}?range=${range}&interval=${interval}&includePrePost=false`;
    const json = await fetchJSON(url);
    const r = json?.chart?.result?.[0];
    if (!r) throw new Error(`Yahoo: empty result for ${symbol}`);
    return r;
  });
}

// Clean close series aligned with dates (drops nulls Yahoo leaves for holidays).
function closeSeries(result) {
  const ts = result.timestamp || [];
  const closes = result.indicators?.quote?.[0]?.close || [];
  const out = [];
  for (let i = 0; i < ts.length; i++) {
    if (closes[i] == null) continue;
    out.push({ ts: ts[i], date: new Date(ts[i] * 1000), close: closes[i] });
  }
  return out;
}

/**
 * Live quote + sparkline + recent close history for one symbol.
 * Two ranges: a 1d quote (whose chartPreviousClose IS yesterday's close, so the
 * DAILY %change is correct) and a 3mo series for the sparkline + history. On a
 * longer range Yahoo's chartPreviousClose is the pre-window close, which would
 * make the daily change wildly wrong — hence the dedicated 1d fetch.
 * @returns {{ price, prev, chg, pct, dayHigh, dayLow, volume, name, spark, history }}
 */
export async function getQuote(symbol) {
  const [day, long] = await Promise.all([
    rawChart(symbol, "1d", "1d"),
    rawChart(symbol, "3mo", "1d"),
  ]);
  const m = day.meta || {};
  const series = closeSeries(long);
  const price = m.regularMarketPrice ?? series.at(-1)?.close ?? null;
  const prev = m.chartPreviousClose ?? m.previousClose ?? series.at(-2)?.close ?? price;
  const chg = price != null && prev != null ? price - prev : 0;
  const pct = prev ? (chg / prev) * 100 : 0;

  // Sparkline = last ~30 daily closes, reindexed {x,y} like the mock.
  const tail = series.slice(-30);
  const spark = tail.map((p, i) => ({ x: i, y: +p.close.toFixed(4) }));

  return {
    price,
    prev,
    chg: +chg.toFixed(4),
    pct: +pct.toFixed(2),
    dayHigh: m.regularMarketDayHigh ?? null,
    dayLow: m.regularMarketDayLow ?? null,
    volume: m.regularMarketVolume ?? null,
    name: m.shortName ?? symbol,
    spark,
    history: series.map((p) => ({ date: p.date, close: +p.close.toFixed(4) })),
  };
}

/**
 * Last price + last-trade time for a list of symbols — used to build real
 * forward curves from individual dated contracts (e.g. CLZ26.NYM). One cached
 * 1d chart fetch each; a delisted contract resolves to {price:null}. The time
 * lets the caller drop an expiring front that stopped trading before the rest.
 * @returns {Promise<Record<string, {price:number|null, time:number|null}>>}
 */
export async function getFrontPrices(symbols) {
  const entries = await Promise.all(
    symbols.map(async (s) => {
      try {
        const r = await rawChart(s, "1d", "1d");
        const p = r?.meta?.regularMarketPrice;
        const t = r?.meta?.regularMarketTime;
        return [s, { price: Number.isFinite(p) ? p : null, time: Number.isFinite(t) ? t : null }];
      } catch {
        return [s, { price: null, time: null }];
      }
    })
  );
  return Object.fromEntries(entries);
}

/** Fetch quotes for many symbols in parallel; failures resolve to null. */
export async function getQuotes(symbols) {
  const entries = await Promise.all(
    symbols.map(async (s) => {
      try {
        return [s, await getQuote(s)];
      } catch (e) {
        console.warn(`[yahoo] ${s} failed: ${e.message}`);
        return [s, null];
      }
    })
  );
  return Object.fromEntries(entries);
}
