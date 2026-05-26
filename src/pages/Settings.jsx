import { User, Globe, Bell, Eye, Circle } from "lucide-react";
import { Card } from "../components/primitives/Card";
import { SectionTitle } from "../components/primitives/SectionTitle";
import { Badge } from "../components/primitives/Badge";

export const PageSettings = () => (
  <div className="space-y-3 max-w-4xl">
    <Card>
      <SectionTitle>Account</SectionTitle>
      <div className="grid grid-cols-2 gap-4 mt-2">
        <div>
          <label className="text-[10px] text-zinc-500 uppercase tracking-wider">Name</label>
          <input defaultValue="Kavya Mehra" className="mt-1 w-full bg-[#0a0b0e] border border-[#1c1d22] focus:border-[#2a2b31] outline-none px-2 h-8 text-[12px] text-zinc-200" />
        </div>
        <div>
          <label className="text-[10px] text-zinc-500 uppercase tracking-wider">Desk</label>
          <input defaultValue="Energy Desk · Mumbai" className="mt-1 w-full bg-[#0a0b0e] border border-[#1c1d22] focus:border-[#2a2b31] outline-none px-2 h-8 text-[12px] text-zinc-200" />
        </div>
      </div>
    </Card>

    <Card>
      <SectionTitle>Display</SectionTitle>
      <div className="space-y-3 mt-2">
        {[
          { l: "Theme", o: ["Dark", "Light", "Auto"], v: "Dark" },
          { l: "Density", o: ["Compact", "Comfortable"], v: "Compact" },
          { l: "Accent", o: ["Amber", "Cyan", "Emerald"], v: "Amber" },
          { l: "Time Zone", o: ["UTC", "Local", "Exchange"], v: "UTC" },
        ].map((s) => (
          <div key={s.l} className="flex items-center justify-between py-2 border-b border-[#15161a] last:border-0">
            <span className="text-[12px] text-zinc-300">{s.l}</span>
            <div className="flex">
              {s.o.map((o) => (
                <button key={o} className={`px-3 h-7 text-[10px] uppercase tracking-wider border ${
                  o === s.v ? "bg-amber-500/10 text-amber-400 border-amber-500/30" : "text-zinc-500 border-[#1c1d22] hover:text-zinc-200"
                }`}>{o}</button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>

    <Card>
      <SectionTitle>Data Sources</SectionTitle>
      <div className="space-y-2 mt-2">
        {[
          { n: "ICE Futures", s: "connected", lat: "12ms" },
          { n: "NYMEX / CME", s: "connected", lat: "18ms" },
          { n: "Platts Real-Time", s: "connected", lat: "84ms" },
          { n: "EIA STEO", s: "scheduled", lat: "weekly" },
          { n: "Bloomberg B-PIPE", s: "disconnected", lat: "—" },
        ].map((d) => (
          <div key={d.n} className="flex items-center justify-between py-2 border-b border-[#15161a] last:border-0">
            <div className="flex items-center gap-2">
              <Circle size={6} fill={d.s === "connected" ? "#10b981" : d.s === "scheduled" ? "#f59e0b" : "#6b7280"} className={d.s === "connected" ? "animate-pulse" : ""} />
              <span className="text-[12px] text-zinc-300">{d.n}</span>
            </div>
            <div className="flex items-center gap-3 text-[10px] text-zinc-500">
              <span className="font-mono">{d.lat}</span>
              <button className="text-amber-400 hover:text-amber-300 uppercase tracking-wider">Configure</button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  </div>
);
