// ============================================================================
// build-history.js — distill the multi-GB 1-minute forward-curve CSVs in /Data
// into a single compact server/data/history.json the backend can load instantly.
//
// Each source CSV is one instrument's full term structure at 1-min resolution:
//   timestamp, c1||contract, c1||weighted_mid, c2||contract, c2||weighted_mid, …
// where c1 is the front month (already rolled), c2 the next, etc.
//
// We extract only what the dashboard needs as *historical* data:
//   • daily front-month close  = last c1 weighted_mid of each UTC day  → price
//     action time-series, correlation, seasonality.
//   • daily term strip (M1..MK)= the day's last full c1..cK weighted-mids → real
//     calendar spreads (M1–M2, M2–M3, …) and butterflies (M1−2·M2+M3) AS HISTORY,
//     powering the Phase 2 regime/regression engine. (Phase 1 only kept the
//     single latest curve snapshot, so these structures had no history.)
//   • latest forward curve     = the final row's c1..cN contracts+prices → the
//     genuine term structure (anchored to the live front by the backend).
//
// Run once after the CSVs change:  node server/scripts/build-history.js
// ============================================================================
import { createReadStream } from "node:fs";
import { writeFile, mkdir } from "node:fs/promises";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_DIR = join(__dirname, "..", "..", "Data");
const OUT_DIR = join(__dirname, "..", "data");
const OUT_FILE = join(OUT_DIR, "history.json");

// Source file → instrument id + quote unit. (No RBOB in the dataset.)
const FILES = [
  { file: "CL_data.csv",  id: "wti",    unit: "$/bbl" },
  { file: "LCO_data.csv", id: "brent",  unit: "$/bbl" },
  { file: "HO_data.csv",  id: "ho",     unit: "$/gal" },
  { file: "LGO_data.csv", id: "gasoil", unit: "$/mt"  },
];

// How many contract slots (M1..MK) to keep in the daily term strip. The CSVs
// carry c1..c14; deferred months thin out in liquidity, so 12 mirrors the M1–M12
// forward curve the dashboard already shows and covers every spread/fly we model.
const TERM_K = 12;

// Pull field N (0-based) out of a CSV line without allocating the whole row.
function fieldAt(line, n) {
  let start = 0;
  for (let i = 0; i < n; i++) {
    start = line.indexOf(",", start);
    if (start === -1) return "";
    start += 1;
  }
  const end = line.indexOf(",", start);
  return end === -1 ? line.slice(start) : line.slice(start, end);
}

// Extract the c1..cK weighted-mids from a CSV line in ONE forward pass.
// Column layout: ts, c1||contract, c1||weighted_mid, c2||contract, c2||weighted_mid, …
// so the mid for contract Mk lives at field index 2k. Returns a length-K array
// (null where a slot is empty), and stops scanning once all K mids are read.
function termMids(line, K) {
  const mids = new Array(K).fill(null);
  let field = 0, start = 0;
  const n = line.length;
  for (let i = 0; i <= n; i++) {
    if (i === n || line.charCodeAt(i) === 44 /* , */) {
      if (field >= 2 && (field & 1) === 0) {       // even field ≥ 2 → a weighted_mid
        const k = field / 2 - 1;                    // field 2 → M1 (k=0)
        if (k < K && i > start) {
          const v = +line.slice(start, i);
          if (Number.isFinite(v)) mids[k] = +v.toFixed(4);
        }
      }
      field++;
      start = i + 1;
      if (field > 2 * K) break;                     // have all K mids — stop early
    }
  }
  return mids;
}

async function processFile({ file, id, unit }) {
  const path = join(DATA_DIR, file);
  const rl = createInterface({ input: createReadStream(path, { encoding: "utf8" }), crlfDelay: Infinity });

  const daily = [];        // [ [YYYY-MM-DD, close], … ] front-month daily close
  const term = [];         // [ [YYYY-MM-DD, [m1..mK]], … ] daily term strip
  let curDate = null;      // day currently being aggregated
  let dayClose = null;     // last c1 price seen this day (with a real c1)
  let dayTerm = null;      // term strip from that same last row (curve & close stay coherent)
  let lastRow = null;      // final data row (for the curve snapshot)
  let lineNo = 0;

  // Flush the day being aggregated into the daily/term series.
  const flush = () => {
    if (curDate !== null && dayClose !== null) {
      daily.push([curDate, dayClose]);
      if (dayTerm) term.push([curDate, dayTerm]);
    }
  };

  for await (const line of rl) {
    lineNo++;
    if (lineNo <= 2) continue;           // skip the #meta and header lines
    if (line.length < 11) continue;
    const date = line.slice(0, 10);      // YYYY-MM-DD (UTC)
    if (date[4] !== "-") continue;       // guard against any stray line

    const mids = termMids(line, TERM_K); // [m1..mK] for this minute
    if (date !== curDate) {
      flush();
      curDate = date;
      dayClose = null;
      dayTerm = null;
    }
    // Snapshot the day's last row that actually carries a front (c1) price, so the
    // daily close and the term strip describe the same instant.
    if (mids[0] != null) {
      dayClose = mids[0];
      dayTerm = mids;
    }
    lastRow = line;
  }
  flush();

  // Forward curve from the final row: walk (contract, price) pairs, keep the
  // first 12 with a real price, labelled M1..M12.
  const curve = [];
  if (lastRow) {
    const cols = lastRow.split(",");
    for (let i = 1; i + 1 < cols.length && curve.length < 12; i += 2) {
      const contract = cols[i].trim();
      const v = +cols[i + 1];
      if (contract && Number.isFinite(v)) {
        curve.push({ m: `M${curve.length + 1}`, contract, v: +v.toFixed(4) });
      }
    }
  }

  const asOf = daily.at(-1)?.[0] ?? null;
  console.log(`  ${id.padEnd(6)} ${daily.length} daily closes, ${term.length} term strips (M1..M${TERM_K}), ${curve.length}-pt curve, asOf ${asOf}`);
  return { id, unit, asOf, daily, term, curve };
}

async function main() {
  console.log("Distilling /Data CSVs → server/data/history.json …");
  const t0 = Date.now();
  const instruments = {};
  for (const spec of FILES) {
    instruments[spec.id] = await processFile(spec);
  }
  await mkdir(OUT_DIR, { recursive: true });
  const out = { generatedAt: new Date().toISOString(), instruments };
  await writeFile(OUT_FILE, JSON.stringify(out));
  const kb = Math.round((JSON.stringify(out).length / 1024));
  console.log(`Done in ${((Date.now() - t0) / 1000).toFixed(1)}s → ${OUT_FILE} (${kb} KB)`);
}

main().catch((e) => { console.error(e); process.exit(1); });
