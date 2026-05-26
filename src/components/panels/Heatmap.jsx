import { Card } from "../primitives/Card";
import { SectionTitle } from "../primitives/SectionTitle";
import { CORR_LABELS, CORR_MATRIX } from "../../data/mock";

export const Heatmap = () => {
  const colorFor = (v) => {
    if (v === 1) return "#1c1d22";
    const intensity = Math.abs(v);
    if (v >= 0) {
      const a = Math.round(intensity * 200);
      return `rgba(16, 185, 129, ${(a / 255).toFixed(2)})`;
    }
    const a = Math.round(intensity * 200);
    return `rgba(239, 68, 68, ${(a / 255).toFixed(2)})`;
  };
  return (
    <Card>
      <SectionTitle sub="30D rolling">Correlation Matrix</SectionTitle>
      <div className="grid gap-px" style={{ gridTemplateColumns: `40px repeat(${CORR_LABELS.length}, 1fr)` }}>
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
