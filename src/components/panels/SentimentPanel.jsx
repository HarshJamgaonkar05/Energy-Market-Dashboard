import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SourceTag } from "../primitives/SourceTag";
import { Sourced } from "../primitives/Sourced";
import { motion } from "framer-motion";
import { useLive } from "../../lib/useLive";

// Composite sentiment computed on the backend from live price momentum + the
// bull/bear balance of recent news (server/compute/derive.js → sentiment()).
const FALLBACK = {
  groups: [
    { name: "Crude", value: 64, lbl: "Bullish" },
    { name: "Distillates", value: 58, lbl: "Bullish" },
    { name: "Gasoline", value: 71, lbl: "V. Bullish" },
    { name: "Gas Oil", value: 46, lbl: "Neutral" },
  ],
  newsIndex: { value: 56, lbl: "Bullish", n: 0, model: "FinBERT" },
};

export const SentimentPanel = () => {
  const { data, live } = useLive("/api/sentiment", FALLBACK, useLive.REFRESH.slow);
  const groups = data.groups || FALLBACK.groups;
  const idx = data.newsIndex || FALLBACK.newsIndex;
  const finbert = idx.model === "FinBERT";
  return (
    <Card>
      <SectionTitle sub="Momentum + FinBERT news" action={<SourceTag live={live} source="derived" note="Per-group gauges are live price momentum (Yahoo). The news tone index is FinBERT scoring recent headlines positive/negative/neutral." />}>Sentiment</SectionTitle>
      {/* FinBERT news tone — model read of the wire, separate from price momentum */}
      <div className="flex items-center justify-between mb-3 pb-3 border-b border-[#1c1d22]">
        <span className="text-[10px] text-zinc-400 uppercase tracking-wider">
          News tone <span className="text-zinc-600 normal-case tracking-normal">· {finbert ? "FinBERT" : "keyword"}</span>
        </span>
        <span className={`text-[11px] font-mono ${idx.value >= 55 ? "text-emerald-400" : idx.value <= 45 ? "text-red-400" : "text-zinc-400"}`}>
          <Sourced source="finbert" note={finbert ? `Mean FinBERT signed score across ${idx.n} headlines, mapped to 0–100.` : "FinBERT unavailable — keyword tilt of recent headlines."} align="end">{idx.value} · {idx.lbl}</Sourced>
        </span>
      </div>
      <div className="space-y-2.5">
        {groups.map((s) => {
          const bull = s.value >= 50;
          return (
            <div key={s.name}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-zinc-400 uppercase tracking-wider">{s.name}</span>
                <span className={`text-[10px] font-mono ${bull ? "text-emerald-400" : "text-red-400"}`}>
                  <Sourced source="derived" note="0–100 composite from price momentum + news balance" align="end">{s.value} · {s.lbl}</Sourced>
                </span>
              </div>
              {/* Center-anchored gauge: each half is 50% of the track, so the
                  bar width is the deviation from 50 (0–50), capped so extreme
                  readings (e.g. 21) never spill outside the panel. */}
              <div className="h-1.5 bg-[#15161a] relative overflow-hidden">
                <div className="absolute inset-y-0 left-1/2 w-px bg-[#2a2b31]" />
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(50, Math.abs(s.value - 50))}%` }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                  className={`absolute inset-y-0 ${bull ? "bg-emerald-500/70 left-1/2" : "bg-red-500/70 right-1/2"}`}
                />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
