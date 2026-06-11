// ============================================================================
// Provenance registry — the single source of truth for WHERE every number on
// the dashboard comes from. Each /api endpoint maps to one of these source
// descriptors so the UI can label data (live / official / derived / modeled)
// and the API can describe itself at /api/sources.
//
//   kind:  live     — fetched fresh from a public feed
//          official — government / exchange data (also live, but authoritative)
//          derived  — computed on the server FROM a live feed
//          modeled  — indicative; no free live feed exists (paywalled upstream)
//          curated  — hand-maintained reference values (policy targets, etc.)
//          schedule — a known real-world release cadence, not a data feed
// ============================================================================

export const SOURCES = {
  yahoo: {
    id: "yahoo",
    label: "Yahoo Finance",
    detail: "Live futures quotes & daily closing history (unofficial public API).",
    kind: "live",
    url: "https://finance.yahoo.com",
  },
  eia: {
    id: "eia",
    label: "EIA",
    detail: "U.S. Energy Information Administration — Weekly Petroleum Status Report (official).",
    kind: "official",
    url: "https://www.eia.gov/opendata/",
  },
  openmeteo: {
    id: "openmeteo",
    label: "Open-Meteo",
    detail: "Open weather-forecast model, refreshed hourly (no key required).",
    kind: "live",
    url: "https://open-meteo.com",
  },
  noaa: {
    id: "noaa",
    label: "NOAA",
    detail: "U.S. NOAA — National Hurricane Center active storms & Climate Prediction Center El Niño index (official, free).",
    kind: "official",
    url: "https://www.nhc.noaa.gov",
  },
  cftc: {
    id: "cftc",
    label: "CFTC",
    detail: "U.S. Commodity Futures Trading Commission — weekly Commitments of Traders (Managed Money positioning), official & free.",
    kind: "official",
    url: "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm",
  },
  financialjuice: {
    id: "financialjuice",
    label: "Financial Juice",
    detail: "Real-time financial newswire (RSS).",
    kind: "live",
    url: "https://www.financialjuice.com",
  },
  finbert: {
    id: "finbert",
    label: "FinBERT",
    detail: "ProsusAI/finbert — a financial-language model scoring each headline positive/negative/neutral, run locally via Transformers.js (ONNX).",
    kind: "derived",
    url: "https://huggingface.co/ProsusAI/finbert",
  },
  dataset: {
    id: "dataset",
    label: "Historical dataset",
    detail: "Proprietary 1-minute term-structure history (2021→present), distilled to daily front-month closes & real forward curves.",
    kind: "dataset",
    url: "",
  },
  derived: {
    id: "derived",
    label: "Derived",
    detail: "Computed on the server from live feeds (spreads, cracks, correlations, sentiment).",
    kind: "derived",
  },
  modeled: {
    id: "modeled",
    label: "No free source",
    detail: "No free or open data source for this value — shown as “—” rather than an assumed figure.",
    kind: "modeled",
  },
  curated: {
    id: "curated",
    label: "Curated",
    detail: "Hand-maintained reference values (published policy targets & recent estimates).",
    kind: "curated",
  },
  schedule: {
    id: "schedule",
    label: "Release schedule",
    detail: "Built from the official U.S. energy-report release cadence (EIA, API, Baker Hughes).",
    kind: "schedule",
  },
};

// Which source backs each endpoint. `mixed` lists the secondary sources an
// endpoint blends in (e.g. the calendar's prior values come from EIA).
export const ENDPOINT_SOURCES = {
  "/api/instruments": { source: "yahoo" },
  "/api/ticker": { source: "yahoo", mixed: ["derived"] },
  "/api/movers": { source: "yahoo", mixed: ["derived"] },
  "/api/series": { source: "dataset" },
  "/api/correlation": { source: "dataset", mixed: ["derived"] },
  "/api/cracks": { source: "derived", mixed: ["yahoo"] },
  "/api/crackhistory": { source: "dataset", mixed: ["yahoo", "derived"] },
  "/api/curves": { source: "dataset", mixed: ["yahoo"] },
  "/api/macro": { source: "yahoo" },
  "/api/inventories": { source: "eia" },
  "/api/stockflows": { source: "eia" },
  "/api/spot": { source: "eia" },
  "/api/opec": { source: "curated" },
  "/api/weather": { source: "openmeteo" },
  "/api/news": { source: "financialjuice", mixed: ["finbert"] },
  "/api/calendar": { source: "schedule", mixed: ["eia"] },
  "/api/freight": { source: "modeled" },
  "/api/rigs": { source: "eia", mixed: ["modeled"] },
  "/api/storms": { source: "noaa" },
  "/api/enso": { source: "noaa" },
  "/api/cot": { source: "cftc" },
  "/api/seasonality": { source: "dataset", mixed: ["derived"] },
  "/api/sentiment": { source: "derived", mixed: ["yahoo", "financialjuice", "finbert"] },
};

// Flat self-describing manifest for GET /api/sources.
export function sourceManifest() {
  return {
    sources: SOURCES,
    endpoints: Object.fromEntries(
      Object.entries(ENDPOINT_SOURCES).map(([path, { source, mixed }]) => [
        path,
        { source, mixed: mixed || [], label: SOURCES[source]?.label ?? source },
      ])
    ),
  };
}
