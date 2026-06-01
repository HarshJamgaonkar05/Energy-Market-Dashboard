import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SourceTag } from "../primitives/SourceTag";
import { Sourced } from "../primitives/Sourced";
import { SHIPPING } from "../../data/mock";
import { useLive } from "../../lib/useLive";

// Port congestion. Live AIS / port-call feeds (MarineTraffic / Kpler) are
// paywalled — there is no free source, so the values show "—" (the tracks stay
// empty rather than drawing a fabricated level). Backend: server/compute/derive.js.
export const ShippingPanel = () => {
  const { data } = useLive("/api/freight", { ports: SHIPPING }, useLive.REFRESH.slow);
  const ports = data.ports || SHIPPING;
  return (
    <Card>
      <SectionTitle sub="Tanker queues" action={<SourceTag modeled label="No source" source="modeled" note="Live AIS / port-call feeds (MarineTraffic, Kpler) are paywalled — no free source." />}>Port Congestion</SectionTitle>
      {ports.map((s) => (
        <div key={s.port} className="flex items-center gap-2 py-1.5 border-b border-[#15161a] last:border-0">
          <span className="text-[11px] text-zinc-300 w-20">{s.port}</span>
          <div className="flex-1 h-1.5 bg-[#15161a]" />
          <span className="font-mono text-[10px] text-zinc-400 w-8 text-right">
            <Sourced source="modeled" note="Port congestion — AIS feeds are paywalled, no free source" align="end" />
          </span>
          <span className="font-mono text-[10px] text-zinc-500 w-12 text-right">
            <Sourced source="modeled" note="Queue delay — no free source" align="end" />
          </span>
        </div>
      ))}
    </Card>
  );
};
