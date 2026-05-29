// Thin labelled section divider used to split a page into clear divisions.
export const Band = ({ icon: Icon, title, sub, right }) => (
  <div className="flex items-center gap-2.5">
    {Icon && (
      <div className="w-6 h-6 flex items-center justify-center bg-amber-500/10 border border-amber-500/25 flex-shrink-0">
        <Icon size={13} className="text-amber-400" strokeWidth={2} />
      </div>
    )}
    <h2 className="text-[12px] font-semibold tracking-[0.1em] text-zinc-100 uppercase whitespace-nowrap">
      {title}
    </h2>
    {sub && <span className="text-[10px] text-zinc-600 whitespace-nowrap hidden sm:inline">{sub}</span>}
    <div className="flex-1 h-px bg-[#1c1d22] mx-1" />
    {right}
  </div>
);
