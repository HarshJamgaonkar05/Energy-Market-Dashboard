# Explanation — Every Data Source, Calculation & Inference

This document explains, in exhaustive detail, **where every number on the Voltaire
Terminal dashboard comes from**, how it is collected, and exactly how each derived
figure is computed. It is the authoritative reference for the data lineage of the app.

It is written so that someone who has never seen the code can understand, for any
value on screen, the answer to three questions:

1. **Where does the raw input come from?** (which external feed, which endpoint)
2. **How is it transformed?** (the exact formula, constants, and units)
3. **How trustworthy is it?** (live / official / derived / curated / modeled, and why)

> **Golden rule of this project:** we never fabricate a number and present it as real.
> If a value cannot be sourced from a free/open feed and cannot be responsibly curated,
> the UI shows an em‑dash **“—”** instead of an invented figure. See §3 and §11.

---

## Table of contents

- [0. Quick mental model](#0-quick-mental-model)
- [1. Design philosophy](#1-design-philosophy)
- [2. System architecture & request lifecycle](#2-system-architecture--request-lifecycle)
- [3. Provenance taxonomy — the six "kinds"](#3-provenance-taxonomy--the-six-kinds)
- [4. The raw data sources](#4-the-raw-data-sources)
  - [4.1 Yahoo Finance (prices, macro)](#41-yahoo-finance--prices--macro)
  - [4.2 EIA Open Data API v2 (US fundamentals)](#42-eia-open-data-api-v2--us-fundamentals)
  - [4.3 Open-Meteo (weather)](#43-open-meteo--weather)
  - [4.4 Financial Juice (news)](#44-financial-juice--news)
- [5. Units & the $/bbl normalization layer](#5-units--the-bbl-normalization-layer)
- [6. Computed market metrics](#6-computed-market-metrics)
- [7. EIA-derived fundamentals](#7-eia-derived-fundamentals)
- [8. Weather-derived metrics](#8-weather-derived-metrics)
- [9. News pipeline & sentiment](#9-news-pipeline--sentiment)
- [10. Curated data (OPEC, calendar)](#10-curated-data-opec-calendar)
- [11. Modeled / no-free-source items → shown as "—"](#11-modeled--no-free-source-items--shown-as-)
- [12. Caching, refresh cadence & failure handling](#12-caching-refresh-cadence--failure-handling)
- [13. Per-panel data lineage](#13-per-panel-data-lineage)
- [14. Quick-reference tables](#14-quick-reference-tables)
- [15. Honest caveats & known limitations](#15-honest-caveats--known-limitations)

---

## 0. Quick mental model

```
 EXTERNAL FEEDS            BACKEND (Node/Express, server/)          FRONTEND (React + Vite, src/)
 ─────────────            ────────────────────────────────         ─────────────────────────────
 Yahoo Finance  ─┐         sources/*.js  → fetch + clean            useLive() polls /api/* on a timer
 EIA v2         ─┤  ──▶    compute/*.js  → derive/normalize  ──▶    panels render data
 Open-Meteo     ─┤         lib/cache.js  → TTL cache + retry        <Sourced>/<SourceTag> show provenance
 Financial Juice─┘         index.js      → /api/* routes            falls back to src/data/mock.js on error
```

- The **backend** does all fetching and math, then serves clean JSON at `/api/*`.
- The **frontend** never calls an external API directly. It polls our own `/api/*`
  endpoints. In dev, Vite proxies `/api` → `http://localhost:3001` (the Node backend).
- If an endpoint is unreachable, the panel keeps the **last good value** or falls back to
  **seeded sample data** (`src/data/mock.js`) and an **offline banner** appears. Sample
  data is static — that is the one situation where the dashboard is *not* live.

Run both halves with **`npm run dev`** (it starts Vite **and** the backend together).
Running only the frontend (`npm run dev:web`) leaves `/api` dead and everything shows
sample data.

---

## 1. Design philosophy

The dashboard mixes data of very different quality. Rather than blur that distinction,
we make it explicit at every value:

1. **Live-first.** Anything obtainable from a free/open feed is fetched live (Yahoo, EIA,
   Open-Meteo, Financial Juice) and refreshed on a cadence appropriate to how fast it
   actually changes.
2. **Derive, don't invent.** Spreads, cracks, correlations, degree-days, and sentiment are
   *computed* from live inputs with transparent formulas (this document). They are as live
   as their inputs.
3. **Curate only what is publicly known and stable.** A small set of reference values
   (OPEC+ policy targets, the US report release calendar) are hand-maintained because they
   change rarely and are published in human-readable form, not via a free API.
4. **Otherwise show “—”.** If a value would require a paywalled feed (Baltic Exchange,
   Kpler/Vortexa, Worldscale, real-time Baker Hughes API, exchange settlement curves), and
   it cannot be curated, we **do not model or guess** it. We render **“—”** and explain why
   on hover. (This replaced an earlier "model & clearly label" approach.)
5. **Provenance is always one hover away.** Every value is wrapped so that hovering it
   reveals its source, kind, and a one-line note.

---

## 2. System architecture & request lifecycle

### Files

| Layer | Path | Responsibility |
| --- | --- | --- |
| Source adapters | `server/sources/yahoo.js`, `eia.js`, `openmeteo.js`, `financialjuice.js` | Fetch a specific upstream and return cleaned data |
| Compute | `server/compute/markets.js`, `derive.js` | Turn raw inputs into the exact shapes the UI renders |
| Cache + fetch | `server/lib/cache.js` | TTL cache; resilient `fetch` with timeout + browser UA; serves stale on error |
| Provenance | `server/lib/sources.js` ↔ `src/lib/sources.js` | The source registry (mirrored on both ends) |
| Routing | `server/index.js` | Maps `/api/*` → compute functions; adds headers, health, 404 |
| Live polling | `src/lib/useLive.js` | Frontend hook that polls an endpoint and manages fallback/stale |
| Provenance UI | `src/components/primitives/Sourced.jsx`, `Tooltip.jsx`, `SourceTag.jsx` | Hover-to-see-source |
| Fallback data | `src/data/mock.js` | Seeded sample values used only when the backend is unreachable |

### Lifecycle of one value (example: the Brent price tile)

1. The dashboard mounts `HeroCard` for Brent. `PageDashboard` calls
   `useLive("/api/instruments", HERO)`.
2. `useLive` immediately `fetch("/api/instruments")` and then re-fetches every 30 s.
3. Vite proxies that to `http://localhost:3001/api/instruments`.
4. `index.js` runs `instruments()` (in `compute/markets.js`).
5. `instruments()` calls `getQuotes(["BZ=F","CL=F","HO=F","RB=F"])` (in `sources/yahoo.js`).
6. `yahoo.js` fetches Yahoo's chart endpoint (cached 45 s in `lib/cache.js`), extracts the
   price/change/sparkline, and returns a clean object.
7. `markets.js` shapes it into `{ sym:"BRENT", val, chg, pct, bbl, spark, … }`.
8. `index.js` adds `X-Data-Source: yahoo` / `X-Data-Kind: live` headers and sends JSON.
9. `useLive` stores it; `HeroCard` renders it, wrapping the number in
   `<Sourced source="yahoo">` so hovering shows "Yahoo Finance · live".
10. If step 3–7 fails, `useLive` keeps the previous good value (or the seeded `HERO`
    fallback) and flips a `stale` flag; the status bar/banner reflect "offline".

### The route wrapper (`server/index.js`)

Every data endpoint is wrapped by `route(producer, path)`:

- Runs the producer; on success sends JSON with `Cache-Control: no-store` and the
  provenance headers `X-Data-Source` / `X-Data-Kind`.
- If the producer returns `null` (e.g. EIA with no key) → **HTTP 503** `{fallback:true}`.
- If it throws → **HTTP 503** `{error, fallback:true}` and logs a warning.
- A 503 tells the frontend "use your fallback", so panels degrade gracefully instead of
  erroring.

There is also a request logger (`[api] GET /path 200 12ms` — latency reveals a real
upstream fetch vs a ~1 ms cache hit), a richer `/api/health`, a self-describing
`/api/sources` manifest, and a JSON 404 for unknown `/api` paths.

---

## 3. Provenance taxonomy — the six "kinds"

Every value maps to exactly one **source key**, and every source key has a **kind**.
This is defined once in `server/lib/sources.js` and mirrored in `src/lib/sources.js`.

| Kind | Meaning | Shown as | Examples |
| --- | --- | --- | --- |
| **live** | Fetched fresh from a public feed | the value | Yahoo prices, Open-Meteo temps, Financial Juice news |
| **official** | Government/authoritative (also live) | the value | EIA inventories, refinery utilization, spot prices |
| **derived** | Computed on the server *from* a live feed | the value | spreads, cracks, correlation, sentiment, Gas Oil proxy |
| **curated** | Hand-maintained reference values | the value | OPEC+ quotas/output |
| **schedule** | A real-world release cadence, not a feed | times/dates | economic calendar |
| **modeled** | No free/open source and not curated | **“—”** | freight, rig count, spare capacity, storage %, etc. |

On the frontend:
- `<Sourced source="…">value</Sourced>` wraps a value. If the kind is **modeled**, it
  renders **“—”** instead of the children (so we never print an assumed number) but still
  explains "no free source" on hover.
- `<SourceTag source="…" note="…">` is the small pill on a panel header (LIVE / Modeled /
  Cached) that also explains itself on hover.
- Charts pass `source` to `ChartTooltip`, so even a hovered chart point shows its origin.

The color dot in tooltips: live = green, official = blue, derived = violet, curated/modeled
= amber, schedule = blue.

---

## 4. The raw data sources

### 4.1 Yahoo Finance — prices & macro

**File:** `server/sources/yahoo.js` · **Kind:** live · **Key:** none required.

**Endpoint (public, unofficial but stable):**
```
GET https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={range}&interval={interval}&includePrePost=false
```
A single call returns **both** a live quote (in `meta`) and the historical close series
(in `indicators.quote[0].close` aligned to `timestamp[]`).

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

> Note: **ICE Gas Oil has no free Yahoo symbol**, so it is *not* fetched directly — it is
> derived from `HO=F` (see §5). Natural gas (`NG=F`) is referenced in code comments but is
> **not** part of the active instrument set.

**Why two fetches per symbol.** `getQuote()` fetches the symbol twice:
- `range=1d, interval=1d` — used only for the **daily % change**, because on a 1-day window
  Yahoo's `meta.chartPreviousClose` is *yesterday's* close, giving the correct daily move.
- `range=3mo, interval=1d` — used for the **sparkline** (last ~30 daily closes) and the
  **history** array (≈90 days) that feeds the normalized series and correlation.

On a longer range, `chartPreviousClose` is the pre-window close, which would make the
"daily" change wildly wrong — hence the dedicated 1-day fetch.

**What `getQuote()` returns:**
```
{
  price,    // meta.regularMarketPrice (fallback: last close)
  prev,     // meta.chartPreviousClose (fallback: previousClose, then 2nd-last close)
  chg,      // price - prev
  pct,      // (chg / prev) * 100
  dayHigh, dayLow, volume, name,
  spark,    // last 30 closes as [{x:0..29, y:close}]
  history,  // [{date, close}] for the whole 3-month window
}
```

**Collection details / quirks:**
- A **browser-like `User-Agent`** header is sent (in `lib/cache.js`) — Yahoo's public chart
  endpoint returns 403 without it.
- Cached **45 s** per `(symbol, range, interval)`. The dashboard polls prices every 30 s, so
  most polls are cheap cache hits and we stay well inside Yahoo's tolerance.
- Holiday/halt gaps (null closes) are dropped when building the clean close series.
- **Overnight behavior:** crude futures trade nearly 24 h on Globex but print thinly
  overnight; outside active hours the price is the last print and can look "frozen" for
  several minutes. That is expected live behavior, not a bug.
- Per-symbol failures resolve to `null` (that instrument shows "—"/fallback) instead of
  failing the whole batch (`getQuotes`).

### 4.2 EIA Open Data API v2 — US fundamentals

**File:** `server/sources/eia.js` · **Kind:** official · **Key:** free key in `server/.env`
(`EIA_API_KEY`). Without a key these endpoints return 503 and the UI uses fallback.

**Endpoint (v2 "series by ID" route):**
```
GET https://api.eia.gov/v2/seriesid/{ID}?api_key={KEY}&sort[0][column]=period&sort[0][direction]=desc&length={N}
```
- The `{ID}` **must be the full legacy form `CATEGORY.SERIES.FREQ`** (e.g.
  `PET.WCESTUS1.W`). The bare series code (`WCESTUS1`) returns 404 on this route.
- Response shape: `{ response: { data: [ { period:"YYYY-MM-DD", value:<number> }, … ] } }`.
- We request newest-first (`direction=desc`), drop nulls, then **reverse to chronological**.
- Cached **6 hours** (the underlying Weekly Petroleum Status Report updates weekly).

**Series used:**

| Series ID | Meaning | Native unit |
| --- | --- | --- |
| `PET.WCESTUS1.W` | US commercial crude stocks **excl. SPR** | thousand bbl |
| `PET.WCSSTUS1.W` | Crude in the Strategic Petroleum Reserve | thousand bbl |
| `PET.W_EPC0_SAX_YCUOK_MBBL.W` | Cushing, OK crude stocks | thousand bbl |
| `PET.WGTSTUS1.W` | US total gasoline stocks | thousand bbl |
| `PET.WDISTUS1.W` | US distillate fuel oil stocks | thousand bbl |
| `PET.WPULEUS3.W` | Refinery % utilization of operable capacity | percent |
| `PET.WCESTP11.W` … `PET.WCESTP51.W` | Crude stocks by PADD region 1–5 | thousand bbl |
| `PET.RWTC.D` | WTI Cushing spot (daily) | $/bbl |
| `PET.RBRTE.D` | Brent Europe spot (daily) | $/bbl |

**Unit conversion.** EIA reports stocks in **thousand barrels**; we convert to **million
barrels (MMbbl)** for display:
```
toMM(kbbl) = round(kbbl / 1000, 1 dp)
```

**Helpers:** `latest(arr) = arr.at(-1).value`, `prior(arr) = arr.at(-2).value` (the
chronological last / second-last weekly prints).

### 4.3 Open-Meteo — weather

**File:** `server/sources/openmeteo.js` · **Kind:** live · **Key:** none required.

**Endpoint:**
```
GET https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}
    &daily=temperature_2m_max,temperature_2m_min&timezone=auto
    &past_days={p}&forecast_days={f}
```
For each day we take the **daily mean** as `mean = (Tmax + Tmin) / 2` (°C).

**Regions** (one representative point each; monthly mean-temp "normals" are a
climatological reference array, °C, Jan→Dec):

| Region | Group | Lat, Lon | Monthly normals (°C, Jan…Dec) |
| --- | --- | --- | --- |
| US Northeast | US | 40.71, −74.0 | −0.5, 0.5, 5, 11, 16, 21, 24, 23, 19, 13, 7, 2 |
| US Midwest | US | 41.88, −87.63 | −4, −2, 4, 10, 16, 22, 24, 23, 19, 12, 5, −2 |
| US Gulf Coast | US | 29.76, −95.37 | 11, 13, 17, 21, 25, 28, 29, 29, 27, 22, 17, 12 |
| NW Europe | EU | 52.37, 4.90 | 4, 4, 7, 10, 14, 17, 19, 19, 16, 12, 7, 5 |
| Northeast Asia | ASIA | 37.57, 126.98 | 1, 2, 7, 13, 18, 22, 26, 27, 22, 16, 9, 3 |
| S. Europe | EU | 41.90, 12.50 | 8, 9, 12, 15, 19, 24, 27, 27, 23, 18, 13, 9 |

- The **temperatures are genuinely live** (Open-Meteo refreshes hourly; cached **1 h** here).
- The **normals are constants** (NOAA-style 30-year monthly means), used as the baseline for
  the anomaly. The UI labels anomaly "vs normal" accordingly.

### 4.4 Financial Juice — news

**File:** `server/sources/financialjuice.js` · **Kind:** live · **Key:** none required.

**Endpoint (RSS):**
```
GET https://www.financialjuice.com/feed.ashx?xy=rss
```
A fast, trader-oriented financial wire (central banks, data prints, OPEC, geopolitics,
commodities, equities). Cached **4 minutes**; we keep up to **24** items.

**Item shape in the feed:**
```xml
<item>
  <title>FinancialJuice: OPEC+ signals possible production cut ...</title>
  <link>https://www.financialjuice.com/News/123/....aspx</link>
  <pubDate>Mon, 01 Jun 2026 02:01:01 GMT</pubDate>
  <guid isPermaLink="false">123</guid>
</item>
```

**Parsing pipeline (regex-based, no XML lib):**
1. Split on `<item>…</item>`.
2. Extract `<title>`, `<link>`, `<pubDate>` with a small tag matcher.
3. **Decode** XML/HTML entities (`&amp; &lt; &gt; &quot; &#39; &#xNN;`) and unwrap `CDATA`.
4. **Strip** the leading `FinancialJuice:` brand prefix from the title.
5. **De-duplicate** by exact title.
6. **Timestamp** `t` = `HH:MM` parsed from `pubDate`.
7. **Classify** into a tag and **score** a severity (below).
8. Emit `{ t, sev, src:"FINJUICE", txt, tag, url }`.

Because Financial Juice is a curated quality wire (not a noisy global crawl), we keep **all**
items rather than filtering to energy-only; the tag taxonomy + the UI's tag filter buttons
let a user narrow to OPEC / CRUDE / GEOPOLITICS, etc.

See §9 for the exact classification/severity rules.

---

## 5. Units & the $/bbl normalization layer

The five instruments quote in three different units. To compute cracks and spreads, every
product is normalized to **$/bbl**. Constants (in `compute/markets.js`):

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

ICE Gas Oil has no free live feed, so it is **derived from NYMEX ULSD (`HO=F`)** — both are
middle distillates that track each other very closely. Its provenance kind is **derived**
(not modeled), so it shows a real value, flagged with a `~` and a tooltip.

Derivation from the live ULSD `$/gal` price:
```
$/gal  ──×42──▶  $/bbl  ──×7.45──▶  $/mt
gasoilPrice($/mt) = ulsdPrice($/gal) × 42 × 7.45
```
Concretely `galToMt(gal) = gal × 42 × 7.45`. The change/percent and sparkline are converted
point-by-point the same way, and its `bbl` value rounds back via `÷ 7.45`. A consequence:
**Gas Oil's correlation and normalized line track Heating Oil almost exactly** (they share a
single underlying series) — this is expected and noted in the UI.

---

## 6. Computed market metrics

All of the following are **derived** (kind = derived) from the live Yahoo inputs above, in
`compute/markets.js`. They are as live as Yahoo.

### 6.1 Instrument tile (`instruments()`)
For each non-proxy instrument from Yahoo:
- `val` = price, rounded to 4 dp for `$/gal` instruments else 2 dp.
- `chg` = `price − prev` (same rounding).
- `pct` = `(chg / prev) × 100`.
- `bbl` = `toBbl(...)` (§5).
- `spark` = last 30 daily closes; `volRaw` = regular-market volume.

### 6.2 Daily % change
Defined entirely by Yahoo's 1-day `chartPreviousClose` (see §4.1). The colored arrow and
the ticker change both use this.

### 6.3 Headline spreads (`headlineSpreads()`, used by ticker & movers)
All in $/bbl using the normalized `bbl` values:
```
BRENT-WTI   = brent.val − wti.val                          (both already $/bbl)
3:2:1 CRACK = (2·rbob.bbl + 1·ho.bbl − 3·wti.bbl) / 3
GASOIL CRK  = gasoil.bbl − brent.bbl
RBOB CRK    = rbob.bbl − wti.bbl
```
In the scrolling ticker these spreads are shown with `chg/pct = 0` (we don't track an
intraday spread change there).

### 6.4 Crack spreads (`cracks()`)
A crack spread is the refining margin: product value minus crude cost, per barrel. The
generic formula for a definition with product legs `legs = [(product, coeff), …]`, a crude,
its coefficient `crudeC`, and a divisor `div`:

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

> Only the **current** crack value is live/derived. The **60-day crack history chart** and
> its 60d hi/lo/avg & change are **modeled** (there is no free intraday crack-history feed),
> so those scalar stats show **“—”** while the illustrative chart line is kept (see §11).

### 6.5 Inter-commodity spreads (`interSpreads()`) — live
```
Brent – WTI            = brent.val − wti.val      [$/bbl]   "Crude arb"
RBOB – Heating Oil     = rbob.val − ho.val        [$/gal]   "Gas–Heat"
Heating Oil – Gas Oil  = ho.bbl  − gasoil.bbl     [$/bbl]   "Distillate"
RBOB – Gas Oil         = rbob.bbl − gasoil.bbl    [$/bbl]   "Light prod"
```

### 6.6 Normalized price series (`seriesAndCorrelation()` → `series`) — live
- Pull each instrument's ~90-day daily-close `history` (Gas Oil reuses ULSD's history).
- **Align** on dates present in *every* series (intersection, keyed by `M/D`).
- **Index to 100** at the first aligned date: `normalized = (close / firstClose) × 100`.
This is what the "Price Action — Normalized" chart plots; it shows *relative* performance,
not absolute price.

### 6.7 Correlation matrix (`correlationMatrix()`) — live
- From the aligned closes, compute **daily simple returns**: `r_t = (c_t − c_{t-1}) / c_{t-1}`.
- Keep the **last 30** returns per instrument (a ~30-day rolling window).
- Compute the **Pearson correlation** for each pair:
  ```
  corr(a,b) = Σ(aᵢ−ā)(bᵢ−b̄) / sqrt( Σ(aᵢ−ā)² · Σ(bᵢ−b̄)² )
  ```
- Output is a 5×5 matrix (Brent, WTI, HO, RBOB, Gasoil), values in [−1, 1], rounded 2 dp.
- **Expected artifact:** Gas Oil ↔ Heating Oil ≈ **1.00**, because Gas Oil is the ULSD
  series unit-converted (§5).

### 6.8 Movers (`movers()`) & ticker (`ticker()`) — live
- **Movers** = the five instruments, filtered to those with a price, **sorted by |% change|
  descending**; volume formatted (e.g. `312000 → "312K"`).
- **Ticker** = the five instruments + the four headline spreads (§6.3), looped for the
  marquee.

### 6.9 Macro block (`macro()`) — live
- Hero tiles for DXY / SPX / VIX / UST10Y from Yahoo (`val/chg/pct/spark`, with per-symbol
  decimal precision: 2 dp for DXY/SPX/VIX, 3 dp for the 10Y yield).
- A 90-day aligned series of `{dxy, spx, vix}` for the Macro charts (aligned by trimming to
  the shortest history length).

---

## 7. EIA-derived fundamentals

All **official** (EIA), computed in `sources/eia.js`. Values display in MMbbl unless noted.

### 7.1 Inventory hero tiles (`inventories().heroes`)
For each of US Crude (`WCESTUS1`), Cushing (`W_EPC0_SAX_YCUOK_MBBL`), SPR (`WCSSTUS1`),
Gasoline (`WGTSTUS1`):
```
cur = toMM(latest weekly value)
prv = toMM(prior weekly value)
chg = cur − prv                  // week-over-week change (MMbbl)
pct = (chg / prv) × 100
```

### 7.2 PADD breakdown (`inventories().padd`)
Crude stocks for regions PADD 1–5 (`WCESTP11`…`WCESTP51`), each as `val = toMM(latest)` and
`chg = toMM(latest) − toMM(prior)`. **Consistency check:** the five PADD values sum to the
national US Crude total — a good signal that the feed is coherent and live.

### 7.3 52-week crude history (`inventories().hist`)
- `total` = last 52 weekly crude values, converted to MMbbl.
- `avg5y` = the **mean of those 52 points** (a flat trailing-year average), drawn as the
  comparison band.

> **Honest caveat:** EIA does not expose the official "5-year average" band as a series, so
> `avg5y` is a **trailing-year mean used as a proxy** and is labeled as an average in the UI.
> It is *derived from real EIA data* (not invented), which is why it is kept rather than
> dashed — but it is not literally the 5-year envelope.

### 7.4 Refinery utilization & distillate
- `refineryUtil` = latest `WPULEUS3` value (percent of operable capacity).
- `distillate` = `toMM(latest WDISTUS1)`.
- `asOf` = the period (date) of the latest crude print.

### 7.5 Weekly builds & draws (`stockFlows()`)
Week-over-week change in total crude stocks, last 20 weeks:
```
eia[i] = toMM(crude[i].value) − toMM(crude[i−1].value)     // negative = draw (bullish)
```
Each point is labeled `M/D`. The "API" line that appears in the chart legend is **modeled**
(the American Petroleum Institute series is members-only) — the backend does not supply it,
so that line has no data.

### 7.6 Official spot (`spot()`, `/api/spot`)
`{ wti: latest(PET.RWTC.D), brent: latest(PET.RBRTE.D) }` — EIA's official daily cash
quotes, a settlement cross-check against the Yahoo futures front month.

---

## 8. Weather-derived metrics

Computed in `sources/openmeteo.js` from the live temperatures (§4.3). The **degree-day base**
is `HDD_BASE = 18.0 °C` (≈ 65 °F).

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

> The **value** of these tiles is live (real degree-day sums). The week-over-week **change**
> shown on the tile has no free prior-period series, so the delta shows **“—”** while the
> value stays live (see §11).

### 8.4 Temperature forecast vs normal (`tempForecast()`)
For NW Europe (default): fetch 7 past days + 14 forecast days; for each day compute
`anom = mean − monthlyNormal`. The series splits into `obs` (the 7 past days) and `fc` (the
14 forecast days), centered so the chart's 0-line is the climatological normal.

---

## 9. News pipeline & sentiment

### 9.1 Classification (`financialjuice.js`)
Each headline is tagged by the **first matching** rule (priority order). Short, ambiguous
tokens use word boundaries so e.g. "warned" does **not** match "war" and "Lebanon" does not
match "ban":

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

### 9.3 Sentiment composite (`derive.js → sentiment()`) — derived
Two independent parts, both computed from live inputs:

**(a) Momentum gauges** (per commodity group), from the instrument daily % changes:
```
score(pct) = clamp( round(50 + pct × 6), 2, 98 )      // 50 = neutral; each +1% ≈ +6 points
label      = ≥70 V.Bullish · ≥55 Bullish · ≥45 Neutral · ≥30 Bearish · else V.Bearish
```
- Crude = `score( (brent.pct + wti.pct) / 2 )`
- Distillates = `score(ho.pct)` · Gasoline = `score(rbob.pct)` · Gas Oil = `score(gasoil.pct)`

**(b) News distribution**, from the share of recent Financial Juice headlines that read
bullish vs bearish:
```
bullish keywords: surge|rally|tighten|draw|cut|widen|firm|gain|rise
bearish keywords: plunge|build|glut|fall|drop|weak|ease|oversupply
bullish% = round(bullCount / N × 100)
bearish% = round(bearCount / N × 100)
neutral% = 100 − bullish% − bearish%      (N = number of headlines, ≥1)
```
> This is a deliberately simple keyword heuristic — a quick read of the wire's tone, not a
> trained sentiment model. Most headlines are neutral, so `neutral%` is typically large.

---

## 10. Curated data (OPEC, calendar)

### 10.1 OPEC+ quotas & compliance (`derive.js → opec()`) — curated
The OPEC+ table is **hand-maintained reference data** (published policy targets + recent
output estimates). It is curated rather than fetched because EIA's STEO only publishes an
OPEC-aggregate forecast that doesn't map onto this OPEC+ table (which includes Russia and
Kazakhstan).

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
member compliance = (quota / prod) × 100
```
> The OPEC+ **values** are curated and shown. A tile's week-over-week **change** (e.g. the
> "OPEC+ COMP" hero delta) has no free source and shows **“—”**.

### 10.2 Economic calendar (`derive.js → calendar()`) — schedule (+ EIA enrichment)
Built from the **real US energy-report release cadence** (times in ET):

| Day | Releases |
| --- | --- |
| Tue | API Crude Stocks (16:30) |
| Wed | EIA Crude Stocks (10:30, high), EIA Gasoline Stocks (10:30), EIA Distillate (10:30, high) |
| Thu | EIA Natural Gas Storage (10:30, high) |
| Fri | Baker Hughes Rig Count (13:00) |

The function rolls forward from today and returns the **next ~6 upcoming releases** with a
weekday + date tag. Consensus forecasts (`fc`) are paywalled and show **“—”**. The one
enrichment: the route (`/api/calendar`) injects the **real prior** for "EIA Crude Stocks"
from the latest live weekly build (from `stockFlows()`), so that `prev` is a genuine number.

---

## 11. Modeled / no-free-source items → shown as "—"

These values would require **paywalled** feeds and cannot be responsibly curated, so per the
project's honesty rule the dashboard shows **“—”** in their place (with a hover note
explaining why). Where a **chart** would otherwise be empty, the modeled chart line is **kept
and clearly badged "Modeled"** (a deliberate choice to preserve the visual), while the scalar
values around it dash.

| Item / panel | Why there is no free source | What would provide it |
| --- | --- | --- |
| Tanker rates (VLCC/Suezmax/Aframax TCE), BDI | Baltic Exchange indices are licensed/paywalled | Baltic Exchange, Clarksons |
| Freight **route spreads** ($/bbl) | Worldscale-based route economics are commercial | Worldscale + broker assessments |
| **Port congestion** % and queue delay | Requires real-time AIS / port-call data | MarineTraffic, Kpler, Vortexa |
| **Baker Hughes rig count** | Baker Hughes publishes Excel only — no free API | Baker Hughes (manual/licensed) |
| **OPEC+ spare capacity** | No free authoritative real-time series | EIA STEO estimates / IEA (licensed) |
| **ENSO / El Niño index** value-change | Not wired to a free climate index feed | NOAA ONI (could be added) |
| **Global crude storage** % (OECD, China SPR, ARA, Cushing fill, floating) | Tank-level data is commercial | Kpler, Vortexa, IEA |
| **Per-PADD refinery utilization** | EIA publishes only the **national** figure | (no free per-PADD breakdown) |
| **Storm tracker** entries | No free severe-weather/tropical-cyclone alert feed wired in | NOAA NHC feeds (could be added) |
| **Forward-curve term structure** (M2–M12) & calendar spreads | Exchange settlement curves are paywalled | CME/ICE settlement data (licensed) |
| **Crack 60-day history** & its hi/lo/avg/change | No free intraday crack-history series | exchange/assessment history (licensed) |

**How the dash is implemented (so it's consistent and reversible):**
- A source whose kind is **modeled** causes `<Sourced>` to render **“—”** instead of its
  child value.
- `HeroCard` renders a clean "—" tile (no delta, no fabricated sparkline, neutral accent)
  when its source kind is modeled.
- `fmt`, `fmtSigned`, and `Delta` are null-safe: any `null/NaN` value renders the dash too.
- Modeled **bars** (port congestion, per-PADD util) render as **empty tracks**; modeled
  **deltas** are removed; the **storm tracker** shows a "no live storm feed" empty state.

> **What is *kept* (not dashed):** Yahoo prices/macro, EIA fundamentals, Open-Meteo
> temps/degree-days, Financial Juice news, everything **derived** from those (spreads,
> cracks, correlation, sentiment, normalized series), OPEC+ quotas/output (**curated**), and
> **Gas Oil** (derived from the live ULSD feed).

---

## 12. Caching, refresh cadence & failure handling

### Backend cache TTLs (`lib/cache.js` + each source)

| Data | TTL | Rationale |
| --- | --- | --- |
| Yahoo chart (prices/macro) | 45 s | intraday; polled every 30 s |
| EIA series | 6 h | underlying data is weekly |
| Open-Meteo (weather + forecast) | 1 h | model refreshes hourly |
| Financial Juice news | 4 min | fast wire, but be polite |

The cache also implements **stale-while-error**: if an upstream refresh fails but we have a
previous good value, we serve the stale value instead of erroring.

### Frontend poll intervals (`useLive.REFRESH`)

| Interval | Value | Used by |
| --- | --- | --- |
| `fast` | 30 s | instruments, ticker, movers, macro, cracks |
| `slow` | 5 min | series, correlation, curves, sentiment, freight, rigs, news |
| `hourly` | 15 min | inventories, weather, calendar |

### The fallback chain (per panel)

1. **Live** — `/api/*` returns 200 → render live data; `live = true`.
2. **Last good** — a later poll fails → keep the previous successful value; `stale = true`.
3. **Seeded sample** — the very first poll fails (backend down) → use `src/data/mock.js`;
   the **offline banner** appears: *"Backend offline — every panel is showing sample data…"*.

This is why a dashboard with **no backend** looks completely static: every panel is on step
3, showing the same seeded numbers forever. Start the backend (`npm run dev`) and the banner
disappears as live data flows in.

---

## 13. Per-panel data lineage

| Panel / tile | Endpoint | Source kind | Core computation |
| --- | --- | --- | --- |
| Instrument hero tiles (Brent/WTI/HO/RBOB) | `/api/instruments` | live (Yahoo) | §6.1 |
| Gas Oil tile | `/api/instruments` | derived | ULSD proxy §5 |
| Scrolling ticker | `/api/ticker` | live + derived | §6.3, §6.8 |
| Market Movers | `/api/movers` | live + derived | §6.8 |
| Price Action — Normalized | `/api/series` | derived | §6.6 |
| Correlation Matrix | `/api/correlation` | derived | §6.7 |
| Crack Spreads (value) | `/api/cracks` | derived | §6.4 |
| Crack 60d chart stats | (client) | **modeled → “—”** | §11 |
| Forward Curve (chart) | `/api/curves` | **modeled (kept, badged)** | front = live, term = modeled §11 |
| Forward Curve C1–C12 slope | `/api/curves` | **modeled → “—”** | §11 |
| Brent–WTI M1 | `/api/curves` | derived | front-month spread |
| Calendar / inter-commodity spreads | `/api/curves` | modeled “—” / derived | §6.5, §11 |
| Macro tiles + charts | `/api/macro` | live (Yahoo) | §6.9 |
| US Crude Inventory by PADD | `/api/inventories` | official (EIA) | §7.1–7.2 |
| US Crude Stocks 52W chart | `/api/inventories` | official + derived band | §7.3 |
| Refinery utilization | `/api/inventories` | official (EIA) | §7.4 |
| Weekly Builds & Draws | `/api/stockflows` | official (EIA) | §7.5 |
| Sentiment gauges + distribution | `/api/sentiment` | derived | §9.3 |
| Weather Risk + degree-day tiles | `/api/weather` | live (Open-Meteo) | §8 |
| Temperature Forecast vs Normal | `/api/weather` | live (Open-Meteo) | §8.4 |
| Breaking News / Newswire | `/api/news` | live (Financial Juice) | §4.4, §9 |
| Economic Calendar | `/api/calendar` | schedule (+EIA prev) | §10.2 |
| OPEC+ Production & Compliance | `/api/opec` | curated | §10.1 |
| Port Congestion / Tanker Rates / Route Spreads | `/api/freight` | **modeled → “—”** (chart kept) | §11 |
| Rig Count | `/api/rigs` | **modeled → “—”** (chart kept) | §11 |
| Global Crude Storage / per-PADD util / Storm Tracker | (client / `/api/inventories`) | **modeled → “—”** | §11 |

---

## 14. Quick-reference tables

### 14.1 Endpoints (`server/index.js`)

| Endpoint | Returns | Source |
| --- | --- | --- |
| `GET /api/health` | `{ ok, time, eia, sources{…} }` | meta |
| `GET /api/sources` | provenance manifest (which feed backs which endpoint) | meta |
| `GET /api/instruments` | 5 instrument tiles | yahoo (+ derived gas oil) |
| `GET /api/ticker` | ticker rows | yahoo + derived |
| `GET /api/movers` | movers, sorted by |%| | yahoo + derived |
| `GET /api/series` | normalized 90D series | derived |
| `GET /api/correlation` | 5×5 matrix | derived |
| `GET /api/cracks` | 10 crack definitions + values | derived |
| `GET /api/curves` | forward curves + inter-spreads | modeled + derived |
| `GET /api/macro` | DXY/SPX/VIX/UST10Y + series | yahoo |
| `GET /api/inventories` | heroes, PADD, 52W hist, refinery util | EIA |
| `GET /api/stockflows` | 20-week WoW crude builds/draws | EIA |
| `GET /api/spot` | EIA official WTI/Brent spot | EIA |
| `GET /api/opec` | quotas, output, compliance | curated |
| `GET /api/weather` | regions, degree-day heroes, forecast | Open-Meteo |
| `GET /api/news` | up to 24 classified headlines | Financial Juice |
| `GET /api/calendar` | next ~6 releases (EIA prev enriched) | schedule + EIA |
| `GET /api/freight` | tanker heroes/rates/routes/ports | modeled |
| `GET /api/rigs` | rig hero + 52W history | modeled |
| `GET /api/sentiment` | momentum gauges + news distribution | derived |

### 14.2 Constants

| Constant | Value | Used for |
| --- | --- | --- |
| `GAL_PER_BBL` | 42 | $/gal → $/bbl |
| `BBL_PER_MT_GASOIL` | 7.45 | $/mt ↔ $/bbl for Gas Oil |
| `HDD_BASE` | 18.0 °C | heating/cooling degree-day base |
| EIA `toMM` divisor | 1000 | thousand bbl → MMbbl |
| Momentum score slope | ×6 per 1% | sentiment gauge |
| Yahoo cache | 45 s | price freshness |
| EIA cache | 6 h | weekly data |
| Open-Meteo cache | 1 h | hourly model |
| Financial Juice cache | 4 min | news wire |

### 14.3 EIA series IDs — see [§4.2](#42-eia-open-data-api-v2--us-fundamentals).

---

## 15. Honest caveats & known limitations

- **Yahoo Finance is an unofficial endpoint.** It's free and stable but not contractually
  guaranteed; the browser-UA header and 45 s cache keep it reliable in practice.
- **Overnight/closed-market prices look frozen** because there are no new prints — that is
  real behavior, not a disconnect. Verify "live" by checking the status bar / banner, or that
  values differ from the seeded fallback (e.g. WTI ≈ 78.92 is the mock value).
- **`avg5y` is a trailing-year mean**, used as a proxy for EIA's official 5-year band, which
  is not exposed as a series (§7.3). It is derived from real EIA data and labeled as such.
- **Gas Oil is a ULSD proxy** (§5), so its correlation with Heating Oil is ~1.0 by
  construction.
- **Sentiment is a keyword heuristic** (§9.3), not a trained model — treat it as a rough
  tone gauge.
- **Financial Juice is a broad financial wire**, so the news panel includes macro/equities
  headlines alongside energy; use the tag filters to narrow.
- **Modeled items show "—"** by design (§11). They are not failures — they mark exactly where
  a paid feed would be required to show a real number.
- **The economic calendar's forecasts (`fc`) are "—"** because consensus estimates are
  paywalled; only the EIA crude **prior** is enriched with a real number.

---

*This document reflects the code in `server/` and `src/` as of this writing. If a formula,
constant, series ID, or provenance changes, update the relevant section here so it stays the
single source of truth for the dashboard's data lineage.*
