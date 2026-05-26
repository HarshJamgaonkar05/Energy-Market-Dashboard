import { Plus, BellRing, Zap, Eye, AlertTriangle, Circle } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { Badge } from "../components/primitives/Badge";
import { ALERTS } from "../data/mock";

export const PageAlerts = () => (
  <div className="space-y-3">
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[13px] font-semibold text-zinc-100">Alerts Center</h2>
          <p className="text-[10px] text-zinc-500 mt-0.5">
            <span className="text-emerald-400 font-mono">{ALERTS.filter((a) => a.act).length}</span> active ·{" "}
            <span className="text-zinc-400 font-mono">{ALERTS.length}</span> total
          </p>
        </div>
        <button className="h-7 px-3 text-[10px] uppercase tracking-wider bg-amber-500 text-zinc-950 font-semibold hover:bg-amber-400">
          <Plus size={11} className="inline mr-1" /> New Alert
        </button>
      </div>
    </Card>

    <Card padding={false}>
      <div className="grid grid-cols-12 px-4 py-2 text-[9px] text-zinc-600 uppercase tracking-wider border-b border-[#1c1d22]">
        <div className="col-span-1">Status</div>
        <div className="col-span-2">Symbol</div>
        <div className="col-span-1">Severity</div>
        <div className="col-span-5">Condition</div>
        <div className="col-span-2">Triggered</div>
        <div className="col-span-1 text-right">Channel</div>
      </div>
      {ALERTS.map((a) => (
        <div key={a.id} className="grid grid-cols-12 px-4 py-2.5 text-[11px] border-b border-[#15161a] last:border-0 hover:bg-white/[0.02]">
          <div className="col-span-1">
            <Circle size={8} fill={a.act ? "#10b981" : "#71717a"} className={a.act ? "animate-pulse" : ""} />
          </div>
          <div className="col-span-2 font-mono text-zinc-200">{a.sym}</div>
          <div className="col-span-1"><Badge tone={a.sev}>{a.sev}</Badge></div>
          <div className="col-span-5 text-zinc-300">{a.msg}</div>
          <div className="col-span-2 font-mono text-zinc-500">{a.t} UTC</div>
          <div className="col-span-1 text-right text-zinc-500 text-[10px]">EMAIL · SLACK</div>
        </div>
      ))}
    </Card>

    <div className="grid grid-cols-3 gap-3">
      <Card>
        <SectionTitle>Triggered Today</SectionTitle>
        <div className="font-mono text-4xl text-amber-400 mt-2">12</div>
        <div className="text-[10px] text-zinc-500 mt-1">3 high · 5 med · 4 low</div>
      </Card>
      <Card>
        <SectionTitle>Active Watchers</SectionTitle>
        <div className="font-mono text-4xl text-emerald-400 mt-2">28</div>
        <div className="text-[10px] text-zinc-500 mt-1">Across 14 instruments</div>
      </Card>
      <Card>
        <SectionTitle>Response Time</SectionTitle>
        <div className="font-mono text-4xl text-sky-400 mt-2">2.4s</div>
        <div className="text-[10px] text-zinc-500 mt-1">Median delivery latency</div>
      </Card>
    </div>
  </div>
);
