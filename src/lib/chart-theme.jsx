export const chartProps = {
  grid: { stroke: "#1c1d22", strokeDasharray: "3 4" },
  axis: {
    stroke: "#3a3b41",
    tick: {
      fill: "#6b6d75",
      fontSize: 10,
      fontFamily: "ui-monospace, SFMono-Regular, monospace",
    },
  },
};

export const ChartTooltip = ({ active, payload, label, unit = "" }) => {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="bg-[#0a0b0e] border border-[#2a2b31] px-3 py-2 shadow-xl">
      <div className="text-[10px] text-zinc-500 mb-1 font-mono">{label}</div>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center justify-between gap-4 text-[11px]">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5" style={{ background: p.color }} />
            <span className="text-zinc-400">{p.name}</span>
          </div>
          <span className="font-mono text-zinc-100">
            {typeof p.value === "number" ? p.value.toFixed(2) : p.value}
            {unit}
          </span>
        </div>
      ))}
    </div>
  );
};
