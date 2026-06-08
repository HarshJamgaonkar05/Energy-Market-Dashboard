// Per-headline FinBERT sentiment chip. `sent` is the record attached to each
// news item by the backend: { label: positive|negative|neutral, score, pos,
// neu, neg, signed }. Renders nothing when sentiment is unavailable (null), so
// the news row degrades cleanly to its keyword tag.
const MAP = {
  positive: { lbl: "POS", cls: "text-emerald-400 border-emerald-900/60 bg-emerald-950/40" },
  negative: { lbl: "NEG", cls: "text-red-400 border-red-900/60 bg-red-950/40" },
  neutral: { lbl: "NEU", cls: "text-zinc-400 border-zinc-700 bg-zinc-800/50" },
};

const pct = (x) => `${Math.round((x ?? 0) * 100)}%`;

export const SentimentChip = ({ sent, className = "" }) => {
  if (!sent) return null;
  const m = MAP[sent.label] || MAP.neutral;
  const title =
    `FinBERT · ${sent.label} ${pct(sent.score)} confidence\n` +
    `pos ${pct(sent.pos)} · neu ${pct(sent.neu)} · neg ${pct(sent.neg)}`;
  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 text-[9px] font-mono font-semibold uppercase tracking-wider border cursor-help ${m.cls} ${className}`}
    >
      {m.lbl}
      <span className="opacity-70 tabular-nums">{(sent.score ?? 0).toFixed(2)}</span>
    </span>
  );
};
