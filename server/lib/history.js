// ============================================================================
// Historical data loader — serves the distilled CSV history (built by
// server/scripts/build-history.js into server/data/history.json).
//
// The raw /Data CSVs are multi-GB 1-minute term-structure files; this module
// loads only the compact distillate (daily front-month closes + the latest real
// forward curve per instrument) once into memory. It backs every *historical*
// panel — price action, correlation, forward-curve structure, seasonality —
// while live front-month prices keep coming from Yahoo.
//
// Dataset universe: WTI, Brent, Heating Oil, Gas Oil (no RBOB in the sheets).
// ============================================================================
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FILE = join(__dirname, "..", "data", "history.json");

// The four instruments present in the proprietary dataset.
export const HISTORY_IDS = ["wti", "brent", "ho", "gasoil"];

let _data = null;
function load() {
  if (_data) return _data;
  try {
    _data = JSON.parse(readFileSync(FILE, "utf8"));
    const n = Object.keys(_data.instruments || {}).length;
    console.log(`  History: loaded ${n} instruments from data/history.json (built ${_data.generatedAt?.slice(0, 10) ?? "?"})`);
  } catch (e) {
    console.warn(`[history] data/history.json missing or unreadable (${e.message}). Run: node server/scripts/build-history.js`);
    _data = { instruments: {} };
  }
  return _data;
}

export function hasHistory(id) {
  return !!load().instruments[id]?.daily?.length;
}

/** Chronological daily front-month closes: [{ iso:"YYYY-MM-DD", date:Date, close }]. */
export function dailyCloses(id) {
  const inst = load().instruments[id];
  if (!inst?.daily) return [];
  return inst.daily.map(([iso, close]) => ({ iso, date: new Date(`${iso}T00:00:00Z`), close }));
}

/** Latest real forward curve for an instrument: [{ m:"M1", contract, v }] or null. */
export function latestCurve(id) {
  return load().instruments[id]?.curve ?? null;
}

/** The as-of date (YYYY-MM-DD) of an instrument's dataset snapshot, or null. */
export function asOf(id) {
  return load().instruments[id]?.asOf ?? null;
}

/** Newest as-of date across the dataset, plus when it was generated. */
export function historyMeta() {
  const inst = load().instruments;
  const asOf = Object.values(inst).map((i) => i.asOf).filter(Boolean).sort().at(-1) ?? null;
  return { asOf, generatedAt: load().generatedAt ?? null, ids: Object.keys(inst) };
}
