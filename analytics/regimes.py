"""
regimes.py — rule-based market-regime classification + historical regime database.

Interpretable-first (the brief stresses explainability): each of five dimensions
maps to a discrete, threshold-defined state, so every classification can be
explained by the exact driver that set it. The HEADLINE regime used for
statistical segmentation is Inventory x Volatility (3x3 = 9 regimes) — the two
dimensions that actually vary across 2021-2026 and so populate every bucket. Term
structure barely moves in-sample (~95% backwardated), so it would not partition
the data; it is recorded per day as context and used as a regression feature
instead. Season / trend are likewise recorded as modifiers/features.

Reads  analytics/out/panel.parquet  (build_panel.py).
Writes server/data/regimes.json     (served by server/compute/regime.js).
Run:   python analytics/regimes.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT_DIR, DATA_DIR

# Spreads/structures we profile per regime (the tradeable universe for signals).
SPREADS = [
    "brent_wti", "ho_gasoil", "gasoil_brent", "ho_brent", "ho_wti",
    "rbob_ho", "crack_321_wti",
    "wti_m1m2", "wti_fly", "brent_m1m2", "gasoil_m1m2", "gasoil_fly",
]

# Instruments for the regime-conditioned correlation matrix.
CORR_INSTR = ["wti", "brent", "ho", "gasoil"]
CORR_LABELS = ["WTI", "Brent", "HO", "Gas Oil"]


def correlation_matrix(df: pd.DataFrame, mask=None) -> dict | None:
    """Correlation of the four instruments' daily returns, optionally on a subset
    of days (e.g. the current regime). Returns are computed on the full series
    first, then masked, so a regime's non-contiguous days don't span gaps."""
    rets = df[[f"{i}_ret" for i in CORR_INSTR]]
    if mask is not None:
        rets = rets[mask]
    rets = rets.dropna()
    if len(rets) < 10:
        return None
    c = rets.corr().values
    return {
        "labels": CORR_LABELS,
        "matrix": [[round(float(c[i][j]), 2) for j in range(len(CORR_INSTR))] for i in range(len(CORR_INSTR))],
        "n": int(len(rets)),
    }

# Minimum observations for a regime's stats to be treated as robust.
MIN_OBS = 40

# ---- Dimension thresholds (absolute → look-ahead-free & explainable) --------
# Inventory: crude stocks vs the 5-year seasonal norm (z-score). Low stocks = tight = bullish.
INV = dict(metric="crude_z", tight=-0.5, oversupp=0.5)
# Term structure: WTI M1–M12 ($/bbl). Positive = backwardation (front rich).
STRUCT = dict(metric="wti_m1m12", bwd=0.5, contango=-0.5)
# Volatility: 20d realized vol of WTI, annualized. Energy sits ~30–40% normally.
VOL = dict(metric="wti_rvol20", low=0.30, high=0.50)
# Trend: WTI vs its 200-day moving average.
TREND = dict(band=0.02)

DIM_DEFS = {
    "inventory": {"metric": "crude_z", "states": ["Tight", "Balanced", "Oversupplied"],
                  "rule": "US crude stocks vs 5y seasonal norm: Tight z<-0.5, Oversupplied z>+0.5"},
    "structure": {"metric": "wti_m1m12", "states": ["Backwardation", "Flat", "Contango"],
                  "rule": "WTI M1-M12 ($/bbl): Backwardation > +0.5, Contango < -0.5"},
    "volatility": {"metric": "wti_rvol20", "states": ["Low", "Normal", "High"],
                   "rule": "WTI 20d realized vol (ann.): Low < 30%, High > 50%"},
    "season": {"metric": "month", "states": ["Heating", "Driving", "Shoulder"],
               "rule": "Heating Oct-Mar, Driving Apr-Aug, Shoulder Sep"},
    "trend": {"metric": "wti vs 200dma", "states": ["Up", "Range", "Down"],
              "rule": "WTI vs 200d MA: Up > +2%, Down < -2%"},
}


def classify(panel: pd.DataFrame) -> pd.DataFrame:
    """Add per-day dimension state columns + a headline regimeId/label to the panel."""
    df = panel.copy()
    ma200 = df["wti"].rolling(200, min_periods=50).mean()
    df["_ma200_dev"] = df["wti"] / ma200 - 1.0
    for inst in CORR_INSTR:
        df[f"{inst}_ret"] = df[inst].pct_change()

    def inv(z):
        if pd.isna(z): return None
        return "Tight" if z < INV["tight"] else "Oversupplied" if z > INV["oversupp"] else "Balanced"

    def struct(s):
        if pd.isna(s): return None
        return "Backwardation" if s > STRUCT["bwd"] else "Contango" if s < STRUCT["contango"] else "Flat"

    def vol(v):
        if pd.isna(v): return None
        return "Low" if v < VOL["low"] else "High" if v > VOL["high"] else "Normal"

    def trend(d):
        if pd.isna(d): return None
        return "Up" if d > TREND["band"] else "Down" if d < -TREND["band"] else "Range"

    df["inventory"] = df[INV["metric"]].map(inv)
    df["structure"] = df[STRUCT["metric"]].map(struct)
    df["volatility"] = df[VOL["metric"]].map(vol)
    df["season"] = df["season"].str.capitalize()
    df["trend"] = df["_ma200_dev"].map(trend)

    # Headline regime = Inventory x Volatility (9 buckets; both vary in-sample).
    inv_short = {"Tight": "tight", "Balanced": "bal", "Oversupplied": "over"}
    vol_short = {"Low": "lo", "Normal": "norm", "High": "hi"}
    ok = lambda v: isinstance(v, str)  # noqa: E731
    df["regimeId"] = [
        f"{inv_short[i]}_{vol_short[v]}" if ok(i) and ok(v) else None
        for i, v in zip(df["inventory"], df["volatility"])
    ]
    df["regimeLabel"] = [
        f"{i} · {v} Vol" if ok(i) and ok(v) else None
        for i, v in zip(df["inventory"], df["volatility"])
    ]
    return df


def half_life(x: pd.Series) -> float | None:
    """AR(1) mean-reversion half-life in trading days: rho from x_t = a + rho·x_{t-1}."""
    x = x.dropna()
    if len(x) < 30:
        return None
    lag = x.shift(1)
    m = pd.concat([x, lag], axis=1).dropna()
    y, xl = m.iloc[:, 0].values, m.iloc[:, 1].values
    rho = np.polyfit(xl, y, 1)[0]
    if not (0 < rho < 1):
        return None
    return float(round(-np.log(2) / np.log(rho), 1))


def spread_stats(sub: pd.DataFrame, full: pd.DataFrame) -> dict:
    """Per-regime distribution of each spread, with where the latest value sits."""
    out = {}
    for sp in SPREADS:
        s = sub[sp].dropna()
        if len(s) < 5:
            continue
        cur = full[sp].dropna()
        cur_v = float(cur.iloc[-1]) if len(cur) else None
        mean, std = float(s.mean()), float(s.std(ddof=0))
        out[sp] = {
            "n": int(len(s)),
            "mean": round(mean, 3),
            "std": round(std, 3),
            "p10": round(float(s.quantile(0.10)), 3),
            "p50": round(float(s.median()), 3),
            "p90": round(float(s.quantile(0.90)), 3),
            "current": None if cur_v is None else round(cur_v, 3),
            "z": None if (cur_v is None or std == 0) else round((cur_v - mean) / std, 2),
            "halfLifeDays": half_life(full[sp]),
        }
    return out


def regime_runs(seq) -> dict[str, list[int]]:
    """Map each regimeId → list of its episode lengths (in trading days).
    Pass the LABELED-ONLY sequence (drop None first) so 1-day holiday gaps don't
    fragment a single regime episode into several."""
    runs: dict[str, list[int]] = {}
    cur, n = None, 0
    for v in seq:
        v = v if isinstance(v, str) else None
        if v == cur:
            n += 1
        else:
            if cur is not None:
                runs.setdefault(cur, []).append(n)
            cur, n = v, 1
    if cur is not None:
        runs.setdefault(cur, []).append(n)
    return runs


def transition_matrix(seq: pd.Series) -> dict:
    """P(next regime | current regime) from the day-to-day regime sequence."""
    s = seq.dropna()
    counts: dict[str, dict[str, int]] = {}
    for a, b in zip(s.iloc[:-1], s.iloc[1:]):
        counts.setdefault(a, {}).setdefault(b, 0)
        counts[a][b] += 1
    probs = {}
    for a, row in counts.items():
        tot = sum(row.values())
        probs[a] = {b: round(c / tot, 3) for b, c in sorted(row.items(), key=lambda kv: -kv[1])}
    return probs


def driver_text(dim: str, state: str, val) -> str:
    v = None if (val is None or (isinstance(val, float) and np.isnan(val))) else round(float(val), 2)
    if dim == "inventory":
        return f"US crude stocks {abs(v):.2f}σ {'below' if v < 0 else 'above'} the 5y seasonal norm" if v is not None else state
    if dim == "structure":
        return f"WTI M1-M12 at {v:+.2f} $/bbl ({state.lower()})" if v is not None else state
    if dim == "volatility":
        return f"WTI 20d realized vol {v:.0%} annualized" if v is not None else state
    if dim == "trend":
        return f"WTI {v:+.1%} vs its 200-day average" if v is not None else state
    if dim == "season":
        return f"{state} season"
    return state


def build_current(df: pd.DataFrame) -> dict:
    row = df.dropna(subset=["regimeId"]).iloc[-1]
    metrics = {"inventory": INV["metric"], "structure": STRUCT["metric"],
               "volatility": VOL["metric"], "trend": "_ma200_dev", "season": "month"}
    states = {}
    for dim, metric in metrics.items():
        st = row[dim]
        val = row.get(metric)
        states[dim] = {
            "state": st,
            "value": None if (val is None or (isinstance(val, float) and pd.isna(val))) else round(float(val), 3),
            "driver": driver_text(dim, st, val if dim != "season" else None),
        }
    return {"date": row.name.strftime("%Y-%m-%d"),
            "regimeId": row["regimeId"], "label": row["regimeLabel"], "states": states}


def main():
    panel = pd.read_parquet(OUT_DIR / "panel.parquet")
    df = classify(panel)

    # Historical regime database (one row per day).
    hist_cols = ["regimeId", "regimeLabel", "inventory", "structure", "volatility", "season", "trend"]
    history = [
        {"date": ts.strftime("%Y-%m-%d"), **{c: (None if pd.isna(r[c]) else r[c]) for c in hist_cols}}
        for ts, r in df.iterrows() if not pd.isna(r["regimeId"])
    ]

    # Catalog: per-regime size, share, persistence, sufficiency + spread behaviour.
    labeled = df.dropna(subset=["regimeId"])
    total = len(labeled)
    all_runs = regime_runs(df["regimeId"].dropna())
    catalog = []
    for rid, sub in labeled.groupby("regimeId"):
        r = all_runs.get(rid, [])
        catalog.append({
            "regimeId": rid,
            "label": sub["regimeLabel"].iloc[0],
            "n": int(len(sub)),
            "share": round(len(sub) / total, 3),
            "avgDurationDays": round(float(np.mean(r)), 1) if r else None,
            "episodes": len(r),
            "sufficient": len(sub) >= MIN_OBS,
            "spreads": spread_stats(sub, df),
        })
    catalog.sort(key=lambda c: -c["n"])

    # Regime-conditioned vs all-history correlation of the four instruments —
    # "how do these move together RIGHT NOW vs on average".
    current = build_current(df)
    cur_mask = df["regimeId"] == current["regimeId"]
    correlation = {
        "all": correlation_matrix(df),
        "regime": correlation_matrix(df, cur_mask),
        "regimeLabel": current["label"],
    }

    out = {
        "generatedAt": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "asOf": df.index.max().strftime("%Y-%m-%d"),
        "dimensions": DIM_DEFS,
        "spreads": SPREADS,
        "current": current,
        "correlation": correlation,
        "history": history,
        "catalog": catalog,
        "transitions": transition_matrix(df["regimeId"]),
    }
    path = DATA_DIR / "regimes.json"
    path.write_text(json.dumps(out))
    print(f"  current regime: {out['current']['label']}  (asOf {out['asOf']})")
    print(f"  regimes: {len(catalog)} ({sum(c['sufficient'] for c in catalog)} sufficient >= {MIN_OBS} obs)  "
          f"| labeled days: {total}")
    print(f"  -> {path}  ({round(path.stat().st_size/1024)} KB)")


if __name__ == "__main__":
    main()
