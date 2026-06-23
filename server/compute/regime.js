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

// ---- Live Signal Engine (Phase 3) ------------------------------------------
/** The live signal-engine feed: trade log, signal log, open positions, live
 *  dislocation board and portfolio stats. Written by Backtesting/engine.py and
 *  hot-reloaded here on mtime change (so a fresh `--live` pass shows with no
 *  server restart). Returns null until the engine has been run at least once. */
export function signalEngine() {
  return loadJson("signal_engine.json");
}

// ---- Historical Backtest (Phase 2 fair value, daily, 5y) -------------------
/** The historical backtest feed: the Phase-2 fundamental fair value traded as a
 *  daily mean-reversion simulation over 2021-2026. Written by
 *  analytics/historical_backtest.py. Returns null until it has been run once. */
export function historicalBacktest() {
  return loadJson("historical_backtest.json");
}

/** The intraday historical backtest feed: a regime-parameterized adaptive fair value
 *  traded over 5 years of 15-min WTI/Brent bars, head-to-head vs a regime-blind control.
 *  Written by analytics/historical_intraday.py. */
export function historicalIntraday() {
  return loadJson("historical_intraday.json");
}

// ---- Shock-absorption study (Phase 3 — regime-aware vs blind through shocks) ----
/** The consolidated shock study: per-shock-window drawdown & recovery (aware vs blind),
 *  the synthetic vol×{1.5,2,3}+gap stress curve, and the de-lever evidence. Written by
 *  analytics/shock_analysis.py. Returns null until it has been run once. */
export function shockAnalysis() {
  return loadJson("shock_analysis.json");
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
