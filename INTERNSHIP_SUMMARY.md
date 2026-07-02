# Energy Markets Internship — One-Page Summary Report

**Author:** Harsh Jamgaonkar · **Deliverable:** Voltaire Energy Terminal + supporting studies · **As of:** 1 July 2026

**What it is.** A single, live energy-markets intelligence terminal (React/Vite front end, Express/Node API, offline Python analytics) that turns free/open data into an interpretable, regime-aware read on crude and products — plus four standalone quantitative studies. Everything is **provenance-tagged** (every number links to its source), **leak-free** (walk-forward, no look-ahead), and honest about its own limits. Deployed to Hugging Face Spaces (Docker, port 7860). Ten dashboard sections; ~30 API endpoints; a *precompute → JSON → serve* architecture so heavy statistics run on a schedule and the live server stays thin.

---

## 1. Projects, analyses & key insights

| # | Project | What it does | Key insight / result |
|---|---|---|---|
| 1 | **Voltaire Terminal** (dashboard) | 10 sections — Dashboard, Analytics, Regime & Signals, Live Backtest, Historical BT, Market Drivers, Inventories, EIA Release Lab, News, CFTC Study. Live feeds: Yahoo (prices/curves), EIA (fundamentals), CFTC (positioning), Open-Meteo/NOAA (weather/storms/ENSO), Financial Juice + FinBERT (news sentiment). | A trading view is only as good as its **context**: prices are framed by regime, curve shape, inventory state and sentiment, not shown in isolation. |
| 2 | **Regime Engine (Phase 2)** | Rule-first classifier across 5 orthogonal dimensions (inventory-z, term structure, volatility, trend, season); headline segmentation = **Inventory × Volatility**. Walk-forward fundamental fair-value regressions of 13 spreads on 13 drivers; a dislocation-signal engine ranking opportunities by magnitude × confidence × robustness. | Spread reversion edges are real **and regime-dependent**: Brent–WTI **83%** hit-rate (vs 49% baseline, +34pt edge), HO–Gasoil 76%, 3-2-1 crack 75%, WTI M1–M2 75%. The sample is ~95% backwardated, so structure is *context*, vol/inventory are the *split*. |
| 3 | **Historical Backtest** (Phase 2, daily, 5.4y) | Fundamental RV mean-reversion on WTI & Brent calendars/flies/arb, 2021–2026, walk-forward fair value, **shock-absorption** sizing vs a regime-blind control. | 161 trades, **profit factor 2.25**, win rate **67.7%**, expectancy **$320/trade**, ~30 trades/yr. Shock absorption trades **fewer, better** than the blind control — risk-adjusted, not P&L-maximised. |
| 4 | **Intraday Backtest Engine** (Phase 3) | RV mean-reversion on **15-min crude spreads** (live company feed), z-entry/z-exit, cost gate, severity-graded de-lever/stand-aside/flatten, full trade log. | A working engine + honest methodology. Gross answers *"does the signal work"*; net (≈1bp slippage) shows these small intraday moves are **where costs bite hardest** — gross ≠ tradeable. |
| 5 | **Crude Inventory Market-Impact Framework** (Phase 4) | Leak-free **expected-build model** (5-yr seasonal + balance + momentum) → **surprise** (actual − expected) → **regime-conditioned** verdict (bullish/bearish/neutral, confidence, top-3 factors, spreads most likely to move). Live engine + PDF + executed notebook + 7 figures + fact-checked research brief. | The weekly EIA number rarely moves oil by itself — the **surprise vs consensus** does, and **only when nothing bigger is happening**. Cushing near tank-tops is a non-linear **tail-risk override** (April-2020 negative WTI). |
| 6 | **EIA Release Lab** (Phase 4) | Freezes a forecast for the **next** Wed 10:30 ET crude release, grades the last print (forecast / surprise / did-price-follow scorecard), shows a regime **impact curve** (% WTI per MMbbl) and the live intraday reaction path. | Over 162 material surprises, surprise→price direction was right **61.7%** of the time — a real but modest edge that decays outside quiet, supply-driven regimes. |
| 7 | **HO–CL Distillate Crack Event Study** | Quantifies the Russia–Ukraine invasion (24 Feb 2022) on the front-month distillate crack from 1-minute tape; reusable `run_event_study()` (also Hurricane Ida). | The event didn't *bump* the crack, it **relocated** it: modest ~2.3σ day, but a **+33% level shift**, **5.3× vol expansion**, peak ~**$129/bbl** at the April ULSD squeeze. The repricing built over weeks, not in one tick. |
| 8 | **CFTC Managed-Money Positioning Study** | 547 weeks (2016–2026), official CFTC API vs EIA spot. Full econometrics: HAC p-values, cross-correlation, Granger, VAR/IRF, half-life, quantile/logit, walk-forward OOS backtest, **Benjamini-Hochberg FDR**. 8-slide deck. | Positioning is **coincident momentum** (Δpos vs same-week return +0.36), **not predictive** (all forward p ≥ 0.29; OOS Sharpe 0.18 < buy-hold 0.35). The lone "edge" fails FDR (0/12 survive). Use as a **crowding gauge**, never a standalone timing signal. |

---

## 2. Models, tools & frameworks developed

- **5-dimension regime classifier** — interpretable, threshold-based, no black box.
- **Walk-forward fundamental fair-value regressions** (OLS/Ridge/Lasso/rolling/regime-specific) — never see their own future.
- **Dislocation signal engine** — combines regime-z and residual-z, weights by OOS R², sample sufficiency and backtested edge, emits a plain-English rationale.
- **Shock-absorption risk layer** — a severity detector (vol jump, ladder step-up, z-breach, intraday spike) driving graded de-lever / stand-aside / flatten, with Sharpe/Sortino/Calmar/CVaR reporting.
- **Leak-free inventory expected-build + surprise + verdict pipeline** (one-command `run_all`).
- **Reusable event-study machinery** and a **rigorous time-series econometrics toolkit** (Granger, VAR/IRF, bootstrap CIs, FDR).
- **Data engineering:** connectors for EIA v2, CFTC Socrata, Yahoo, Open-Meteo, NOAA; FinBERT sentiment; caching with provenance; Docker/HF-Spaces deploy.

---

## 3. Key learnings

1. **Surprise beats level** — markets price the deviation from consensus, not the raw build/draw.
2. **Regime conditioning is everything** — the same signal is high-value in a quiet, supply-driven market and noise under an OPEC/geopolitical/macro override.
3. **Discipline over cleverness** — walk-forward, no look-ahead, and **multiple-testing honesty (FDR)** are what separate a real edge from "look-where-you-looked."
4. **Term structure and inventories are the purest fundamentals** — time spreads and stocks-vs-5-yr-average move ahead of, and explain, the headline price.
5. **Costs are part of the signal** — an intraday edge that survives gross can vanish net.

---

## 4. How this applies to energy-market analysis

The terminal operationalises the full analyst workflow: **read the regime → check inventories & term structure → size the surprise → weight it by the backdrop → express it in the right spread, sized for the shock.** It gives a desk (a) a live, sourced situational read, (b) pre-release base cases and post-release scorecards on the week's biggest catalyst, (c) validated relative-value dislocations with confidence, and (d) an honest account of what *doesn't* predict (positioning), so capital isn't wasted on it.

---

## 5. Grounding from *Oil Macro Trading* (course reading)

The book's framework maps directly onto what was built, and sharpened several calls:

- **Inventories as the shock absorber (Ch 6).** The EIA Wed-10:30 release, the **5-year-average** tightness metric, **days-of-forward-cover**, and Cushing as a storage tail — all are the backbone of the Inventory Framework and Release Lab. The book's "surprise vs consensus, weighted by regime" is exactly the engine's design.
- **The forward curve & time spreads (Ch 8).** Backwardation/contango and the **M1–M2 spread as a purer fundamental signal than outright price** is the term-structure dimension of the regime model and the calendar-spread structures in both backtests. The four case studies (2008, 2014, 2020, 2022) are the historical episodes the inventory research brief conditions on.
- **Benchmark relationships (Ch 9).** **Brent–WTI** and quality spreads as tradeable, fundamentally-driven differentials underpin the highest-edge structure (Brent–WTI, 83% reversion hit-rate).
- **Crack spreads & the downstream (Ch 4).** The **3-2-1 crack** and HO/gasoil cracks are core signals; the HO–CL event study is a live demonstration of a distillate-crack regime shift from a supply shock (the 2022 diesel crisis the book cites).
- **The measurement layer (Ch 7).** EIA/IEA/OPEC data hierarchy, Baker Hughes rig count as a leading shale indicator, and CFTC positioning are the exact feeds wired into the terminal — and the book's caution that positioning is a **coincident crowding gauge** independently matches the CFTC study's verdict.
- **Geopolitics & the risk-premium fade (Ch 10).** Spare capacity as "the denominator that converts news into price," and the **50–80% fade** of a spike once supply reroutes, is the intuition behind treating OPEC/geopolitical events as regime *overrides* that down-weight inventory surprises.
- **The instruments (Ch 11).** BRN/CL/RB/HO/GO contract mechanics — cash vs physical settlement, roll timing, and the **$/MT→$/bbl gasoil unit conversion** — informed correct roll handling, front-month construction and unit discipline throughout the data pipeline.

---

*Repository deliverables: `deliverables/Crude_Inventory_Framework.pdf`, `deliverables/Phase4_Release_Lab_Explained.pdf`, `HO_CL_Event_Study.ipynb/.pdf`, `CFTC_Analysis/REPORT.md` + `public/cftc/presentation.html`, `Backtesting/STRATEGY.pdf`, and the live terminal (`npm run dev`).*
