export const Badge = ({ children, tone = "default", className = "" }) => {
  const tones = {
    default: "bg-zinc-800/60 text-zinc-300 border-zinc-700",
    bull: "bg-emerald-950/40 text-emerald-400 border-emerald-900/60",
    bear: "bg-red-950/40 text-red-400 border-red-900/60",
    warn: "bg-amber-950/40 text-amber-400 border-amber-900/60",
    info: "bg-sky-950/40 text-sky-400 border-sky-900/60",
    high: "bg-red-950/40 text-red-400 border-red-900/60",
    med: "bg-amber-950/40 text-amber-400 border-amber-900/60",
    low: "bg-zinc-800/60 text-zinc-400 border-zinc-700",
  };
  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider border ${
        tones[tone] || tones.default
      } ${className}`}
    >
      {children}
    </span>
  );
};
