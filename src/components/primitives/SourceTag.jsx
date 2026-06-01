import { Circle } from "lucide-react";
import { Tooltip } from "./Tooltip";
import { sourceOf, KIND_COLOR } from "../../lib/sources";

// Tiny provenance pill shown on panels so it's always clear whether a number is
// a real live feed, a modeled/indicative figure (no free source), or cached
// fallback after an upstream hiccup. Pass `source` to make the pill explain
// itself on hover (label + detail of the underlying feed).
//
//   <SourceTag live source="yahoo" />            → green "LIVE", hover for detail
//   <SourceTag modeled label="INDICATIVE" source="modeled" />
//   <SourceTag stale />                           → zinc "CACHED"
export const SourceTag = ({ live = false, stale = false, modeled = false, label, source, note, className = "" }) => {
  let pill;
  if (modeled) {
    pill = (
      <span className={`inline-flex items-center gap-1 text-[8px] font-semibold uppercase tracking-[0.14em] text-amber-500/80 ${className}`}>
        {label || "Modeled"}
      </span>
    );
  } else if (stale) {
    pill = (
      <span className={`inline-flex items-center gap-1 text-[8px] font-semibold uppercase tracking-[0.14em] text-zinc-600 ${className}`}>
        Cached
      </span>
    );
  } else {
    pill = (
      <span className={`inline-flex items-center gap-1 text-[8px] font-semibold uppercase tracking-[0.14em] ${live ? "text-emerald-500/80" : "text-zinc-600"} ${className}`}>
        <Circle size={4} fill="currentColor" className={live ? "animate-pulse" : ""} />
        {label || (live ? "Live" : "—")}
      </span>
    );
  }

  if (!source) return pill;

  const s = sourceOf(source);
  const color = KIND_COLOR[s.kind];
  const content = (
    <span className="block">
      <span className="flex items-center gap-1.5 text-[10px] font-semibold text-zinc-100">
        <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />
        {s.label}
        <span className="text-[8px] font-semibold uppercase tracking-wider" style={{ color }}>{s.kind}</span>
      </span>
      <span className="mt-0.5 block text-[10px] leading-snug text-zinc-400">{note || s.detail}</span>
    </span>
  );
  return (
    <Tooltip content={content} align="end" className="cursor-help">
      {pill}
    </Tooltip>
  );
};
