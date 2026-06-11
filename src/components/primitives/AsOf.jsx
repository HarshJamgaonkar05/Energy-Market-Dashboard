import { Clock } from "lucide-react";

// Tiny data-freshness badge — shows the as-of / through date of a panel's data
// so a reading is never silently stale. Hover for the full note. Renders nothing
// when no date is available (so it's safe to drop onto any panel).
//
//   <AsOf date="2026-06-05" />            → "as of 2026-06-05"
//   <AsOf date={lastDate} prefix="through" />
export const AsOf = ({ date, prefix = "as of", className = "" }) => {
  if (!date) return null;
  return (
    <span
      className={`inline-flex items-center gap-1 text-[9px] font-mono text-zinc-600 ${className}`}
      title={`Data ${prefix} ${date}`}
    >
      <Clock size={9} className="flex-shrink-0" />
      {prefix} {date}
    </span>
  );
};
