# Explanation — Every Data Source, Calculation & Inference

This document explains, in exhaustive detail, **where every number on the Voltaire
Terminal dashboard comes from**, how it is collected, and exactly how each derived figure
is computed. It is the authoritative reference for the data lineage of the app.

It is written so that someone who has never seen the code can answer, for any value on
screen, three questions:

1. **Where does the raw input come from?** — which external feed, which exact endpoint (every
   source below is a **clickable link**).
2. **How is it transformed?** — the exact formula, constants, and units.
3. **How trustworthy is it?** — live / official / derived / curated / modeled, and why.

> **Golden rule of this project:** we never fabricate a number and present it as real.
> If a value cannot be sourced from a free/open feed and cannot be responsibly curated,
> the UI shows an em‑dash **"—"** instead of an invented figure. See [§3](#3-provenance-taxonomy--the-six-kinds) and [§14](#14-modeled--no-free-source-items--shown-as-).

> **Status of the data as documented:** all seven live feeds were probed end-to-end and are
> connected and replying — `eia: live`, `finbert: live`, `yahoo / openmeteo / financialjuice
> / noaa / cftc` all returning fresh data, every `/api/*` endpoint `HTTP 200`. See
> [§18](#18-honest-caveats--known-limitations) for the standing caveats.

---

## Table of contents

- [0. Quick mental model](#0-quick-mental-model)
- [1. Design philosophy](#1-design-philosophy)
- [2. System architecture & request lifecycle](#2-system-architecture--request-lifecycle)
- [3. Provenance taxonomy — the six "kinds"](#3-provenance-taxonomy--the-six-kinds)
- [4. The raw data sources (clickable)](#4-the-raw-data-sources-clickable)
  - [4.1 Yahoo Finance — prices, macro, dated contracts](#41-yahoo-finance--prices-macro-dated-contracts)
  - [4.2 EIA Open Data API v2 — US fundamentals](#42-eia-open-data-api-v2--us-fundamentals)
  - [4.3 Open-Meteo — weather](#43-open-meteo--weather)
  - [4.4 Financial Juice — news](#44-financial-juice--news)
  - [4.5 NOAA — storms & ENSO](#45-noaa--storms--enso)
  - [4.6 CFTC — Commitments of Traders](#46-cftc--commitments-of-traders)
  - [4.7 FinBERT — local news-sentiment model](#47-finbert--local-news-sentiment-model)
- [5. Units & the $/bbl normalization layer](#5-units--the-bbl-normalization-layer)
- [6. Computed market metrics](#6-computed-market-metrics)
- [7. EIA-derived fundamentals](#7-eia-derived-fundamentals)
- [8. Weather-derived metrics](#8-weather-derived-metrics)
- [9. News pipeline & FinBERT sentiment](#9-news-pipeline--finbert-sentiment)
- [10. CFTC speculative positioning (COT)](#10-cftc-speculative-positioning-cot)
- [11. Seasonality](#11-seasonality)
- [12. NOAA storms & ENSO](#12-noaa-storms--enso)
- [13. Curated data (OPEC, calendar)](#13-curated-data-opec-calendar)
- [14. Modeled / no-free-source items → shown as "—"](#14-modeled--no-free-source-items--shown-as-)
- [15. Caching, refresh cadence & failure handling](#15-caching-refresh-cadence--failure-handling)
- [16. Per-panel data lineage](#16-per-panel-data-lineage)
- [17. Quick-reference tables](#17-quick-reference-tables)
- [18. Honest caveats & known limitations](#18-honest-caveats--known-limitations)

---

## 0. Quick mental model

```
 EXTERNAL FEEDS              BACKEND (Node/Express, server/)         FRONTEND (React + Vite, src/)
 ─────────────              ────────────────────────────────        ─────────────────────────────
 Yahoo Finance  ─┐           sources/*.js  → fetch + clean           useLive() polls /api/* on a timer
 EIA v2         ─┤           compute/*.js  → derive / normalize       panels render data
 Open-Meteo     ─┤    ──▶    lib/cache.js  → TTL cache + retry  ──▶   <Sourced>/<SourceTag> show provenance
 Financial Juice─┤           lib/sources.js→ provenance registry      falls back to src/data/mock.js on error
 NOAA · CFTC    ─┤           index.js      → /api/* routes
 FinBERT (local)─┘           (no inference network — runs in-process)
```

- The **backend** does all fetching and math, then serves clean JSON at `/api/*`.
- The **frontend** never calls an external API directly. It polls our own `/api/*` endpoints.
  In dev, Vite proxies `/api` → `http://localhost:3001` (the Node backend).
- If an endpoint is unreachable, the panel keeps the **last good value** or falls back to
  **seeded sample data** (`src/data/mock.js`) and an **offline banner** appears. Sample data
  is static — that is the one situation where the dashboard is *not* live.
- **FinBERT is special:** it is an actual ML model (ProsusAI/finbert) that runs **locally,
  in-process**, with no API and no inference-time network. It downloads once to a disk cache.

Run both halves with **`npm run dev`** (it starts Vite **and** the backend together).
Running only the frontend (`npm run dev:web`) leaves `/api` dead and everything shows sample
data.

---

## 1. Design philosophy

The dashboard mixes data of very different quality. Rather than blur that distinction, we make
it explicit at every value:

1. **Live-first.** Anything obtainable from a free/open feed is fetched live (Yahoo, EIA,
   Open-Meteo, Financial Juice, NOAA, CFTC) and refreshed on a cadence appropriate to how fast
   it actually changes.
2. **Derive, don't invent.** Spreads, cracks, correlations, forward curves, degree-days,
   seasonality, and sentiment are *computed* from live inputs with transparent formulas (this
   document). They are as live as their inputs.
3. **Curate only what is publicly known and stable.** A small set of reference values (OPEC+
   policy targets, the US report release calendar) are hand-maintained because they change
   rarely and are published in human-readable form, not via a free API.
4. **Otherwise show "—".** If a value would require a paywalled feed (Baltic Exchange,
   Kpler/Vortexa, Worldscale, real-time Baker Hughes API) and it cannot be curated, we **do not
   model or guess** it. We render **"—"** and explain why on hover.
5. **Provenance is always one hover away.** Every value is wrapped so that hovering it reveals
   its source, kind, and a one-line note.

---

## 2. System architecture & request lifecycle

### Files

| Layer | Path | Responsibility |
| --- | --- | --- |
| Source adapters | [`server/sources/`](server/sources/) `yahoo.js`, `eia.js`, `openmeteo.js`, `financialjuice.js`, `noaa.js`, `cftc.js`, `finbert.js` | Fetch a specific upstream and return cleaned data |
| Compute | [`server/compute/`](server/compute/) `markets.js`, `derive.js`, `seasonality.js` | Turn raw inputs into the exact shapes the UI renders |
| Cache + fetch | [`server/lib/cache.js`](server/lib/cache.js) | TTL cache; resilient `fetch` with timeout + browser UA; serves stale on error |
| Provenance | [`server/lib/sources.js`](server/lib/sources.js) ↔ [`src/lib/sources.js`](src/lib/sources.js) | The source registry, mirrored on both ends |
| Routing | [`server/index.js`](server/index.js) | Maps `/api/*` → compute functions; adds headers, health, 404 |
| Live polling | [`src/lib/useLive.js`](src/lib/useLive.js) | Frontend hook that polls an endpoint and manages fallback/stale |
| Provenance UI | [`src/components/primitives/`](src/components/primitives/) `Tooltip.jsx`, `SentimentChip.jsx` (+ `Sourced`/`SourceTag`) | Hover-to-see-source |
| Fallback data | [`src/data/mock.js`](src/data/mock.js) | Seeded sample values used only when the backend is unreachable |

### Lifecycle of one value (example: the Brent price tile)

1. The dashboard mounts a `HeroCard` for Brent and calls `useLive("/api/instruments", HERO)`.
2. `useLive` immediately `fetch("/api/instruments")` and then re-fetches on its interval.
3. Vite proxies that to `http://localhost:3001/api/instruments`.
4. [`server/index.js`](server/index.js) runs `instruments()` (in [`server/compute/markets.js`](server/compute/markets.js)).
5. `instruments()` calls `getQuotes(["BZ=F","CL=F","HO=F","RB=F"])` (in [`server/sources/yahoo.js`](server/sources/yahoo.js)).
6. `yahoo.js` fetches Yahoo's chart endpoint (cached 45 s), extracts price/change/sparkline, and
   returns a clean object.
7. `markets.js` shapes it into `{ sym:"BRENT", val, chg, pct, bbl, spark, … }`.
8. `index.js` adds `X-Data-Source: yahoo` / `X-Data-Kind: live` headers and sends JSON.
9. `useLive` stores it; `HeroCard` renders it, wrapping the number in `<Sourced source="yahoo">`
   so hovering shows "Yahoo Finance · live".
10. If steps 3–7 fail, `useLive` keeps the previous good value (or the seeded `HERO` fallback)
    and flips a `stale` flag; the status bar/banner reflect "offline".

### The route wrapper ([`server/index.js`](server/index.js))

Every data endpoint is wrapped by `route(producer, path)`:

- Runs the producer; on success sends JSON with `Cache-Control: no-store` and the provenance
  headers `X-Data-Source` / `X-Data-Kind`.
- If the producer returns `null` (e.g. EIA with no key) → **HTTP 503** `{fallback:true}`.
- If it throws → **HTTP 503** `{error, fallback:true}` and logs a warning.
- A 503 tells the frontend "use your fallback", so panels degrade gracefully instead of erroring.

There is also a request logger (`[api] GET /path 200 12ms` — latency reveals a real upstream
fetch vs a ~1 ms cache hit), a richer `/api/health` (which reports `eia` and `finbert` status),
a self-describing `/api/sources` manifest, and a JSON 404 for unknown `/api` paths.

---

## 3. Provenance taxonomy — the six "kinds"

Every value maps to exactly one **source key**, and every source key has a **kind**. This is
defined once in [`server/lib/sources.js`](server/lib/sources.js) and mirrored in
[`src/lib/sources.js`](src/lib/sources.js).

| Kind | Meaning | Shown as | Examples |
| --- | --- | --- | --- |
| **live** | Fetched fresh from a public feed | the value | Yahoo prices, Open-Meteo temps, Financial Juice news |
| **official** | Government/authoritative (also live) | the value | EIA inventories, NOAA storms/ENSO, CFTC positioning |
| **derived** | Computed on the server *from* a live feed | the value | spreads, cracks, correlation, seasonality, FinBERT sentiment, Gas Oil proxy |
| **curated** | Hand-maintained reference values | the value | OPEC+ quotas/output |
| **schedule** | A real-world release cadence, not a feed | times/dates | economic calendar |
| **modeled** | No free/open source and not curated | **"—"** | freight, rig count, port congestion, etc. |

On the frontend:
- `<Sourced source="…">value</Sourced>` wraps a value. If the kind is **modeled**, it renders
  **"—"** instead of the children (so we never print an assumed number) but still explains "no
  free source" on hover.
- `<SourceTag source="…" note="…">` is the small pill on a panel header (LIVE / Official /
  Derived / Modeled / Cached) that also explains itself on hover.
- Charts pass `source` to `ChartTooltip`, so even a hovered chart point shows its origin.

The dot color in tooltips (`KIND_COLOR` in [`src/lib/sources.js`](src/lib/sources.js)): live =
green `#10b981`, official = blue `#38bdf8`, derived = violet `#a78bfa`, curated/modeled = amber
`#f59e0b`, schedule = blue.

---

## 4. The raw data sources (clickable)

| # | Source | Kind | Used for | Primary link | Exact endpoint(s) used |
| --- | --- | --- | --- | --- | --- |
| 4.1 | **Yahoo Finance** | live | prices, macro, dated contracts, monthly history | [finance.yahoo.com](https://finance.yahoo.com) | [`/v8/finance/chart/{symbol}`](https://query1.finance.yahoo.com/v8/finance/chart/CL=F?range=1d&interval=1d) |
| 4.2 | **EIA Open Data v2** | official | US oil fundamentals | [eia.gov/opendata](https://www.eia.gov/opendata/) · [register a key](https://www.eia.gov/opendata/register.php) | [`/v2/seriesid/{ID}`](https://api.eia.gov/v2/seriesid/PET.WCESTUS1.W) |
| 4.3 | **Open-Meteo** | live | weather, degree-days | [open-meteo.com](https://open-meteo.com) | [`/v1/forecast`](https://api.open-meteo.com/v1/forecast?latitude=40.71&longitude=-74&daily=temperature_2m_max,temperature_2m_min) |
| 4.4 | **Financial Juice** | live | news wire | [financialjuice.com](https://www.financialjuice.com) | [`/feed.ashx?xy=rss`](https://www.financialjuice.com/feed.ashx?xy=rss) |
| 4.5 | **NOAA** (NHC + CPC) | official | storms, ENSO | [nhc.noaa.gov](https://www.nhc.noaa.gov) · [cpc.ncep.noaa.gov](https://www.cpc.ncep.noaa.gov) | [`CurrentStorms.json`](https://www.nhc.noaa.gov/CurrentStorms.json) · [`oni.ascii.txt`](https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt) |
| 4.6 | **CFTC** | official | Commitments of Traders | [cftc.gov COT](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm) | [`publicreporting.cftc.gov/resource/72hh-3qpy.json`](https://publicreporting.cftc.gov/resource/72hh-3qpy.json) |
| 4.7 | **FinBERT** (local) | derived | news sentiment | [ProsusAI/finbert](https://huggingface.co/ProsusAI/finbert) · [Xenova/finbert (ONNX)](https://huggingface.co/Xenova/finbert) | runs locally via [Transformers.js](https://github.com/huggingface/transformers.js) |

### 4.1 Yahoo Finance — prices, macro, dated contracts

**File:** [`server/sources/yahoo.js`](server/sources/yahoo.js) · **Kind:** live · **Key:** none.

**Endpoint (public, unofficial but stable):**
```
GET https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={range}&interval={interval}&includePrePost=false
```
A single call returns **both** a live quote (in `meta`) and the historical close series (in
`indicators.quote[0].close` aligned to `timestamp[]`).

**Symbols used:**

| Our id | Symbol | Instrument | Native unit |
| --- | --- | --- | --- |
| `brent` | `BZ=F` | Brent crude front future | $/bbl |
| `wti` | `CL=F` | WTI crude front future | $/bbl |
| `ho` | `HO=F` | NYMEX ULSD / "Heating Oil" | $/gal |
| `rbob` | `RB=F` | RBOB gasoline | $/gal |
| `DXY` | `DX-Y.NYB` | US Dollar Index | index |
| `SPX` | `^GSPC` | S&P 500 | index |
| `VIX` | `^VIX` | CBOE Volatility Index | index |
| `UST10Y` | `^TNX` | US 10-year Treasury yield | % |
| (curve) | `CL`/`BZ`/`HO`/`RB` `{MonthCode}{YY}.NYM` | individual dated contracts | per root |

> **ICE Gas Oil has no free Yahoo symbol**, so it is *not* fetched directly — it is derived
> from `HO=F` (see [§5](#5-units--the-bbl-normalization-layer)).

**Three different fetch shapes:**

- **`getQuote(symbol)`** — fetches the symbol **twice**:
  - `range=1d, interval=1d` — used only for the **daily % change**, because on a 1-day window
    Yahoo's `meta.chartPreviousClose` is *yesterday's* close, giving the correct daily move.
  - `range=3mo, interval=1d` — used for the **sparkline** (last ~30 daily closes) and the
    **history** array (≈90 days) that feeds the normalized series and correlation.

  On a longer range, `chartPreviousClose` is the pre-window close, which would make the "daily"
  change wildly wrong — hence the dedicated 1-day fetch. It returns:
  ```
  { price, prev, chg, pct, dayHigh, dayLow, volume, name, spark[], history[] }
  ```
- **`getFrontPrices(symbols)`** — one cached 1d chart fetch per symbol, returning
  `{price, time}` (last trade + last-trade timestamp). Used to build the **real forward curves**
  from individual dated contracts ([§6.6](#66-forward-curves-real--forwardcurves)). A delisted
  contract resolves to `{price:null}`.
- **`monthlyCloses(symbol, "10y")`** — `range=10y, interval=1mo`, cached **12 h**. Returns
  ~10 years of monthly closes used for **seasonality** ([§11](#11-seasonality)).

**Collection details / quirks:**
- A **browser-like `User-Agent`** header is sent (in [`server/lib/cache.js`](server/lib/cache.js))
  — Yahoo's public chart endpoint returns 403 without it.
- Cached **45 s** per `(symbol, range, interval)`. The dashboard polls prices every 30 s, so most
  polls are cheap cache hits and we stay well inside Yahoo's tolerance.
- Holiday/halt gaps (null closes) are dropped when building the clean close series (`closeSeries`).
- **Overnight behavior:** crude futures trade nearly 24 h but print thinly overnight; outside
  active hours the price is the last print and can look "frozen". That is expected live behavior.
- Per-symbol failures resolve to `null` (that instrument shows "—"/fallback) instead of failing
  the whole batch (`getQuotes`).

### 4.2 EIA Open Data API v2 — US fundamentals

**File:** [`server/sources/eia.js`](server/sources/eia.js) · **Kind:** official · **Key:** free
key in `server/.env` (`EIA_API_KEY`). [Register here](https://www.eia.gov/opendata/register.php).
Without a key these endpoints return 503 and the UI uses fallback. *(Probed live: `eia: true`.)*

**Endpoint (v2 "series by ID" route):**
```
GET https://api.eia.gov/v2/seriesid/{ID}?api_key={KEY}&sort[0][column]=period&sort[0][direction]=desc&length={N}
```
- The `{ID}` **must be the full legacy form `CATEGORY.SERIES.FREQ`** (e.g. `PET.WCESTUS1.W`).
  The bare series code (`WCESTUS1`) returns 404 on this route.
- Response shape: `{ response: { data: [ { period:"YYYY-MM-DD", value:<number> }, … ] } }`.
- We request newest-first (`direction=desc`), drop nulls, then **reverse to chronological**.
- Cached **6 hours** (the underlying Weekly Petroleum Status Report updates weekly).

**Series used:**

| Series ID | Meaning | Native unit | Link |
| --- | --- | --- | --- |
| `PET.WCESTUS1.W` | US commercial crude stocks **excl. SPR** | thousand bbl | [page](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=WCESTUS1&f=W) |
| `PET.WCSSTUS1.W` | Crude in the Strategic Petroleum Reserve | thousand bbl | [page](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=WCSSTUS1&f=W) |
| `PET.W_EPC0_SAX_YCUOK_MBBL.W` | Cushing, OK crude stocks | thousand bbl | [page](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=W_EPC0_SAX_YCUOK_MBBL&f=W) |
| `PET.WGTSTUS1.W` | US total gasoline stocks | thousand bbl | [page](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=WGTSTUS1&f=W) |
| `PET.WDISTUS1.W` | US distillate fuel oil stocks | thousand bbl | [page](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=WDISTUS1&f=W) |
| `PET.WPULEUS3.W` | Refinery % utilization of operable capacity | percent | [page](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=WPULEUS3&f=W) |
| `PET.WCESTP11.W` … `PET.WCESTP51.W` | Crude stocks by PADD region 1–5 | thousand bbl | [PADD map](https://www.eia.gov/tools/glossary/index.php?id=petroleum%20administration%20for%20defense%20district) |
| `PET.RWTC.D` | WTI Cushing spot (daily) | $/bbl | [page](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=RWTC&f=D) |
| `PET.RBRTE.D` | Brent Europe spot (daily) | $/bbl | [page](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=RBRTE&f=D) |

**Unit conversion.** EIA reports stocks in **thousand barrels**; we convert to **million barrels
(MMbbl)** for display: `toMM(kbbl) = round(kbbl / 1000, 1 dp)`.

**Helpers:** `latest(arr) = arr.at(-1).value`, `prior(arr) = arr.at(-2).value` (the chronological
last / second-last weekly prints).

**How much history we pull:** crude `WCESTUS1` is fetched **285 weeks** (~5.4 years) so the
5-year seasonal band has 5 prior years per week-of-year; the other headline series fetch 8 weeks;
PADD series 4 weeks; spot 5 days. (Details in [§7](#7-eia-derived-fundamentals).)

### 4.3 Open-Meteo — weather

**File:** [`server/sources/openmeteo.js`](server/sources/openmeteo.js) · **Kind:** live · **Key:**
none. **Site:** [open-meteo.com](https://open-meteo.com).

**Endpoint:**
```
GET https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}
    &daily=temperature_2m_max,temperature_2m_min&timezone=auto
    &past_days={p}&forecast_days={f}
```
For each day we take the **daily mean** as `mean = (Tmax + Tmin) / 2` (°C).

**Regions** (one representative point each; monthly mean-temp "normals" are a climatological
reference array, °C, Jan→Dec):

| Region | Group | Lat, Lon | Monthly normals (°C, Jan…Dec) |
| --- | --- | --- | --- |
| US Northeast | US | 40.71, −74.0 | −0.5, 0.5, 5, 11, 16, 21, 24, 23, 19, 13, 7, 2 |
| US Midwest | US | 41.88, −87.63 | −4, −2, 4, 10, 16, 22, 24, 23, 19, 12, 5, −2 |
| US Gulf Coast | US | 29.76, −95.37 | 11, 13, 17, 21, 25, 28, 29, 29, 27, 22, 17, 12 |
| NW Europe | EU | 52.37, 4.90 | 4, 4, 7, 10, 14, 17, 19, 19, 16, 12, 7, 5 |
| Northeast Asia | ASIA | 37.57, 126.98 | 1, 2, 7, 13, 18, 22, 26, 27, 22, 16, 9, 3 |
| S. Europe | EU | 41.90, 12.50 | 8, 9, 12, 15, 19, 24, 27, 27, 23, 18, 13, 9 |

- The **temperatures are genuinely live** (Open-Meteo refreshes hourly; cached **1 h** here).
- The **normals are constants** (NOAA-style 30-year monthly means), the baseline for the anomaly.
  The UI labels anomaly "vs normal".

### 4.4 Financial Juice — news

**File:** [`server/sources/financialjuice.js`](server/sources/financialjuice.js) · **Kind:** live
· **Key:** none. **Site:** [financialjuice.com](https://www.financialjuice.com).

**Endpoint (RSS):** [`https://www.financialjuice.com/feed.ashx?xy=rss`](https://www.financialjuice.com/feed.ashx?xy=rss)

A fast, trader-oriented financial wire (central banks, data prints, OPEC, geopolitics,
commodities, equities). Cached **4 minutes**; we keep up to **24** items.

**Parsing pipeline (regex-based, no XML lib):**
1. Split on `<item>…</item>`.
2. Extract `<title>`, `<link>`, `<pubDate>` with a small tag matcher (`tagOf`).
3. **Decode** XML/HTML entities (`&amp; &lt; &gt; &quot; &#39; &#xNN;`) and unwrap `CDATA`.
4. **Strip** the leading `FinancialJuice:` brand prefix from the title.
5. **De-duplicate** by exact title.
6. **Timestamp** `t` = `HH:MM` parsed from `pubDate`.
7. **Classify** into a tag and **score** a severity ([§9.1–9.2](#91-classification-financialjuicejs)).
8. **Score sentiment** with FinBERT ([§4.7](#47-finbert--local-news-sentiment-model), [§9.3](#93-finbert-sentiment-per-headline)).
9. Emit `{ t, sev, src:"FINJUICE", txt, tag, url, sent }`.

Because Financial Juice is a curated quality wire (not a noisy global crawl), we keep **all**
items rather than filtering to energy-only; the tag taxonomy + the UI's tag filters let a user
narrow to OPEC / CRUDE / GEOPOLITICS, etc.

### 4.5 NOAA — storms & ENSO

**File:** [`server/sources/noaa.js`](server/sources/noaa.js) · **Kind:** official · **Key:** none.
Two free US-government feeds; both refresh slowly so we cache hard.

- **Active tropical cyclones** — National Hurricane Center
  [`https://www.nhc.noaa.gov/CurrentStorms.json`](https://www.nhc.noaa.gov/CurrentStorms.json)
  (site: [nhc.noaa.gov](https://www.nhc.noaa.gov)). Covers the **Atlantic + East/Central Pacific**
  basins (the NHC's remit) — Gulf-of-Mexico systems are the ones that actually move oil/gas, so
  this is the relevant free feed. Cached **30 min**.
- **ENSO / El Niño** — Climate Prediction Center Oceanic Niño Index (ONI)
  [`https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt`](https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt)
  (site: [cpc.ncep.noaa.gov](https://www.cpc.ncep.noaa.gov)). The standard 3-month running SST
  anomaly in the Niño-3.4 region. Cached **12 h**.

Derivation in [§12](#12-noaa-storms--enso). *(Probed live: TD Amanda + one other system, ONI +0.48
"Neutral".)*

### 4.6 CFTC — Commitments of Traders

**File:** [`server/sources/cftc.js`](server/sources/cftc.js) · **Kind:** official · **Key:** none.

**Endpoint (Socrata, Disaggregated Futures-Only):**
[`https://publicreporting.cftc.gov/resource/72hh-3qpy.json`](https://publicreporting.cftc.gov/resource/72hh-3qpy.json)
(report home: [cftc.gov COT](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm)).

We track **"Managed Money"** (speculative funds) for the four energy contracts that match the
dashboard's instruments. We filter by the **stable contract code** (names get renamed over the
years, codes don't):

| Our id | CFTC code | Contract |
| --- | --- | --- |
| WTI | `067651` | WTI-PHYSICAL (NYMEX WTI) |
| BRENT | `06765T` | BRENT LAST DAY (NYMEX) |
| RBOB | `111659` | GASOLINE RBOB (NYMEX) |
| HO | `022651` | NY HARBOR ULSD (NYMEX) |

Released weekly (Friday ~15:30 ET, as of the prior Tuesday). We pull ~160 weeks (~3 years) so the
current net position can be placed inside its own historical range (percentile). Cached **6 h**.
Derivation in [§10](#10-cftc-speculative-positioning-cot). *(Probed live: as-of 2026-06-02.)*

### 4.7 FinBERT — local news-sentiment model

**File:** [`server/sources/finbert.js`](server/sources/finbert.js) · **Kind:** derived · **Key:**
none. **Model:** [ProsusAI/finbert](https://huggingface.co/ProsusAI/finbert) via its ONNX port
[Xenova/finbert](https://huggingface.co/Xenova/finbert), run locally with
[Transformers.js (`@huggingface/transformers`)](https://github.com/huggingface/transformers.js).

FinBERT is BERT fine-tuned on financial text; it classifies a sentence as **positive / negative /
neutral**. We use it to score each newswire headline, replacing an older bull/bear keyword regex.

**How it runs:**
- The model is **downloaded once** (quantized `q8` weights, falling back to full precision) into a
  disk cache, then runs **in-process** — no Python, no API key, **no inference-time network**.
- The pipeline is lazily built **once** (a singleton promise), **background-warmed on import** so
  the first `/api/news` request isn't the one that waits.
- A per-headline `Map` cache means repeated wire items are never re-scored.
- **Graceful degradation:** if the model can't load (offline first run, unsupported platform),
  `scoreHeadlines` resolves to `null`, headlines carry `sent: null`, and sentiment transparently
  falls back to the keyword heuristic. `/api/health` reports `finbert: loading | live | unavailable`.

Derivation in [§9.3](#93-finbert-sentiment-per-headline). *(Probed live: `finbert: live`, all 24
headlines scored.)*

---

## 5. Units & the $/bbl normalization layer

The instruments quote in three different units. To compute cracks and spreads, every product is
normalized to **$/bbl**. Constants (in [`server/compute/markets.js`](server/compute/markets.js)):

```
GAL_PER_BBL        = 42     // 1 barrel = 42 US gallons (RBOB & ULSD quote in $/gal)
BBL_PER_MT_GASOIL  = 7.45   // ≈ barrels of gas oil per metric tonne (ICE Gas Oil quotes in $/mt)
```

The `bbl` field on each instrument (`toBbl(id, val)`):

| Instrument | Native quote | → $/bbl conversion |
| --- | --- | --- |
| Brent, WTI | $/bbl | unchanged |
| Heating Oil (ULSD), RBOB | $/gal | `$/gal × 42` |
| Gas Oil | $/mt | `$/mt ÷ 7.45` |

### The Gas Oil proxy (important)

ICE Gas Oil has no free live feed, so it is **derived from NYMEX ULSD (`HO=F`)** — both are middle
distillates that track each other very closely. Its provenance kind is **derived** (not modeled),
so it shows a real value, flagged with a `~` and a tooltip ("Proxied from live NYMEX ULSD (HO=F),
unit-converted to $/mt.").

Derivation from the live ULSD `$/gal` price:
```
$/gal  ──×42──▶  $/bbl  ──×7.45──▶  $/mt
gasoilPrice($/mt) = ulsdPrice($/gal) × 42 × 7.45      // galToMt(gal) = gal × 42 × 7.45
```
The change/percent and sparkline are converted point-by-point the same way, and its `bbl` value
rounds back via `÷ 7.45`. A consequence: **Gas Oil's correlation and normalized line track
Heating Oil almost exactly** (they share a single underlying series) — expected, and noted in the UI.

---

## 6. Computed market metrics

All of the following are **derived** from the live Yahoo inputs above, in
[`server/compute/markets.js`](server/compute/markets.js). They are as live as Yahoo.

### 6.1 Instrument tile (`instruments()`)
For each non-proxy instrument from Yahoo:
- `val` = price, rounded to 4 dp for `$/gal` instruments else 2 dp.
- `chg` = `price − prev` (same rounding).
- `pct` = Yahoo's `(chg / prev) × 100` (2 dp).
- `bbl` = `toBbl(...)` ([§5](#5-units--the-bbl-normalization-layer)).
- `spark` = last 30 daily closes; `volRaw` = regular-market volume.

Gas Oil is built from the ULSD base via `galToMt` as in [§5](#5-units--the-bbl-normalization-layer).

### 6.2 Daily % change
Defined entirely by Yahoo's 1-day `chartPreviousClose` (see
[§4.1](#41-yahoo-finance--prices-macro-dated-contracts)). The colored arrow and the ticker change
both use this.

### 6.3 Headline spreads (`headlineSpreads()`, used by ticker & movers)
All in $/bbl using the normalized `bbl` values:
```
BRENT-WTI   = brent.val − wti.val                          (both already $/bbl)
3:2:1 CRACK = (2·rbob.bbl + 1·ho.bbl − 3·wti.bbl) / 3
GASOIL CRK  = gasoil.bbl − brent.bbl
RBOB CRK    = rbob.bbl − wti.bbl
```
In the scrolling ticker these spreads are shown with `chg/pct = 0` (no intraday spread change there).

### 6.4 Crack spreads (`cracks()`)
A crack spread is the refining margin: product value minus crude cost, per barrel. The generic
formula for a definition with product legs `legs = [(product, coeff), …]`, a crude, its
coefficient `crudeC`, and a divisor `div`:

```
value = ( Σ coeff·product.bbl  −  crudeC·crude.bbl ) / div          [$/bbl]
```

The ten shipped definitions:

| id | Label | Formula (in $/bbl) | Group |
| --- | --- | --- | --- |
| `rbob-wti` | RBOB Crack | `rbob − wti` | Product Cracks |
| `rbob-brent` | RBOB Crack | `rbob − brent` | Product Cracks |
| `ho-wti` | Heating Oil Crack | `ho − wti` | Product Cracks |
| `ho-brent` | Heating Oil Crack | `ho − brent` | Product Cracks |
| `gasoil-brent` | Gas Oil Crack | `gasoil − brent` | Product Cracks |
| `gasoil-wti` | Gas Oil Crack | `gasoil − wti` | Product Cracks |
| `321-wti` | 3:2:1 Crack | `(2·rbob + 1·ho − 3·wti) / 3` | Refining Margins |
| `321-brent` | 3:2:1 Crack | `(2·rbob + 1·ho − 3·brent) / 3` | Refining Margins |
| `211-wti` | 2:1:1 Crack | `(1·rbob + 1·ho − 2·wti) / 2` | Refining Margins |
| `532-wti` | 5:3:2 Crack | `(3·rbob + 2·ho − 5·wti) / 5` | Refining Margins |

**Worked example (3:2:1 vs WTI):** with WTI = $80/bbl, RBOB = $2.40/gal, ULSD = $2.50/gal:
`rbob.bbl = 2.40×42 = 100.8`, `ho.bbl = 2.50×42 = 105.0`, so
`(2×100.8 + 105.0 − 3×80) / 3 = (201.6 + 105.0 − 240)/3 = 66.6/3 = $22.20/bbl`.

> Only the **current** crack value is live/derived. The **60-day crack history chart** and its
> 60d hi/lo/avg & change are **modeled** (no free intraday crack-history feed), so those scalar
> stats show **"—"** while the illustrative chart line is kept ([§14](#14-modeled--no-free-source-items--shown-as-)).

### 6.5 Inter-commodity spreads (`interSpreads()`) — live
```
Brent – WTI            = brent.val − wti.val      [$/bbl]   "Crude arb"
RBOB – Heating Oil     = rbob.val − ho.val        [$/gal]   "Gas–Heat"
Heating Oil – Gas Oil  = ho.bbl  − gasoil.bbl     [$/bbl]   "Distillate"
RBOB – Gas Oil         = rbob.bbl − gasoil.bbl    [$/bbl]   "Light prod"
```

### 6.6 Forward curves (REAL) — `forwardCurves()`

> **This is now a genuine term structure, not a model.** (It used to be a straight-line model;
> the modeled version still exists as a fallback — see the end of this section.)

Yahoo serves **individual dated NYMEX/ICE contracts for free**, e.g. `CLZ26.NYM` = WTI Dec-2026.
So the Brent / WTI / HO / RBOB curves are built from **consecutive real contract settlements**:

**Symbol construction (`contractSymbols`):** `{root}{MonthCode}{YY}.NYM`
- Roots: `BZ` (Brent), `CL` (WTI), `HO` (ULSD), `RB` (RBOB) — all on `.NYM`.
- Month codes (Jan→Dec): `F G H J K M N Q U V X Z`.
- We probe `CURVE_HORIZON = 15` consecutive months starting from the current month, so 12 still
  land after an expired front drops out.

**Building each curve:**
1. One **batched, 10-min-cached** fetch (`curve:prices`) of every dated contract via
   `getFrontPrices` (forward curves barely move intraday, so this stays well clear of rate limits).
2. Find `maxTime` = the freshest last-trade among that instrument's contracts (≈ "now").
3. **Skip a stale FRONT only:** if the first contract stopped trading more than `FRESH_LAG = 30 h`
   before `maxTime`, it's an expiring/expired month — skip it. (Yahoo's continuous `BZ=F`/`CL=F`
   roll early, so the dated front ≠ continuous front during expiry week.) Once the active front is
   found, **keep every later month** — back-month staleness is just illiquidity, and its last
   settle is still a real curve point.
4. Take the first **12** valid points → `data: [{m:"M1", v}, … {m:"M12", v}]`, flagged
   `modeled:false, source:"yahoo"` (UI shows a green "Live curve" tag; the C1–C12 slope renders a
   real number).
5. If fewer than 12 real points resolve, fall back to the **modeled** straight-line curve for that
   instrument so the API always serves exactly M1..M12.

**Gas Oil curve (proxied, derived):** ICE Gas Oil has no free dated feed, so its curve is the
**shape of the real ULSD (HO) curve, scaled to the live Gas Oil front** and kept in $/mt:
```
gasoil.curve[i] = gasoilFront × ( ho.curve[i] / ho.curve[0] )
```
Flagged `modeled:true, source:"derived"` ("Proxied" tag).

**Modeled fallback (`curves()`):** a straight line from the live front using a curated monthly
slope `CURVE_SLOPE = { brent:−0.34, wti:−0.30, ho:−0.012, rbob:0.009, gasoil:−2.8 }`, i.e.
`v(Mi) = front + slope·(i−1)`. Only used when the real dated contracts don't resolve to a full 12.

*(Probed live: Brent/WTI/HO/RBOB all `modeled:false` with 12 real points; Gas Oil `modeled:true`
proxied.)*

### 6.7 Normalized price series (`seriesAndCorrelation()` → `series`) — live
- Pull each instrument's ~90-day daily-close `history` (Gas Oil reuses ULSD's history).
- **Align** on dates present in *every* series (intersection, keyed by `M/D`).
- **Index to 100** at the first aligned date: `normalized = (close / firstClose) × 100`.

This is the "Price Action — Normalized" chart; it shows *relative* performance, not absolute price.

### 6.8 Correlation matrix (`correlationMatrix()`) — live
- From the aligned closes, compute **daily simple returns**: `r_t = (c_t − c_{t-1}) / c_{t-1}`.
- Keep the **last 30** returns per instrument (a ~30-day rolling window).
- Compute the **Pearson correlation** for each pair:
  ```
  corr(a,b) = Σ(aᵢ−ā)(bᵢ−b̄) / sqrt( Σ(aᵢ−ā)² · Σ(bᵢ−b̄)² )
  ```
- Output is a 5×5 matrix (Brent, WTI, HO, RBOB, Gasoil), values in [−1, 1], rounded 2 dp.
- **Expected artifact:** Gas Oil ↔ Heating Oil ≈ **1.00**, because Gas Oil is the ULSD series
  unit-converted ([§5](#5-units--the-bbl-normalization-layer)).

### 6.9 Movers (`movers()`) & ticker (`ticker()`) — live
- **Movers** = the instruments with a price, **sorted by |% change| descending**; volume
  formatted (e.g. `312000 → "312K"`).
- **Ticker** = the instruments + the four headline spreads ([§6.3](#63-headline-spreads-headlinespreads-used-by-ticker--movers)), looped for the marquee.

### 6.10 Macro block (`macro()`) — live
- Hero tiles for DXY / SPX / VIX / UST10Y from Yahoo (`val/chg/pct/spark`, with per-symbol
  precision: 2 dp for DXY/SPX/VIX, 3 dp for the 10Y yield).
- A 90-day aligned series of `{dxy, spx, vix}` for the Macro charts (aligned by trimming to the
  shortest history length).

---

## 7. EIA-derived fundamentals

All **official** (EIA), computed in [`server/sources/eia.js`](server/sources/eia.js). Values
display in MMbbl unless noted.

### 7.1 Inventory hero tiles (`inventories().heroes`)
For US Crude (`WCESTUS1`), Cushing (`W_EPC0_SAX_YCUOK_MBBL`), SPR (`WCSSTUS1`), Gasoline
(`WGTSTUS1`):
```
cur = toMM(latest weekly value)
prv = toMM(prior weekly value)
chg = cur − prv                  // week-over-week change (MMbbl)
pct = (chg / prv) × 100
```

### 7.2 PADD breakdown (`inventories().padd`)
Crude stocks for regions PADD 1–5 (`WCESTP11`…`WCESTP51`), each as `val = toMM(latest)` and
`chg = toMM(latest) − toMM(prior)`. **Consistency check:** the five PADD values sum to the
national US Crude total — a good signal the feed is coherent and live.

### 7.3 52-week crude history with a REAL 5-year seasonal band (`inventories().hist`)

> This replaced the old flat "trailing-year mean" proxy. It is now the genuine seasonal envelope.

**`seasonalBand(rows, curYear)`** builds, for each **week-of-year**, the min / max / avg across the
**5 calendar years preceding the current year** (the current year is excluded so "this year vs
history" is honest):
- `weekOfYear(period) = floor(dayOfYear / 7) + 1`.
- The window is `{curYear−1 … curYear−5}`; readings outside it are ignored.
- For each week-of-year bucket: `min`, `max`, `avg` of those prior-year MMbbl values.

The last 52 weekly crude points are then emitted with the band attached:
```
hist[i] = {
  w:     "M/D",
  total: toMM(this week's crude),
  avg5y: band[woy].avg,            // dashed comparison line
  min5y, max5y,
  band:  [min, max],               // Recharts renders a [lo,hi] dataKey as a filled envelope
}
```
So the chart shows exactly where current stocks sit inside the normal seasonal range. The
`ChartTooltip` formats the array band as "lo–hi".

### 7.4 Refinery utilization & distillate
- `refineryUtil` = latest `WPULEUS3` value (percent of operable capacity).
- `distillate` = `toMM(latest WDISTUS1)`.
- `asOf` = the period (date) of the latest crude print.

### 7.5 Weekly builds & draws (`stockFlows()`)
Week-over-week change in total crude stocks, last 20 weeks (fetched 24, differenced to 20):
```
eia[i] = toMM(crude[i].value) − toMM(crude[i−1].value)     // negative = draw (bullish)
```
Each point is labeled `M/D`. The "API" line in the chart legend is **modeled** (the American
Petroleum Institute series is members-only) — the backend supplies no data for it.

### 7.6 Calendar priors (`weeklyChanges()`)
Week-over-week change (MMbbl) for crude / gasoline / distillate, used to fill the economic
calendar's **prior** column with the real last print ([§13.2](#132-economic-calendar-derivejs--calendar--schedule--eia-enrichment)).

### 7.7 Official spot (`spot()`, `/api/spot`)
`{ wti: latest(PET.RWTC.D), brent: latest(PET.RBRTE.D) }` — EIA's official daily cash quotes, a
settlement cross-check against the Yahoo futures front month. *(Probed live: WTI 95.96, Brent 98.29.)*

---

## 8. Weather-derived metrics

Computed in [`server/sources/openmeteo.js`](server/sources/openmeteo.js) from the live
temperatures ([§4.3](#43-open-meteo--weather)). The **degree-day base** is `HDD_BASE = 18.0 °C`
(≈ 65 °F).

### 8.1 Degree days (per day)
```
HDD = max(0, 18 − mean)     // heating demand: how far below base
CDD = max(0, mean − 18)     // cooling demand: how far above base
mean = (Tmax + Tmin) / 2
```

### 8.2 Regional row (`weather().regions[*]`)
For each region, using a 7-day forecast window:
```
temp     = round(today's mean)
anom     = round(today's mean − monthlyNormal[currentMonth], 1 dp)   // "vs normal"
hdd      = Σ HDD over the 7 days   (rounded)
cdd      = Σ CDD over the 7 days   (rounded)
severity = "high"  if hdd > 70  OR anom < −3
           "med"   if hdd > 35  OR |anom| > 1.5
           "low"   otherwise
```

### 8.3 Hero tiles (`weather().heroes`)
- `usHdd` = sum of HDD across the **US-group** regions (Northeast + Midwest + Gulf Coast).
- `euHdd` = sum of HDD across the **EU-group** regions (NW Europe + S. Europe).
- `asiaCdd` = sum of CDD across the **ASIA-group** region (Northeast Asia).

> The **value** of these tiles is live (real degree-day sums). The week-over-week **change** has
> no free prior-period series, so the delta shows **"—"** while the value stays live.

### 8.4 Temperature forecast vs normal (`tempForecast()`)
For NW Europe (default): fetch 7 past days + 14 forecast days; for each day compute
`anom = mean − monthlyNormal`. The series splits into `obs` (the 7 past days) and `fc` (the 14
forecast days), centered so the chart's 0-line is the climatological normal. Day labels are
`D-7 … D0 … D+13`.

---

## 9. News pipeline & FinBERT sentiment

### 9.1 Classification ([`financialjuice.js`](server/sources/financialjuice.js))
Each headline is tagged by the **first matching** rule (priority order). Short, ambiguous tokens
use word boundaries so e.g. "warned" does **not** match "war" and "Lebanon" does not match "ban":

| Tag | Trigger (regex, case-insensitive) |
| --- | --- |
| GEOPOLITICS | `sanction, strike, attack, \bwar\b, hormuz, drone, tanker seiz, red sea, ukraine, israel, \biran\b, missile, conflict, embargo` |
| OPEC | `\bopec\b, saudi, quota, \bjmmc\b, riyadh, abu dhabi` |
| FREIGHT | `tanker, freight, shipping, vessel, suez, \bport\b, baltic, cargo` |
| STOCKS | `inventor, stockpile, \beia\b, crude stocks, oil stocks, \bdrawdown\b, storage` |
| WEATHER | `hurricane, storm, cold snap, heatwave, polar vortex, \bweather\b, freeze` |
| PRODUCTS | `diesel, gasoline, petrol, refiner, crack, distillate, \bjet\b, ulsd, rbob, naphtha` |
| CRUDE | `crude, brent, \bwti\b, \bopec\+, barrel, \boil\b, petroleum, \blng\b, natural gas, nat gas` |
| MACRO (default) | `\bfed\b, dollar, inflation, interest rate, \bgdp\b, economy, treasury, \bpmi\b, \becb\b, payroll, \bcpi\b, yield, central bank` — and anything unmatched |

### 9.2 Severity
```
HIGH if title matches: surge|plunge|spike|soar|crash|\bwar\b|sanction|strike|attack|hormuz|halt|disrupt|\bcut\b|\bban\b|tumble|slump
MED  if title matches: \bopec\b|inventor|\bfed\b|\brate\b|forecast|\brise\b|\bfall\b|widen|tighten|\bpmi\b|\bcpi\b|beat|miss
LOW  otherwise
```
Severity drives the badge color and the "high-severity" alert icon.

### 9.3 FinBERT sentiment (per headline)
([`finbert.js`](server/sources/finbert.js)) Each headline is run through the model with
`top_k: 3`, returning the probability of each class. We `shape()` that into:
```
label  = argmax class ("positive" | "negative" | "neutral")
score  = P(winning class)             // confidence
pos, neg, neu = the three class probabilities
signed = P(positive) − P(negative)    // ∈ [−1, 1] — the single tone number we use downstream
```
This `sent` object rides along on each `/api/news` item and feeds the `SentimentChip` (POS / NEU /
NEG + confidence) on every news row.

### 9.4 Sentiment composite (`derive.js → sentiment()`) — derived
Two independent parts, both from live inputs:

**(a) Momentum gauges** (per commodity group), from the instrument daily % changes:
```
score(pct) = clamp( round(50 + pct × 6), 2, 98 )      // 50 = neutral; each +1% ≈ +6 points
label      = ≥70 V.Bullish · ≥55 Bullish · ≥45 Neutral · ≥30 Bearish · else V.Bearish
```
- Crude = `score( (brent.pct + wti.pct) / 2 )`
- Distillates = `score(ho.pct)` · Gasoline = `score(rbob.pct)` · Gas Oil = `score(gasoil.pct)`

**(b) News tone**, from FinBERT scores on recent headlines:
```
distribution.bullish = round( #positive / N × 100 )
distribution.bearish = round( #negative / N × 100 )
distribution.neutral = 100 − bullish − bearish
newsIndex.value      = clamp( round(50 + mean(signed) × 50), 2, 98 )   // mean tone, 50-centered
newsIndex.model      = "FinBERT"
```
**Keyword fallback** (only when FinBERT produced no scores, e.g. model still loading or
unavailable): the distribution counts bull/bear keywords (`surge|rally|tighten|draw|cut|widen|firm
|gain|rise` vs `plunge|build|glut|fall|drop|weak|ease|oversupply`), and the index is centered on
`(bullish − bearish)/2`. `model` then reads `"keyword"`. *(Probed live: `model: "finbert"`,
newsIndex 62 "Bullish" over 24 headlines.)*

---

## 10. CFTC speculative positioning (COT)

**Official**, computed in [`server/sources/cftc.js`](server/sources/cftc.js) from the
[CFTC Socrata feed](https://publicreporting.cftc.gov/resource/72hh-3qpy.json). Endpoint
`/api/cot`; UI panel `CotPanel.jsx` on the **Drivers** page ("Speculative Positioning").

For each of the four contracts ([§4.6](#46-cftc--commitments-of-traders)) we pull ~160 weeks of
Managed-Money longs/shorts and compute:
```
net        = mmLong − mmShort                               // the speculative net length
netChg     = net(this week) − net(last week)                // week-over-week swing
pctile     = round( (net − min(netHistory)) / (max − min) × 100 )   // 0 = most short ever, 100 = most long ever
extreme    = "crowded long"  if pctile ≥ 85
             "crowded short" if pctile ≤ 15
             else null                                       // contrarian flag
longShare  = round( mmLong / (mmLong + mmShort) × 100 )      // % of MM book that is long
netPctOi   = round( net / openInterest × 100, 1 )           // net as a share of total open interest
commNet    = prod_merc_long − prod_merc_short                // producers/merchants = the hedgers
hist       = last 104 weeks of net (M/D-labeled) for the area chart
```
The percentile is the key read: it places this week's net inside its own ~3-year range, so an
extreme flags **crowded** positioning (a classic contrarian setup). Output is
`{ markets:[…], asOf }`. *(Probed live: WTI as-of 2026-06-02, MM net +90,765, longShare 63%.)*

---

## 11. Seasonality

**Derived** (Yahoo monthly closes), computed in
[`server/compute/seasonality.js`](server/compute/seasonality.js). Endpoint `/api/seasonality`;
UI panel `SeasonalityPanel.jsx` on the **Analytics** page. Cached **12 h**. It reuses the same
"average across prior periods" idea as the EIA 5-year band, extended from weeks to months and to
prices. Returns **7 series** (4 price + 3 crack).

**Input:** `monthlyCloses("CL=F" | "BZ=F" | "RB=F" | "HO=F")` (~10 years, 1-month bars).

**Price series** (`priceMonths`, one per WTI / Brent / RBOB / HO):
```
for each consecutive pair of monthly closes: ret = (close_b / close_a − 1) × 100
bucket each ret by the calendar month of the later close
avgRet[m] = mean of that month's returns
hit[m]    = % of years that month was positive          // "hit rate"
path      = cumulative product of (1 + avgRet/100), indexed to 100   // the typical seasonal path
```
The chart draws `avgRet` bars (current calendar month highlighted amber) plus the cumulative
`path` line.

**Crack series** (`crackMonths`, RBOB-WTI / HO-WTI / 321-WTI; products ×42 to $/bbl): monthly
product/crude closes are aligned on shared year-months, then the **average crack LEVEL** ($/bbl)
is taken per calendar month, plus `current` = the latest month's crack:
```
RBOB-WTI = rbob×42 − wti
HO-WTI   = ho×42 − wti
321-WTI  = (2·rbob×42 + ho×42 − 3·wti) / 3
```
*(Probed live: WTI June seasonal avg, 7 series, ~9 years each.)*

---

## 12. NOAA storms & ENSO

**Official**, computed in [`server/sources/noaa.js`](server/sources/noaa.js). Both replaced former
"—" stubs, so the Storm Tracker and the ENSO tile on the **Drivers** page are now live.

### 12.1 Storm tracker (`storms()`, `/api/storms`)
From [NHC `CurrentStorms.json`](https://www.nhc.noaa.gov/CurrentStorms.json) (`activeStorms[]`):
```
winds    = Number(intensity)                       // sustained winds, knots
kind     = CLASS[classification]                   // TD/TS/HU/TY → readable label
cat      = Saffir-Simpson from winds (hurricanes only):
             ≥137 Cat 5 · ≥113 Cat 4 · ≥96 Cat 3 · ≥83 Cat 2 · ≥64 Cat 1
basin    = BASIN[binNumber prefix]                 // AL→Atlantic, EP→E.Pacific, CP→C.Pacific
severity = HU/MH/TY → (winds≥96 "high" else "med") · TS/STS → "med" · else "low"
```
plus `pressure`, `lat`, `lon`, `movement` (`dir speedkt`), `updated`. The list is **sorted
strongest-first**, returned as `{ storms[], count, asOf }`. When the feed is empty the UI shows an
honest "No active tropical cyclones" state — still LIVE-tagged. *(Probed live: 2 active E. Pacific
depressions.)*

### 12.2 ENSO / El Niño (`enso()`, `/api/enso`)
From [CPC `oni.ascii.txt`](https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt) (a whitespace
table; the ONI value is the last column `ANOM` of the last row):
```
oni   = last row's ANOM
prior = previous row's ANOM
chg   = oni − prior
phase = oni ≥ +0.5 "El Niño" · oni ≤ −0.5 "La Niña" · else "Neutral"
season, year = first two columns (e.g. "MAM", "2026")
```
*(Probed live: ONI +0.48, phase "Neutral".)*

---

## 13. Curated data (OPEC, calendar)

### 13.1 OPEC+ quotas & compliance (`derive.js → opec()`) — curated
The OPEC+ table is **hand-maintained reference data** (published policy targets + recent output
estimates). It is curated rather than fetched because EIA's STEO only publishes an OPEC-aggregate
forecast that doesn't map onto this OPEC+ table (which includes Russia and Kazakhstan).

| Member | Quota (mb/d) | Output (mb/d) |
| --- | --- | --- |
| Saudi Arabia | 9.00 | 8.97 |
| Russia | 9.00 | 9.18 |
| Iraq | 4.00 | 4.22 |
| UAE | 2.91 | 2.92 |
| Kuwait | 2.41 | 2.39 |
| Kazakhstan | 1.47 | 1.65 |
| Nigeria | 1.50 | 1.38 |
| Algeria | 0.91 | 0.90 |

```
total.quota / total.prod aggregated across members
compliance = (total.quota / total.prod) × 100        // ≥100% = at/below target; <100% = overproducing
```
> The OPEC+ **values** are curated and shown. A tile's week-over-week **change** has no free source
> and shows **"—"**.

### 13.2 Economic calendar (`derive.js → calendar()`) — schedule (+ EIA enrichment)
Built from the **real US energy-report release cadence** (times in ET):

| Day | Releases |
| --- | --- |
| Tue | API Crude Stocks (16:30) |
| Wed | EIA Crude Stocks (10:30, high), EIA Gasoline Stocks (10:30), EIA Distillate (10:30, high) |
| Thu | EIA Natural Gas Storage (10:30, high) |
| Fri | Baker Hughes Rig Count (13:00) |

The function rolls forward from today and returns the **next ~6 upcoming releases** with a weekday
+ date tag. Consensus forecasts (`fc`) are paywalled and show **"—"**. The enrichment: the
`/api/calendar` route injects the **real prior** for EIA Crude / Gasoline / Distillate from the
latest live weekly builds (`weeklyChanges()`, [§7.6](#76-calendar-priors-weeklychanges)), so those
`prev` cells are genuine numbers. *(Probed live: EIA Crude prev −8.0M, Gasoline +3.4M, Distillate
+1.5M.)*

---

## 14. Modeled / no-free-source items → shown as "—"

These values would require **paywalled** feeds and cannot be responsibly curated, so per the
project's honesty rule the dashboard shows **"—"** in their place (with a hover note explaining
why). Where a **chart** would otherwise be empty, the modeled chart line is **kept and clearly
badged "Modeled"** (a deliberate choice to preserve the visual), while the scalar values around it
dash.

| Item / panel | Endpoint | Why there is no free source | What would provide it |
| --- | --- | --- | --- |
| Tanker rates (VLCC/Suezmax/Aframax TCE), BDI | `/api/freight` | Baltic Exchange indices are licensed | Baltic Exchange, Clarksons |
| Freight **route spreads** ($/bbl) | `/api/freight` | Worldscale route economics are commercial | Worldscale + broker assessments |
| **Port congestion** % and queue delay | `/api/freight` | Requires real-time AIS / port-call data | MarineTraffic, Kpler, Vortexa |
| **Baker Hughes rig count** | `/api/rigs` | Baker Hughes publishes Excel only — no free API | Baker Hughes (manual/licensed) |
| **OPEC+ spare capacity** | (client) | No free authoritative real-time series | EIA STEO / IEA (licensed) |
| **Global crude storage** % (OECD, China SPR, ARA, Cushing fill, floating) | (client) | Tank-level data is commercial | Kpler, Vortexa, IEA |
| **Per-PADD refinery utilization** | (client) | EIA publishes only the **national** figure | (no free per-PADD breakdown) |
| **Crack 60-day history** & its hi/lo/avg/change | (client) | No free intraday crack-history series | exchange/assessment history (licensed) |

> **Note on `freight`/`rigs` endpoints:** the backend produces a *deterministic, day-seeded
> synthetic* series for these (so a kept chart line is stable within a day). The frontend treats
> the source as **modeled**, so `<Sourced source="modeled">` renders **"—"** for every scalar
> while the chart line is drawn and badged "Modeled". No fabricated number is ever presented as
> real.

**What graduated OUT of this list** (now live, no longer "—"): the **forward-curve term structure**
(M2–M12) and C1–C12 slope ([§6.6](#66-forward-curves-real--forwardcurves)), the **storm tracker**
and **ENSO** index ([§12](#12-noaa-storms--enso)), and the **5-year inventory band**
([§7.3](#73-52-week-crude-history-with-a-real-5-year-seasonal-band-inventorieshist)).

**How the dash is implemented (consistent and reversible):**
- A source whose kind is **modeled** causes `<Sourced>` to render **"—"** instead of its child.
- `HeroCard` renders a clean "—" tile (no delta, no fabricated sparkline) when its source is modeled.
- `fmt`, `fmtSigned`, and `Delta` are null-safe: any `null/NaN` value renders the dash too.

---

## 15. Caching, refresh cadence & failure handling

### Backend cache TTLs ([`server/lib/cache.js`](server/lib/cache.js) + each source)

| Data | TTL | Rationale |
| --- | --- | --- |
| Yahoo chart (prices/macro) | 45 s | intraday; polled every 30 s |
| Yahoo forward-curve contracts (`curve:prices`) | 10 min | deferred contracts settle ~daily |
| Yahoo monthly closes (seasonality) | 12 h | monthly bars move slowly |
| EIA series | 6 h | underlying data is weekly |
| Open-Meteo (weather + forecast) | 1 h | model refreshes hourly |
| Financial Juice news | 4 min | fast wire, but be polite |
| NOAA storms | 30 min | NHC updates a few times a day |
| NOAA ENSO (ONI) | 12 h | monthly index |
| CFTC COT | 6 h | weekly release |
| Seasonality | 12 h | derived from monthly bars |

The cache also implements **stale-while-error**: if an upstream refresh fails but we have a
previous good value, we serve the stale value instead of erroring (`cached()`). `fetchJSON` /
`fetchText` add a 12 s timeout (`AbortController`) and the browser-UA header.

### Frontend poll intervals (`useLive.REFRESH`)

| Interval | Value | Used by |
| --- | --- | --- |
| `fast` | 30 s | instruments, ticker, movers, macro, cracks |
| `slow` | 5 min | series, correlation, curves, sentiment, freight, rigs, news, cot, seasonality |
| `hourly` | 15 min | inventories, weather, calendar, storms, enso |

### The fallback chain (per panel)

1. **Live** — `/api/*` returns 200 → render live data; `live = true`.
2. **Last good** — a later poll fails → keep the previous successful value; `stale = true`.
3. **Seeded sample** — the very first poll fails (backend down) → use
   [`src/data/mock.js`](src/data/mock.js); the **offline banner** appears.

This is why a dashboard with **no backend** looks completely static: every panel is on step 3.
Start the backend (`npm run dev`) and the banner disappears as live data flows in.

---

## 16. Per-panel data lineage

| Panel / tile | Endpoint | Source kind | Core computation |
| --- | --- | --- | --- |
| Instrument hero tiles (Brent/WTI/HO/RBOB) | `/api/instruments` | live (Yahoo) | [§6.1](#61-instrument-tile-instruments) |
| Gas Oil tile | `/api/instruments` | derived | ULSD proxy [§5](#5-units--the-bbl-normalization-layer) |
| Scrolling ticker | `/api/ticker` | live + derived | [§6.3](#63-headline-spreads-headlinespreads-used-by-ticker--movers), [§6.9](#69-movers-movers--ticker-ticker--live) |
| Market Movers | `/api/movers` | live + derived | [§6.9](#69-movers-movers--ticker-ticker--live) |
| Price Action — Normalized | `/api/series` | derived | [§6.7](#67-normalized-price-series-seriesandcorrelation--series--live) |
| Correlation Matrix | `/api/correlation` | derived | [§6.8](#68-correlation-matrix-correlationmatrix--live) |
| Crack Spreads (value) | `/api/cracks` | derived | [§6.4](#64-crack-spreads-cracks) |
| Crack 60d chart stats | (client) | **modeled → "—"** | [§14](#14-modeled--no-free-source-items--shown-as-) |
| Forward Curve (chart) + C1–C12 slope | `/api/curves` | **live (Yahoo dated contracts)** | [§6.6](#66-forward-curves-real--forwardcurves) |
| Gas Oil forward curve | `/api/curves` | derived (proxied) | [§6.6](#66-forward-curves-real--forwardcurves) |
| Inter-commodity spreads | `/api/curves` | derived | [§6.5](#65-inter-commodity-spreads-interspreads--live) |
| Macro tiles + charts | `/api/macro` | live (Yahoo) | [§6.10](#610-macro-block-macro--live) |
| US Crude Inventory by PADD | `/api/inventories` | official (EIA) | [§7.1–7.2](#71-inventory-hero-tiles-inventoriesheroes) |
| US Crude Stocks 52W + 5y band | `/api/inventories` | official (EIA) | [§7.3](#73-52-week-crude-history-with-a-real-5-year-seasonal-band-inventorieshist) |
| Refinery utilization / distillate | `/api/inventories` | official (EIA) | [§7.4](#74-refinery-utilization--distillate) |
| Weekly Builds & Draws | `/api/stockflows` | official (EIA) | [§7.5](#75-weekly-builds--draws-stockflows) |
| EIA official spot | `/api/spot` | official (EIA) | [§7.7](#77-official-spot-spot-apispot) |
| Sentiment gauges + news index | `/api/sentiment` | derived (FinBERT + momentum) | [§9.4](#94-sentiment-composite-derivejs--sentiment--derived) |
| News rows + per-headline chip | `/api/news` | live (FJ) + derived (FinBERT) | [§4.4](#44-financial-juice--news), [§9](#9-news-pipeline--finbert-sentiment) |
| Weather Risk + degree-day tiles | `/api/weather` | live (Open-Meteo) | [§8](#8-weather-derived-metrics) |
| Temperature Forecast vs Normal | `/api/weather` | live (Open-Meteo) | [§8.4](#84-temperature-forecast-vs-normal-tempforecast) |
| Economic Calendar | `/api/calendar` | schedule (+EIA prev) | [§13.2](#132-economic-calendar-derivejs--calendar--schedule--eia-enrichment) |
| OPEC+ Production & Compliance | `/api/opec` | curated | [§13.1](#131-opec-quotas--compliance-derivejs--opec--curated) |
| Speculative Positioning (COT) | `/api/cot` | official (CFTC) | [§10](#10-cftc-speculative-positioning-cot) |
| Seasonality | `/api/seasonality` | derived (Yahoo) | [§11](#11-seasonality) |
| Storm Tracker | `/api/storms` | official (NOAA NHC) | [§12.1](#121-storm-tracker-storms-apistorms) |
| ENSO / El Niño tile | `/api/enso` | official (NOAA CPC) | [§12.2](#122-enso--el-niño-enso-apienso) |
| Port Congestion / Tanker Rates / Routes | `/api/freight` | **modeled → "—"** (chart kept) | [§14](#14-modeled--no-free-source-items--shown-as-) |
| Rig Count | `/api/rigs` | **modeled → "—"** (chart kept) | [§14](#14-modeled--no-free-source-items--shown-as-) |
| Alerts (bell + toasts) | (client) | derived from live polls | [§17.4](#174-alerts-client-side) |

---

## 17. Quick-reference tables

### 17.1 Endpoints ([`server/index.js`](server/index.js))

| Endpoint | Returns | Source |
| --- | --- | --- |
| `GET /api/health` | `{ ok, time, eia, finbert, sources{…} }` | meta |
| `GET /api/sources` | provenance manifest (which feed backs which endpoint) | meta |
| `GET /api/instruments` | 5 instrument tiles | yahoo (+ derived gas oil) |
| `GET /api/ticker` | ticker rows | yahoo + derived |
| `GET /api/movers` | movers, sorted by \|%\| | yahoo + derived |
| `GET /api/series` | normalized 90D series | derived |
| `GET /api/correlation` | 5×5 matrix | derived |
| `GET /api/cracks` | 10 crack definitions + values | derived |
| `GET /api/curves` | real forward curves + inter-spreads | yahoo + derived |
| `GET /api/macro` | DXY/SPX/VIX/UST10Y + series | yahoo |
| `GET /api/inventories` | heroes, PADD, 52W hist + 5y band, refinery util | EIA |
| `GET /api/stockflows` | 20-week WoW crude builds/draws | EIA |
| `GET /api/spot` | EIA official WTI/Brent spot | EIA |
| `GET /api/opec` | quotas, output, compliance | curated |
| `GET /api/weather` | regions, degree-day heroes, forecast | Open-Meteo |
| `GET /api/news` | up to 24 classified + FinBERT-scored headlines | Financial Juice + FinBERT |
| `GET /api/calendar` | next ~6 releases (EIA prev enriched) | schedule + EIA |
| `GET /api/freight` | tanker heroes/rates/routes/ports | modeled |
| `GET /api/rigs` | rig hero + 52W history | modeled |
| `GET /api/storms` | active tropical cyclones | NOAA NHC |
| `GET /api/enso` | ONI value + phase | NOAA CPC |
| `GET /api/cot` | Managed-Money positioning, 4 contracts | CFTC |
| `GET /api/seasonality` | 7 monthly seasonality series | derived (Yahoo) |
| `GET /api/sentiment` | momentum gauges + FinBERT news index | derived |

### 17.2 Constants

| Constant | Value | Used for |
| --- | --- | --- |
| `GAL_PER_BBL` | 42 | $/gal → $/bbl |
| `BBL_PER_MT_GASOIL` | 7.45 | $/mt ↔ $/bbl for Gas Oil |
| `HDD_BASE` | 18.0 °C | heating/cooling degree-day base |
| EIA `toMM` divisor | 1000 | thousand bbl → MMbbl |
| Momentum score slope | ×6 per 1% | sentiment gauge |
| FinBERT index slope | ×50 on mean signed | news index |
| Curve `FRESH_LAG` | 30 h | drop a stale expiring front |
| Curve `CURVE_HORIZON` | 15 | probe extra months to land 12 |
| COT extreme thresholds | ≥85 / ≤15 pctile | crowded long / short |
| Seasonal band window | 5 prior calendar years | EIA inventory envelope |

### 17.3 Source links (all clickable)

| Source | Site | Exact endpoint |
| --- | --- | --- |
| Yahoo Finance | [finance.yahoo.com](https://finance.yahoo.com) | [chart API](https://query1.finance.yahoo.com/v8/finance/chart/CL=F?range=1d&interval=1d) |
| EIA Open Data v2 | [eia.gov/opendata](https://www.eia.gov/opendata/) ([register](https://www.eia.gov/opendata/register.php)) | [seriesid route](https://api.eia.gov/v2/seriesid/PET.WCESTUS1.W) |
| Open-Meteo | [open-meteo.com](https://open-meteo.com) | [forecast API](https://api.open-meteo.com/v1/forecast?latitude=40.71&longitude=-74&daily=temperature_2m_max,temperature_2m_min) |
| Financial Juice | [financialjuice.com](https://www.financialjuice.com) | [RSS feed](https://www.financialjuice.com/feed.ashx?xy=rss) |
| NOAA NHC | [nhc.noaa.gov](https://www.nhc.noaa.gov) | [CurrentStorms.json](https://www.nhc.noaa.gov/CurrentStorms.json) |
| NOAA CPC | [cpc.ncep.noaa.gov](https://www.cpc.ncep.noaa.gov) | [oni.ascii.txt](https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt) |
| CFTC COT | [cftc.gov COT](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm) | [Socrata 72hh-3qpy](https://publicreporting.cftc.gov/resource/72hh-3qpy.json) |
| FinBERT | [ProsusAI/finbert](https://huggingface.co/ProsusAI/finbert) | [Xenova/finbert ONNX](https://huggingface.co/Xenova/finbert) · [Transformers.js](https://github.com/huggingface/transformers.js) |

### 17.4 Alerts (client-side)

The Alerts system ([`src/lib/alerts.jsx`](src/lib/alerts.jsx)) is **fully client-side** — it polls
`instruments` / `cracks` / `curves`, flattens them into alertable metrics (prices, daily move %,
cracks, curve slopes), and evaluates **edge-triggered** threshold rules (fire once on cross,
re-arm after crossing back). It also has an **auto-watch** "drastic move" detector on the majors.
Rules and fired events persist to `localStorage`; fires raise a bell badge + toast + browser
Notification. No backend, no account, no external data of its own.

---

## 18. Honest caveats & known limitations

- **All seven live feeds were verified connected and replying** at the time of writing: every
  `/api/*` endpoint returned `HTTP 200`, `eia: live`, `finbert: live`, and the data was sensible
  (live prices, a real 12-point forward curve, COT as-of 2026-06-02, ONI +0.48, weather anomalies,
  24 FinBERT-scored headlines). No source was broken.
- **Yahoo Finance is an unofficial endpoint.** Free and stable but not contractually guaranteed;
  the browser-UA header and 45 s cache keep it reliable in practice.
- **Overnight/closed-market prices look frozen** because there are no new prints — that is real
  behavior, not a disconnect. Verify "live" via the status bar / banner, or that values differ
  from the seeded fallback.
- **Gas Oil is a ULSD proxy** ([§5](#5-units--the-bbl-normalization-layer)), so its correlation
  with Heating Oil is ~1.0 by construction, and its forward curve is the ULSD curve shape scaled
  to the live front.
- **FinBERT sentiment is a model read, not a forecast.** It scores *headline tone*; treat the news
  index as a tone gauge, not a price signal. If the model can't load, it transparently degrades to
  the keyword heuristic (`/api/health` and `sentiment.model` say which is active).
- **Financial Juice is a broad financial wire**, so the news panel includes macro/equities
  headlines alongside energy; use the tag filters to narrow.
- **NHC covers Atlantic + E/C Pacific only** (its remit). That's the relevant basin set for US
  Gulf oil/gas; storms elsewhere won't appear.
- **EIA's free API rate-limits by IP** and can return slow HTML/504 pages under burst load (e.g.
  two dev servers + manual tests at once). When that happens inventories 503 and the UI shows the
  seeded fallback — transient, recovers on cooldown.
- **Security note:** `fetchJSON` error messages currently echo the full request URL, which for EIA
  includes the `api_key` in plaintext logs / 503 bodies. It's a free, low-value key, but consider
  redacting the query string in error messages.
- **Modeled items show "—" by design** ([§14](#14-modeled--no-free-source-items--shown-as-)).
  They are not failures — they mark exactly where a paid feed would be required to show a real
  number. The economic calendar's consensus `fc` is "—" for the same reason (only the EIA *prior*
  is enriched).
- **Install quirk:** the repo pins `vite ^8` while `@vitejs/plugin-react` peers ≤7 — install with
  `--legacy-peer-deps`.

---

*This document reflects the code in `server/` and `src/` as of this writing. If a formula,
constant, series ID, or provenance changes, update the relevant section here so it stays the
single source of truth for the dashboard's data lineage.*
