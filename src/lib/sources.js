// ============================================================================
// Source registry (frontend mirror of server/lib/sources.js).
//
// Every number on the dashboard traces back to one of these. The <Sourced>
// wrapper and <SourceTag> read from here so a hover anywhere can answer
// "where did this come from?" without an extra network round-trip.
//
//   kind:  live · official · derived · modeled · curated · schedule
// ============================================================================

export const SOURCES = {
  yahoo: {
    label: "Yahoo Finance",
    detail: "Live futures quote / daily closing history.",
    kind: "live",
  },
  eia: {
    label: "EIA",
    detail: "U.S. Energy Information Administration — Weekly Petroleum Status Report.",
    kind: "official",
  },
  openmeteo: {
    label: "Open-Meteo",
    detail: "Open weather-forecast model, refreshed hourly.",
    kind: "live",
  },
  financialjuice: {
    label: "Financial Juice",
    detail: "Real-time financial newswire (RSS).",
    kind: "live",
  },
  derived: {
    label: "Derived",
    detail: "Computed on the server from live feeds.",
    kind: "derived",
  },
  modeled: {
    label: "No free source",
    detail: "No free or open data source for this value — shown as “—” rather than an assumed figure.",
    kind: "modeled",
  },
  curated: {
    label: "Curated",
    detail: "Hand-maintained reference values (published policy targets & recent estimates).",
    kind: "curated",
  },
  schedule: {
    label: "Release schedule",
    detail: "Official U.S. energy-report release cadence (EIA · API · Baker Hughes).",
    kind: "schedule",
  },
};

// Dot / accent colour per provenance kind (matches the dashboard palette).
export const KIND_COLOR = {
  live: "#10b981",
  official: "#38bdf8",
  derived: "#a78bfa",
  modeled: "#f59e0b",
  curated: "#f59e0b",
  schedule: "#38bdf8",
};

// Resolve a source key to its descriptor (falls back to "modeled" if unknown).
export const sourceOf = (key) => SOURCES[key] || SOURCES.modeled;
