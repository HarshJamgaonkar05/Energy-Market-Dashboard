import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { Badge } from "../primitives/Badge";
import { ECON } from "../../data/mock";
import { useLive } from "../../lib/useLive";

// Derived from the real U.S. energy-report release cadence (EIA Wed/Thu, API
// Tue, Baker Hughes Fri) — see server/compute/derive.js. Forecast/prior values
// are paywalled, so they show "—".
export const EconCalendar = () => {
  const { data: econ } = useLive("/api/calendar", ECON, useLive.REFRESH.hourly);
  return (
    <Card>
      <SectionTitle sub="Scheduled releases">Economic Calendar</SectionTitle>
      {econ.map((e, i) => (
        <div key={i} className="flex items-center gap-2 py-1.5 border-b border-[#15161a] last:border-0">
          <span className="font-mono text-[10px] text-zinc-500 w-10">{e.t}</span>
          <Badge tone={e.imp}>{e.imp.toUpperCase()}</Badge>
          <span className="text-[11px] text-zinc-300 flex-1 truncate">{e.evt}</span>
          <span className="font-mono text-[10px] text-zinc-400">{e.fc}</span>
        </div>
      ))}
    </Card>
  );
};
