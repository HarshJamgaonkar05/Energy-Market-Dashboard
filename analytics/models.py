"""
models.py — regression "fair value" models for each spread / butterfly.

For every target we fit a ladder of models and compare them (the brief's "compare
model performance across conditions rather than one universal model"):

  • OLS         — interpretable baseline; standardized coefficients = driver importance.
  • Ridge/Lasso — regularized fit on collinear drivers; Lasso also selects features.
  • Rolling OLS — 120-day window → time-varying betas (relationship stability).
  • Regime OLS  — a separate fit inside each sufficient regime; R²/coefs compared.

Honesty: the displayed FAIR-VALUE line and the residual that feeds signals are
produced WALK-FORWARD (expanding window, refit every 21 trading days on raw
features), so a day's fair value never sees its own or future data. The
walk-forward prediction also yields the out-of-sample R².

Reads  analytics/out/panel.parquet · Writes server/data/models.json
Run:   python analytics/models.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LassoCV, RidgeCV

from common import OUT_DIR, DATA_DIR
from regimes import SPREADS, classify, MIN_OBS

# Fundamental + macro + market-state drivers (NOT the target spread itself → no
# circularity). Momentum/vol of the underlyings capture risk-on/off and demand
# trend that move term structure; Lasso decides which actually matter per target.
FEATURES = [
    "crude_z", "distillate_z", "crude_wow", "distillate_wow", "refinery_util",
    "wti_rvol20", "wti_mom20", "ho_mom20", "dxy", "vix", "ust10y",
    "month_sin", "month_cos",
]
SPREAD_LABELS = {
    "brent_wti": "Brent-WTI", "ho_gasoil": "HO-Gas Oil", "gasoil_brent": "Gas Oil crack",
    "ho_brent": "HO crack (Brent)", "ho_wti": "HO crack (WTI)", "rbob_ho": "RBOB-HO",
    "crack_321_wti": "3:2:1 crack", "wti_m1m2": "WTI M1-M2", "wti_fly": "WTI M1-M2-M3 fly",
    "brent_m1m2": "Brent M1-M2", "gasoil_m1m2": "Gas Oil M1-M2", "gasoil_fly": "Gas Oil fly",
}

MIN_TRAIN = 250   # trading days before walk-forward starts predicting
REFIT = 21        # refit cadence (days) for the walk-forward fair value
ROLL = 120        # rolling-regression window


def r2(y, yhat) -> float:
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    ok = ~(np.isnan(y) | np.isnan(yhat))
    if ok.sum() < 5:
        return float("nan")
    y, yhat = y[ok], yhat[ok]
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    return float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")


def walk_forward(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Expanding-window OLS, refit every REFIT days. Returns fair value (NaN until MIN_TRAIN)."""
    n = len(y)
    fv = np.full(n, np.nan)
    i = MIN_TRAIN
    while i < n:
        model = LinearRegression().fit(X[:i], y[:i])
        end = min(i + REFIT, n)
        fv[i:end] = model.predict(X[i:end])
        i = end
    return fv


def rolling_betas(X: pd.DataFrame, y: pd.Series, feats: list[str]) -> dict:
    """Rolling-window OLS betas for a few key features, downsampled to ~weekly."""
    idx, betas = [], {f: [] for f in feats}
    cols = [X.columns.get_loc(f) for f in feats]
    Xv, yv = X.values, y.values
    for end in range(ROLL, len(y) + 1, 5):  # step 5 ≈ weekly
        sl = slice(end - ROLL, end)
        try:
            coef = LinearRegression().fit(Xv[sl], yv[sl]).coef_
        except Exception:  # noqa: BLE001
            continue
        idx.append(X.index[end - 1].strftime("%Y-%m-%d"))
        for f, c in zip(feats, cols):
            betas[f].append(round(float(coef[c]), 4))
    return {"window": ROLL, "dates": idx, "betas": betas}


def fit_target(df: pd.DataFrame, target: str) -> dict | None:
    sub = df[FEATURES + [target, "regimeId"]].dropna(subset=FEATURES + [target])
    if len(sub) < MIN_TRAIN + 60:
        return None
    X, y = sub[FEATURES], sub[target]

    # Standardized OLS → coefficient importance (comparable magnitudes).
    Xs = (X - X.mean()) / X.std(ddof=0)
    ols = LinearRegression().fit(Xs, y)
    coef = {f: round(float(c), 3) for f, c in zip(FEATURES, ols.coef_)}
    r2_in = r2(y, ols.predict(Xs))

    # Walk-forward fair value + honest OOS R² + residuals.
    fv = walk_forward(X.values, y.values)
    fv_s = pd.Series(fv, index=sub.index)
    resid = y - fv_s
    r2_oos = r2(y[~fv_s.isna()], fv_s.dropna())

    # Ridge / Lasso on standardized features (regularization + selection).
    ridge = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(Xs, y)
    lasso = LassoCV(alphas=np.logspace(-3, 1, 30), max_iter=20000, n_jobs=None).fit(Xs, y)
    selected = [f for f, c in zip(FEATURES, lasso.coef_) if abs(c) > 1e-4]

    # Top drivers by |standardized OLS coef|.
    top = sorted(coef.items(), key=lambda kv: -abs(kv[1]))[:4]
    rolling = rolling_betas(Xs, y, [f for f, _ in top])

    # Regime-specific OLS — relationships compared across market conditions.
    by_regime = {}
    for rid, g in sub.groupby("regimeId"):
        if len(g) < MIN_OBS:
            continue
        gx = (g[FEATURES] - g[FEATURES].mean()) / g[FEATURES].std(ddof=0)
        gx = gx.fillna(0.0)  # a feature constant within a regime → 0 (no effect)
        m = LinearRegression().fit(gx, g[target])
        by_regime[rid] = {
            "n": int(len(g)),
            "r2": round(r2(g[target], m.predict(gx)), 3),
            "coef": {f: round(float(c), 3) for f, c in zip(FEATURES, m.coef_)},
        }

    # Fair-value series for the chart (only where walk-forward predicts).
    fair = [
        {"date": ts.strftime("%Y-%m-%d"), "actual": round(float(a), 3), "fv": round(float(f), 3)}
        for ts, a, f in zip(sub.index, y.values, fv) if not np.isnan(f)
    ]
    rstd = float(resid.std(ddof=0))
    rlast = float(resid.dropna().iloc[-1]) if resid.notna().any() else None

    return {
        "label": SPREAD_LABELS.get(target, target),
        "n": int(len(sub)),
        "features": FEATURES,
        "global": {
            "r2_in": round(r2_in, 3),
            "r2_oos": round(r2_oos, 3),
            "coef": coef,
            "topDrivers": [f for f, _ in top],
        },
        "ridge": {"r2_in": round(r2(y, ridge.predict(Xs)), 3), "alpha": round(float(ridge.alpha_), 4)},
        "lasso": {"r2_in": round(r2(y, lasso.predict(Xs)), 3), "alpha": round(float(lasso.alpha_), 4),
                  "selected": selected},
        "rolling": rolling,
        "byRegime": by_regime,
        "fairValue": fair,
        "residual": {
            "latest": None if rlast is None else round(rlast, 3),
            "std": round(rstd, 3),
            "z": None if (rlast is None or rstd == 0) else round(rlast / rstd, 2),
        },
    }


def main():
    panel = pd.read_parquet(OUT_DIR / "panel.parquet")
    df = classify(panel)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    out = {"generatedAt": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
           "asOf": df.index.max().strftime("%Y-%m-%d"), "features": FEATURES, "models": {}}
    for target in SPREADS:
        res = fit_target(df, target)
        if res:
            out["models"][target] = res
            g = res["global"]
            print(f"  {target:14} n={res['n']:4} R2_in={g['r2_in']:.2f} R2_oos={g['r2_oos']:.2f} "
                  f"drivers={','.join(g['topDrivers'][:3])} regimes={len(res['byRegime'])}")

    path = DATA_DIR / "models.json"
    path.write_text(json.dumps(out))
    print(f"  -> {path}  ({round(path.stat().st_size/1024)} KB, {len(out['models'])} models)")


if __name__ == "__main__":
    main()
