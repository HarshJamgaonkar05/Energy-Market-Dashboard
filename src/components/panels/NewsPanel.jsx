import { ExternalLink, AlertTriangle, Circle } from "lucide-react";
import { motion } from "framer-motion";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { Badge } from "../primitives/Badge";
import { NEWS } from "../../data/mock";

export const NewsPanel = ({ compact = false }) => (
  <Card padding={false} className="flex flex-col">
    <div className="p-4 pb-2 flex-shrink-0">
      <SectionTitle sub="Live wire">
        <span className="inline-flex items-center gap-1.5">
          Breaking News
          <Circle size={5} fill="#ef4444" className="animate-pulse" />
        </span>
      </SectionTitle>
      {!compact && (
        <div className="flex items-center gap-1 mb-2">
          {["ALL", "CRUDE", "GAS", "LNG", "FREIGHT"].map((t) => (
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
      {NEWS.map((n, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, x: -4 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.04 }}
          className="px-3 py-2 border-b border-[#15161a] hover:bg-white/[0.02] cursor-pointer last:border-0 group"
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[9px] font-mono text-zinc-600">{n.t}</span>
            <span className="text-[9px] font-bold text-zinc-400 tracking-wider">{n.src}</span>
            <Badge tone={n.sev}>{n.tag}</Badge>
            {n.sev === "high" && (
              <AlertTriangle size={9} className="text-red-400 ml-auto" />
            )}
          </div>
          <p className="text-[11px] text-zinc-300 leading-snug group-hover:text-zinc-100 transition-colors">
            {n.txt}
          </p>
        </motion.div>
      ))}
    </div>
  </Card>
);
