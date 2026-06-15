import { FlaskConical } from "lucide-react";

// Unmistakable banner for sections whose numbers are SIMULATED (no free data
// source exists). Stronger than the hover-only SourceTag — it makes clear, at a
// glance, that the values are illustrative shapes, not a live market feed.
export const SimulatedBanner = ({ children }) => (
  <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-950/30 border border-amber-900/50 text-[10px] text-amber-300/90">
    <FlaskConical size={12} className="flex-shrink-0 text-amber-400" />
    <span>
      <strong className="font-semibold uppercase tracking-wider">Simulated</strong>{" — "}
      {children || "illustrative shapes only, not a live market feed. No free source exists for this data."}
    </span>
  </div>
);
