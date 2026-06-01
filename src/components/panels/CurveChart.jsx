import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SourceTag } from "../primitives/SourceTag";
import { Sourced } from "../primitives/Sourced";
import { FWD_CURVES } from "../../data/mock";
import { chartProps, ChartTooltip } from "../../lib/chart-theme";
import { fmt, fmtSigned } from "../../lib/format";
import { useLive } from "../../lib/useLive";

const CURVE_NOTE = "Front month anchored to the live Yahoo quote; the term structure uses a curated slope (exchange settlement curves are paywalled).";

// Forward curves are MODELED: the front month is anchored to the live Yahoo
// quote, but the term structure uses a curated slope (exchange settlement
// curves are paywalled). Backend: server/compute/markets.js → curves().
export const CurveChart = () => {
  const { data: curves } = useLive("/api/curves", FWD_CURVES, useLive.REFRESH.slow);
  const brent = (curves.brent || FWD_CURVES.brent).data;
  const wti = (curves.wti || FWD_CURVES.wti).data;
  const data = brent.map((p, i) => ({ m: p.m, brent: p.v, wti: wti[i]?.v }));

  const bSlope = brent[0].v - brent[11].v;
  const wSlope = wti[0].v - wti[11].v;
  const m1 = brent[0].v - wti[0].v;

  return (
    <Card padding={false}>
      <div className="p-4 pb-2">
        <SectionTitle sub="Front 12 months" action={<SourceTag modeled label="Modeled curve" source="modeled" note={CURVE_NOTE} />}>Forward Curve Structure</SectionTitle>
      </div>
      <div className="h-48 px-2 pb-2">
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 8, right: 20, bottom: 6, left: 0 }}>
            <CartesianGrid {...chartProps.grid} />
            <XAxis dataKey="m" {...chartProps.axis} />
            <YAxis {...chartProps.axis} domain={["auto", "auto"]} width={40} />
            <Tooltip content={<ChartTooltip unit=" $/bbl" source="modeled" />} />
            <Line type="monotone" dataKey="brent" stroke="#f59e0b" strokeWidth={1.6} dot={{ r: 2.5, fill: "#f59e0b" }} name="Brent" isAnimationActive={false} />
            <Line type="monotone" dataKey="wti" stroke="#38bdf8" strokeWidth={1.6} dot={{ r: 2.5, fill: "#38bdf8" }} name="WTI" isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="px-4 pb-3 grid grid-cols-3 gap-3 border-t border-[#1c1d22] pt-3">
        <div>
          <div className="text-[9px] text-zinc-600 uppercase tracking-wider">Brent C1-C12</div>
          <div className="font-mono text-[13px] text-amber-400">
            <Sourced source="modeled" note={CURVE_NOTE} align="start">{fmtSigned(-bSlope)}</Sourced>
          </div>
          <div className="text-[9px] text-zinc-500">{bSlope >= 0 ? "Backwardation" : "Contango"}</div>
        </div>
        <div>
          <div className="text-[9px] text-zinc-600 uppercase tracking-wider">WTI C1-C12</div>
          <div className="font-mono text-[13px] text-sky-400">
            <Sourced source="modeled" note={CURVE_NOTE} align="start">{fmtSigned(-wSlope)}</Sourced>
          </div>
          <div className="text-[9px] text-zinc-500">{wSlope >= 0 ? "Backwardation" : "Contango"}</div>
        </div>
        <div>
          <div className="text-[9px] text-zinc-600 uppercase tracking-wider">Brent-WTI M1</div>
          <div className="font-mono text-[13px] text-zinc-100">
            <Sourced source="derived" note="Front-month Brent − WTI · from live Yahoo quotes" align="end">${fmt(m1)}</Sourced>
          </div>
          <div className="text-[9px] text-zinc-500">spread</div>
        </div>
      </div>
    </Card>
  );
};
