import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SourceTag } from "../primitives/SourceTag";
import { Sourced } from "../primitives/Sourced";
import { Badge } from "../primitives/Badge";
import { ECON } from "../../data/mock";
import { useLive } from "../../lib/useLive";

// Derived from the real U.S. energy-report release cadence (EIA Wed/Thu, API
// Tue, Baker Hughes Fri) — see server/compute/derive.js. Consensus forecasts
// are paywalled (show "—"); the EIA crude prior is enriched from the live WPSR.
export const EconCalendar = () => {
  const { data: econ } = useLive("/api/calendar", ECON, useLive.REFRESH.hourly);
  return (
    <Card>
      <SectionTitle
        sub="Scheduled releases"
        action={<SourceTag live label="Schedule" source="schedule" note="Official U.S. energy-report release cadence; the EIA crude prior is the live WPSR print." />}
      >
        Economic Calendar
      </SectionTitle>
      {econ.map((e, i) => {
        const isEia = /EIA/.test(e.evt);
        const prevSrc = isEia && e.prev !== "—" ? "eia" : "schedule";
        const prevNote = isEia && e.prev !== "—"
          ? "Prior week's actual print · EIA Weekly Petroleum Status Report"
          : "Consensus/prior is paywalled — shown when available";
        return (
          <div key={i} className="flex items-center gap-2 py-1.5 border-b border-[#15161a] last:border-0">
            {(e.day || e.today) && (
              <span className={`font-mono text-[9px] w-7 ${e.today ? "text-amber-400" : "text-zinc-600"}`}>
                {e.today ? "TODAY" : e.day}
              </span>
            )}
            <span className="font-mono text-[10px] text-zinc-500 w-10">{e.t}</span>
            <Badge tone={e.imp}>{e.imp.toUpperCase()}</Badge>
            <span className="text-[11px] text-zinc-300 flex-1 truncate">{e.evt}</span>
            <span className="font-mono text-[10px] text-zinc-400">
              {e.prev && e.prev !== "—"
                ? <Sourced source={prevSrc} note={prevNote} align="end">{e.fc !== "—" ? e.fc : e.prev}</Sourced>
                : <Sourced source="schedule" note="Forecast/prior is paywalled" align="end">{e.fc}</Sourced>}
            </span>
          </div>
        );
      })}
    </Card>
  );
};
