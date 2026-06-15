import { ExternalLink, AlertTriangle, Circle } from "lucide-react";
import { motion } from "framer-motion";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { Badge } from "../primitives/Badge";
import { NEWS } from "../../data/mock";
import { useLive } from "../../lib/useLive";

// Live financial newswire — Financial Juice RSS (see server/sources/financialjuice.js).
// Falls back to the seeded NEWS headlines if the backend or feed is unreachable.
// In `compact` mode (side rails) we cap the list to the freshest few. In `fill`
// mode (the Dashboard right rail) the panel stretches to fill the column height
// and scrolls through the whole wire, so no blank space is left below it.
export const NewsPanel = ({ compact = false, fill = false, limit }) => {
  const { data: news, live } = useLive("/api/news", NEWS, useLive.REFRESH.slow);
  const max = limit ?? (fill ? Infinity : compact ? 5 : Infinity);
  const items = Number.isFinite(max) ? news.slice(0, max) : news;

  return (
    <Card padding={false} className={`flex flex-col ${fill ? "flex-1 min-h-0" : ""}`}>
      <div className="p-4 pb-2 flex-shrink-0">
        <SectionTitle sub={compact ? "Live wire" : `Live wire · ${news.length} headlines`}>
          <span className="inline-flex items-center gap-1.5">
            Breaking News
            <Circle size={5} fill={live ? "#10b981" : "#ef4444"} className="animate-pulse" />
          </span>
        </SectionTitle>
        {!compact && (
          <div className="flex items-center flex-wrap gap-1 mb-2">
            {["ALL", "OPEC", "GEOPOLITICS", "CRUDE", "PRODUCTS", "FREIGHT", "MACRO"].map((t) => (
              <button
                key={t}
                className={`px-1.5 h-5 text-[9px] font-mono tracking-wider ${
                  t === "ALL"
                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                    : "text-zinc-500 border border-transparent hover:text-zinc-200"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="flex-1 overflow-y-auto px-1 pb-1">
        {items.map((n, i) => (
          <motion.a
            key={i}
            href={n.url || undefined}
            target={n.url ? "_blank" : undefined}
            rel="noreferrer"
            initial={{ opacity: 0, x: -4 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: Math.min(i * 0.04, 0.6) }}
            className="block px-3 py-2 border-b border-[#15161a] hover:bg-white/[0.02] cursor-pointer last:border-0 group"
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[9px] font-mono text-zinc-600">{n.t}</span>
              <span
                className="text-[9px] font-bold text-zinc-400 tracking-wider cursor-help"
                title={`${n.src === "FINJUICE" ? "Financial Juice" : n.src} · live financial newswire`}
              >
                {n.src}
              </span>
              <Badge tone={n.sev}>{n.tag}</Badge>
              {n.sev === "high" && (
                <AlertTriangle size={9} className="text-red-400 ml-auto" />
              )}
            </div>
            <p className="text-[11px] text-zinc-300 leading-snug group-hover:text-zinc-100 transition-colors">
              {n.txt}
            </p>
          </motion.a>
        ))}
      </div>
    </Card>
  );
};
