---
name: phase2-regime-engine
description: Phase 2 of the Voltaire energy dashboard — regime classification + regression signal engine; scope and key decisions
metadata:
  type: project
---

Phase 2 (started 2026-06-12) turns the Voltaire Energy Terminal from an info platform into a
market-analysis engine: classify market regimes, segment history by regime, fit
OLS/Ridge/Lasso/rolling/regime-specific regressions on spreads & butterflies, and surface ranked,
explainable opportunities in a new dashboard page. Full plan in repo `PHASE2_PLAN.md`.

Key decisions:
- **Compute stack:** Python batch layer (sklearn/statsmodels/hmmlearn) emits regimes.json /
  models.json / signals.json into `server/data/`; Node serves them and overlays live Yahoo prices.
  Mirrors the existing build-history precompute→JSON→serve pattern. No Python in the hot path.
- **Data gap (resolved):** distilled `history.json` only kept front-month daily closes + one curve
  snapshot — no term structure over time, so calendar spreads/butterflies couldn't be historical.
  User HAS the raw `/Data/*.csv` term-structure files → plan extends build-history.js to also keep a
  daily M1..MK strip (`term` field), back-compatible with existing `daily`/`curve`.
- **Approach:** interpretable rule-based regimes first (inventory z, vol percentile, curve state,
  season, trend), HMM/k-means only as a cross-check — brief stresses explainability.

Dataset reality: daily front closes 2021→present for WTI/Brent/HO/GasOil (~1300 aligned days);
RBOB only ~2y from Yahoo; weekly EIA inventories ~5y; macro needs a multi-year Yahoo pull.

Progress (as of 2026-06-15):
- **P2.0 done**: build-history.js extended to emit daily M1–M12 `term` strip (history.json 151KB→829KB,
  back-compat). `analytics/` Python layer (venv at analytics/.venv) with common.py + build_panel.py →
  analytics/out/panel.parquet (1851 rows × 59 cols). `npm run analytics` runs analytics/run.py.
- **P2.1 done**: regimes.py → server/data/regimes.json (9 regimes, 1727 labeled days). Served by
  server/compute/regime.js via /api/regime/{current,catalog,history}. New frontend page src/pages/Regime.jsx
  ("Regime & Signals" in nav). Headline regime = Inventory × Volatility (NOT term-structure — sample is
  ~95% backwardated so structure doesn't partition; kept as recorded dim + regression feature).
- **P2.2 done**: models.py → server/data/models.json (12 spreads). Each spread regressed on 11 fundamental/macro
  drivers (FEATURES list) via OLS+RidgeCV+LassoCV+120d rolling+per-regime OLS. Fair value is WALK-FORWARD
  (expanding window, refit every 21d) → honest OOS R². Served /api/regression + /api/regression/:spread.
- **P2.3 done**: signals.py → server/data/signals.json. Ranks by dislocation(regime z + residual z) × confidence
  (OOS R² + sufficiency) × robustness(sign agreement + half-life), with generated rationale. Served /api/signals.
- Frontend Regime.jsx now has SignalsTable + RegressionPanel (actual-vs-fv chart, driver β bars, rolling β,
  R²-by-regime) in addition to Current Regime / Explorer / Timeline. Full pipeline `npm run analytics` ~4.6s.
- **Remaining: P2.4 (optional)** HMM/k-means unsupervised cross-check vs the rule-based regimes.

Review sprint (2026-06-15) — 5 improvements shipped on top of Phase 2:
1. Models strengthened: added momentum features (wti_mom20, ho_mom20 from underlying prices, no leakage)
   to build_panel + models FEATURES. Lifted OOS R2 (rbob_ho 0.46, ho_wti 0.41, calendar spreads ~doubled).
2. backtest.py (new stage): validates dislocation signal mean-reversion (|residual z|>1.5 → reverts over 10d).
   Strong edge: 67-83% hit vs ~50% baseline. Feeds confidence in signals.py + shown in Regime SignalsTable.
3. Regime-conditioned correlation: regimes.py emits correlation.{all,regime} of the 4 instruments; exposed on
   /api/regime/current; Analytics CorrelationInsight shows regime vs all-history; crack panel shows "vs current
   regime" z; RegimeBadge on crack/seasonality bands.
4. Supply/demand balance: eia.supplyDemand() (production/imports/exports/refinery throughput → implied balance,
   days-of-supply, YoY) → /api/balance → SupplyDemandBalance card on Inventories.
5. Market-narrative header: regime.js buildNarrative() fuses regime+top signal+biggest mover → /api/narrative →
   NarrativeHeader banner atop Dashboard. Freight section on Drivers now has a loud SimulatedBanner (new primitive).
Pipeline now build_panel→regimes→models→backtest→signals (~5s). All builds clean, endpoints verified.
- Gotchas: Windows console is cp1252 — keep print()s ASCII or set PYTHONIOENCODING=utf-8. Compute rolling
  vol on each instrument's own dropna'd series (union index has holiday-gap NaNs that poison rolling windows).
