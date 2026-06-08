// ============================================================================
// Derived / modeled datasets that have no clean free live feed.
//   • calendar  — built from the known U.S. energy-report release cadence (real)
//   • opec      — curated published quotas + EIA total production (mixed)
//   • freight   — MODELED tanker rates / BDI / routes (Baltic Exchange is paid)
//   • rigs      — MODELED Baker Hughes 52W (BH publishes Excel only, no API)
//   • sentiment — COMPUTED from live price momentum + news severity
// Everything modeled is flagged so the UI can badge it "indicative".
// ============================================================================

// Deterministic PRNG seeded by an integer (so a "modeled" series is stable
// within a day but shifts day-to-day, giving a live-ish feel).
const rng = (seed) => {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return () => (s = (s * 16807) % 2147483647) / 2147483647;
};
const daySeed = () => Math.floor(Date.now() / 86_400_000); // changes once per day

// ----------------------------------------------------------------------------
// Economic calendar — real U.S. release schedule (times in ET). We surface
// today's releases; if none today, we roll forward to the next scheduled days.
// Forecast/prior numbers are paywalled, so fc/prev show "—" unless the route
// enriches them (e.g. prev crude build from EIA).
// ----------------------------------------------------------------------------
const SCHEDULE = {
  2: [{ t: "16:30", evt: "API Crude Stocks", imp: "med" }], // Tue
  3: [
    { t: "10:30", evt: "EIA Crude Stocks", imp: "high" },
    { t: "10:30", evt: "EIA Gasoline Stocks", imp: "med" },
    { t: "10:30", evt: "EIA Distillate", imp: "high" },
  ], // Wed
  4: [{ t: "10:30", evt: "EIA Natural Gas Storage", imp: "high" }], // Thu
  5: [{ t: "13:00", evt: "Baker Hughes Rig Count", imp: "med" }], // Fri
};

const DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

// Collect the upcoming week of scheduled releases (today first), each tagged
// with its weekday + date. `enrich` supplies real forecast/prior numbers for
// named events (e.g. EIA crude build pulled from the live WPSR) — anything not
// enriched shows "—" because the consensus/prior figures are paywalled.
export function calendar(enrich = {}, limit = 6) {
  const now = new Date();
  const out = [];
  for (let offset = 0; offset < 7 && out.length < limit; offset++) {
    const day = new Date(now);
    day.setUTCDate(now.getUTCDate() + offset);
    const events = SCHEDULE[day.getUTCDay()] || [];
    for (const e of events) {
      if (out.length >= limit) break;
      out.push({
        day: DOW[day.getUTCDay()],
        date: `${day.getUTCMonth() + 1}/${day.getUTCDate()}`,
        today: offset === 0,
        t: e.t,
        evt: e.evt,
        imp: e.imp,
        fc: enrich[e.evt]?.fc ?? "—",
        prev: enrich[e.evt]?.prev ?? "—",
      });
    }
  }
  return out;
}

// ----------------------------------------------------------------------------
// OPEC+ quotas (published policy targets) + per-member output (recent estimates).
// These are policy/curated numbers — EIA's STEO only publishes an OPEC-only
// aggregate (and is forecast-oriented), which doesn't map cleanly onto this
// OPEC+ table that includes Russia/Kazakhstan. compliance = quota / output * 100.
// ----------------------------------------------------------------------------
const OPEC_QUOTAS = [
  { member: "Saudi Arabia", quota: 9.0,  prod: 8.97 },
  { member: "Russia",       quota: 9.0,  prod: 9.18 },
  { member: "Iraq",         quota: 4.0,  prod: 4.22 },
  { member: "UAE",          quota: 2.91, prod: 2.92 },
  { member: "Kuwait",       quota: 2.41, prod: 2.39 },
  { member: "Kazakhstan",   quota: 1.47, prod: 1.65 },
  { member: "Nigeria",      quota: 1.5,  prod: 1.38 },
  { member: "Algeria",      quota: 0.91, prod: 0.9 },
];

export function opec() {
  const quotas = OPEC_QUOTAS.map((m) => ({ ...m }));
  const total = quotas.reduce(
    (a, m) => ({ quota: +(a.quota + m.quota).toFixed(2), prod: +(a.prod + m.prod).toFixed(2) }),
    { quota: 0, prod: 0 }
  );
  const compliance = +((total.quota / total.prod) * 100).toFixed(1);
  return { quotas, total, compliance, productionSource: "curated (targets & recent estimates)" };
}

// ----------------------------------------------------------------------------
// MODELED freight: tanker TCE rates, Baltic Dry, route spreads, port congestion.
// (AIS + Baltic Exchange indices are paywalled.)
// ----------------------------------------------------------------------------
export function freight() {
  const r = rng(daySeed() + 500);
  const j = (base, amp) => +(base + (r() - 0.5) * amp).toFixed(0);
  const heroes = [
    { sym: "VLCC TD3C", name: "AG–China",     val: j(38000, 6000), unit: "$/day" },
    { sym: "SUEZMAX",   name: "TD20 WAF–UK",  val: j(51000, 7000), unit: "$/day" },
    { sym: "AFRAMAX",   name: "TD25 USGC–UK", val: j(48000, 6000), unit: "$/day" },
    { sym: "BDI",       name: "Baltic Dry",   val: j(1840, 200),   unit: "" },
  ].map((h) => {
    const chg = +((r() - 0.5) * h.val * 0.06).toFixed(0);
    return { ...h, chg, pct: +((chg / h.val) * 100).toFixed(2) };
  });

  const rates = Array.from({ length: 60 }, (_, i) => ({
    t: i,
    vlcc: Math.round(28000 + Math.sin(i / 8) * 8000 + i * 100),
    suezmax: Math.round(38000 + Math.cos(i / 6) * 12000 + i * 80),
    aframax: Math.round(42000 + Math.sin(i / 5) * 10000 + i * 60),
  }));

  const routes = [
    { r: "USGC–NWE", v: +(4.82 + (r() - 0.5)).toFixed(2) },
    { r: "AG–Asia",  v: +(2.14 + (r() - 0.5)).toFixed(2) },
    { r: "WAF–Asia", v: +(3.41 + (r() - 0.5)).toFixed(2) },
    { r: "NSEA–USGC",v: +(2.86 + (r() - 0.5)).toFixed(2) },
  ].map((x) => ({ ...x, c: +((r() - 0.5) * 0.5).toFixed(2) }));

  const ports = [
    { port: "Singapore", base: 78 }, { port: "Rotterdam", base: 54 },
    { port: "Fujairah", base: 67 }, { port: "Houston", base: 41 },
    { port: "Suez", base: 92 }, { port: "Shanghai", base: 61 },
  ].map((p) => {
    const congestion = Math.max(20, Math.min(99, Math.round(p.base + (r() - 0.5) * 10)));
    return { port: p.port, congestion, delay: `${(congestion / 18).toFixed(1)}d` };
  });

  return { modeled: true, heroes, rates, routes, ports };
}

// ----------------------------------------------------------------------------
// MODELED Baker Hughes weekly rig count (oil + gas), 52 weeks + hero tile.
// ----------------------------------------------------------------------------
export function rigs() {
  const r = rng(daySeed() + 77);
  let oil = 515, gas = 101;
  const hist = Array.from({ length: 52 }, (_, i) => {
    oil += (r() - 0.5) * 7 - 0.32;
    gas += (r() - 0.5) * 3 - 0.04;
    return { w: i, oil: Math.round(oil), gas: Math.round(gas) };
  });
  const last = hist.at(-1), prev = hist.at(-2);
  return {
    modeled: true,
    hist,
    hero: { sym: "US OIL RIGS", name: "Baker Hughes", val: last.oil, chg: last.oil - prev.oil, unit: "rigs" },
  };
}

// ----------------------------------------------------------------------------
// COMPUTED sentiment: blend live price momentum (instrument %chg) with the tone
// of recent news. News tone now comes from FinBERT (a financial-language model)
// scoring each headline positive/negative/neutral — see sources/finbert.js. If
// FinBERT is unavailable the headlines carry no `sent`, and we transparently
// fall back to the old bull/bear keyword heuristic.
// ----------------------------------------------------------------------------
const lblFor = (v) => (v >= 70 ? "V. Bullish" : v >= 55 ? "Bullish" : v >= 45 ? "Neutral" : v >= 30 ? "Bearish" : "V. Bearish");

// Keyword fallback distribution (used only when FinBERT produced no scores).
function keywordDistribution(newsItems) {
  const bullishKw = /surge|rally|tighten|draw|cut|widen|firm|gain|rise/i;
  const bearishKw = /plunge|build|glut|fall|drop|weak|ease|oversupply/i;
  let bull = 0, bear = 0;
  for (const n of newsItems) {
    if (bullishKw.test(n.txt)) bull++;
    else if (bearishKw.test(n.txt)) bear++;
  }
  const total = Math.max(1, newsItems.length);
  const bullish = Math.round((bull / total) * 100);
  const bearish = Math.round((bear / total) * 100);
  return { bullish, neutral: Math.max(0, 100 - bullish - bearish), bearish };
}

export function sentiment(instruments = [], newsItems = []) {
  const byId = (id) => instruments.find((i) => i.id === id) || {};
  // momentum → 50-centered score (each 1% move ≈ 6 points)
  const score = (pct) => Math.max(2, Math.min(98, Math.round(50 + (pct || 0) * 6)));

  const crude = (byId("brent").pct + byId("wti").pct) / 2;
  const groups = [
    { name: "Crude", value: score(crude) },
    { name: "Distillates", value: score(byId("ho").pct) },
    { name: "Gasoline", value: score(byId("rbob").pct) },
    { name: "Gas Oil", value: score(byId("gasoil").pct) },
  ].map((g) => ({ ...g, lbl: lblFor(g.value) }));

  // News tone from FinBERT, when present on the items.
  const scored = newsItems.filter((n) => n.sent);
  const model = scored.length ? "finbert" : "keyword";

  let distribution, newsIndex;
  if (scored.length) {
    // Distribution = share of headlines per FinBERT class.
    const n = scored.length;
    const pos = scored.filter((s) => s.sent.label === "positive").length;
    const neg = scored.filter((s) => s.sent.label === "negative").length;
    const bullish = Math.round((pos / n) * 100);
    const bearish = Math.round((neg / n) * 100);
    distribution = { bullish, neutral: Math.max(0, 100 - bullish - bearish), bearish };

    // News index = mean signed score (P(pos) − P(neg)) mapped to 0–100.
    const meanSigned = scored.reduce((s, x) => s + x.sent.signed, 0) / n;
    const value = Math.max(2, Math.min(98, Math.round(50 + meanSigned * 50)));
    newsIndex = { value, lbl: lblFor(value), n, model: "FinBERT" };
  } else {
    distribution = keywordDistribution(newsItems);
    // Keyword index = bull/bear tilt centered at 50.
    const value = Math.max(2, Math.min(98, Math.round(50 + (distribution.bullish - distribution.bearish) / 2)));
    newsIndex = { value, lbl: lblFor(value), n: newsItems.length, model: "keyword" };
  }

  return { groups, distribution, newsIndex, model };
}
