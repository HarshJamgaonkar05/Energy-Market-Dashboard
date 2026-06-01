# VOLTAIRE Terminal

Institutional-grade Energy Markets Intelligence Dashboard, wired to **live, free, open data sources** through a lightweight Node backend.

Inspired by Bloomberg Terminal, Kpler, TradingView, Vortexa, and Refinitiv. Dark institutional aesthetic, dense information layout, monospaced data cells, market-tone color signaling (bull green / bear red / amber accent).

> **Where does every number come from?** See **[Explanation.md](Explanation.md)** — an exhaustive, value-by-value account of how each data source is collected and how every figure is calculated, normalized, or inferred (and why some show "—").

## Prerequisites

- **Node.js 18+** (check with `node -v`)
- **npm** (ships with Node) or **pnpm** / **yarn** if you prefer

## Quick start

```bash
npm install                       # use --legacy-peer-deps if npm complains about the vite peer range
cp server/.env.example server/.env   # then paste your free EIA key (optional, see below)
npm run dev                       # starts Vite (5173) + the data backend (3001) together
```

Open **http://localhost:5173**. The Vite dev server proxies `/api/*` to the backend, so there's one origin and no CORS setup.

> **Run both.** `npm run dev` now launches the frontend **and** the data backend together. If you only run the frontend (`npm run dev:web`) without the backend, every panel silently falls back to seeded **sample data** (a banner warns you), so prices look frozen — that just means the API on port 3001 isn't running.

Everything works **without any API key** (live prices, macro, weather, news, etc.). One free key unlocks the US fundamentals panels — see [Live data & sources](#live-data--sources).

## Available scripts

| Command           | What it does                                              |
| ----------------- | --------------------------------------------------------- |
| `npm run dev`     | **Frontend + backend together** (recommended) with reload |
| `npm run dev:web` | Vite dev server only (frontend; API panels show samples)  |
| `npm run dev:api` | Node/Express data backend only, on port 3001              |
| `npm run server`  | Alias for the backend (`dev:api`)                         |
| `npm run dev:all` | Alias for `npm run dev`                                    |
| `npm run build`   | Production build into `dist/`                             |
| `npm run preview` | Serve the production build locally to verify              |

## Live data & sources

The backend (`server/`) fetches from free/open sources, caches them with sensible TTLs, computes the derived datasets (cracks, correlation, normalized series, sentiment), and serves everything under `/api/*`. The frontend polls via a small `useLive()` hook (`src/lib/useLive.js`) and **falls back to the seeded mock data** in `src/data/mock.js` whenever a source is unavailable — so the UI never blanks out.

| Data | Source | Key? |
| --- | --- | --- |
| WTI · Brent · Heating Oil · RBOB live prices, sparklines, movers, ticker | **Yahoo Finance** chart API (`CL=F, BZ=F, HO=F, RB=F`) | none |
| Normalized 90D price action + 30D correlation matrix | Yahoo daily history → computed | none |
| Crack spreads, inter-commodity spreads | Computed from live product/crude prices | none |
| Macro: S&P 500, VIX, 10Y yield, Dollar Index | Yahoo (`^GSPC, ^VIX, ^TNX, DX-Y.NYB`) | none |
| Temperature forecast, heating/cooling degree-days, regional anomaly | **Open-Meteo** | none |
| Financial newswire (tagged + severity-classified) | **Financial Juice** RSS | none |
| Economic calendar | Derived from the real US release cadence (EIA/API/Baker Hughes) | none |
| Sentiment | Computed from price momentum + news bull/bear balance | none |
| US inventories (crude/Cushing/SPR/gasoline/distillate), PADD, 52W history, refinery utilization, weekly builds/draws | **EIA Open Data API v2** | **free key** |
| OPEC production (aggregate) | EIA STEO (quotas are curated policy targets) | free key |

### EIA key (optional but recommended)

Register a free key (instant) at **https://www.eia.gov/opendata/register.php**, then put it in `server/.env`:

```
EIA_API_KEY=your_key_here
```

Without it, the inventory / refinery / stock-flow / OPEC panels show seeded fallback data and the status bar reads *"Fundamentals: add EIA key"*. With it, they go live automatically.

### Modeled / indicative data (no free source exists)

These are paywalled in the real world, so they're **modeled and clearly tagged** in the UI (amber "Modeled" / "Indicative" labels):

- **Forward curves M1–M12** — front month anchored to the live quote; term-structure slope is curated.
- **Tanker rates (VLCC/Suezmax/Aframax), Baltic Dry, port congestion** — Baltic Exchange & AIS feeds are paid.
- **Weekly rig count** — Baker Hughes publishes spreadsheets only (no API).
- **Gas Oil** — no free ICE Gas Oil feed, so it's proxied from NYMEX ULSD (both middle distillates) and marked with a `~`. As a consequence its correlation/normalized line tracks Heating Oil closely.
- **Storm tracker, global storage utilization, ENSO index** — illustrative.

## Project structure

```
voltaire-terminal/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── public/
│   └── favicon.svg
└── src/
    ├── main.jsx                       # ReactDOM root
    ├── App.jsx                        # Shell: sidebar + topbar + ticker + page router
    ├── index.css                      # Tailwind layers + global styles
    │
    ├── lib/
    │   ├── tokens.js                  # Design tokens (color constants)
    │   ├── format.js                  # fmt, fmtSigned number formatters
    │   └── chart-theme.jsx            # Recharts theme + custom ChartTooltip
    │
    ├── data/
    │   └── mock.js                    # Seeded mock data + generators
    │
    ├── components/
    │   ├── HeroCard.jsx               # Headline metric tile with sparkline
    │   ├── primitives/
    │   │   ├── Card.jsx
    │   │   ├── SectionTitle.jsx
    │   │   ├── Badge.jsx
    │   │   └── Delta.jsx
    │   ├── layout/
    │   │   ├── Sidebar.jsx            # Collapsible nav (13 pages)
    │   │   └── TopBar.jsx             # Search, market status, watchlist, clock
    │   └── panels/
    │       ├── MultiChart.jsx
    │       ├── Heatmap.jsx            # Correlation matrix
    │       ├── CurveChart.jsx         # Forward curves
    │       ├── MoversPanel.jsx
    │       ├── NewsPanel.jsx
    │       ├── SentimentPanel.jsx
    │       ├── EconCalendar.jsx
    │       ├── AlertsSummary.jsx
    │       ├── InventorySnap.jsx
    │       ├── ShippingPanel.jsx
    │       ├── PipelinePanel.jsx
    │       └── WeatherRisk.jsx
    │
    └── pages/
        ├── Dashboard.jsx              # Overview (heroes + 12-col grid)
        ├── Crude.jsx                  # WTI/Brent w/ SVG candlesticks
        ├── Products.jsx               # Refined products
        ├── Gas.jsx                    # Henry Hub / TTF / EU storage
        ├── Lng.jsx                    # JKM + vessel tracking
        ├── Freight.jsx                # Tanker rates + route congestion map
        ├── Macro.jsx                  # DXY / SPX / VIX / yields
        ├── Weather.jsx                # Temp forecast + anomaly heatmap
        ├── Inventories.jsx            # 52W stocks + PADD breakdown
        ├── News.jsx                   # Filterable newswire
        ├── Analytics.jsx              # 4-panel custom workspace
        ├── Alerts.jsx                 # Alert rules + history
        └── Settings.jsx
```

## Tech stack

- **React 18** + **Vite 5** (JSX, fast HMR)
- **Tailwind CSS 3** for styling (utility-first, arbitrary-value friendly)
- **Recharts** for charting (Area, Line, Bar, Composed, Scatter, with custom theming)
- **Framer Motion** for transitions (page transitions, ticker animation, sidebar collapse)
- **Lucide React** for icons

The Node backend lives in `server/` (Express, ESM, zero build step):

```
server/
├── index.js              # Express app + /api/* routes
├── .env.example          # EIA_API_KEY + PORT
├── lib/cache.js          # TTL cache + resilient fetch helpers
├── sources/
│   ├── yahoo.js          # live quotes + history
│   ├── eia.js            # US fundamentals (key)
│   ├── openmeteo.js      # weather / degree-days
│   └── financialjuice.js # financial newswire (RSS)
└── compute/
    ├── markets.js        # instruments, ticker, series, correlation, cracks, curves, macro
    └── derive.js         # calendar, OPEC, freight (modeled), rigs (modeled), sentiment
```

## How navigation works

The sidebar's NAV array drives a flat state-based router in `App.jsx`. Clicking a sidebar item updates `active`, which keys into the `PAGES` map to render the matching page component. Switching from this lightweight router to **React Router** later is straightforward — replace `<Page />` with `<Outlet />` and wire the NAV `to` props.

## Converting to TypeScript (optional)

The project ships as JSX for the fastest possible boot. To migrate:

1. `npm install -D typescript @types/react @types/react-dom`
2. Add a `tsconfig.json` (Vite's React + TS template has a working one).
3. Rename all `.jsx` → `.tsx` and `.js` (except configs) → `.ts`.
4. Add prop type annotations incrementally. Most components take simple props that infer cleanly.

## Notes on style

The aesthetic deliberately avoids "rounded-2xl, soft pastels, shadow-md" AI-generic vibes. Instead:

- Sharp, square corners (no `rounded-*`)
- Tight 1px borders in `#1c1d22`
- Monospaced figures with `tabular-nums` for stable column alignment
- 9-11px label eyebrows in tracked uppercase
- Subtle hover states (border brightens, no fill changes)
- Animated ticker strip with `framer-motion` (60s loop)
- Single amber accent (`#f59e0b`) reserved for highlights and active states

## Mock data (now the fallback)

`src/data/mock.js` is still here, but its role flipped: the seeded datasets are now the **graceful-degradation fallback**. Every panel calls `useLive("/api/…", <mock fallback>)`; if the backend or an upstream source is down, the panel quietly renders the mock instead of erroring. The shapes returned by `/api/*` mirror the mock exports exactly.

## License

MIT — use freely.
