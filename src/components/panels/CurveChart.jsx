import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
} from "recharts";
import { ResponsiveContainer } from "../../lib/ResponsiveContainer";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SourceTag } from "../primitives/SourceTag";
import { AsOf } from "../primitives/AsOf";
import { Sourced } from "../primitives/Sourced";
import { FWD_CURVES } from "../../data/mock";
import { chartProps, ChartTooltip } from "../../lib/chart-theme";
import { fmt, fmtSigned } from "../../lib/format";
import { useLive } from "../../lib/useLive";

const DATASET_NOTE = "Live front month (Yahoo) carried along the real forward-curve structure from the historical dataset (M1–M12).";
const MODEL_NOTE = "Front month anchored to the live Yahoo quote; the term structure uses a curated slope (no dataset curve for this instrument).";

// Forward curves carry the live Yahoo front along the REAL term structure from
// the historical dataset (Brent/WTI/HO/Gas Oil): M1 is today's live price and
// M2..M12 preserve the dataset's observed calendar spreads, parallel-shifted
// onto that front — so the level is live while the shape is the real data. RBOB
// (not in the dataset) is the lone live Yahoo dated-contract strip; anything
// without a curve falls back to a modeled slope (flagged via `modeled`).
// Backend: server/compute/markets.js → forwardCurves().
export const CurveChart = () => {
  const { data: curves } = useLive("/api/curves", FWD_CURVES, useLive.REFRESH.slow);
  const brentCurve = curves.brent || FWD_CURVES.brent;
  const wtiCurve = curves.wti || FWD_CURVES.wti;
  const brent = brentCurve.data;
  const wti = wtiCurve.data;
  const data = brent.map((p, i) => ({ m: p.m, brent: p.v, wti: wti[i]?.v }));

  // Real when the backend served a live or dataset-backed curve (modeled === false).
  const real = brentCurve.modeled === false && wtiCurve.modeled === false;
  const src = real ? (brentCurve.source || "dataset") : "modeled";
  const note = real ? (brentCurve.sourceNote || DATASET_NOTE) : MODEL_NOTE;

  const bSlope = brent[0].v - brent.at(-1).v;
  const wSlope = wti[0].v - wti.at(-1).v;
  const m1 = brent[0].v - wti[0].v;

  return (
    <Card padding={false}>
      <div className="p-4 pb-2">
        <SectionTitle sub={src === "yahoo" ? "Front 12 months · live dated contracts" : "Front 12 months · M1 live, structure from dataset"} action={<div className="flex items-center gap-2">
          {real && brentCurve.structureAsOf && <AsOf date={brentCurve.structureAsOf} prefix="structure" />}
          {real
            ? <SourceTag live label={src === "yahoo" ? "Live curve" : "Live + dataset"} source={src} note={note} />
            : <SourceTag modeled label="Modeled curve" source="modeled" note={MODEL_NOTE} />}
        </div>}>Forward Curve Structure</SectionTitle>
      </div>
      <div className="h-48 px-2 pb-2">
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 8, right: 20, bottom: 6, left: 0 }}>
            <CartesianGrid {...chartProps.grid} />
            <XAxis dataKey="m" {...chartProps.axis} />
            <YAxis {...chartProps.axis} domain={["auto", "auto"]} width={40} />
            <Tooltip content={<ChartTooltip unit=" $/bbl" source={src} />} />
            <Line type="monotone" dataKey="brent" stroke="#f59e0b" strokeWidth={1.6} dot={{ r: 2.5, fill: "#f59e0b" }} name="Brent" isAnimationActive={false} />
            <Line type="monotone" dataKey="wti" stroke="#38bdf8" strokeWidth={1.6} dot={{ r: 2.5, fill: "#38bdf8" }} name="WTI" isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="px-4 pb-3 grid grid-cols-3 gap-3 border-t border-[#1c1d22] pt-3">
        <div>
          <div className="text-[9px] text-zinc-600 uppercase tracking-wider">Brent C1-C12</div>
          <div className="font-mono text-[13px] text-amber-400">
            <Sourced source={src} note={note} align="start">{fmtSigned(-bSlope)}</Sourced>
          </div>
          <div className="text-[9px] text-zinc-500">{bSlope >= 0 ? "Backwardation" : "Contango"}</div>
        </div>
        <div>
          <div className="text-[9px] text-zinc-600 uppercase tracking-wider">WTI C1-C12</div>
          <div className="font-mono text-[13px] text-sky-400">
            <Sourced source={src} note={note} align="start">{fmtSigned(-wSlope)}</Sourced>
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
