import { Fragment } from "react";
import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { SourceTag } from "../primitives/SourceTag";
import { Sourced } from "../primitives/Sourced";
import { CORR_LABELS, CORR_MATRIX } from "../../data/mock";
import { useLive } from "../../lib/useLive";

// 30D rolling correlation computed from live Yahoo daily returns
// (server/compute/markets.js). Gas Oil is proxied from ULSD, so its row tracks
// Heating Oil closely — see the modeled note on the instruments.
export const Heatmap = ({ title = "Correlation Matrix", sub = "30D rolling" }) => {
  const { data, live } = useLive(
    "/api/correlation",
    { labels: CORR_LABELS, matrix: CORR_MATRIX },
    useLive.REFRESH.slow
  );
  const labels = data.labels || CORR_LABELS;
  const matrix = data.matrix || CORR_MATRIX;

  const colorFor = (v) => {
    if (v === 1) return "#1c1d22";
    const intensity = Math.abs(v);
    const a = (Math.round(intensity * 200) / 255).toFixed(2);
    return v >= 0 ? `rgba(16, 185, 129, ${a})` : `rgba(239, 68, 68, ${a})`;
  };
  return (
    <Card>
      {title && <SectionTitle sub={sub} action={<SourceTag live={live} source="derived" note="30-day rolling correlation of daily returns, computed from live Yahoo closes. Gas Oil tracks Heating Oil (proxy)." />}>{title}</SectionTitle>}
      <div className="grid gap-px" style={{ gridTemplateColumns: `52px repeat(${labels.length}, 1fr)` }}>
        <div />
        {labels.map((l) => (
          <div key={l} className="text-[9px] text-zinc-500 uppercase tracking-wider text-center pb-1">
            {l}
          </div>
        ))}
        {matrix.map((row, i) => (
          <Fragment key={`row-${i}`}>
            <div className="text-[9px] text-zinc-500 uppercase tracking-wider flex items-center pr-1.5 justify-end">
              {labels[i]}
            </div>
            {row.map((v, j) => (
              <div
                key={`${i}-${j}`}
                className="aspect-square flex items-center justify-center text-[9px] font-mono text-zinc-100 transition-all hover:ring-1 hover:ring-amber-500/60 cursor-pointer"
                style={{ background: colorFor(v) }}
              >
                <Sourced source="derived" note={`${labels[i]} ↔ ${labels[j]} · 30D return correlation (Yahoo closes)`}>
                  {v.toFixed(2)}
                </Sourced>
              </div>
            ))}
          </Fragment>
        ))}
      </div>
    </Card>
  );
};
