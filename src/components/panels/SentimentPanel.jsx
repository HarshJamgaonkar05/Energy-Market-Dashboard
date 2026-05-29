import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SourceTag } from "../primitives/SourceTag";
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
};

export const SentimentPanel = () => {
  const { data, live } = useLive("/api/sentiment", FALLBACK, useLive.REFRESH.slow);
  const groups = data.groups || FALLBACK.groups;
  return (
    <Card>
      <SectionTitle sub="Momentum + news" action={<SourceTag live={live} />}>Sentiment</SectionTitle>
      <div className="space-y-2.5">
        {groups.map((s) => {
          const bull = s.value >= 50;
          return (
            <div key={s.name}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-zinc-400 uppercase tracking-wider">{s.name}</span>
                <span className={`text-[10px] font-mono ${bull ? "text-emerald-400" : "text-red-400"}`}>
                  {s.value} · {s.lbl}
                </span>
              </div>
              <div className="h-1.5 bg-[#15161a] relative">
                <div className="absolute inset-y-0 left-1/2 w-px bg-[#2a2b31]" />
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.abs(s.value - 50) * 2}%` }}
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
