import { HeroCard } from "../components/HeroCard";
import { MultiChart } from "../components/panels/MultiChart";
import { Heatmap } from "../components/panels/Heatmap";
import { CurveChart } from "../components/panels/CurveChart";
import { MoversPanel } from "../components/panels/MoversPanel";
import { NewsPanel } from "../components/panels/NewsPanel";
import { SentimentPanel } from "../components/panels/SentimentPanel";
import { EconCalendar } from "../components/panels/EconCalendar";
import { AlertsSummary } from "../components/panels/AlertsSummary";
import { InventorySnap } from "../components/panels/InventorySnap";
import { ShippingPanel } from "../components/panels/ShippingPanel";
import { PipelinePanel } from "../components/panels/PipelinePanel";
import { WeatherRisk } from "../components/panels/WeatherRisk";
import { HERO } from "../data/mock";

export const PageDashboard = () => (
  <div className="space-y-3">
    {/* Hero row */}
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-px bg-[#1c1d22]">
      {HERO.map((d) => (
        <HeroCard key={d.sym} d={d} />
      ))}
    </div>

    {/* Main grid */}
    <div className="grid grid-cols-12 gap-3">
      {/* Left + center */}
      <div className="col-span-12 lg:col-span-8 space-y-3">
        <MultiChart />
        <div className="grid grid-cols-2 gap-3">
          <CurveChart />
          <Heatmap />
        </div>
        <MoversPanel />
      </div>

      {/* Right rail */}
      <div className="col-span-12 lg:col-span-4 space-y-3">
        <NewsPanel compact />
        <SentimentPanel />
        <EconCalendar />
        <AlertsSummary />
      </div>
    </div>

    {/* Bottom row */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
      <InventorySnap />
      <WeatherRisk />
      <ShippingPanel />
      <PipelinePanel />
    </div>
  </div>
);
