// ============================================================================
// Open-Meteo — free, no key, CORS-friendly weather forecast API.
//   GET /v1/forecast?latitude=&longitude=&daily=temperature_2m_max,..._min
// Temperatures and degree-days below are genuinely LIVE (refreshed hourly by
// Open-Meteo). The per-region monthly "normal" used for the anomaly is a
// climatological reference constant (NOAA-style 30y normals, °C) — the UI
// labels anomaly as "vs normal" accordingly.
// ============================================================================
import { cached, fetchJSON } from "../lib/cache.js";

const BASE = "https://api.open-meteo.com/v1/forecast";
const HDD_BASE = 18.0; // °C heating-degree-day base (~65°F)

// Representative point + monthly mean-temp normals (°C, Jan..Dec) per region.
const REGIONS = [
  { key: "US Northeast",  lat: 40.71, lon: -74.0,  group: "US",   norm: [-0.5, 0.5, 5, 11, 16, 21, 24, 23, 19, 13, 7, 2] },
  { key: "US Midwest",    lat: 41.88, lon: -87.63, group: "US",   norm: [-4, -2, 4, 10, 16, 22, 24, 23, 19, 12, 5, -2] },
  { key: "US Gulf Coast", lat: 29.76, lon: -95.37, group: "US",   norm: [11, 13, 17, 21, 25, 28, 29, 29, 27, 22, 17, 12] },
  { key: "NW Europe",     lat: 52.37, lon: 4.90,   group: "EU",   norm: [4, 4, 7, 10, 14, 17, 19, 19, 16, 12, 7, 5] },
  { key: "Northeast Asia",lat: 37.57, lon: 126.98, group: "ASIA", norm: [1, 2, 7, 13, 18, 22, 26, 27, 22, 16, 9, 3] },
  { key: "S. Europe",     lat: 41.90, lon: 12.50,  group: "EU",   norm: [8, 9, 12, 15, 19, 24, 27, 27, 23, 18, 13, 9] },
];

async function dailyTemps(lat, lon, pastDays = 0, forecastDays = 7) {
  const url =
    `${BASE}?latitude=${lat}&longitude=${lon}` +
    `&daily=temperature_2m_max,temperature_2m_min&timezone=auto` +
    `&past_days=${pastDays}&forecast_days=${forecastDays}`;
  const j = await fetchJSON(url);
  const t = j?.daily?.time || [];
  const hi = j?.daily?.temperature_2m_max || [];
  const lo = j?.daily?.temperature_2m_min || [];
  return t.map((date, i) => ({ date, mean: (hi[i] + lo[i]) / 2 }));
}

const hdd = (mean) => Math.max(0, HDD_BASE - mean);
const cdd = (mean) => Math.max(0, mean - HDD_BASE);

// ----------------------------------------------------------------------------
// Regional weather risk rows + heating/cooling degree-day hero tiles.
// One fetch per region, all cached 1h.
// ----------------------------------------------------------------------------
export async function weather() {
  return cached("openmeteo:regions", 60 * 60_000, async () => {
    const month = new Date().getMonth();
    const rows = await Promise.all(
      REGIONS.map(async (r) => {
        try {
          const days = await dailyTemps(r.lat, r.lon, 0, 7);
          const todayMean = days[0]?.mean ?? null;
          const normal = r.norm[month];
          const anom = todayMean != null ? +(todayMean - normal).toFixed(1) : 0;
          const hdd7 = +days.reduce((s, d) => s + hdd(d.mean), 0).toFixed(0);
          const cdd7 = +days.reduce((s, d) => s + cdd(d.mean), 0).toFixed(0);
          const severity = hdd7 > 70 || anom < -3 ? "high" : hdd7 > 35 || Math.abs(anom) > 1.5 ? "med" : "low";
          return { reg: r.key, group: r.group, temp: Math.round(todayMean), anom, hdd: hdd7, cdd: cdd7, severity };
        } catch (e) {
          console.warn(`[open-meteo] ${r.key} failed: ${e.message}`);
          return null;
        }
      })
    );
    const regions = rows.filter(Boolean);

    const sumBy = (g, field) =>
      regions.filter((r) => r.group === g).reduce((s, r) => s + r[field], 0);

    return {
      regions,
      heroes: {
        usHdd: sumBy("US", "hdd"),
        euHdd: sumBy("EU", "hdd"),
        asiaCdd: sumBy("ASIA", "cdd"),
      },
      asOf: new Date().toISOString().slice(0, 10),
    };
  });
}

// ----------------------------------------------------------------------------
// 14-day temperature forecast vs normal for the chart (NW Europe default).
// `obs` = past 7 days of actuals, `fc` = next 14 days of forecast.
// ----------------------------------------------------------------------------
export async function tempForecast(regionKey = "NW Europe") {
  const r = REGIONS.find((x) => x.key === regionKey) || REGIONS[3];
  return cached(`openmeteo:fc:${r.key}`, 60 * 60_000, async () => {
    const month = new Date().getMonth();
    const days = await dailyTemps(r.lat, r.lon, 7, 14);
    const normal = r.norm[month];
    // Center the series on "normal" so the chart's 0-line = climatological normal.
    return days.map((d, i) => {
      const anom = +(d.mean - normal).toFixed(1);
      const isPast = i < 7;
      return {
        d: `D${i - 7 >= 0 ? "+" : ""}${i - 7}`,
        obs: isPast ? anom : null,
        fc: !isPast ? anom : null,
      };
    });
  });
}
