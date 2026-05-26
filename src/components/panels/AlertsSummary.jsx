import { BellRing } from "lucide-react";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { Badge } from "../primitives/Badge";
import { ALERTS } from "../../data/mock";

export const AlertsSummary = () => (
  <Card>
    <SectionTitle sub={`${ALERTS.filter((a) => a.act).length} active`}>Alerts</SectionTitle>
    {ALERTS.slice(0, 4).map((a) => (
      <div key={a.id} className="flex items-start gap-2 py-1.5 border-b border-[#15161a] last:border-0">
        <Badge tone={a.sev}>{a.sev.toUpperCase()}</Badge>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-mono text-zinc-200">{a.sym}</div>
          <div className="text-[10px] text-zinc-500 truncate">{a.msg}</div>
        </div>
        <span className="font-mono text-[9px] text-zinc-600">{a.t}</span>
      </div>
    ))}
  </Card>
);
