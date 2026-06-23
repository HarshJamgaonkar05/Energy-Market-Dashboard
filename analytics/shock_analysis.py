"""
shock_analysis.py — the consolidated SHOCK-ABSORPTION study (mentor's primary axis).

It answers one question three ways: when the market shocks, does the REGIME-AWARE book
de-risk better than the regime-BLIND control?

  1. OBSERVED shock windows — data-driven shock dates over the 5-year daily history (a vol
     jump vs the trailing median, or a transition INTO a high-vol regime). For each window
     we measure the drawdown each arm takes and how long it needs to recover, head-to-head.
  2. SYNTHETIC STRESS — re-run both arms with the shock windows amplified vol×{1.5, 2, 3}
     plus a gap jump, and compare how each arm's max drawdown grows. A shock-absorbing book
     degrades sub-linearly; a fixed-size book degrades ~linearly.
  3. DE-LEVER EVIDENCE — the aware book's size/severity path through the worst real shock,
     showing the layer actually cutting risk (not a cosmetic label).

Built on the SAME daily engine as historical_backtest.py (regression fair value, the regime
layer on top) so the numbers reconcile. Everything is causal / out-of-sample.

Reads  analytics/out/panel.parquet + server/data/backtest.json
Writes server/data/shock_analysis.json
Run:   python analytics/shock_analysis.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT_DIR, DATA_DIR
from regimes import classify
import regime_strategy as rs
import historical_backtest as hb

INITIAL_CAPITAL = hb.INITIAL_CAPITAL
MULT = hb.MULT
HORIZON = 20            # trading days per shock window
STRESS_FACTORS = [1.5, 2.0, 3.0]
STRESS_WIN = 10        # bars per amplified shock window in the synthetic stress


def build_frames(df):
    """The tradeable daily frames (regression FV, OOS-validated) + per-structure hit-rate."""
    edges = hb.phase2_edges()
    out = []
    for target, label in hb.UNIVERSE:
        frame, oos = hb.regression_frame(df, target)
        if frame is None or not np.isfinite(oos) or oos < hb.MIN_OOS:
            continue
        out.append((target, label, frame, hb.hit_for(target, edges)))
    return out


def simulate_arms(frames, cfg, stress=None):
    """Run aware + blind across all structures (optionally on stressed frames); return the
    portfolio daily PnL for each arm plus the aware trades and per-bar size/severity maps."""
    aware_pnls, blind_pnls, aware_trades = [], [], []
    size_map, sev_map = {}, {}
    for target, label, frame, hit in frames:
        f = stress(frame.copy()) if stress else frame
        residual = (f["spread"] - f["fv"]).to_numpy(float)
        hl = rs.trailing_halflife(residual, f["vol_state"].to_numpy(object), f["seg"].to_numpy(), cfg)
        legs = rs._legs_of({"structure": target})
        a = rs.simulate_structure(f, cfg, mode="aware", legs_count=legs, structure=target,
                                  label=label, hit_rate=hit, halflife=hl)
        b = rs.simulate_structure(f, cfg, mode="blind", legs_count=legs, structure=target,
                                  label=label, hit_rate=hit, halflife=hl)
        aware_pnls.append(a["pnl"]); blind_pnls.append(b["pnl"]); aware_trades += a["trades"]
        size_map[target] = a["size"]; sev_map[target] = a["severity"]
    return (rs.portfolio_daily_pnl(aware_pnls), rs.portfolio_daily_pnl(blind_pnls),
            aware_trades, size_map, sev_map)


def make_stress(shock_dates, factor):
    """A stress transform: inside each shock window amplify the deviation moves AND the vol
    proxy by `factor`, and add a gap jump at the window open. Causal / deterministic."""
    starts = [pd.Timestamp(d) for d in shock_dates]

    def transform(frame):
        idx = frame.index
        for k, s in enumerate(starts):
            end = s + pd.Timedelta(days=STRESS_WIN * 2)
            mask = (idx >= s) & (idx <= end)
            if not mask.any():
                continue
            dev = frame.loc[mask, "spread"] - frame.loc[mask, "fv"]
            frame.loc[mask, "spread"] = frame.loc[mask, "fv"] + factor * dev      # amplify dislocations
            frame.loc[mask, "bar_vol"] = frame.loc[mask, "bar_vol"] * factor       # vol proxy spikes
            # a one-bar gap jump at the window open (sign alternates → not curve-fit to either arm)
            first = frame.loc[mask].index[0]
            gap = (1 if k % 2 == 0 else -1) * factor * float(dev.abs().median() or 0.0) * 2.0
            frame.loc[first, "spread"] += gap
        return frame
    return transform


def window_block(daily_pnl, windows, initial):
    rows = []
    for w in windows:
        dd = rs.window_drawdown(daily_pnl, w["_start_ts"], w["horizonDays"], initial)
        rows.append(dd)
    return rows


def main():
    panel = pd.read_parquet(OUT_DIR / "panel.parquet")
    df = classify(panel)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    cfg = rs.DAILY_CONFIG
    cfg.mult = MULT
    cfg.slip_per_leg = 0.0

    years = max((df.index.max() - df.index.min()).days / 365.25, 1e-9)
    frames = build_frames(df)
    print(f"  shock study on {len(frames)} validated structures, {len(df)} days")

    # ---- base case (no stress) --------------------------------------------
    aware_daily, blind_daily, aware_trades, size_map, sev_map = simulate_arms(frames, cfg)
    base = {
        "aware": rs.risk_metrics(aware_daily, INITIAL_CAPITAL, years),
        "blind": rs.risk_metrics(blind_daily, INITIAL_CAPITAL, years),
    }

    # ---- observed shock windows -------------------------------------------
    windows = rs.find_shock_windows(df["wti_rvol20"], df["regimeId"], horizon_days=HORIZON)
    aware_w = window_block(aware_daily, windows, INITIAL_CAPITAL)
    blind_w = window_block(blind_daily, windows, INITIAL_CAPITAL)
    win_rows = []
    aware_better = 0
    for w, aw, bw in zip(windows, aware_w, blind_w):
        better = abs(aw["drawdown"]) <= abs(bw["drawdown"])
        aware_better += int(better)
        win_rows.append({
            "start": w["start"], "kind": w["kind"], "severity": w["severity"],
            "horizonDays": w["horizonDays"], "aware": aw, "blind": bw,
            "awareDeeperDDavoided": round(abs(bw["drawdown"]) - abs(aw["drawdown"]), 2),
        })
    win_summary = {
        "count": len(win_rows),
        "avgAwareDD": round(float(np.mean([r["aware"]["drawdown"] for r in win_rows])), 2) if win_rows else 0.0,
        "avgBlindDD": round(float(np.mean([r["blind"]["drawdown"] for r in win_rows])), 2) if win_rows else 0.0,
        "awareShallowerPct": round(aware_better / len(win_rows), 3) if win_rows else 0.0,
    }

    # ---- synthetic stress: vol×{1.5,2,3} + gap on the shock windows --------
    shock_dates = [w["start"] for w in windows]
    stress_rows = [{"factor": 1.0, "aware": base["aware"], "blind": base["blind"],
                    "ddRatioAwareVsBlind": round(abs(base["aware"]["maxDrawdown"]) /
                                                 abs(base["blind"]["maxDrawdown"]), 3)
                    if base["blind"]["maxDrawdown"] else None}]
    for fac in STRESS_FACTORS:
        a_d, b_d, _, _, _ = simulate_arms(frames, cfg, stress=make_stress(shock_dates, fac))
        am = rs.risk_metrics(a_d, INITIAL_CAPITAL, years)
        bm = rs.risk_metrics(b_d, INITIAL_CAPITAL, years)
        stress_rows.append({
            "factor": fac, "aware": am, "blind": bm,
            "ddRatioAwareVsBlind": round(abs(am["maxDrawdown"]) / abs(bm["maxDrawdown"]), 3) if bm["maxDrawdown"] else None,
        })
        print(f"  stress x{fac}: aware maxDD ${am['maxDrawdown']:,.0f} | blind maxDD ${bm['maxDrawdown']:,.0f}")

    # ---- de-lever evidence: size/severity through the worst real shock -----
    de_lever = []
    if windows:
        worst = max(windows, key=lambda w: w["severity"])
        s0 = worst["_start_ts"] - pd.Timedelta(days=10)
        s1 = worst["_start_ts"] + pd.Timedelta(days=HORIZON * 2)
        sizes = pd.concat(size_map.values(), axis=1, sort=True).mean(axis=1)
        sevs = pd.concat(sev_map.values(), axis=1, sort=True).mean(axis=1)
        for ts in sizes.index:
            if s0 <= ts <= s1:
                de_lever.append({"t": ts.strftime("%Y-%m-%d"),
                                 "size": round(float(sizes[ts]), 3),
                                 "severity": round(float(sevs.get(ts, 0.0)), 3)})

    out = {
        "generatedAt": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "asOf": df.index.max().strftime("%Y-%m-%d"),
        "horizon": "daily",
        "method": ("Shock dates are data-driven (vol jump vs trailing median, or a transition into a "
                   "high-vol regime). For each, the regime-aware book and the regime-blind control are "
                   "compared head-to-head on drawdown and recovery; the synthetic stress re-runs both "
                   "with the shock windows amplified vol×{1.5,2,3}+gap. Daily engine, out-of-sample."),
        "base": base,
        "windows": win_rows,
        "windowSummary": win_summary,
        "stress": stress_rows,
        "deLeverDuringWorstShock": {
            "window": windows[0]["start"] if windows else None,
            "worstShock": max(windows, key=lambda w: w["severity"])["start"] if windows else None,
            "series": de_lever,
        },
        "attribution": {"awareByRegime": rs.per_regime(aware_trades)},
    }
    path = DATA_DIR / "shock_analysis.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf8")
    print(f"\n  shock windows: {win_summary['count']} | aware shallower DD in "
          f"{win_summary['awareShallowerPct']*100:.0f}% | avg DD aware ${win_summary['avgAwareDD']:,.0f} "
          f"vs blind ${win_summary['avgBlindDD']:,.0f}")
    print(f"  -> {path}  ({round(path.stat().st_size/1024)} KB)")


if __name__ == "__main__":
    main()
