import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Zap, Activity, X } from "lucide-react";
import { useAlerts, eventHeadline, eventSub, eventUp } from "../../lib/alerts";

const Toast = ({ t, onDismiss }) => {
  useEffect(() => {
    const id = setTimeout(() => onDismiss(t.id), 7000);
    return () => clearTimeout(id);
  }, [t.id, onDismiss]);

  const up = eventUp(t);
  const auto = t.type === "auto";
  const Icon = auto ? Activity : Zap;
  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 24, scale: 0.98 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 24, scale: 0.98 }}
      transition={{ duration: 0.18 }}
      className="w-72 bg-[#0a0b0e] border border-[#2a2b31] shadow-2xl flex overflow-hidden"
    >
      <div className={`w-0.5 flex-shrink-0 ${up ? "bg-emerald-500" : "bg-red-500"}`} />
      <div className="flex-1 p-2.5">
        <div className="flex items-center gap-1.5 mb-1">
          <Icon size={11} className={auto ? "text-amber-400" : up ? "text-emerald-400" : "text-red-400"} fill={auto ? "none" : "currentColor"} />
          <span className="text-[9px] font-semibold uppercase tracking-[0.14em] text-zinc-400">
            {auto ? "Drastic move" : "Alert triggered"}
          </span>
        </div>
        <div className="text-[11px] text-zinc-100 leading-snug">{eventHeadline(t)}</div>
        <div className="text-[9px] font-mono text-zinc-500 mt-0.5">{eventSub(t)}</div>
      </div>
      <button
        onClick={() => onDismiss(t.id)}
        aria-label="Dismiss"
        className="px-1.5 text-zinc-600 hover:text-zinc-300 transition-colors"
      >
        <X size={12} />
      </button>
    </motion.div>
  );
};

export const ToastHost = () => {
  const alerts = useAlerts();
  if (!alerts) return null;
  return (
    <div className="fixed bottom-5 right-5 z-[60] flex flex-col gap-2 pointer-events-none [&>*]:pointer-events-auto">
      <AnimatePresence initial={false}>
        {alerts.toasts.map((t) => (
          <Toast key={t.id} t={t} onDismiss={alerts.dismissToast} />
        ))}
      </AnimatePresence>
    </div>
  );
};
