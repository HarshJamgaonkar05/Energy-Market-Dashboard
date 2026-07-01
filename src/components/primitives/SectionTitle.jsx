// Panel header. `action` (a SourceTag, control, etc.) renders on the right when
// provided; when omitted we render nothing there — no decorative buttons that
// imply refresh/expand/more actions the app doesn't actually wire up.
export const SectionTitle = ({ children, action, sub }) => (
  <div className="flex items-center justify-between mb-3">
    <div className="flex items-baseline gap-2">
      <h3 className="text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">
        {children}
      </h3>
      {sub && <span className="text-[10px] text-zinc-600">{sub}</span>}
    </div>
    {action || null}
  </div>
);
