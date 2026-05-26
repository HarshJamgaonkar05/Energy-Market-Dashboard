import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Wifi } from "lucide-react";
import { Sidebar } from "./components/layout/Sidebar";
import { TopBar } from "./components/layout/TopBar";
import { PageDashboard } from "./pages/Dashboard";
import { PageCrude } from "./pages/Crude";
import { PageProducts } from "./pages/Products";
import { PageGas } from "./pages/Gas";
import { PageLng } from "./pages/Lng";
import { PageFreight } from "./pages/Freight";
import { PageMacro } from "./pages/Macro";
import { PageWeather } from "./pages/Weather";
import { PageInventories } from "./pages/Inventories";
import { PageNews } from "./pages/News";
import { PageAnalytics } from "./pages/Analytics";
import { PageAlerts } from "./pages/Alerts";
import { PageSettings } from "./pages/Settings";
import { HERO } from "./data/mock";
import { fmt, fmtSigned } from "./lib/format";

const PAGES = {
  dashboard: { title: "Dashboard", el: PageDashboard },
  crude: { title: "Crude Oil", el: PageCrude },
  products: { title: "Refined Products", el: PageProducts },
  gas: { title: "Natural Gas", el: PageGas },
  lng: { title: "LNG", el: PageLng },
  freight: { title: "Freight & Shipping", el: PageFreight },
  macro: { title: "Macro", el: PageMacro },
  weather: { title: "Weather", el: PageWeather },
  inventories: { title: "Inventories & Storage", el: PageInventories },
  news: { title: "News & Sentiment", el: PageNews },
  analytics: { title: "Analytics Workspace", el: PageAnalytics },
  alerts: { title: "Alerts Center", el: PageAlerts },
  settings: { title: "Settings", el: PageSettings },
};

// ============================================================================
// APP ROOT
// ============================================================================
export default function App() {
  const [active, setActive] = useState("dashboard");
  const [collapsed, setCollapsed] = useState(false);
  const Page = PAGES[active].el;

  return (
    <div className="flex h-screen w-full bg-[#08090b] text-zinc-100 overflow-hidden" style={{ fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif" }}>
      <Sidebar active={active} setActive={setActive} collapsed={collapsed} setCollapsed={setCollapsed} />

      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar pageTitle={PAGES[active].title} />

        {/* Ticker strip */}
        <div className="h-7 bg-[#0a0b0e] border-b border-[#1c1d22] overflow-hidden flex items-center text-[10px] font-mono">
          <motion.div
            animate={{ x: ["0%", "-50%"] }}
            transition={{ duration: 60, ease: "linear", repeat: Infinity }}
            className="flex items-center gap-6 whitespace-nowrap pl-4"
          >
            {[...HERO, ...HERO].map((d, i) => (
              <span key={i} className="flex items-center gap-1.5">
                <span className="text-zinc-500">{d.sym}</span>
                <span className="text-zinc-200">{fmt(d.val, d.val < 10 ? 3 : 2)}</span>
                <span className={d.chg >= 0 ? "text-emerald-400" : "text-red-400"}>
                  {fmtSigned(d.chg)} ({fmtSigned(d.pct)}%)
                </span>
                <span className="text-zinc-700">|</span>
              </span>
            ))}
          </motion.div>
        </div>

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
          <span className="flex items-center gap-1.5"><Wifi size={10} className="text-emerald-500" /> Connected</span>
          <span>Latency 12ms</span>
          <span>API 99.97% · 24h</span>
          <span className="ml-auto">Voltaire Terminal © 2026</span>
          <span className="text-zinc-700">·</span>
          <span>v4.7.2 build 8841</span>
        </footer>
      </div>
    </div>
  );
}
