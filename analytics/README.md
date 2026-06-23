# Voltaire — offline analytics (Phase 2 regime engine + Phase 3 strategy)

Python batch layer that turns the historical dataset + EIA fundamentals + the 1-minute
WTI/Brent feed into the **regime / regression / signal / backtest** artifacts the dashboard
serves. It follows a *precompute → JSON → serve* pattern: heavy statistics run here and write
static JSON into `server/data/`, so the live Node server stays thin and never runs Python in
the request path.

## Pipeline

| Stage | Script | Output | Phase |
|---|---|---|---|
| Feature panel | `build_panel.py` | `analytics/out/panel.parquet` | 2 |
| Regime engine | `regimes.py` | `server/data/regimes.json` | 2 |
| Regressions | `models.py` | `server/data/models.json` | 2 |
| Signal validation | `backtest.py` | `server/data/backtest.json` | 2 |
| Ranked signals | `signals.py` | `server/data/signals.json` | 2 |
| **Daily backtest** | `historical_backtest.py` | `server/data/historical_backtest.json` | 3 |
| **Intraday backtest** | `historical_intraday.py` | `server/data/historical_intraday.json` | 3 |
| **Shock study** | `shock_analysis.py` | `server/data/shock_analysis.json` | 3 |
| **Robustness** | `robustness.py` | `server/data/robustness.json` | 3 |

`regime_strategy.py` is the **shared Phase-3 core** (regime parameters, fair-value filters,
regime-conditioned z, vol-target sizing, the shock detector/response, the regime-blind control,
and the risk metrics) imported by all three backtest engines — including the live
`Backtesting/engine.py`.

## Phase 2 — the regime model

`panel.parquet` is the single feature table (one row per trading day, 2021→present): prices,
inter-commodity spreads, cracks, calendar spreads, butterflies, realized vol, curve state, EIA
inventory levels/changes/seasonal-z, seasonal flags and macro.

The **regime** is classified rule-first across five dimensions (inventory, term structure,
volatility, trend, season); the headline segmentation is **Inventory × Volatility** (the two
that actually vary across 2021–2026 — the sample is ~95% backwardated, so term structure is
recorded as context, not a split axis). Per regime we also measure each spread's mean,
dispersion, reversion half-life, and the regime-to-regime transition matrix.

The **fair-value regressions** (`models.py`) are produced **walk-forward / out-of-sample**, so
a day's fair value never sees its own or future data; that honest setup is what tells us which
spreads the model can genuinely price (strong OOS R² for the cracks, *negative* for some
butterflies — which Phase 3 then refuses to trade).

## Phase 3 — the regime-driven strategy

All three engines share `regime_strategy.py`. The regime model **drives** the strategy: a
regime-conditioned z (residual ÷ same-vol-state expanding std), per-vol-state entry/exit/stop
and max-hold (× the regime's trailing half-life), vol-target sizing, a structure whitelist, and
a shock-absorption layer (de-lever / stand-aside / flatten through volatility spikes). Each
engine also runs a **regime-blind control** so the head-to-head isolates the regime model's
contribution. Fair value is the walk-forward regression (daily) or a regime-parameterized
adaptive EWMA (intraday/live). See `docs/STRATEGY.md` and `docs/FINAL_BACKTESTING_REPORT.md`.

Headline (regime-aware, risk-first): **daily** Sharpe 0.82 / max DD −21% (vs blind 0.38 / −61%);
**intraday** Sharpe 5.44, net ≈ $1.55M, profitable 6/6 years, t-stat ≈ 12; **shock study** —
shallower drawdown than blind in 100% of 28 windows.

## Setup

The virtual environment lives at the **repo root** (`.venv`), shared with the rest of the repo:

```bash
python -m venv .venv
.venv\Scripts\pip install -r analytics/requirements.txt        # Windows
# .venv/bin/pip install -r analytics/requirements.txt           # macOS/Linux
```

Prerequisites:
- `server/data/history.json` built **with term strips** — run `node server/scripts/build-history.js`
  after placing the raw term-structure CSVs in `/Data/`.
- `server/.env` with `EIA_API_KEY` (inventory features; without it those columns are NaN).
- For the intraday backtest: `Data/CL_data.csv` and `Data/LCO_data.csv` (1-minute WTI/Brent).

## Run

```bash
.venv\Scripts\python analytics\run.py                  # full pipeline (Phase 2 + Phase 3)
.venv\Scripts\python analytics\run.py regimes          # one stage
.venv\Scripts\python analytics\historical_intraday.py  # one engine (builds a 15-min cache on first run)
```

Cadence: rerun when the dataset refreshes or after the weekly EIA release (Wed). Live
front-month prices stay real-time via the Node layer; the models refresh on this batch.

> Note: the `npm run analytics` convenience script points at `analytics/.venv` — the venv is now
> at the repo root (`.venv`), so prefer `.venv\Scripts\python analytics\run.py` directly.
