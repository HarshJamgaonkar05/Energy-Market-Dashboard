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

async function processFile({ file, id, unit }) {
  const path = join(DATA_DIR, file);
  const rl = createInterface({ input: createReadStream(path, { encoding: "utf8" }), crlfDelay: Infinity });

  const daily = [];        // [ [YYYY-MM-DD, close], … ] front-month daily close
  let curDate = null;      // day currently being aggregated
  let dayClose = null;     // last non-empty c1 price seen this day
  let lastRow = null;      // final data row (for the curve snapshot)
  let lineNo = 0;

  for await (const line of rl) {
    lineNo++;
    if (lineNo <= 2) continue;           // skip the #meta and header lines
    if (line.length < 11) continue;
    const date = line.slice(0, 10);      // YYYY-MM-DD (UTC)
    if (date[4] !== "-") continue;       // guard against any stray line

    const c1 = fieldAt(line, 2);         // c1||weighted_mid
    if (date !== curDate) {
      if (curDate !== null && dayClose !== null) daily.push([curDate, dayClose]);
      curDate = date;
      dayClose = null;
    }
    if (c1 !== "") {
      const v = +c1;
      if (Number.isFinite(v)) dayClose = +v.toFixed(4);
    }
    lastRow = line;
  }
  if (curDate !== null && dayClose !== null) daily.push([curDate, dayClose]);

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
  console.log(`  ${id.padEnd(6)} ${daily.length} daily closes, ${curve.length}-pt curve, asOf ${asOf}`);
  return { id, unit, asOf, daily, curve };
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
