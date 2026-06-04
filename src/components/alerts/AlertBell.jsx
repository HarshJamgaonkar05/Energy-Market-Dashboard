import { useState, useRef, useEffect } from "react";
import { Bell, Plus, Trash2, Check, Activity } from "lucide-react";
import { useAlerts, eventHeadline, eventSub, eventUp } from "../../lib/alerts";
import { fmt } from "../../lib/format";

const opLabel = (op) => (op === ">" ? "above" : "below");

const timeAgo = (ts) => {
  const s = Math.floor((Date.now() - ts) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
};

// Sensible default for the threshold input given a metric's current value.
const roundForInput = (v) => {
  if (v == null) return "";
  const a = Math.abs(v);
  const dp = a >= 100 ? 0 : a >= 1 ? 2 : 3;
  return String(+v.toFixed(dp));
};

// --- Add-rule form -----------------------------------------------------------
const AddRule = ({ metrics, onAdd, prefill, onPrefillConsumed }) => {
  const [metricId, setMetricId] = useState(metrics[0]?.id || "");
  const [op, setOp] = useState(">");
  const [threshold, setThreshold] = useState("");
  const inputRef = useRef(null);

  const current = metrics.find((m) => m.id === metricId);

  // Adopt the first metric once they load; never leave the select on an empty id.
  useEffect(() => {
    if (!metrics.some((m) => m.id === metricId) && metrics.length) setMetricId(metrics[0].id);
  }, [metrics, metricId]);

  // Pre-fill the threshold with the metric's current value when the metric
  // changes (or first loads) so the user just nudges it — not on every poll.
  useEffect(() => {
    const m = metrics.find((x) => x.id === metricId);
    if (m) setThreshold(roundForInput(m.value));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [metricId, metrics.length]);

  // Quick-add from a price tile: point the form at that metric and focus it.
  useEffect(() => {
    if (!prefill?.metricId) return;
    if (metrics.some((m) => m.id === prefill.metricId)) {
      setMetricId(prefill.metricId);
      setOp(">");
      requestAnimationFrame(() => { inputRef.current?.focus(); inputRef.current?.select(); });
      onPrefillConsumed?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefill]);

  const submit = (e) => {
    e.preventDefault();
    if (!current || threshold === "" || Number.isNaN(Number(threshold))) return;
    onAdd({ metricId, op, threshold, label: current.label, unit: current.unit });
    inputRef.current?.focus();
  };

  if (!metrics.length) {
    return <div className="px-3 py-3 text-[10px] text-zinc-600">Connecting to the live tape — you can add an alert in a moment.</div>;
  }

  const groups = [...new Set(metrics.map((m) => m.group))];

  return (
    <form onSubmit={submit} className="px-3 py-2.5 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-[9px] uppercase tracking-[0.16em] text-zinc-500">New alert</span>
        {current && (
          <span className="text-[9px] font-mono text-zinc-500">now <span className="text-zinc-300">{fmt(current.value)}</span> {current.unit}</span>
        )}
      </div>

      <select
        value={metricId}
        onChange={(e) => setMetricId(e.target.value)}
        className="w-full h-7 bg-[#0e0f12] border border-[#1c1d22] text-[11px] text-zinc-200 px-1.5 focus:border-amber-500/40 outline-none"
      >
        {groups.map((g) => (
          <optgroup key={g} label={g}>
            {metrics.filter((m) => m.group === g).map((m) => (
              <option key={m.id} value={m.id}>{m.label}</option>
            ))}
          </optgroup>
        ))}
      </select>

      <div className="flex items-center gap-2">
        {/* Above / below as a tactile segmented toggle */}
        <div className="flex border border-[#1c1d22] h-7 flex-shrink-0">
          {[">", "<"].map((o) => (
            <button
              key={o}
              type="button"
              onClick={() => setOp(o)}
              className={`px-2 text-[10px] uppercase tracking-wider transition-colors ${
                op === o
                  ? o === ">" ? "bg-emerald-500/15 text-emerald-400" : "bg-red-500/15 text-red-400"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {opLabel(o)}
            </button>
          ))}
        </div>
        <input
          ref={inputRef}
          type="number"
          step="any"
          value={threshold}
          onChange={(e) => setThreshold(e.target.value)}
          placeholder={current ? roundForInput(current.value) : "level"}
          className="flex-1 min-w-0 h-7 bg-[#0e0f12] border border-[#1c1d22] text-[11px] font-mono text-zinc-200 px-2 focus:border-amber-500/40 outline-none"
        />
        <button
          type="submit"
          className="h-7 px-2.5 inline-flex items-center gap-1 bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[10px] uppercase tracking-wider hover:bg-amber-500/20 transition-colors flex-shrink-0"
        >
          <Plus size={11} /> Add
        </button>
      </div>

      {current && (
        <p className="text-[9px] text-zinc-600 leading-snug">
          Notify when <span className="text-zinc-400">{current.label}</span> goes {opLabel(op)}{" "}
          <span className="font-mono text-zinc-400">{threshold || "…"}</span> {current.unit}. Fires once on the cross, then re-arms after it crosses back.
        </p>
      )}
    </form>
  );
};

// --- Bell + dropdown ---------------------------------------------------------
export const AlertBell = () => {
  const alerts = useAlerts();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const onClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  // Quick-add from a tile opens the dropdown (and marks the inbox read).
  useEffect(() => {
    if (alerts?.compose) {
      setOpen(true);
      alerts.markRead();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [alerts?.compose]);

  if (!alerts) return null;
  const {
    rules, events, metricMap, unreadCount, addRule, removeRule, clearEvents, markRead,
    notifPermission, requestNotifications, compose, clearComposer,
    autoOn, sensitivity, autoWatch, toggleAuto, setSensitivity,
  } = alerts;

  const toggle = () => {
    setOpen((o) => {
      if (!o) markRead();
      return !o;
    });
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={toggle}
        aria-label={`Alerts${unreadCount ? ` (${unreadCount} new)` : ""}`}
        aria-expanded={open}
        className={`relative w-7 h-7 flex items-center justify-center border transition-colors ${
          open ? "border-[#2a2b31] bg-white/[0.03] text-zinc-200" : "border-transparent text-zinc-400 hover:text-zinc-200"
        }`}
      >
        <Bell size={15} strokeWidth={1.75} />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[14px] h-[14px] px-0.5 flex items-center justify-center bg-amber-500 text-[8px] font-bold text-zinc-950 rounded-full">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-[344px] bg-[#0a0b0e] border border-[#2a2b31] shadow-2xl z-50">
          <div className="flex items-center justify-between px-3 h-9 border-b border-[#1c1d22]">
            <span className="text-[11px] font-semibold tracking-[0.12em] text-zinc-300 uppercase">Alerts</span>
            {notifPermission === "default" && (
              <button onClick={requestNotifications} className="text-[9px] uppercase tracking-wider text-amber-500/80 hover:text-amber-400">
                Enable notifications
              </button>
            )}
            {notifPermission === "granted" && (
              <span className="text-[9px] uppercase tracking-wider text-emerald-500/70 inline-flex items-center gap-1"><Check size={10} /> Notifications on</span>
            )}
            {notifPermission === "denied" && (
              <span className="text-[9px] uppercase tracking-wider text-zinc-600">Notifications blocked</span>
            )}
          </div>

          {/* Triggered inbox */}
          <div className="max-h-40 overflow-y-auto">
            <div className="flex items-center justify-between px-3 py-1.5 sticky top-0 bg-[#0a0b0e]">
              <span className="text-[9px] uppercase tracking-[0.16em] text-zinc-600">Triggered</span>
              {events.length > 0 && (
                <button onClick={clearEvents} className="text-[9px] uppercase tracking-wider text-zinc-600 hover:text-zinc-400">Clear</button>
              )}
            </div>
            {events.length === 0 ? (
              <div className="px-3 pb-2 text-[10px] text-zinc-600">Nothing has fired yet. Auto-watch flags sudden moves on its own; add a rule for your own levels.</div>
            ) : (
              events.map((e) => {
                const up = eventUp(e);
                return (
                  <div key={e.id} className="flex items-start gap-2 px-3 py-1.5 border-t border-[#15161a]">
                    <span className={`mt-1 w-1.5 h-1.5 rounded-full flex-shrink-0 ${up ? "bg-emerald-500" : "bg-red-500"}`} />
                    <div className="min-w-0 flex-1">
                      <div className="text-[11px] text-zinc-200 flex items-center gap-1.5">
                        {e.type === "auto" && <span className="flex-shrink-0 text-[7px] font-bold uppercase tracking-wider text-amber-400 border border-amber-500/30 px-1 leading-[1.5]">Auto</span>}
                        <span className="truncate">{eventHeadline(e)}</span>
                      </div>
                      <div className="text-[9px] text-zinc-600 font-mono">{eventSub(e)} · {timeAgo(e.at)}</div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Rule manager */}
          <div className="border-t border-[#1c1d22] max-h-40 overflow-y-auto">
            <div className="px-3 py-1.5 text-[9px] uppercase tracking-[0.16em] text-zinc-600 sticky top-0 bg-[#0a0b0e]">
              Active rules · {rules.length}
            </div>
            {rules.length === 0 ? (
              <div className="px-3 pb-2 text-[10px] text-zinc-600">No rules yet.</div>
            ) : (
              rules.map((r) => {
                const cur = metricMap[r.metricId]?.value;
                const gap = cur == null ? null : (r.op === ">" ? r.threshold - cur : cur - r.threshold);
                return (
                  <div key={r.id} className="flex items-center gap-2 px-3 py-1.5 border-t border-[#15161a] group">
                    <span
                      className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${r.armed ? "bg-zinc-600" : "bg-amber-400 animate-pulse"}`}
                      title={r.armed ? "Watching" : "Triggered"}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="text-[11px] text-zinc-300 truncate">
                        {r.label} <span className={r.op === ">" ? "text-emerald-400/80" : "text-red-400/80"}>{opLabel(r.op)}</span>{" "}
                        <span className="font-mono">{fmt(r.threshold)}</span> <span className="text-zinc-600">{r.unit}</span>
                      </div>
                      <div className="text-[9px] font-mono text-zinc-600">
                        {cur == null
                          ? "waiting for data…"
                          : r.armed
                            ? `now ${fmt(cur)} · ${fmt(Math.abs(gap))} to go`
                            : `triggered · now ${fmt(cur)} ${r.unit}`}
                      </div>
                    </div>
                    <button
                      onClick={() => removeRule(r.id)}
                      aria-label="Remove alert"
                      className="text-zinc-700 hover:text-red-400 transition-colors opacity-60 group-hover:opacity-100 flex-shrink-0"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                );
              })
            )}
          </div>

          <div className="border-t border-[#1c1d22]">
            <AddRule metrics={alerts.metrics} onAdd={addRule} prefill={compose} onPrefillConsumed={clearComposer} />
          </div>

          {/* Auto-watch — built-in drastic-move detection on the majors */}
          <div className="border-t border-[#1c1d22] px-3 py-2.5">
            <div className="flex items-center justify-between gap-2">
              <div className="min-w-0">
                <div className="text-[10px] uppercase tracking-wider text-zinc-300 flex items-center gap-1.5">
                  <Activity size={11} className="text-amber-400" /> Auto-watch
                </div>
                <div
                  className="text-[9px] text-zinc-600 mt-0.5 cursor-help"
                  title={autoWatch.map((w) => `${w.label}: ±${w.move}${w.kind === "pct" ? "%" : " " + w.unit}`).join("\n")}
                >
                  Flags sudden moves in {autoWatch.length} majors {autoOn ? "" : "· paused"}
                </div>
              </div>
              <button
                role="switch"
                aria-checked={autoOn}
                aria-label="Toggle auto-watch"
                onClick={toggleAuto}
                className={`relative w-9 h-5 rounded-full transition-colors flex-shrink-0 ${autoOn ? "bg-amber-500/80" : "bg-[#1c1d22] border border-[#2a2b31]"}`}
              >
                <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-zinc-100 transition-all ${autoOn ? "left-[18px]" : "left-0.5"}`} />
              </button>
            </div>
            {autoOn && (
              <div className="mt-2">
                <div className="flex border border-[#1c1d22] h-6">
                  {["relaxed", "normal", "sensitive"].map((s) => (
                    <button
                      key={s}
                      onClick={() => setSensitivity(s)}
                      className={`flex-1 text-[9px] uppercase tracking-wider transition-colors ${
                        sensitivity === s ? "bg-amber-500/15 text-amber-400" : "text-zinc-500 hover:text-zinc-300"
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
                <p className="text-[9px] text-zinc-600 mt-1.5 leading-snug">
                  How big a sudden move (vs ~10 min ago) must be before it flags — each value has its own threshold (hover the line above). Cools down 30 min after a hit.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
