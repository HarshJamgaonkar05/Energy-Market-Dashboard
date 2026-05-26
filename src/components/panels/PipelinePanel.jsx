import { fmtSigned } from "../../lib/format";
import { motion } from "framer-motion";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";

export const PipelinePanel = () => {
  const flows = [
    { name: "Cushing → Houston", val: 1820, max: 2400, dir: "S", chg: +3.2 },
    { name: "Permian → Corpus", val: 2640, max: 3100, dir: "S", chg: +1.8 },
    { name: "Nordstream 1", val: 0, max: 1650, dir: "—", chg: 0 },
    { name: "Druzhba Pipeline", val: 740, max: 1200, dir: "W", chg: -2.4 },
  ];
  return (
    <Card>
      <SectionTitle sub="kbpd · live">Pipeline Flows</SectionTitle>
      {flows.map((f) => {
        const w = f.max ? (f.val / f.max) * 100 : 0;
        return (
          <div key={f.name} className="py-1.5 border-b border-[#15161a] last:border-0">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[11px] text-zinc-300">{f.name}</span>
              <span className="font-mono text-[10px] text-zinc-200">
                {f.val.toLocaleString()} <span className="text-zinc-600">/ {f.max.toLocaleString()}</span>
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-1 bg-[#15161a]">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${w}%` }}
                  transition={{ duration: 0.7 }}
                  className={`h-full ${w > 80 ? "bg-amber-500/70" : "bg-sky-500/70"}`}
                />
              </div>
              <span className={`font-mono text-[9px] w-12 text-right ${f.chg >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {f.chg !== 0 ? fmtSigned(f.chg, 1) + "%" : "—"}
              </span>
            </div>
          </div>
        );
      })}
    </Card>
  );
};
