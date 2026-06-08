// ============================================================================
// NOAA — free, no-key U.S. government feeds for two things the dashboard used
// to show as "—" because no source was wired:
//
//   • storms()  National Hurricane Center active tropical cyclones
//                 GET https://www.nhc.noaa.gov/CurrentStorms.json
//                 Covers the Atlantic + East/Central Pacific basins (the NHC's
//                 remit). Gulf-of-Mexico systems are the ones that actually move
//                 oil/gas, so this is the relevant free feed.
//
//   • enso()    Climate Prediction Center Oceanic Niño Index (ONI)
//                 GET https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
//                 The standard El Niño / La Niña gauge (3-month running SST
//                 anomaly in the Niño-3.4 region). ≥+0.5 El Niño, ≤−0.5 La Niña.
//
// Both are official/authoritative and refresh slowly, so we cache hard.
// ============================================================================
import { cached, fetchJSON, fetchText } from "../lib/cache.js";

// NHC classification code → readable label.
const CLASS = {
  TD: "Trop. Depression",
  TS: "Tropical Storm",
  HU: "Hurricane",
  STD: "Subtrop. Depression",
  STS: "Subtropical Storm",
  PTC: "Potential TC",
  TY: "Typhoon",
  MH: "Major Hurricane",
};

// binNumber prefix (e.g. "AL1", "EP2") → basin name.
const BASIN = { AL: "Atlantic", EP: "E. Pacific", CP: "C. Pacific" };

// Saffir-Simpson category from sustained winds (knots), hurricanes only.
function category(cls, winds) {
  if (cls !== "HU" && cls !== "MH" && cls !== "TY") return CLASS[cls] || cls;
  if (winds == null) return "Hurricane";
  if (winds >= 137) return "Cat 5";
  if (winds >= 113) return "Cat 4";
  if (winds >= 96) return "Cat 3";
  if (winds >= 83) return "Cat 2";
  if (winds >= 64) return "Cat 1";
  return "Hurricane";
}

// Map to the dashboard's low/med/high severity palette.
function severityOf(cls, winds) {
  if (cls === "HU" || cls === "MH" || cls === "TY") return winds >= 96 ? "high" : "med";
  if (cls === "TS" || cls === "STS") return "med";
  return "low"; // TD / PTC / subtropical depression
}

export async function storms() {
  return cached("noaa:storms", 30 * 60_000, async () => {
    const j = await fetchJSON("https://www.nhc.noaa.gov/CurrentStorms.json", { timeout: 15_000 });
    const active = Array.isArray(j?.activeStorms) ? j.activeStorms : [];
    const list = active.map((s) => {
      const winds = Number(s.intensity) || null; // sustained winds, knots
      const cls = s.classification;
      const bin = String(s.binNumber || "").slice(0, 2);
      return {
        id: s.id,
        name: s.name,
        cls,
        kind: CLASS[cls] || cls,
        cat: category(cls, winds),
        winds,
        pressure: Number(s.pressure) || null, // millibar
        basin: BASIN[bin] || s.binNumber || "—",
        lat: s.latitudeNumeric ?? null,
        lon: s.longitudeNumeric ?? null,
        movement: s.movementDir && s.movementSpeed ? `${s.movementDir} ${s.movementSpeed}kt` : null,
        severity: severityOf(cls, winds),
        updated: s.lastUpdate || null,
      };
    });
    // Strongest first.
    list.sort((a, b) => (b.winds || 0) - (a.winds || 0));
    return { storms: list, count: list.length, asOf: new Date().toISOString() };
  });
}

export async function enso() {
  return cached("noaa:enso", 12 * 60 * 60_000, async () => {
    const txt = await fetchText("https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt", { timeout: 15_000 });
    // Whitespace table: "SEAS  YR  TOTAL  ANOM" header, then rows like
    // "MAM   2026  28.06   0.48". The ONI value is the last column (ANOM).
    const rows = txt
      .trim()
      .split(/\r?\n/)
      .slice(1)
      .map((l) => l.trim().split(/\s+/))
      .filter((c) => c.length >= 4 && !Number.isNaN(+c[3]));
    if (rows.length === 0) throw new Error("NOAA ONI: no rows");

    const last = rows.at(-1);
    const prev = rows.at(-2);
    const oni = +(+last[3]).toFixed(2);
    const prior = prev ? +(+prev[3]).toFixed(2) : null;
    const phase = oni >= 0.5 ? "El Niño" : oni <= -0.5 ? "La Niña" : "Neutral";
    return {
      oni,
      prior,
      chg: prior != null ? +(oni - prior).toFixed(2) : null,
      season: last[0], // e.g. "MAM" (Mar-Apr-May)
      year: last[1],
      phase,
    };
  });
}
