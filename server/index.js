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
import { currentRegime, regimeCatalog, regimeHistory, regressionList, regression, signals, buildNarrative, signalEngine, historicalBacktest, historicalIntraday, inventorySignal, releaseLab } from "./compute/regime.js";
import { spawn } from "node:child_process";
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

// ---- Regime & signals (Phase 2 — precomputed offline by analytics/) ----
app.get("/api/regime/current", route(() => currentRegime(), "/api/regime/current"));
app.get("/api/regime/catalog", route(() => regimeCatalog(), "/api/regime/catalog"));
app.get("/api/regime/history", route(() => regimeHistory(), "/api/regime/history"));
app.get("/api/regression", route(() => regressionList(), "/api/regression"));
app.get("/api/regression/:spread", route((req) => regression(req.params.spread), "/api/regression"));
app.get("/api/signals", route(() => signals(), "/api/signals"));
// Live Signal Engine — the Phase-2 framework run on the live intraday feed:
// trade log, persistent signal/opportunity log, open positions and live stats.
app.get("/api/signal-engine", route(() => signalEngine(), "/api/signal-engine"));
app.get("/api/historical-backtest", route(() => historicalBacktest(), "/api/historical-backtest"));
app.get("/api/historical-intraday", route(() => historicalIntraday(), "/api/historical-intraday"));
// Market-narrative briefing — fuses the regime, the top signal and the biggest
// live mover into one headline for the Dashboard.
app.get("/api/narrative", route(async () => buildNarrative(movers(await instruments())), "/api/narrative"));

// ---- Fundamentals (EIA-backed; 503 -> frontend mock fallback if no key) ----
app.get("/api/inventories", route(() => eia.inventories(), "/api/inventories"));
// Live crude-inventory cross-check engine (analytics/inventory_engine.py): the
// pre-release verdict for the next EIA release + the last print's surprise/cross-check.
app.get("/api/inventory-signal", route(() => inventorySignal(), "/api/inventory-signal"));
// EIA Release Lab — the live FORWARD forecast for the next release + the graded last
// print. On every visit we check whether the snapshot is stale (old, or a new EIA week
// has landed) and, if so, kick a throttled background regenerate so the page keeps
// updating itself without the button — while still returning the current data instantly.
app.get("/api/release-lab", route(() => { maybeRefreshReleaseLab(); return releaseLab(); }, "/api/release-lab"));
// The dashboard's "Run the latest EIA release" button: spawn the Python pipeline
// (analytics/release_lab.py --run), then return the fresh snapshot. Single-flight:
// concurrent presses share the one in-progress run instead of stacking processes.
const REPO_ROOT = join(__dirname, "..");
const PY = process.platform === "win32"
  ? join(REPO_ROOT, ".venv", "Scripts", "python.exe")
  : join(REPO_ROOT, ".venv", "bin", "python");  // matches the venv the Dockerfile builds
// PATH fallback when the bundled venv isn't present (python3 on Linux/Spaces, python on Windows).
const PY_FALLBACK = process.env.PYTHON_BIN || (process.platform === "win32" ? "python" : "python3");
let releaseRun = null; // the in-flight Promise, or null when idle

function runReleaseLab() {
  if (releaseRun) return releaseRun;            // single-flight: reuse the running one
  const script = join(REPO_ROOT, "analytics", "release_lab.py");
  const python = existsSync(PY) ? PY : PY_FALLBACK;
  releaseRun = new Promise((resolve) => {
    const t0 = Date.now();
    console.log(`[release-lab] running ${python} ${script} --run`);
    let out = "", err = "";
    let child;
    try {
      child = spawn(python, [script, "--run"], { cwd: REPO_ROOT });
    } catch (e) {
      return resolve({ ok: false, error: `could not start python: ${e.message}` });
    }
    const timer = setTimeout(() => { try { child.kill(); } catch {} },
      Number(process.env.RELEASE_LAB_TIMEOUT_MS) || 180000); // 3 min hard cap
    child.stdout.on("data", (d) => (out += d));
    child.stderr.on("data", (d) => (err += d));
    child.on("error", (e) => { clearTimeout(timer); resolve({ ok: false, error: e.message }); });
    child.on("close", (code) => {
      clearTimeout(timer);
      const ms = Date.now() - t0;
      console.log(`[release-lab] exited ${code} in ${ms}ms`);
      if (code !== 0) {
        return resolve({ ok: false, code, error: (err || out || "pipeline failed").slice(-1500) });
      }
      const data = releaseLab(); // re-read the freshly written JSON (mtime-aware)
      resolve({ ok: true, ms, data });
    });
  }).finally(() => { releaseRun = null; });
  return releaseRun;
}

app.post("/api/release-lab/run", async (_req, res) => {
  try {
    const r = await runReleaseLab();
    if (!r.ok) return res.status(503).json({ error: r.error || "run failed", fallback: true });
    res.set("Cache-Control", "no-store").json({ ok: true, ranInMs: r.ms, ...r.data });
  } catch (e) {
    res.status(503).json({ error: e.message, fallback: true });
  }
});

// ---- On-visit auto-refresh: keep the "live engine" fresh with no button press. -----
// Regenerate in the background when the snapshot is stale — older than a window that
// tightens as the next release approaches, or when the upcoming release date has passed
// (a new print likely landed). Throttled so concurrent visits never stack Python runs.
const RL_STALE_HOURS = Number(process.env.RELEASE_LAB_STALE_HOURS) || 6;
const RL_AUTORUN_MIN_MS = Number(process.env.RELEASE_LAB_AUTORUN_MS) || 60 * 60 * 1000;
let lastReleaseAutoRun = 0;

function releaseLabStale(snap) {
  if (!snap || !snap.generatedAt || (!snap.upcoming && !snap.last)) return true;
  const gen = Date.parse(snap.generatedAt);
  if (!Number.isFinite(gen)) return true;
  const ageHours = (Date.now() - gen) / 3.6e6;
  // A new EIA week has probably published: the upcoming release date is now in the past
  // yet the snapshot was generated before it — regenerate to roll forward + grade it.
  const relStr = snap.upcoming?.target?.release_date;
  if (relStr) {
    const rel = Date.parse(`${relStr}T14:30:00Z`); // ~10:30 ET WPSR
    if (Number.isFinite(rel) && Date.now() > rel && gen < rel) return true;
  }
  const days = snap.upcoming?.target?.days_until;
  const window = typeof days === "number" && days <= 2 ? 3 : RL_STALE_HOURS; // refresh eagerly near the print
  return ageHours >= window;
}

function maybeRefreshReleaseLab() {
  const now = Date.now();
  if (releaseRun) return;                                  // a run is already in flight
  if (now - lastReleaseAutoRun < RL_AUTORUN_MIN_MS) return; // throttle
  let snap = null;
  try { snap = releaseLab(); } catch { /* missing/corrupt → treat as stale */ }
  if (!releaseLabStale(snap)) return;
  lastReleaseAutoRun = now;
  console.log("[release-lab] snapshot stale — background auto-refresh");
  runReleaseLab().catch(() => {});                         // fire-and-forget; next poll serves it
}
app.get("/api/balance", route(() => eia.supplyDemand(), "/api/balance"));
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
