import { Thermometer } from "lucide-react";
import { fmtSigned } from "../../lib/format";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SourceTag } from "../primitives/SourceTag";
import { WEATHER } from "../../data/mock";
import { useLive } from "../../lib/useLive";

// Live regional temperatures + heating-degree-days from Open-Meteo (no key).
// Anomaly = current vs climatological monthly normal. See server/sources/openmeteo.js.
export const WeatherRisk = () => {
  const { data, live } = useLive("/api/weather", { regions: WEATHER }, useLive.REFRESH.hourly);
  const regions = data.regions || WEATHER;
  return (
    <Card>
      <SectionTitle sub="vs normal" action={<SourceTag live={live} />}>Weather Risk</SectionTitle>
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
            <span className="font-mono text-[10px] text-zinc-400 w-10 text-right">{w.temp}°C</span>
            <span className={`font-mono text-[10px] w-12 text-right ${w.anom < 0 ? "text-sky-400" : "text-amber-400"}`}>
              {fmtSigned(w.anom, 1)}°
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
};
