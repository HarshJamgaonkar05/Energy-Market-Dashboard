import { Circle } from "lucide-react";

// Tiny provenance pill shown on panels so it's always clear whether a number is
// a real live feed, a modeled/indicative figure (no free source), or cached
// fallback after an upstream hiccup.
//
//   <SourceTag live />                         → green "LIVE"
//   <SourceTag modeled label="INDICATIVE" />   → amber, for no-free-source data
//   <SourceTag stale />                         → zinc "CACHED"
export const SourceTag = ({ live = false, stale = false, modeled = false, label, className = "" }) => {
  if (modeled) {
    return (
      <span className={`inline-flex items-center gap-1 text-[8px] font-semibold uppercase tracking-[0.14em] text-amber-500/80 ${className}`}>
        {label || "Modeled"}
      </span>
    );
  }
  if (stale) {
    return (
      <span className={`inline-flex items-center gap-1 text-[8px] font-semibold uppercase tracking-[0.14em] text-zinc-600 ${className}`}>
        Cached
      </span>
    );
  }
  return (
    <span className={`inline-flex items-center gap-1 text-[8px] font-semibold uppercase tracking-[0.14em] ${live ? "text-emerald-500/80" : "text-zinc-600"} ${className}`}>
      <Circle size={4} fill="currentColor" className={live ? "animate-pulse" : ""} />
      {label || (live ? "Live" : "—")}
    </span>
  );
};
