// ============================================================================
// Voltaire Terminal — backend API.
// Aggregates free/open data sources (Yahoo Finance, EIA, Open-Meteo, GDELT)
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

import { instruments, ticker, movers, seriesAndCorrelation, cracks, curves, interSpreads, macro } from "./compute/markets.js";
import { calendar, opec, freight, rigs, sentiment } from "./compute/derive.js";
import * as eia from "./sources/eia.js";
import { weather, tempForecast } from "./sources/openmeteo.js";
import { news } from "./sources/gdelt.js";

const app = express();
app.use(cors());

// Wrap an async producer: send JSON, or 503 (so the frontend uses its fallback)
// with a short error note. Never crash the process on an upstream hiccup.
const route = (producer) => async (req, res) => {
  try {
    const data = await producer(req);
    if (data == null) return res.status(503).json({ error: "source unavailable", fallback: true });
    res.set("Cache-Control", "no-store").json(data);
  } catch (err) {
    console.warn(`[api] ${req.path} -> ${err.message}`);
    res.status(503).json({ error: err.message, fallback: true });
  }
};

app.get("/api/health", (_req, res) =>
  res.json({ ok: true, eia: eia.eiaEnabled(), time: new Date().toISOString() })
);

// ---- Markets (Yahoo-backed, live) ----
app.get("/api/instruments", route(() => instruments()));
app.get("/api/ticker", route(async () => ticker(await instruments())));
app.get("/api/movers", route(async () => movers(await instruments())));
app.get("/api/series", route(async () => (await seriesAndCorrelation()).series));
app.get("/api/correlation", route(async () => (await seriesAndCorrelation()).correlation));
app.get("/api/cracks", route(async () => cracks(await instruments())));
app.get("/api/curves", route(async () => {
  const instr = await instruments();
  return { ...curves(instr), inter: interSpreads(instr) };
}));
app.get("/api/macro", route(() => macro()));

// ---- Fundamentals (EIA-backed; 503 -> frontend mock fallback if no key) ----
app.get("/api/inventories", route(() => eia.inventories()));
app.get("/api/stockflows", route(() => eia.stockFlows()));
app.get("/api/opec", route(async () => opec(await eia.opecProduction())));

// ---- Context (weather live, news live, calendar real, freight/rigs modeled) ----
app.get("/api/weather", route(async () => ({ ...(await weather()), forecast: await tempForecast() })));
app.get("/api/news", route(() => news()));
app.get("/api/calendar", route(() => calendar()));
app.get("/api/freight", route(() => freight()));
app.get("/api/rigs", route(() => rigs()));
app.get("/api/sentiment", route(async () => {
  const [instr, n] = await Promise.all([instruments(), news().catch(() => [])]);
  return sentiment(instr, n);
}));

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`\n  Voltaire backend on http://localhost:${PORT}`);
  console.log(`  EIA key: ${eia.eiaEnabled() ? "loaded ✓" : "missing (inventory panels will use frontend fallback)"}`);
  console.log(`  Sources: Yahoo Finance · EIA v2 · Open-Meteo · GDELT\n`);
});
