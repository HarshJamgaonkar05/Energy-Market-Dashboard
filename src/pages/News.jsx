import { useState } from "react";
import { motion } from "framer-motion";
import { ExternalLink, AlertTriangle, Circle } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { Badge } from "../components/primitives/Badge";
import { NEWS } from "../data/mock";
import { EconCalendar } from "../components/panels/EconCalendar";
import { SentimentPanel } from "../components/panels/SentimentPanel";
import { useLive } from "../lib/useLive";

const SENT_FALLBACK = { distribution: { bullish: 38, neutral: 42, bearish: 20 } };

export const PageNews = () => {
  const [filter, setFilter] = useState("ALL");
  // Live energy newswire (GDELT) + computed sentiment distribution.
  const { data: news, live } = useLive("/api/news", NEWS, useLive.REFRESH.hourly);
  const { data: sent } = useLive("/api/sentiment", SENT_FALLBACK, useLive.REFRESH.slow);
  const dist = sent.distribution || SENT_FALLBACK.distribution;
  const filtered = filter === "ALL" ? news : news.filter((n) => n.tag === filter);

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-9">
          <Card padding={false}>
            <div className="p-4 border-b border-[#1c1d22] flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <h2 className="text-[13px] font-semibold text-zinc-100">Newswire</h2>
                <Circle size={6} fill={live ? "#10b981" : "#ef4444"} className="animate-pulse" />
                <span className="text-[10px] text-zinc-500 uppercase tracking-wider">{live ? "Live · GDELT" : "Cached"} · {filtered.length} stories</span>
              </div>
              <div className="flex items-center flex-wrap gap-1">
                {["ALL", "OPEC", "GEOPOLITICS", "CRUDE", "PRODUCTS", "FREIGHT", "STOCKS", "MACRO", "WEATHER"].map((t) => (
                  <button
                    key={t}
                    onClick={() => setFilter(t)}
                    className={`px-2 h-6 text-[9px] font-mono tracking-wider ${
                      filter === t ? "bg-amber-500/10 text-amber-400 border border-amber-500/30" : "text-zinc-500 border border-transparent hover:text-zinc-200"
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>
            <div>
              {filtered.map((n, i) => (
                <motion.a
                  key={i}
                  href={n.url || undefined}
                  target={n.url ? "_blank" : undefined}
                  rel="noreferrer"
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: Math.min(i * 0.02, 0.5) }}
                  className="block px-4 py-3 border-b border-[#15161a] hover:bg-white/[0.02] cursor-pointer group last:border-0"
                >
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="font-mono text-[10px] text-zinc-600">{n.t}</span>
                    <span className="text-[10px] font-bold text-zinc-400 tracking-wider">{n.src}</span>
                    <Badge tone={n.sev}>{n.tag}</Badge>
                    {n.sev === "high" && <AlertTriangle size={10} className="text-red-400" />}
                    <ExternalLink size={10} className="text-zinc-700 opacity-0 group-hover:opacity-100 ml-auto" />
                  </div>
                  <p className="text-[12px] text-zinc-200 leading-snug group-hover:text-zinc-100">{n.txt}</p>
                </motion.a>
              ))}
            </div>
          </Card>
        </div>

        <div className="col-span-12 lg:col-span-3 space-y-3">
          <SentimentPanel />
          <Card>
            <SectionTitle sub="From newswire">Sentiment Distribution</SectionTitle>
            <div className="space-y-2">
              {[
                { l: "Bullish", v: dist.bullish, c: "#10b981" },
                { l: "Neutral", v: dist.neutral, c: "#71717a" },
                { l: "Bearish", v: dist.bearish, c: "#ef4444" },
              ].map((s) => (
                <div key={s.l}>
                  <div className="flex justify-between text-[10px] mb-1">
                    <span className="text-zinc-400">{s.l}</span>
                    <span className="font-mono text-zinc-300">{s.v}%</span>
                  </div>
                  <div className="h-1.5 bg-[#15161a]">
                    <motion.div initial={{ width: 0 }} animate={{ width: `${s.v}%` }} transition={{ duration: 0.6 }} style={{ background: s.c, opacity: 0.7 }} className="h-full" />
                  </div>
                </div>
              ))}
            </div>
          </Card>
          <EconCalendar />
        </div>
      </div>
    </div>
  );
};
