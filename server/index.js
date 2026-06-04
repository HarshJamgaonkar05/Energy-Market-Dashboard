// ============================================================================
// Voltaire Terminal — backend API.
// Aggregates free/open data sources (Yahoo Finance, EIA, Open-Meteo, Financial Juice)
// and serves them to the React frontend at /api/*. Run: `npm run server`
// (or `npm run dev:all` to start Vite + this together).
// ============================================================================
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import dotenv from "dotenv";
import express from "express";
import cors from "cors";

const __dirname = dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: join(__dirname, ".env") });

import { instruments, ticker, movers, seriesAndCorrelation, cracks, forwardCurves, interSpreads, macro } from "./compute/markets.js";
import { calendar, opec, freight, rigs, sentiment } from "./compute/derive.js";
import * as eia from "./sources/eia.js";
import { weather, tempForecast } from "./sources/openmeteo.js";
import { news } from "./sources/financialjuice.js";
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
    sources: {
      yahoo: "live",
      openmeteo: "live",
      financialjuice: "live",
      eia: eia.eiaEnabled() ? "live" : "missing key — fundamentals use fallback",
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
  // Enrich the schedule with the latest *real* EIA weekly crude build as the
  // "prior" for the EIA Crude Stocks release; everything else stays "—".
  const flows = await eia.stockFlows().catch(() => null);
  const lastBuild = flows?.at(-1)?.eia;
  const enrich = Number.isFinite(lastBuild)
    ? { "EIA Crude Stocks": { prev: `${lastBuild >= 0 ? "+" : ""}${lastBuild.toFixed(1)}M` } }
    : {};
  return calendar(enrich);
}, "/api/calendar"));
app.get("/api/freight", route(() => freight(), "/api/freight"));
app.get("/api/rigs", route(() => rigs(), "/api/rigs"));
app.get("/api/sentiment", route(async () => {
  const [instr, n] = await Promise.all([instruments(), news().catch(() => [])]);
  return sentiment(instr, n);
}, "/api/sentiment"));

// JSON 404 for any other /api path (so the SPA proxy never gets HTML back).
app.use("/api", (_req, res) => res.status(404).json({ error: "unknown endpoint" }));

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`\n  Voltaire backend on http://localhost:${PORT}`);
  console.log(`  EIA key: ${eia.eiaEnabled() ? "loaded ✓" : "missing (inventory panels will use frontend fallback)"}`);
  console.log(`  Sources: Yahoo Finance · EIA v2 · Open-Meteo · Financial Juice\n`);
});
