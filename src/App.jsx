import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Wifi, WifiOff } from "lucide-react";
import { Sidebar } from "./components/layout/Sidebar";
import { TopBar } from "./components/layout/TopBar";
import { PageDashboard } from "./pages/Dashboard";
import { PageAnalytics } from "./pages/Analytics";
import { PageDrivers } from "./pages/Drivers";
import { PageInventories } from "./pages/Inventories";
import { PageNews } from "./pages/News";
import { AlertsProvider } from "./lib/alerts";
import { ToastHost } from "./components/alerts/ToastHost";
import { useLive } from "./lib/useLive";

const PAGES = {
  dashboard: { title: "Dashboard", el: PageDashboard },
  analytics: { title: "Analytics", el: PageAnalytics },
  drivers: { title: "Market Drivers", el: PageDrivers },
  inventories: { title: "Inventories & Storage", el: PageInventories },
  news: { title: "News & Sentiment", el: PageNews },
};

// ============================================================================
// APP ROOT
// ============================================================================
export default function App() {
  const [active, setActive] = useState("dashboard");
  const [collapsed, setCollapsed] = useState(false);
  const Page = PAGES[active].el;

  // Backend health for the status bar.
  const { data: health, live, stale: healthStale } = useLive("/api/health", { ok: false, eia: false }, useLive.REFRESH.slow);
  // The /api proxy is unreachable (backend not running) → every panel is showing
  // seeded sample data, not live feeds. Make that unmistakable.
  const backendDown = healthStale;

  return (
    <AlertsProvider>
    <div className="flex h-screen w-full bg-[#08090b] text-zinc-100 overflow-hidden" style={{ fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif" }}>
      <Sidebar active={active} setActive={setActive} collapsed={collapsed} setCollapsed={setCollapsed} />

      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar pageTitle={PAGES[active].title} />

        {/* Backend-offline banner — shown only once a health poll has actually failed */}
        {backendDown && (
          <div className="flex items-center gap-2 bg-amber-950/40 border-b border-amber-900/50 px-4 py-1.5 text-[10px] text-amber-300/90">
            <WifiOff size={12} className="flex-shrink-0 text-amber-400" />
            <span>
              Backend offline — every panel is showing <strong className="font-semibold">sample data</strong>, not live feeds. Start the API with{" "}
              <code className="px-1 py-0.5 bg-black/40 border border-amber-900/50 rounded text-amber-200">npm run dev</code>{" "}
              (runs web + API together).
            </span>
          </div>
        )}

        <main className="flex-1 overflow-y-auto p-3 bg-[#08090b]">
          <AnimatePresence mode="wait">
            <motion.div
              key={active}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.18 }}
            >
              <Page />
            </motion.div>
          </AnimatePresence>
        </main>

        {/* Status bar */}
        <footer className="h-6 bg-[#0a0b0e] border-t border-[#1c1d22] flex items-center px-4 gap-4 text-[10px] font-mono text-zinc-500">
          {health.ok ? (
            <span className="flex items-center gap-1.5"><Wifi size={10} className="text-emerald-500" /> {live ? "Live feed" : "Connected"}</span>
          ) : (
            <span className="flex items-center gap-1.5"><WifiOff size={10} className="text-red-500" /> Offline · mock data</span>
          )}
          <span>Yahoo · EIA{health.eia ? " ✓" : " ✗"} · Open-Meteo · Financial Juice</span>
          <span className="hidden md:inline">{health.eia ? "Fundamentals live" : "Fundamentals: add EIA key"}</span>
        </footer>
      </div>
      <ToastHost />
    </div>
    </AlertsProvider>
  );
}
