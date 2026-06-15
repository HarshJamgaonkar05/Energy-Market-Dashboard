// ============================================================================
// Regime serving layer — loads the Phase 2 analytics artifacts that the Python
// batch step produces (analytics/run.py → server/data/{regimes,models,signals}.json)
// and serves them to the frontend Regime & Signals page.
//
// Like history.js this keeps each file in memory, but hot-reloads when its mtime
// changes (so a fresh `python analytics/run.py` is picked up without restarting
// the server). The heavy statistics are all precomputed offline; this module
// just reads and slices them.
// ============================================================================
import { readFileSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA = join(__dirname, "..", "data");

// Generic mtime-aware JSON loader, one cache slot per filename.
const _cache = new Map(); // name -> { mtime, data }
function loadJson(name) {
  const file = join(DATA, name);
  let mtime = 0;
  try {
    mtime = statSync(file).mtimeMs;
  } catch {
    return null; // not built yet
  }
  const hit = _cache.get(name);
  if (hit && hit.mtime === mtime) return hit.data;
  try {
    const data = JSON.parse(readFileSync(file, "utf8"));
    _cache.set(name, { mtime, data });
    return data;
  } catch (e) {
    console.warn(`[regime] data/${name} unreadable (${e.message}). Run: python analytics/run.py`);
    return null;
  }
}

// ---- Regimes ---------------------------------------------------------------
/** Current regime + dimension definitions + regime-conditioned correlation. */
export function currentRegime() {
  const d = loadJson("regimes.json");
  if (!d) return null;
  return {
    current: d.current, dimensions: d.dimensions, correlation: d.correlation,
    asOf: d.asOf, generatedAt: d.generatedAt,
  };
}

/** Per-regime catalog: size, share, persistence, sufficiency + spread behaviour. */
export function regimeCatalog() {
  const d = loadJson("regimes.json");
  if (!d) return null;
  return { catalog: d.catalog, spreads: d.spreads, asOf: d.asOf };
}

/** Daily regime history strip + the transition matrix. */
export function regimeHistory() {
  const d = loadJson("regimes.json");
  if (!d) return null;
  return { history: d.history, transitions: d.transitions, asOf: d.asOf };
}

// ---- Regressions -----------------------------------------------------------
/** Lightweight list of available fair-value models (for the spread selector). */
export function regressionList() {
  const d = loadJson("models.json");
  if (!d) return null;
  const list = Object.entries(d.models).map(([spread, m]) => ({
    spread, label: m.label, r2_in: m.global.r2_in, r2_oos: m.global.r2_oos,
    topDrivers: m.global.topDrivers,
  }));
  return { asOf: d.asOf, features: d.features, list };
}

/** Full regression model for one spread (coefs, fair-value series, rolling, by-regime). */
export function regression(spread) {
  const d = loadJson("models.json");
  if (!d) return null;
  const m = d.models[spread];
  if (!m) return { error: "unknown spread", available: Object.keys(d.models) };
  return { spread, asOf: d.asOf, features: d.features, ...m };
}

// ---- Signals ---------------------------------------------------------------
/** Ranked analytical opportunities under the current regime. */
export function signals() {
  const d = loadJson("signals.json");
  if (!d) return null;
  return d;
}

// ---- Intraday strategy backtest (Phase 3) ----------------------------------
/** Full intraday backtest of the Phase-2 strategy (BackTesting/backtest.py):
 *  summary, per-structure bifurcation, equity curve and the complete trade log. */
export function intradayBacktest() {
  const d = loadJson("intraday_backtest.json");
  if (!d) return null;
  return d;
}

// ---- Narrative -------------------------------------------------------------
/** Synthesize a one-line market briefing from the regime, the top signal and the
 *  biggest live mover — the Dashboard's headline. Pure: live movers are passed in
 *  (the route fetches them); regime/signals come from the precomputed artifacts. */
export function buildNarrative(movers = []) {
  const reg = currentRegime();
  if (!reg?.current) return null;
  const cur = reg.current;
  const st = cur.states || {};
  const sig = signals();
  const top = sig?.opportunities?.[0] || null;
  const mover = [...movers].sort((a, b) => Math.abs(b.pct) - Math.abs(a.pct))[0] || null;

  const drv = [];
  if (st.volatility?.state) drv.push(`${st.volatility.state.toLowerCase()} volatility`);
  if (st.structure?.state) drv.push(st.structure.state.toLowerCase());
  if (st.inventory?.state) drv.push(`${st.inventory.state.toLowerCase()} inventories`);

  let headline = `${cur.label} regime — ${drv.slice(0, 3).join(", ")}.`;
  if (top) {
    headline += ` Top dislocation: ${top.label} ${Math.abs(top.combinedZ).toFixed(1)}σ ${top.direction} vs its regime norm`;
    headline += top.backtest ? ` (${Math.round(top.backtest.hitRate * 100)}% historical reversion).` : ".";
  }
  if (mover && mover.pct != null) {
    headline += ` Biggest mover: ${mover.sym} ${mover.pct >= 0 ? "+" : ""}${mover.pct}%.`;
  }

  return {
    asOf: reg.asOf,
    regimeId: cur.regimeId,
    regimeLabel: cur.label,
    drivers: Object.entries(st).map(([dim, s]) => ({ dim, state: s.state, driver: s.driver })),
    topSignal: top && {
      label: top.label, spread: top.spread, direction: top.direction, z: top.combinedZ,
      confidence: top.confidenceLabel, hitRate: top.backtest?.hitRate ?? null,
    },
    mover: mover && { sym: mover.sym, pct: mover.pct },
    headline,
  };
}
