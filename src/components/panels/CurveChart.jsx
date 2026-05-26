import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { FWD_CURVE } from "../../data/mock";
import { chartProps, ChartTooltip } from "../../lib/chart-theme";

export const CurveChart = () => (
  <Card padding={false}>
    <div className="p-4 pb-2">
      <SectionTitle sub="Front 12 months">Forward Curve Structure</SectionTitle>
    </div>
    <div className="h-48 px-2 pb-2">
      <ResponsiveContainer>
        <LineChart data={FWD_CURVE} margin={{ top: 8, right: 20, bottom: 6, left: 0 }}>
          <CartesianGrid {...chartProps.grid} />
          <XAxis dataKey="m" {...chartProps.axis} />
          <YAxis {...chartProps.axis} domain={["auto", "auto"]} width={40} />
          <Tooltip content={<ChartTooltip unit=" $/bbl" />} />
          <Line type="monotone" dataKey="brent" stroke="#f59e0b" strokeWidth={1.6} dot={{ r: 2.5, fill: "#f59e0b" }} name="Brent" isAnimationActive={false} />
          <Line type="monotone" dataKey="wti" stroke="#38bdf8" strokeWidth={1.6} dot={{ r: 2.5, fill: "#38bdf8" }} name="WTI" isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
    <div className="px-4 pb-3 grid grid-cols-3 gap-3 border-t border-[#1c1d22] pt-3">
      <div>
        <div className="text-[9px] text-zinc-600 uppercase tracking-wider">Brent C1-C12</div>
        <div className="font-mono text-[13px] text-amber-400">-$3.80</div>
        <div className="text-[9px] text-zinc-500">Backwardation</div>
      </div>
      <div>
        <div className="text-[9px] text-zinc-600 uppercase tracking-wider">WTI C1-C12</div>
        <div className="font-mono text-[13px] text-sky-400">-$3.52</div>
        <div className="text-[9px] text-zinc-500">Backwardation</div>
      </div>
      <div>
        <div className="text-[9px] text-zinc-600 uppercase tracking-wider">Spread M1</div>
        <div className="font-mono text-[13px] text-zinc-100">$3.55</div>
        <div className="text-[9px] text-emerald-400">+0.12</div>
      </div>
    </div>
  </Card>
);
