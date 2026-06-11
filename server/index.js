// ============================================================================
// Voltaire Terminal — backend API.
// Aggregates free/open data sources (Yahoo Finance, EIA, Open-Meteo, Financial Juice)
// and serves them to the React frontend at /api/*. Run: `npm run server`
// (or `npm run dev:all` to start Vite + this together).
// ============================================================================
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { existsSync } from "node:fs";
import dotenv from "dotenv";
import express from "express";
import cors from "cors";

const __dirname = dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: join(__dirname, ".env") });

import { instruments, ticker, movers, seriesAndCorrelation, cracks, crackHistory, forwardCurves, interSpreads, macro } from "./compute/markets.js";
import { calendar, opec, freight, rigs, sentiment } from "./compute/derive.js";
import * as eia from "./sources/eia.js";
import { weather, tempForecast } from "./sources/openmeteo.js";
import { storms, enso } from "./sources/noaa.js";
import { cot } from "./sources/cftc.js";
import { seasonality } from "./compute/seasonality.js";
import { news } from "./sources/financialjuice.js";
import { finbertReady, finbertDisabled } from "./sources/finbert.js";
import { sourceManifest, SOURCES, ENDPOINT_SOURCES } from "./lib/sources.js";

const app = express();
app.use(cors());

// Lightweight request log: method, path, status, and latency for every call.
app.use((req, res, next) => {
  const t0 = Date.now();
  res.on("finish", () => {
    if (req.path.startsWith("/api")) {
      console.log(`[api] ${req.method} ${req.path} ${res.statusCode} ${Date.now() - t0}ms`);
    }
  });
  next();
});

// Wrap an async producer: send JSON, or 503 (so the frontend uses its fallback)
// with a short error note. Never crash the process on an upstream hiccup. Each
// successful response is tagged with its provenance so API consumers (and the
// UI) always know where a number came from.
const route = (producer, path) => async (req, res) => {
  try {
    const data = await producer(req);
    if (data == null) return res.status(503).json({ error: "source unavailable", fallback: true });
    const prov = path ? ENDPOINT_SOURCES[path] : null;
    if (prov) {
      res.set("X-Data-Source", prov.source);
      res.set("X-Data-Kind", SOURCES[prov.source]?.kind ?? "unknown");
    }
    res.set("Cache-Control", "no-store").json(data);
  } catch (err) {
    console.warn(`[api] ${req.path} -> ${err.message}`);
    res.status(503).json({ error: err.message, fallback: true });
  }
};

// ---- Meta ----
app.get("/api/health", (_req, res) =>
  res.json({
    ok: true,
    time: new Date().toISOString(),
    eia: eia.eiaEnabled(),
    finbert: finbertDisabled() ? "unavailable" : finbertReady() ? "live" : "loading",
    sources: {
      yahoo: "live",
      openmeteo: "live",
      financialjuice: "live",
      eia: eia.eiaEnabled() ? "live" : "missing key — fundamentals use fallback",
      finbert: finbertDisabled()
        ? "model unavailable — news sentiment uses keyword fallback"
        : finbertReady() ? "live" : "loading model…",
    },
  })
);

// Self-describing provenance manifest: which feed backs which endpoint.
app.get("/api/sources", (_req, res) => res.json(sourceManifest()));

// ---- Markets (Yahoo-backed, live) ----
app.get("/api/instruments", route(() => instruments(), "/api/instruments"));
app.get("/api/ticker", route(async () => ticker(await instruments()), "/api/ticker"));
app.get("/api/movers", route(async () => movers(await instruments()), "/api/movers"));
app.get("/api/series", route(async () => (await seriesAndCorrelation()).series, "/api/series"));
app.get("/api/correlation", route(async () => (await seriesAndCorrelation()).correlation, "/api/correlation"));
app.get("/api/cracks", route(async () => cracks(await instruments()), "/api/cracks"));
app.get("/api/crackhistory", route(() => crackHistory(), "/api/crackhistory"));
app.get("/api/curves", route(async () => {
  const instr = await instruments();
  return { ...(await forwardCurves(instr)), inter: interSpreads(instr) };
}, "/api/curves"));
app.get("/api/macro", route(() => macro(), "/api/macro"));

// ---- Fundamentals (EIA-backed; 503 -> frontend mock fallback if no key) ----
app.get("/api/inventories", route(() => eia.inventories(), "/api/inventories"));
app.get("/api/stockflows", route(() => eia.stockFlows(), "/api/stockflows"));
app.get("/api/spot", route(() => eia.spot(), "/api/spot"));
app.get("/api/opec", route(() => opec(), "/api/opec"));

// ---- Context (weather live, news live, calendar real, freight/rigs modeled) ----
app.get("/api/weather", route(async () => ({ ...(await weather()), forecast: await tempForecast() }), "/api/weather"));
app.get("/api/news", route(() => news(), "/api/news"));
app.get("/api/calendar", route(async () => {
  // Fill the "prior" column with the latest *real* EIA weekly builds/draws for
  // crude, gasoline and distillate. The consensus FORECAST stays "—" (paywalled).
  const wc = await eia.weeklyChanges().catch(() => null);
  const fmtB = (v) => (v == null ? null : `${v >= 0 ? "+" : ""}${v.toFixed(1)}M`);
  const enrich = {};
  if (wc?.crude != null) enrich["EIA Crude Stocks"] = { prev: fmtB(wc.crude) };
  if (wc?.gasoline != null) enrich["EIA Gasoline Stocks"] = { prev: fmtB(wc.gasoline) };
  if (wc?.distillate != null) enrich["EIA Distillate"] = { prev: fmtB(wc.distillate) };
  return calendar(enrich);
}, "/api/calendar"));
app.get("/api/freight", route(() => freight(), "/api/freight"));
// Real EIA monthly rig count; falls back to the modeled 52-week series if the
// EIA key is missing or the fetch fails.
app.get("/api/rigs", route(async () => (await eia.rigs().catch(() => null)) ?? rigs(), "/api/rigs"));
app.get("/api/storms", route(() => storms(), "/api/storms"));
app.get("/api/enso", route(() => enso(), "/api/enso"));
app.get("/api/cot", route(() => cot(), "/api/cot"));
app.get("/api/seasonality", route(() => seasonality(), "/api/seasonality"));
app.get("/api/sentiment", route(async () => {
  const [instr, n] = await Promise.all([instruments(), news().catch(() => [])]);
  return sentiment(instr, n);
}, "/api/sentiment"));

// JSON 404 for any other /api path (so the SPA proxy never gets HTML back).
app.use("/api", (_req, res) => res.status(404).json({ error: "unknown endpoint" }));

// In production we serve the built frontend (Vite `dist/`) from this same server,
// so the whole app is one origin (no CORS, one URL). In dev there is no `dist/`
// and Vite serves the UI on :5173 + proxies /api here — so this block is skipped.
const distDir = join(__dirname, "..", "dist");
if (existsSync(distDir)) {
  app.use(express.static(distDir));
  // SPA fallback: any non-/api route returns index.html.
  app.get("*", (_req, res) => res.sendFile(join(distDir, "index.html")));
  console.log("  Serving built frontend from /dist");
}

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`\n  Voltaire backend on http://localhost:${PORT}`);
  console.log(`  EIA key: ${eia.eiaEnabled() ? "loaded ✓" : "missing (inventory panels will use frontend fallback)"}`);
  console.log(`  Sources: Yahoo Finance · EIA v2 · Open-Meteo · Financial Juice\n`);
});
