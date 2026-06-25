import { useState, lazy, Suspense } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Wifi, WifiOff } from "lucide-react";
import { Sidebar } from "./components/layout/Sidebar";
import { TopBar } from "./components/layout/TopBar";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { AlertsProvider } from "./lib/alerts";
import { ToastHost } from "./components/alerts/ToastHost";
import { useLive } from "./lib/useLive";

// Pages are code-split (lazy) so the initial load only ships the Dashboard +
// shared chart vendor; the other views download on first visit.
//
// On a sleeping free host the first chunk fetch after a cold start can time out,
// which would otherwise surface as "Failed to fetch dynamically imported
// module". `lazyRetry` retries the import a few times with backoff (giving the
// instance time to wake) before giving up — so a cold start self-heals.
const lazyRetry = (importer) =>
  lazy(async () => {
    let lastErr;
    for (let attempt = 0; attempt < 4; attempt++) {
      try {
        const mod = await importer();
        sessionStorage.removeItem("chunk-reload"); // a load succeeded → reset the reload guard
        return mod;
      } catch (err) {
        lastErr = err;
        await new Promise((r) => setTimeout(r, 500 * (attempt + 1)));
      }
    }
    throw lastErr;
  });

const PageDashboard = lazyRetry(() => import("./pages/Dashboard").then((m) => ({ default: m.PageDashboard })));
const PageAnalytics = lazyRetry(() => import("./pages/Analytics").then((m) => ({ default: m.PageAnalytics })));
const PageRegime = lazyRetry(() => import("./pages/Regime").then((m) => ({ default: m.PageRegime })));
const PageSignalEngine = lazyRetry(() => import("./pages/SignalEngine").then((m) => ({ default: m.PageSignalEngine })));
const PageHistoricalBacktest = lazyRetry(() => import("./pages/HistoricalBacktest").then((m) => ({ default: m.PageHistoricalBacktest })));
const PageDrivers = lazyRetry(() => import("./pages/Drivers").then((m) => ({ default: m.PageDrivers })));
const PageInventories = lazyRetry(() => import("./pages/Inventories").then((m) => ({ default: m.PageInventories })));
const PageReleaseLab = lazyRetry(() => import("./pages/ReleaseLab").then((m) => ({ default: m.PageReleaseLab })));
const PageNews = lazyRetry(() => import("./pages/News").then((m) => ({ default: m.PageNews })));

const PAGES = {
  dashboard: { title: "Dashboard", el: PageDashboard },
  analytics: { title: "Analytics", el: PageAnalytics },
  regime: { title: "Regime & Signals", el: PageRegime },
  signalengine: { title: "Strategy Backtest", el: PageSignalEngine },
  historical: { title: "Historical Backtest", el: PageHistoricalBacktest },
  drivers: { title: "Market Drivers", el: PageDrivers },
  inventories: { title: "Inventories & Storage", el: PageInventories },
  releaselab: { title: "EIA Release Lab", el: PageReleaseLab },
  news: { title: "News & Sentiment", el: PageNews },
};

// Lightweight loading skeleton shown while a page chunk loads.
const PageSkeleton = () => (
  <div className="space-y-3 animate-pulse">
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-px bg-[#1c1d22]">
      {Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-20 bg-[#0e0f12]" />)}
    </div>
    <div className="grid grid-cols-12 gap-3">
      <div className="col-span-12 lg:col-span-8 h-72 bg-[#0e0f12] border border-[#1c1d22]" />
      <div className="col-span-12 lg:col-span-4 h-72 bg-[#0e0f12] border border-[#1c1d22]" />
    </div>
  </div>
);

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
    <div className="flex h-screen w-full bg-[#08090b] text-zinc-100 overflow-hidden print:h-auto print:overflow-visible print:block" style={{ fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif" }}>
      <Sidebar active={active} setActive={setActive} collapsed={collapsed} setCollapsed={setCollapsed} />

      <div className="flex-1 flex flex-col overflow-hidden print:overflow-visible">
        <TopBar pageTitle={PAGES[active].title} />

        {/* Backend-offline banner — shown only once a health poll has actually failed */}
        {backendDown && (
          <div className="no-print flex items-center gap-2 bg-amber-950/40 border-b border-amber-900/50 px-4 py-1.5 text-[10px] text-amber-300/90">
            <WifiOff size={12} className="flex-shrink-0 text-amber-400" />
            <span>
              Backend offline — every panel is showing <strong className="font-semibold">sample data</strong>, not live feeds. Start the API with{" "}
              <code className="px-1 py-0.5 bg-black/40 border border-amber-900/50 rounded text-amber-200">npm run dev</code>{" "}
              (runs web + API together).
            </span>
          </div>
        )}

        <main className="flex-1 overflow-y-auto p-3 bg-[#08090b] print:overflow-visible print:p-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={active}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.18 }}
            >
              <ErrorBoundary resetKey={active}>
                <Suspense fallback={<PageSkeleton />}>
                  <Page />
                </Suspense>
              </ErrorBoundary>
            </motion.div>
          </AnimatePresence>
        </main>

        {/* Status bar */}
        <footer className="no-print h-6 bg-[#0a0b0e] border-t border-[#1c1d22] flex items-center px-4 gap-4 text-[10px] font-mono text-zinc-500">
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
