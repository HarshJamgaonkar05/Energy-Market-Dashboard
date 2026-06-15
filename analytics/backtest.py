"""
backtest.py — does the dislocation signal actually work?

For each spread we reproduce the walk-forward fair value (models.py), form the
residual = actual - fair value, standardize it with an EXPANDING std (no
look-ahead), and ask: historically, when |residual z| crossed the signal
threshold, did the spread mean-revert over the next HORIZON days?

Reported per spread:
  • hitRate         — % of signal days where |residual| shrank over HORIZON days
  • baselineHitRate — the same on ALL days (unconditional reversion rate ~50%)
  • edge            — hitRate − baseline (the signal's lift)
  • avgFavMove      — mean move toward fair value after a signal (spread units)

A signal with hitRate well above baseline and a positive avgFavMove is one we can
trust; signals.py folds these numbers into each opportunity's confidence.

Reads analytics/out/panel.parquet · Writes server/data/backtest.json
Run:   python analytics/backtest.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT_DIR, DATA_DIR
from regimes import SPREADS, classify
from models import FEATURES, walk_forward, MIN_TRAIN

HORIZON = 10     # trading days to measure reversion over
THRESH = 1.5     # |residual z| that defines a dislocation signal
MIN_SIGNALS = 10 # below this, the spread's backtest is "insufficient"


def residual(df: pd.DataFrame, target: str):
    sub = df[FEATURES + [target]].dropna()
    if len(sub) < MIN_TRAIN + HORIZON + 30:
        return None, None
    fv = walk_forward(sub[FEATURES].values, sub[target].values)
    fv = pd.Series(fv, index=sub.index)
    return sub[target], (sub[target] - fv)


def backtest_target(df: pd.DataFrame, target: str) -> dict | None:
    spread, resid = residual(df, target)
    if resid is None:
        return None
    r = resid.dropna()
    if len(r) < 60:
        return None
    z = (r / r.expanding(min_periods=30).std()).values
    rv = r.values
    spv = spread.reindex(r.index).values
    n = len(rv)

    sig_rev, sig_fav, base_rev = [], [], []
    for i in range(n - HORIZON):
        rt, rth = rv[i], rv[i + HORIZON]
        if np.isnan(rt) or np.isnan(rth):
            continue
        reverted = abs(rth) < abs(rt)
        base_rev.append(reverted)
        if abs(z[i]) >= THRESH:
            sig_rev.append(reverted)
            sig_fav.append(np.sign(rt) * (spv[i] - spv[i + HORIZON]))  # >0 = toward fair value

    if len(sig_rev) < MIN_SIGNALS:
        return {"nSignals": len(sig_rev), "sufficient": False}
    hit = float(np.mean(sig_rev))
    base = float(np.mean(base_rev)) if base_rev else None
    return {
        "nSignals": len(sig_rev),
        "hitRate": round(hit, 3),
        "baselineHitRate": None if base is None else round(base, 3),
        "edge": None if base is None else round(hit - base, 3),
        "avgFavMove": round(float(np.mean(sig_fav)), 3),
        "sufficient": True,
    }


def main():
    panel = pd.read_parquet(OUT_DIR / "panel.parquet")
    df = classify(panel)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    out = {"generatedAt": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
           "asOf": df.index.max().strftime("%Y-%m-%d"),
           "horizonDays": HORIZON, "thresholdSigma": THRESH, "spreads": {}}
    for sp in SPREADS:
        res = backtest_target(df, sp)
        if res:
            out["spreads"][sp] = res
            if res.get("sufficient"):
                print(f"  {sp:14} n={res['nSignals']:3} hit={res['hitRate']:.0%} "
                      f"base={res['baselineHitRate']:.0%} edge={res['edge']:+.0%} favMove={res['avgFavMove']:+.2f}")
            else:
                print(f"  {sp:14} insufficient ({res['nSignals']} signals)")

    path = DATA_DIR / "backtest.json"
    path.write_text(json.dumps(out))
    print(f"  -> {path}  ({round(path.stat().st_size/1024)} KB)")


if __name__ == "__main__":
    main()
