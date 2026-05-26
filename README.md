# VOLTAIRE Terminal

Institutional-grade Energy Markets Intelligence Dashboard. Frontend-only, mock-data-driven.

Inspired by Bloomberg Terminal, Kpler, TradingView, Vortexa, and Refinitiv. Dark institutional aesthetic, dense information layout, monospaced data cells, market-tone color signaling (bull green / bear red / amber accent).

## Prerequisites

- **Node.js 18+** (check with `node -v`)
- **npm** (ships with Node) or **pnpm** / **yarn** if you prefer

## Quick start

```bash
npm install
npm run dev
```

The dev server opens automatically at **http://localhost:5173**.

## Available scripts

| Command           | What it does                                  |
| ----------------- | --------------------------------------------- |
| `npm run dev`     | Start Vite dev server with hot reload         |
| `npm run build`   | Production build into `dist/`                 |
| `npm run preview` | Serve the production build locally to verify  |

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

No backend, no auth, no database. All data is generated client-side from seeded PRNGs in `src/data/mock.js` so the layout is reproducible on every reload.

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

## Mock data

All datasets are derived from a small set of seeded random helpers (`seededRand`, `genSeries`, `genSpark`) in `src/data/mock.js`. To wire real data later, replace the imports in each page/panel with API calls (React Query or SWR recommended). The shape of each dataset is documented inline.

## License

MIT — use freely.
