import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import { useLive } from "./useLive";
import { fmt } from "./format";

// ============================================================================
// Alerts — turn the passive terminal into something that watches FOR you.
//
// Two kinds of alert share one inbox / toast / notification path:
//   • RULES   — user-defined thresholds on any live metric (price, crack, curve
//               slope, daily %). Edge-triggered: fires once when the value first
//               crosses, re-arms only after it crosses back.
//   • AUTO    — a built-in "drastic move" watch on the major values, on by
//               default. Each metric has its OWN sense of "drastic" (crude ~1.5%,
//               products swing more, the crack is absolute $/bbl); a move beyond
//               that vs ~10 min ago fires once, then the metric cools down so a
//               sustained move doesn't spam. A global sensitivity scales them all.
//
// Everything persists to localStorage; no backend/account needed.
// ============================================================================

const RULES_KEY = "voltaire.alerts.rules";
const EVENTS_KEY = "voltaire.alerts.events";
const SEEN_KEY = "voltaire.alerts.seenAt";
const AUTO_KEY = "voltaire.alerts.autoOn";
const SENS_KEY = "voltaire.alerts.sens";

const load = (key, fallback) => {
  try {
    const raw = localStorage.getItem(key);
    return raw == null ? fallback : JSON.parse(raw);
  } catch {
    return fallback;
  }
};
const save = (key, val) => {
  try {
    localStorage.setItem(key, JSON.stringify(val));
  } catch {
    /* quota / private mode — alerts just won't persist */
  }
};

// Short, friendly instrument names for alert labels.
const NICE = { BRENT: "Brent", WTI: "WTI", HO: "Heating Oil", RBOB: "RBOB", GASOIL: "Gas Oil" };

// Auto-watch config — the "majors" and each one's own "drastic" threshold.
// `kind:"pct"` = % move vs ~10 min ago (level-independent); `kind:"abs"` = move
// in the metric's own unit. Products (HO/RBOB) swing more than crude, so their
// thresholds are looser; the 3:2:1 refining crack is watched in absolute $/bbl.
const AUTO_WATCH = {
  "px:BRENT": { kind: "pct", move: 1.5 },
  "px:WTI": { kind: "pct", move: 1.5 },
  "px:HO": { kind: "pct", move: 1.8 },
  "px:RBOB": { kind: "pct", move: 2.2 },
  "px:GASOIL": { kind: "pct", move: 1.8 },
  "crk:321-wti": { kind: "abs", move: 2.5 },
};
// Sensitivity scales every auto threshold (lower multiplier = fires more readily).
export const SENS = { relaxed: 1.6, normal: 1, sensitive: 0.6 };
const AUTO_WINDOW_MS = 10 * 60_000; // look-back for "how much has it moved"
const AUTO_COOLDOWN_MS = 30 * 60_000; // per-metric quiet period after a fire

// Flatten the live feeds into a flat list of alertable metrics. Each carries its
// current value so the UI can show it and the engine can test against it.
function buildMetrics(instruments, cracks, curves) {
  const out = [];
  for (const d of instruments || []) {
    const nm = NICE[d?.sym] || d?.name || d?.sym;
    if (d?.val != null) out.push({ id: `px:${d.sym}`, label: nm, group: "Price", unit: d.unit || "$", value: d.val });
    if (d?.pct != null) out.push({ id: `chg:${d.sym}`, label: `${nm} daily %`, group: "Daily move", unit: "%", value: d.pct });
  }
  for (const c of cracks || []) {
    if (c?.value == null) continue;
    out.push({ id: `crk:${c.id}`, label: c.vs ? `${c.label} vs ${c.vs}` : c.label, group: "Cracks", unit: "$/bbl", value: c.value });
  }
  const slope = (c, name) => {
    if (!c?.data || c.data.length < 12) return;
    out.push({ id: `curve:${name}`, label: `${name.toUpperCase()} M1–M12 slope`, group: "Curve structure", unit: "$/bbl", value: +(c.data[0].v - c.data[11].v).toFixed(2) });
  };
  slope(curves?.brent, "brent");
  slope(curves?.wti, "wti");
  return out;
}

// --- shared event formatting (used by the inbox + toasts) -------------------
const sign = (n) => (n >= 0 ? "+" : "");
export const eventUp = (e) => (e.type === "auto" ? e.dir === "up" : e.op === ">");
export const eventHeadline = (e) =>
  e.type === "auto"
    ? `${e.label} ${e.dir === "up" ? "jumped" : "dropped"} ${e.kind === "pct" ? `${sign(e.movePct)}${fmt(e.movePct)}%` : `${sign(e.moveAbs)}${fmt(e.moveAbs)}`}`
    : `${e.label} ${e.op === ">" ? "above" : "below"} ${fmt(e.threshold)}`;
export const eventSub = (e) =>
  e.type === "auto" ? `${fmt(e.from)} → ${fmt(e.to)} ${e.unit} · ${e.windowMin}m` : `hit ${fmt(e.value)} ${e.unit}`;

const AlertsContext = createContext(null);
export const useAlerts = () => useContext(AlertsContext);

let _id = 0;
const uid = () => `${Date.now().toString(36)}-${(_id++).toString(36)}`;

export function AlertsProvider({ children }) {
  const [rules, setRules] = useState(() => load(RULES_KEY, []));
  const [events, setEvents] = useState(() => load(EVENTS_KEY, []));
  const [seenAt, setSeenAt] = useState(() => load(SEEN_KEY, 0));
  const [toasts, setToasts] = useState([]);
  const [compose, setCompose] = useState(null); // {metricId} pending in the add form
  const [autoOn, setAutoOn] = useState(() => load(AUTO_KEY, true));
  const [sensitivity, setSensitivity] = useState(() => load(SENS_KEY, "normal"));
  const [notifPermission, setNotifPermission] = useState(
    typeof Notification !== "undefined" ? Notification.permission : "unsupported"
  );

  // Poll the feeds alerts can fire on (cached server-side, so this is cheap).
  const { data: instruments } = useLive("/api/instruments", []);
  const { data: cracks } = useLive("/api/cracks", []);
  const { data: curves } = useLive("/api/curves", {}, useLive.REFRESH.slow);

  const metrics = useMemo(() => buildMetrics(instruments, cracks, curves), [instruments, cracks, curves]);
  const metricMap = useMemo(() => Object.fromEntries(metrics.map((m) => [m.id, m])), [metrics]);

  // Rolling per-metric history + cooldowns for auto-watch (don't need re-render).
  const histRef = useRef({});
  const coolRef = useRef({});
  const autoOnRef = useRef(autoOn);
  autoOnRef.current = autoOn;
  const sensRef = useRef(sensitivity);
  sensRef.current = sensitivity;

  useEffect(() => save(RULES_KEY, rules), [rules]);
  useEffect(() => save(EVENTS_KEY, events), [events]);
  useEffect(() => save(SEEN_KEY, seenAt), [seenAt]);
  useEffect(() => save(AUTO_KEY, autoOn), [autoOn]);
  useEffect(() => save(SENS_KEY, sensitivity), [sensitivity]);

  // Push fired events into the inbox + toasts + browser notifications.
  const fireEvents = (fired) => {
    if (!fired.length) return;
    setEvents((prev) => [...fired, ...prev].slice(0, 50));
    setToasts((prev) => [...prev, ...fired].slice(-5));
    if (typeof Notification !== "undefined" && Notification.permission === "granted") {
      for (const e of fired) {
        try {
          // eslint-disable-next-line no-new
          new Notification(`⚡ ${eventHeadline(e)}`, { body: eventSub(e), tag: e.metricId || e.ruleId });
        } catch {
          /* notifications best-effort */
        }
      }
    }
  };

  // RULES — edge-triggered evaluation on every metric/rules change.
  useEffect(() => {
    if (!rules.length || !metrics.length) return;
    const fired = [];
    let changed = false;
    const next = rules.map((r) => {
      const m = metricMap[r.metricId];
      if (!m || m.value == null) return r;
      const sat = r.op === ">" ? m.value > r.threshold : m.value < r.threshold;
      if (sat && r.armed) {
        changed = true;
        fired.push({ id: uid(), type: "rule", ruleId: r.id, label: m.label, op: r.op, threshold: r.threshold, value: m.value, unit: r.unit, at: Date.now() });
        return { ...r, armed: false };
      }
      if (!sat && !r.armed) {
        changed = true;
        return { ...r, armed: true };
      }
      return r;
    });
    fireEvents(fired);
    if (changed) setRules(next);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [metricMap, rules]);

  // AUTO — drastic-move watch on the majors. Runs once per poll (metricMap id).
  useEffect(() => {
    if (!autoOnRef.current || !metrics.length) return;
    const now = Date.now();
    const mult = SENS[sensRef.current] ?? 1;
    const fired = [];
    for (const [mid, cfg] of Object.entries(AUTO_WATCH)) {
      const m = metricMap[mid];
      if (!m || m.value == null) continue;
      const buf = (histRef.current[mid] ||= []);
      buf.push({ t: now, v: m.value });
      while (buf.length && buf[0].t < now - AUTO_WINDOW_MS) buf.shift();
      if (buf.length < 2 || (coolRef.current[mid] || 0) > now) continue;
      const base = buf[0].v;
      if (!base) continue;
      const moveAbs = m.value - base;
      const movePct = (moveAbs / Math.abs(base)) * 100;
      const measure = cfg.kind === "pct" ? movePct : moveAbs;
      if (Math.abs(measure) >= cfg.move * mult) {
        coolRef.current[mid] = now + AUTO_COOLDOWN_MS;
        fired.push({
          id: uid(), type: "auto", metricId: mid, label: m.label, dir: measure >= 0 ? "up" : "down",
          kind: cfg.kind, movePct: +movePct.toFixed(2), moveAbs: +moveAbs.toFixed(2),
          from: base, to: m.value, unit: m.unit, windowMin: Math.max(1, Math.round((now - buf[0].t) / 60_000)), at: now,
        });
      }
    }
    fireEvents(fired);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [metricMap]);

  const requestNotifications = async () => {
    if (typeof Notification === "undefined") return "unsupported";
    if (Notification.permission !== "default") return Notification.permission;
    const p = await Notification.requestPermission();
    setNotifPermission(p);
    return p;
  };

  const addRule = ({ metricId, op, threshold, label, unit }) => {
    setRules((prev) => [...prev, { id: uid(), metricId, op, threshold: Number(threshold), label, unit, armed: true, createdAt: Date.now() }]);
    if (notifPermission === "default") requestNotifications();
  };
  const removeRule = (id) => setRules((prev) => prev.filter((r) => r.id !== id));
  const clearEvents = () => setEvents([]);
  const markRead = () => setSeenAt(Date.now());
  const dismissToast = (id) => setToasts((prev) => prev.filter((t) => t.id !== id));
  const openComposer = (metricId) => setCompose({ metricId, at: Date.now() });
  const clearComposer = () => setCompose(null);
  const toggleAuto = () => {
    setAutoOn((v) => !v);
    if (notifPermission === "default") requestNotifications();
  };

  // Effective auto-watch thresholds (after sensitivity) for the settings UI.
  const autoWatch = useMemo(
    () => Object.entries(AUTO_WATCH).map(([id, cfg]) => {
      const m = metricMap[id];
      return { id, label: m?.label || id, kind: cfg.kind, move: +(cfg.move * (SENS[sensitivity] ?? 1)).toFixed(2), unit: cfg.kind === "pct" ? "%" : m?.unit || "$/bbl" };
    }),
    [metricMap, sensitivity]
  );

  const unreadCount = useMemo(() => events.filter((e) => e.at > seenAt).length, [events, seenAt]);

  const value = {
    rules, metrics, metricMap, events, toasts, compose,
    unreadCount, notifPermission,
    autoOn, sensitivity, autoWatch,
    addRule, removeRule, clearEvents, markRead, dismissToast, requestNotifications,
    openComposer, clearComposer, toggleAuto, setSensitivity,
  };

  return <AlertsContext.Provider value={value}>{children}</AlertsContext.Provider>;
}
