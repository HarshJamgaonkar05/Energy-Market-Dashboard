# Voltaire — Phase 2 analytics (regime engine)

Offline Python batch layer that turns the historical dataset + EIA fundamentals into
the **regime / regression / signal** artifacts the dashboard serves. It follows the
same *precompute → JSON → serve* pattern as `server/scripts/build-history.js`: heavy
statistics run here on a schedule and write static JSON into `server/data/`, so the
live Node server stays thin and never runs Python in the request path.

## Pipeline

| Stage | Script | Output | Status |
|---|---|---|---|
| Feature panel | `build_panel.py` | `analytics/out/panel.parquet` | ✅ P2.0 |
| Regime engine | `regimes.py` | `server/data/regimes.json` | ✅ P2.1 |
| Regressions | `models.py` | `server/data/models.json` | ✅ P2.2 |
| Signal backtest | `backtest.py` | `server/data/backtest.json` | ✅ |
| Signals | `signals.py` | `server/data/signals.json` | ✅ P2.3 |

`panel.parquet` is the single feature table (one row per trading day, 2021→present):
prices, inter-commodity spreads, cracks, calendar spreads, butterflies, realized vol,
curve state, EIA inventory levels/changes/seasonal-z, seasonal flags and macro.

The **regime** is classified rule-first across five dimensions (inventory, term
structure, volatility, trend, season); the headline segmentation is
**Inventory × Volatility** (the two that actually vary across 2021–2026 — the sample
is ~95 % backwardated, so term structure is recorded as context, not a split axis).

## Setup

```bash
python -m venv analytics/.venv
analytics/.venv/Scripts/pip install -r analytics/requirements.txt   # Windows
# analytics/.venv/bin/pip install -r analytics/requirements.txt      # macOS/Linux
```

Prerequisites:
- `server/data/history.json` built **with term strips** — run `node server/scripts/build-history.js`
  after placing the raw term-structure CSVs in `/Data/`.
- `server/.env` with `EIA_API_KEY` (inventory features; without it those columns are NaN).

## Run

```bash
analytics/.venv/Scripts/python analytics/run.py            # full pipeline
analytics/.venv/Scripts/python analytics/run.py regimes    # one stage
npm run analytics                                          # convenience wrapper
```

Cadence: rerun when the dataset refreshes or after the weekly EIA release (Wed). Live
front-month prices stay real-time via the Node layer; the models refresh on this batch.
