import { ArrowUp, ArrowDown } from "lucide-react";
import { fmt, fmtSigned } from "../../lib/format";

export const Delta = ({ v, pct, size = "sm" }) => {
  const up = v >= 0;
  const cls = size === "lg" ? "text-sm" : "text-[11px]";
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
