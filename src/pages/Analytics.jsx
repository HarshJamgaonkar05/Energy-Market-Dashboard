import { useState } from "react";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { Layers, GitBranch, Plus, Maximize2, MoreHorizontal } from "lucide-react";
import { Heatmap } from "../components/panels/Heatmap";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { Badge } from "../components/primitives/Badge";
import { chartProps, ChartTooltip } from "../lib/chart-theme";
import { genSeries, seededRand } from "../data/mock";

export const PageAnalytics = () => {
  const [layout, setLayout] = useState("quad");
  return (
    <div className="space-y-3">
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-[13px] font-semibold text-zinc-100">Quant Workspace</h2>
            <p className="text-[10px] text-zinc-500 mt-0.5">Drag, resize, save layouts · Default workspace: Crude / Gas / Spreads</p>
          </div>
          <div className="flex items-center gap-2">
            {["single", "dual", "quad", "grid"].map((l) => (
              <button
                key={l}
                onClick={() => setLayout(l)}
                className={`px-2 h-7 text-[10px] font-mono uppercase ${
                  layout === l ? "bg-amber-500/10 text-amber-400 border border-amber-500/30" : "text-zinc-500 border border-transparent hover:text-zinc-200"
                }`}
              >
                {l}
              </button>
            ))}
            <button className="h-7 px-3 text-[10px] uppercase tracking-wider bg-amber-500 text-zinc-950 font-semibold hover:bg-amber-400">
              <Plus size={11} className="inline mr-1" /> Add Panel
            </button>
          </div>
        </div>
      </Card>

      <div className={`grid gap-3 ${layout === "single" ? "grid-cols-1" : layout === "dual" ? "grid-cols-2" : "grid-cols-2 lg:grid-cols-2"}`}>
        <Card padding={false}>
          <div className="p-3 flex items-center justify-between border-b border-[#1c1d22]">
            <span className="text-[10px] font-mono tracking-wider text-zinc-300">BRENT · M1</span>
            <div className="flex gap-1 text-zinc-600">
              <button className="hover:text-zinc-200"><Maximize2 size={11} /></button>
              <button className="hover:text-zinc-200"><MoreHorizontal size={12} /></button>
            </div>
          </div>
          <div className="h-60 p-2">
            <ResponsiveContainer>
              <LineChart data={genSeries(101, 60, 82, 2)}>
                <CartesianGrid {...chartProps.grid} />
                <XAxis dataKey="t" {...chartProps.axis} />
                <YAxis {...chartProps.axis} width={40} />
                <Tooltip content={<ChartTooltip />} />
                <Line type="monotone" dataKey="v" stroke="#f59e0b" strokeWidth={1.4} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card padding={false}>
          <div className="p-3 flex items-center justify-between border-b border-[#1c1d22]">
            <span className="text-[10px] font-mono tracking-wider text-zinc-300">BRENT-WTI SPREAD</span>
            <div className="flex gap-1 text-zinc-600">
              <button className="hover:text-zinc-200"><Maximize2 size={11} /></button>
              <button className="hover:text-zinc-200"><MoreHorizontal size={12} /></button>
            </div>
          </div>
          <div className="h-60 p-2">
            <ResponsiveContainer>
              <AreaChart data={Array.from({ length: 60 }, (_, i) => ({ t: i, v: 3 + Math.sin(i / 7) * 1.2 + Math.random() * 0.6 }))}>
                <defs>
                  <linearGradient id="ws" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#38bdf8" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid {...chartProps.grid} />
                <XAxis dataKey="t" {...chartProps.axis} />
                <YAxis {...chartProps.axis} width={36} />
                <Tooltip content={<ChartTooltip />} />
                <Area type="monotone" dataKey="v" stroke="#38bdf8" fill="url(#ws)" strokeWidth={1.4} isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card padding={false}>
          <div className="p-3 flex items-center justify-between border-b border-[#1c1d22]">
            <span className="text-[10px] font-mono tracking-wider text-zinc-300">REALIZED VOL · 30D</span>
            <div className="flex gap-1 text-zinc-600">
              <button className="hover:text-zinc-200"><Maximize2 size={11} /></button>
              <button className="hover:text-zinc-200"><MoreHorizontal size={12} /></button>
            </div>
          </div>
          <div className="h-60 p-2">
            <ResponsiveContainer>
              <BarChart data={Array.from({ length: 30 }, (_, i) => ({ t: i, v: 18 + Math.sin(i / 4) * 6 + Math.random() * 3 }))}>
                <CartesianGrid {...chartProps.grid} />
                <XAxis dataKey="t" {...chartProps.axis} />
                <YAxis {...chartProps.axis} width={36} />
                <Tooltip content={<ChartTooltip unit="%" />} />
                <Bar dataKey="v" fill="#10b981" fillOpacity={0.7} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card padding={false}>
          <div className="p-3 flex items-center justify-between border-b border-[#1c1d22]">
            <span className="text-[10px] font-mono tracking-wider text-zinc-300">CORR EXPLORER</span>
            <div className="flex gap-1 text-zinc-600">
              <button className="hover:text-zinc-200"><Maximize2 size={11} /></button>
              <button className="hover:text-zinc-200"><MoreHorizontal size={12} /></button>
            </div>
          </div>
          <div className="p-4">
            <Heatmap />
          </div>
        </Card>
      </div>

      <Card>
        <SectionTitle>Strategy Notes</SectionTitle>
        <textarea
          defaultValue={"WTI-Brent at -$3.55. Watch for narrowing into USGC SPR refilling.\nLNG JKM-TTF arbitrage closed — flows redirecting Atlantic basin.\nFreight (TD3C) elevated, possible drag on Asian crude differentials."}
          className="w-full bg-[#0a0b0e] border border-[#1c1d22] focus:border-[#2a2b31] outline-none p-3 text-[11px] text-zinc-300 font-mono leading-relaxed resize-none"
          rows={5}
        />
      </Card>
    </div>
  );
};
