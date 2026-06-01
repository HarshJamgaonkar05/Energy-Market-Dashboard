import { ArrowUp, ArrowDown } from "lucide-react";
import { fmt, fmtSigned, DASH } from "../../lib/format";

export const Delta = ({ v, pct, size = "sm" }) => {
  const cls = size === "lg" ? "text-sm" : "text-[11px]";
  // No real change available → neutral dash, no arrow/colour (don't imply a direction).
  if (v == null || Number.isNaN(Number(v))) {
    return <span className={`inline-flex items-center font-mono ${cls} text-zinc-600`}>{DASH}</span>;
  }
  const up = v >= 0;
  return (
    <span
      className={`inline-flex items-center gap-1 font-mono ${cls} ${
        up ? "text-emerald-400" : "text-red-400"
      }`}
    >
      {up ? <ArrowUp size={10} /> : <ArrowDown size={10} />}
      {fmtSigned(v)} ({fmtSigned(pct)}%)
    </span>
  );
};
