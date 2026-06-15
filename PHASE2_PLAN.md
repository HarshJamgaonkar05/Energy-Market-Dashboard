# Phase 2 — Regime-Based Market Analysis & Signal Generation

**Goal:** move from a market *information* platform (Phase 1) to a market *analysis engine*.
Classify market regimes, segment history by regime, fit regression models per regime,
and surface ranked, explainable analytical opportunities for spreads and butterflies —
all visible in the dashboard.

**Design principles (from the brief):** robustness, interpretability, and the ability to
explain *why* an opportunity is highlighted under the current regime.

---

## 0. Architecture

A three-layer pipeline that mirrors Phase 1's existing **precompute → JSON → serve** pattern
(the same shape as [build-history.js](server/scripts/build-history.js) → `history.json` → Node).

```
  RAW DATA                      PYTHON BATCH (analytics/)            NODE (server/)            REACT (src/)
  ────────                      ────────────────────────            ──────────────            ───────────
  /Data/*.csv  ──┐
  history.json ──┼─► build_panel.py ─► panel.parquet ─► regimes.py ──► regimes.json ─┐
  EIA weekly   ──┤                                     models.py  ──► models.json   ─┼─► regime.js ─► /api/regime/*  ─► Regime.jsx
  Yahoo macro  ──┘                                     signals.py ──► signals.json  ─┘                /api/signals
```

**Why a Python batch layer (decided):** ridge/lasso/rolling/regime regressions and HMM
clustering are mature in `scikit-learn` / `statsmodels`; reimplementing them in JS would be
error-prone and hard to validate. Python runs **offline/on a schedule**, emits static JSON
artifacts, and the live Node server stays thin — it just serves those artifacts and overlays
today's live front-month price from Yahoo. No new runtime in the hot path.

**Decided scope:** the raw term-structure CSVs are available, so we **extend the distiller to
keep daily M1/M2/M3… closes**, unlocking real calendar spreads *and* butterflies as historical
time series — not just the single latest-curve snapshot we have today.

---

## 1. Data foundation

### 1.1 Extend the history distiller — `server/scripts/build-history.js`

Today [processFile()](server/scripts/build-history.js#L48) keeps only the front-month daily
close (`c1`) plus one final-row curve snapshot. We extend it to also keep a **daily term strip**.

- For each UTC day, capture the day's last non-empty `c1..cK` weighted-mids (K = 6 is enough for
  M1–M2, M2–M3 spreads and the M1·M2·M3 fly; keep 12 if cheap).
- Add a `term` field to each instrument:
  ```json
  "wti": {
    "daily":  [["2021-01-04", 47.62], ...],          // unchanged (back-compat)
    "term":   [["2021-01-04", [47.62, 47.40, 47.18, ...]], ...],   // NEW: daily M1..MK
    "curve":  [{ "m": "M1", "contract": "...", "v": ... }, ...],   // unchanged
    "asOf":   "2026-05-22"
  }
  ```
- **Back-compatible:** `daily` and `curve` keep their current shape, so existing
  [history.js](server/lib/history.js), [markets.js](server/compute/markets.js), and
  [seasonality.js](server/compute/seasonality.js) are untouched.
- **Prerequisite:** drop the raw CSVs back into `/Data/` (`CL_data.csv`, `LCO_data.csv`,
  `HO_data.csv`, `LGO_data.csv`) and re-run `node server/scripts/build-history.js`.
- Add a tiny accessor `termCloses(id)` to [history.js](server/lib/history.js) so both Node and
  the Python step can read the strip. (Python reads the JSON directly.)

### 1.2 Feature panel — `analytics/build_panel.py` (NEW)

Assembles **one row per trading day, 2021→present** — the single substrate for both regime
classification and regression.

| Group | Features |
|---|---|
| Prices | WTI, Brent, HO, Gas Oil (front), RBOB (Yahoo 2y) |
| Inter-commodity spreads | Brent–WTI, HO–GasOil, RBOB–HO, RBOB–GasOil |
| Cracks ($/bbl) | HO–WTI, HO–Brent, GasOil–Brent, 3:2:1 (needs RBOB) |
| Calendar spreads | per instrument: M1–M2, M2–M3, M1–M6 (from new `term`) |
| Butterflies | per instrument: M1 − 2·M2 + M3 (calendar fly); inter-commodity fly |
| Curve state | front-vs-back slope, backwardation/contango flag |
| Volatility | 20d realized vol of returns (per instrument + per spread) |
| Inventory | EIA crude / distillate / gasoline level, WoW change, **z-score vs 5y seasonal band** (reuse the band logic from [eia.js](server/sources/eia.js#L62)), refinery utilization |
| Seasonal | month, heating/driving/shoulder season flag |
| Macro | DXY, VIX, SPX, UST10Y (pull **multi-year** daily from Yahoo, not the 90d the live `macro()` keeps) |

- Weekly EIA features are **forward-filled** onto the daily index.
- Output: `analytics/out/panel.parquet` (+ a `panel.csv` for eyeballing).
- EIA pull is cached to `analytics/cache/eia/*.json` so reruns don't hammer the API.

---

## 2. Regime classification — `analytics/regimes.py` (NEW)

**Interpretable-first, with an unsupervised cross-check** (the brief stresses explainability).

### 2.1 Rule-based dimensions (the primary, explainable classifier)
Each of the brief's five dimensions → a discrete state, computed from the panel:

| Dimension | States | Rule |
|---|---|---|
| Inventory | Tight / Balanced / Oversupplied | crude+distillate seasonal z-score thresholds (e.g. z < −0.5 / −0.5..0.5 / > 0.5) |
| Term structure | Backwardation / Flat / Contango | sign & magnitude of M1–M12 (or M1–M6) slope |
| Volatility | Low / Normal / High | realized-vol percentile (e.g. <33 / 33–66 / >66) + VIX/OVX overlay |
| Seasonality | Heating / Driving / Shoulder | calendar month |
| Trend | Up / Range / Down | front vs 50/200-day moving averages |

The **composite regime** is the tuple of states (plus a small set of human-named "headline"
regimes, e.g. *"Tight-Backwardated-HighVol"*). Because it's rule-based, every classification is
fully explainable — we can list exactly which driver put us in the regime.

### 2.2 Unsupervised cross-check
Fit **HMM** (`hmmlearn`) and **k-means/GMM** (`sklearn`) on the standardized panel. HMM fits
naturally — regimes are persistent states with transition dynamics. We use this to (a) validate
the rule-based regimes, (b) characterize each cluster, and (c) surface transition probabilities.
The rules stay the headline; clustering is the supporting evidence.

### 2.3 Historical regime database + metrics
Label **every historical day** with its regime. Emit `regimes.json`:
```json
{
  "current": { "label": "Tight-Backwardated-HighVol", "asOf": "...",
               "dimensions": { "inventory": {"state":"Tight","z":-0.8,"driver":"..."}, ... } },
  "history": [ { "date":"...", "label":"..." }, ... ],
  "catalog": [ { "label":"...", "n": 142, "share": 0.11, "avgDurationDays": 18,
                 "sufficient": true } ],          // sufficiency flag if n < threshold
  "transitions": { "from→to": prob, ... }
}
```
Per regime we also store the **spread/fly behaviour**: n, mean/median level, vol, percentile
bands, mean-reversion half-life, hit rates. (The sufficiency check guarantees each regime has
enough observations for meaningful stats — flagged when thin.)

---

## 3. Regression stack — `analytics/models.py` (NEW)

For each spread/fly target, fit and compare a ladder of models (the brief's "compare across
conditions rather than one universal model"):

1. **OLS** — interpretable baseline → per-spread "fair value" + coefficients.
2. **Ridge / Lasso** — regularization for collinear energy features; **Lasso drives feature
   selection** (which drivers actually matter).
3. **Rolling regression** — e.g. 120-day window → **time-varying betas** = relationship
   stability over time.
4. **Regime-specific regression** — separate fit *within each regime*; compare coefficients and
   R² across regimes.

**Evaluation:** walk-forward / out-of-sample R², residual diagnostics (stationarity,
autocorrelation), coefficient stability. Emit `models.json`:
```json
{ "brent-wti": {
    "global":  { "r2": 0.71, "coef": {...}, "fairValue": [{"date":"...","fv":...,"actual":...}] },
    "byRegime":{ "Tight-Backwardated-HighVol": { "r2":0.83, "coef":{...}, "n":142 }, ... },
    "rollingBeta": [{"date":"...","betas":{...}}],
    "selectedFeatures": ["inv_z","rvol_20","curve_slope"] } }
```

---

## 4. Signal generation — `analytics/signals.py` (NEW)

- **Residual = actual − regime-conditioned fair value** (use the current regime's model).
- **Rank** each opportunity by a composite score:
  - **Magnitude** — standardized residual (σ from fair value within the regime).
  - **Confidence** — regime model R² and observation count `n`.
  - **Robustness** — agreement across OLS/Ridge/rolling, residual mean-reversion (half-life).
- Emit `signals.json`:
```json
{ "asOf":"...", "regime":"Tight-Backwardated-HighVol",
  "opportunities": [
    { "spread":"gasoil-brent", "actual": 24.1, "expected": 19.8, "residualZ": 2.3,
      "direction":"rich", "confidence": 0.81, "robustness":"high",
      "rationale":"In Tight-Backwardated regimes (n=142, R²=0.83), the Gas Oil crack averages
                   ~$20 and the model expects $19.8 given current inventory z (−0.8) and 20d vol.
                   Actual is +2.3σ rich; residuals mean-revert with a ~9-day half-life." } ] }
```
The `rationale` is generated from the model facts (regime, drivers, expected vs actual,
confidence) — explainable by construction.

---

## 5. Orchestration — `analytics/` plumbing (NEW)

- `analytics/run.py` — runs `build_panel → regimes → models → signals` end to end, writing all
  JSON into `server/data/` (next to `history.json`) so Node loads them with no path juggling.
- `analytics/requirements.txt` — `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `hmmlearn`,
  `pyarrow`, `requests`.
- `analytics/README.md` — how to run; cadence (e.g. nightly / on EIA release day).
- `package.json` — add `"analytics": "python analytics/run.py"` for convenience.
- Artifacts (`regimes.json`, `models.json`, `signals.json`) committed like `history.json` is, so
  the deployed Space serves them without needing Python at runtime.

---

## 6. Node serving layer

- **`server/compute/regime.js` (NEW)** — load the three JSON artifacts (cached, like
  [history.js](server/lib/history.js)); expose `currentRegime()`, `regimeHistory()`,
  `regression(spread)`, `signals()`. Overlay **today's live spread value** (from the existing
  Yahoo instruments) onto the precomputed fair value so the "actual vs expected" is current.
- **`server/index.js`** — add routes alongside the existing ones ([index.js](server/index.js#L84)):
  ```
  GET /api/regime/current      GET /api/regime/history
  GET /api/regression/:spread  GET /api/signals
  ```
- **`server/lib/sources.js`** — add a `regime` source descriptor and `ENDPOINT_SOURCES` entries
  (kind: `derived`, "computed offline from the historical dataset + EIA fundamentals") so the new
  panels carry provenance badges like every other panel.

---

## 7. Frontend — new "Regime & Signals" page

- **`src/pages/Regime.jsx` (NEW)** — registered in [PAGES](src/App.jsx#L40) and
  [NAV](src/components/layout/Sidebar.jsx#L7) (icon e.g. `Activity` / `Gauge`). Sections:
  1. **Current Regime card** — composite label + per-dimension state chips with the *driver*
     behind each (inventory z, vol percentile, curve state, season), plus a regime-history strip
     (timeline of past regimes).
  2. **Regime explorer** — pick a regime → its historical spread stats, sample periods,
     transition probabilities, sufficiency badge.
  3. **Regression panel** — per spread: fair-value-vs-actual chart, coefficients / Lasso-selected
     features, R², rolling-beta line.
  4. **Ranked Opportunities table** — spread/fly · regime · expected vs actual · residual σ ·
     confidence · robustness · plain-English rationale (expandable).
- **`src/lib/useLive`** — reuse as-is; the four endpoints poll on `REFRESH.slow`.
- **`src/data/mock.js`** — add seeded fallbacks shaped like the new endpoints (so the page renders
  offline, consistent with every other panel).
- Reuse existing primitives: `Card`, `Band`, `SourceTag`, `Sourced`, `chart-theme`,
  `ResponsiveContainer`. The z-score/percentile context already in
  [Analytics CrackSpreads](src/pages/Analytics.jsx#L64) is the visual template for the residual stats.

---

## 8. Milestones (incremental, each shippable)

| Phase | Deliverable | Acceptance | Status |
|---|---|---|---|
| **P2.0 Data** | Extended distiller (`term`) + `build_panel.py` → `panel.parquet` | Panel has all features, no gaps, 2021→present | ✅ done — 1,851 rows × 59 cols |
| **P2.1 Regime** | `regimes.py` (rule-based) + `/api/regime/*` + Regime page | Live regime + drivers render; timeline + explorer populated | ✅ done — 9 regimes, 1,727 labeled days |
| **P2.2 Models** | `models.py` (OLS→Ridge/Lasso→rolling→regime) + `/api/regression/:spread` + panel | Fair-value vs actual chart; coefficients; walk-forward R² reported | ✅ done — 12 models, walk-forward OOS R² |
| **P2.3 Signals** | `signals.py` + `/api/signals` + Ranked Opportunities table | Ranked list with explanations renders end-to-end | ✅ done — 12 ranked, dual-method corroboration |
| **P2.4 (opt.)** | HMM/clustering cross-check + transition matrix in Regime explorer | Clusters compared to rule-based regimes | ⏳ optional |

**Implementation notes (P2.2–P2.3 as built):**
- `models.py` fits each spread on 11 fundamental/macro drivers (no other prices → no circularity): standardized OLS (driver importance), RidgeCV + LassoCV (regularization + selection), 120d rolling OLS (β stability), and a separate OLS per sufficient regime. The displayed **fair value is walk-forward** (expanding window, refit every 21d) so residuals never see their own data; that same walk-forward gives the honest OOS R². Result: cracks moderately predictable (rbob_ho 0.39, 3:2:1 0.35, ho_wti 0.31 OOS), calendar spreads weaker, butterflies/Brent–WTI near-unpredictable from fundamentals (negative OOS) — the model-quality differentiation the brief asked for.
- `signals.py` ranks opportunities by **dislocation × confidence × robustness**, where dislocation corroborates two independent read-outs (regime-relative z **and** regression residual z), confidence = OOS R² + regime sufficiency, robustness = sign agreement + mean-reversion half-life. Each carries a generated plain-English rationale.
- Served via `/api/regression`, `/api/regression/:spread`, `/api/signals`; the Regime page now has a **Ranked Opportunities** table (expandable rationale) and a **Fair-Value Models** panel (actual-vs-fv chart, driver β bars, rolling β, R²-by-regime).

**Implementation notes (P2.0–P2.1 as built):**
- Distiller now emits a daily `term` strip (M1–M12, $-converted in the panel); `history.json` grew 151 KB → 829 KB, back-compatible.
- Headline regime is **Inventory × Volatility** (not × term-structure): 2021–2026 is ~95 % backwardated, so structure doesn't partition the sample — it's kept as a recorded dimension + regression feature. All five dimensions still drive the Current-Regime card.
- Analytics layer: `analytics/` venv (pandas/numpy/sklearn/statsmodels/hmmlearn), `run.py` orchestrator, artifacts written to `server/data/`. `npm run analytics` runs it.
- Served via `server/compute/regime.js` (hot-reloads on file mtime) → `/api/regime/{current,catalog,history}` → new **Regime & Signals** page (Current Regime card, Regime Explorer with per-regime spread stats + transitions, Regime Timeline).

---

## 9. Risks & open items

- **RBOB history is short** (~2y from Yahoo vs ~5y dataset) — 3:2:1 crack and RBOB spreads have
  fewer observations per regime; flag where sufficiency is thin.
- **Macro history depth** — need a multi-year Yahoo daily pull for DXY/VIX/etc.; confirm Yahoo
  returns enough history for these symbols.
- **Regime granularity vs sufficiency** — too many composite states → thin buckets. Start coarse
  (3 states × key dimensions), merge rare regimes, expand only where `n` supports it.
- **Look-ahead bias** — all regime labels, z-scores, and model fits used for a given day must use
  only data available up to that day (walk-forward); the seasonal band already excludes the
  current year, which is the right instinct to carry through.
- **Artifact freshness** — decide the batch cadence (nightly / on EIA Wednesday release). Live
  prices stay real-time via the Node overlay; the *models* refresh on the batch schedule.
