import { Info } from "lucide-react";
import { Tooltip } from "./Tooltip";

// A subtle inline "what is this?" affordance: a tiny info icon that reveals a
// short plain-English explanation on hover/focus. Used to explain dashboard
// metrics and jargon without adding visible body text. Pass an optional `title`
// for a bold lead line above the explanation.
//
//   <InfoDot text="Week-over-week change. Negative = draw (bullish)." />
export const InfoDot = ({ text, title, align = "center", size = 11, className = "" }) => {
  if (!text) return null;
  const content = (
    <span className="block">
      {title && <span className="mb-0.5 block text-[10px] font-semibold text-zinc-100">{title}</span>}
      <span className="block text-[10px] leading-snug text-zinc-400">{text}</span>
    </span>
  );
  return (
    <Tooltip content={content} align={align} className={`cursor-help align-middle ${className}`}>
      <Info size={size} strokeWidth={2} className="text-zinc-600 hover:text-zinc-300 transition-colors" />
    </Tooltip>
  );
};
