import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { CORR_LABELS, CORR_MATRIX } from "../../data/mock";

export const Heatmap = ({ title = "Correlation Matrix", sub = "30D rolling" }) => {
  const colorFor = (v) => {
    if (v === 1) return "#1c1d22";
    const intensity = Math.abs(v);
    const a = (Math.round(intensity * 200) / 255).toFixed(2);
    return v >= 0 ? `rgba(16, 185, 129, ${a})` : `rgba(239, 68, 68, ${a})`;
  };
  return (
    <Card>
      {title && <SectionTitle sub={sub}>{title}</SectionTitle>}
      <div className="grid gap-px" style={{ gridTemplateColumns: `52px repeat(${CORR_LABELS.length}, 1fr)` }}>
        <div />
        {CORR_LABELS.map((l) => (
          <div key={l} className="text-[9px] text-zinc-500 uppercase tracking-wider text-center pb-1">
            {l}
          </div>
        ))}
        {CORR_MATRIX.map((row, i) => (
          <>
            <div key={`l-${i}`} className="text-[9px] text-zinc-500 uppercase tracking-wider flex items-center pr-1.5 justify-end">
              {CORR_LABELS[i]}
            </div>
            {row.map((v, j) => (
              <div
                key={`${i}-${j}`}
                className="aspect-square flex items-center justify-center text-[9px] font-mono text-zinc-100 transition-all hover:ring-1 hover:ring-amber-500/60 cursor-pointer"
                style={{ background: colorFor(v) }}
              >
                {v.toFixed(2)}
              </div>
            ))}
          </>
        ))}
      </div>
    </Card>
  );
};
