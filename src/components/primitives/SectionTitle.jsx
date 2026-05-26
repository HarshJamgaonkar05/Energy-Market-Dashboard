import { RefreshCw, Maximize2, MoreHorizontal } from "lucide-react";

export const SectionTitle = ({ children, action, sub }) => (
  <div className="flex items-center justify-between mb-3">
    <div className="flex items-baseline gap-2">
      <h3 className="text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">
        {children}
      </h3>
      {sub && <span className="text-[10px] text-zinc-600">{sub}</span>}
    </div>
    {action || (
      <div className="flex items-center gap-1.5 text-zinc-500">
        <button className="hover:text-zinc-200 transition-colors">
          <RefreshCw size={11} />
        </button>
        <button className="hover:text-zinc-200 transition-colors">
          <Maximize2 size={11} />
        </button>
        <button className="hover:text-zinc-200 transition-colors">
          <MoreHorizontal size={12} />
        </button>
      </div>
    )}
  </div>
);
