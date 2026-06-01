import { Tooltip } from "./Tooltip";
import { sourceOf, KIND_COLOR } from "../../lib/sources";
import { DASH } from "../../lib/format";

// Wrap any data value so hovering it reveals where the number comes from.
//
//   <Sourced source="yahoo">{fmt(price)}</Sourced>
//   <Sourced source="eia" note="WPSR · WCESTUS1 · weekly">…</Sourced>
//
// If the source kind is "modeled" (no free/open feed and not curated), we do
// NOT render the wrapped value — we show "—" instead of an assumed number. The
// hover still explains why. `note` overrides the default blurb; `align` is
// forwarded to the tooltip for edge-of-card values.
export const Sourced = ({ source, note, align, children, className = "" }) => {
  const s = sourceOf(source);
  const color = KIND_COLOR[s.kind];
  const unavailable = s.kind === "modeled";

  const content = (
    <span className="block">
      <span className="flex items-center gap-1.5 text-[10px] font-semibold text-zinc-100">
        <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />
        {s.label}
        <span className="text-[8px] font-semibold uppercase tracking-wider" style={{ color }}>
          {s.kind}
        </span>
      </span>
      <span className="mt-0.5 block text-[10px] leading-snug text-zinc-400">{note || s.detail}</span>
    </span>
  );

  return (
    <Tooltip content={content} align={align} className={className}>
      {unavailable ? (
        <span className="cursor-help text-zinc-600">{DASH}</span>
      ) : (
        <span className="cursor-help underline decoration-transparent decoration-dotted underline-offset-2 transition-colors hover:decoration-zinc-500">
          {children}
        </span>
      )}
    </Tooltip>
  );
};
