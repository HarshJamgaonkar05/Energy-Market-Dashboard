import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SHIPPING } from "../../data/mock";
import { motion } from "framer-motion";

export const ShippingPanel = () => (
  <Card>
    <SectionTitle sub="Live AIS">Port Congestion</SectionTitle>
    {SHIPPING.map((s) => {
      const sev = s.congestion > 75 ? "bg-red-500/70" : s.congestion > 55 ? "bg-amber-500/70" : "bg-emerald-500/70";
      return (
        <div key={s.port} className="flex items-center gap-2 py-1.5 border-b border-[#15161a] last:border-0">
          <span className="text-[11px] text-zinc-300 w-20">{s.port}</span>
          <div className="flex-1 h-1.5 bg-[#15161a]">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${s.congestion}%` }}
              transition={{ duration: 0.6 }}
              className={`h-full ${sev}`}
            />
          </div>
          <span className="font-mono text-[10px] text-zinc-400 w-8 text-right">{s.congestion}%</span>
          <span className="font-mono text-[10px] text-zinc-500 w-12 text-right">{s.delay}</span>
        </div>
      );
    })}
  </Card>
);
