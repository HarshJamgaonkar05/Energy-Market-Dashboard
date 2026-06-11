import { Thermometer, Flame, Snowflake } from "lucide-react";
import { fmtSigned } from "../../lib/format";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SourceTag } from "../primitives/SourceTag";
import { Sourced } from "../primitives/Sourced";
import { WEATHER } from "../../data/mock";
import { useLive } from "../../lib/useLive";

const SIG_COLOR = { bullish: "text-emerald-400", bearish: "text-red-400", neutral: "text-zinc-500" };

// Live regional temperatures + heating-degree-days from Open-Meteo (no key).
// Anomaly = current vs climatological monthly normal. See server/sources/openmeteo.js.
export const WeatherRisk = () => {
  const { data, live } = useLive("/api/weather", { regions: WEATHER }, useLive.REFRESH.hourly);
  const regions = data.regions || WEATHER;
  const demand = data.demand;
  return (
    <Card>
      <SectionTitle sub="vs normal" action={<SourceTag live={live} source="openmeteo" note="Open-Meteo forecast model; anomaly is vs the climatological monthly normal." />}>Weather Risk</SectionTitle>
      <div className="space-y-1.5">
        {regions.map((w) => (
          <div key={w.reg} className="flex items-center gap-2 py-1 border-b border-[#15161a] last:border-0">
            <Thermometer
              size={11}
              className={
                w.severity === "high"
                  ? "text-red-400"
                  : w.severity === "med"
                  ? "text-amber-400"
                  : "text-zinc-500"
              }
            />
            <span className="text-[10px] text-zinc-300 flex-1 truncate">{w.reg}</span>
            <span className="font-mono text-[10px] text-zinc-400 w-10 text-right">
              <Sourced source="openmeteo" note="Daily mean temperature · Open-Meteo" align="end">{w.temp}°C</Sourced>
            </span>
            <span className={`font-mono text-[10px] w-12 text-right ${w.anom < 0 ? "text-sky-400" : "text-amber-400"}`}>
              <Sourced source="derived" note="Anomaly = today's mean − climatological normal (Open-Meteo + NOAA-style normals)" align="end">{fmtSigned(w.anom, 1)}°</Sourced>
            </span>
          </div>
        ))}
      </div>

      {/* Weather-driven demand signal — degree-day anomaly → product demand read */}
      {demand && (
        <div className="mt-2 pt-2 border-t border-[#1c1d22]">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[9px] uppercase tracking-[0.14em] text-zinc-600">Demand read · vs normal</span>
            <SourceTag source="derived" label="Derived" note="Aggregate actual vs climatological-normal heating/cooling degree days across all regions → product-demand signal (colder ⇒ bullish distillate/gas; hotter ⇒ bullish power burn)." />
          </div>
          {[
            { k: "heating", icon: Snowflake, lbl: "Heating", d: demand.heating },
            { k: "cooling", icon: Flame, lbl: "Cooling", d: demand.cooling },
          ].map(({ k, icon: Icon, lbl, d }) => d && (
            <div key={k} className="flex items-center gap-2 py-0.5">
              <Icon size={11} className="text-zinc-500" />
              <span className="text-[10px] text-zinc-300 w-12">{lbl}</span>
              <span className="text-[9px] text-zinc-600 flex-1 truncate">{d.drives}</span>
              <span className="font-mono text-[10px] text-zinc-400 w-10 text-right">
                <Sourced source="derived" note={`Degree-day anomaly vs climatological normal across all regions`} align="end">{fmtSigned(d.anomPct, 0)}%</Sourced>
              </span>
              <span className={`text-[9px] uppercase tracking-wider w-12 text-right font-semibold ${SIG_COLOR[d.signal]}`}>{d.signal}</span>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
