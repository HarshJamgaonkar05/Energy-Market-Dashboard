"""
run.py — run the Phase 2 analytics pipeline end to end.

  build_panel  → analytics/out/panel.parquet   (feature panel)
  regimes      → server/data/regimes.json       (regime classification + database)
  models       → server/data/models.json        (regressions)
  backtest     → server/data/backtest.json      (signal validation / hit-rates)
  signals      → server/data/signals.json       (ranked opportunities)
  historical_backtest → server/data/historical_backtest.json (5y daily trade sim)

The JSON artifacts land in server/data/ next to history.json, so the Node backend
serves them with no path juggling. Run after the dataset or EIA data refreshes:
    python analytics/run.py
"""
from __future__ import annotations

import importlib
import sys
import time

# Stages run in order; later stages are skipped gracefully until they exist.
STAGES = ["build_panel", "regimes", "models", "backtest", "signals", "historical_backtest"]


def main():
    only = sys.argv[1:]  # e.g. `python run.py regimes` to run one stage
    t0 = time.time()
    for name in STAGES:
        if only and name not in only:
            continue
        try:
            mod = importlib.import_module(name)
        except ModuleNotFoundError:
            print(f"[skip] {name} not implemented yet")
            continue
        print(f"[{name}]")
        mod.main()
    print(f"\nPipeline done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
