"""
historical_backtest.py — the Phase-2 fundamental fair value, backtested as a daily
TRADE SIMULATION over the full 2021-2026 history, NOW with shock absorption, risk-led
metrics, and a regime-blind control.

This is the *correct* home for the Phase-2 model. Intraday (Phase 3) it could not be
used — the feed had no fundamentals, its level was stale, and it was flat over a few
days. On DAILY history with the fundamental features present, it is exactly the right
tool, and the sample is large enough to mean something (~5 years).

Method (honest, out-of-sample) — the SIGNAL is unchanged from before:
  • Fair value = the Phase-2 regression, produced WALK-FORWARD (expanding window,
    refit every 21 days) so a day's fair value never sees its own or future data.
  • Signal = residual z = (actual − fair value) / EXPANDING std  (no look-ahead).
  • Trade  = fade |z| >= 1.5; exit on reversion to fair (|z| <= 0.5), a 3σ stop, or a
    20-trading-day time stop. Base size 1 unit/trade.

What is NEW (mirrors analytics/shock.py — applied to BOTH the daily & intraday books):
  • SHOCK ABSORPTION — the "aware" arm de-levers, stands aside, and flattens through a
    measured shock (a vol jump, a step UP the vol-state ladder, or a z-breach).
  • RISK-LED METRICS — Sharpe / Sortino / Calmar / max drawdown ($/%) / CVaR / % time
    in market, on a mark-to-market daily-return series.
  • A REGIME-BLIND CONTROL — the SAME strategy with the shock layer off (= main's old
    behaviour), so the head-to-head isolates what shock absorption contributes.

Reads  analytics/out/panel.parquet  +  server/data/backtest.json (Phase-2 hit-rates)
Writes server/data/historical_backtest.json  (+ out/historical_trades.csv)
Run:   python analytics/historical_backtest.py            # gross
       python analytics/historical_backtest.py --slip 0.02  # charge per-leg cost
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import replace

import numpy as np
import pandas as pd

from common import OUT_DIR, DATA_DIR
from regimes import classify
from models import FEATURES, walk_forward, MIN_TRAIN
import shock

# ---- Strategy parameters (daily horizon) — UNCHANGED -----------------------
Z_ENTRY = 1.5          # fade when |residual z| >= this (Phase-2 validated threshold)
Z_EXIT = 0.5           # take profit once reverted to within this of fair value
Z_STOP = 3.0           # stop if the dislocation widens to |z| >= this
MAX_HOLD_DAYS = 20     # time stop, in trading days (~1 month)
MULT = 1000            # $1.00/bbl move on a 1,000-bbl unit = $1,000
INITIAL_CAPITAL = 250_000
SLIP_PER_LEG = 0.0     # per-leg, per-side slippage in price units; 0 = gross

# The shock policy for the daily horizon (z_stop kept in lock-step with Z_STOP).
DAILY_SHOCK = replace(shock.DAILY_SHOCK, z_stop=Z_STOP)

# WTI & Brent only — calendars, butterflies, and the Brent-WTI arb.
# (target panel column, display label, Phase-2 hit-rate key, active?)
CRUDE = [
    ("wti_m1m2",   "WTI M1-M2",         "wti_m1m2",   True),
    ("wti_m2m3",   "WTI M2-M3",         "wti_m1m2",   True),
    ("wti_fly",    "WTI M1-M2-M3 fly",  "wti_fly",    True),
    ("brent_m1m2", "Brent M1-M2",       "brent_m1m2", False),
    ("brent_m2m3", "Brent M2-M3",       "brent_m1m2", False),
    ("brent_fly",  "Brent M1-M2-M3 fly","wti_fly",    True),
    ("brent_wti",  "Brent-WTI arb",     "brent_wti",  True),
]

STRATEGY_NAME = "Phase-2 fundamental RV mean-reversion + shock absorption (WTI & Brent, daily, 5y)"
STRATEGY_DESC = ("Fair value from the Phase-2 fundamentals regression (walk-forward, out-of-sample); "
                 "fade a >=1.5sigma residual dislocation; exit on reversion to fair (|z|<=0.5), a 3sigma "
                 "stop, or a 20-day time stop. 1 unit/trade. SHOCK ABSORPTION (aware arm): de-lever, "
                 "stand aside, and flatten through a measured shock (vol jump / vol-state step-up / "
                 "z-breach). A regime-BLIND control (shock off) runs alongside; results are read "
                 "risk-first (Sharpe / Calmar / drawdown / CVaR on mark-to-market daily returns).")


def legs_count(spread: str) -> int:
    return 4 if spread.endswith("fly") else 2


def phase2_edges() -> dict:
    try:
        return json.loads((DATA_DIR / "backtest.json").read_text(encoding="utf8")).get("spreads", {})
    except Exception:
        return {}


def edge_for(spread: str, edges: dict):
    bt = edges.get(spread)
    if bt and bt.get("sufficient"):
        return round(float(bt["hitRate"]), 3)
    return None


def residual_z(df: pd.DataFrame, target: str):
    """Walk-forward fair value, actual spread, and the expanding-std residual z —
    all aligned on the dates where the out-of-sample fair value exists. UNCHANGED."""
    sub = df[FEATURES + [target]].dropna()
    if len(sub) < MIN_TRAIN + 60:
        return None
    fv = pd.Series(walk_forward(sub[FEATURES].values, sub[target].values), index=sub.index)
    resid = (sub[target] - fv).dropna()
    if len(resid) < 60:
        return None
    z = resid / resid.expanding(min_periods=30).std()
    idx = z.dropna().index
    return sub[target].reindex(idx), fv.reindex(idx), z.reindex(idx)


def build_frame(df: pd.DataFrame, target: str):
    """Per-structure frame the shock core walks: spread, regression fair value, the
    (unchanged) residual z, the day's vol-state & regime label, a causal spread-vol
    proxy, and a single segment (daily spreads are continuous — no roll/session breaks)."""
    rz = residual_z(df, target)
    if rz is None:
        return None
    spread, fv, z = rz
    idx = spread.index
    bar_vol = spread.diff().rolling(10, min_periods=3).std()
    return pd.DataFrame({
        "spread": spread, "fv": fv, "z": z,
        "vol_state": df["volatility"].reindex(idx),
        "regime": df["regimeLabel"].reindex(idx),
        "bar_vol": bar_vol.reindex(idx),
        "seg": 0,
    })


def run_arm(frames: dict, mode: str, edges: dict):
    """Run every active structure under one arm; return (trades, opens, pnls, in_markets)."""
    trades, opens, pnls, in_markets = [], [], [], []
    for target, label, hitkey, active in CRUDE:
        if not active or target not in frames:
            continue
        res = shock.simulate(
            frames[target], mode=mode, z_entry=Z_ENTRY, z_exit=Z_EXIT, z_stop=Z_STOP,
            max_hold=MAX_HOLD_DAYS, shock=DAILY_SHOCK, legs_count=legs_count(target),
            structure=target, label=label, hit_rate=edge_for(hitkey, edges),
            horizon="daily", mult=MULT, slip_per_leg=SLIP_PER_LEG, gate_cost=0.0, warmup=0,
        )
        trades += res["trades"]
        if res["open"]:
            opens.append(res["open"])
        pnls.append(res["pnl"])
        in_markets.append(res["in_market"])
    return trades, opens, pnls, in_markets


def arm_block(trades, pnls, in_markets, years):
    daily = shock.portfolio_daily_pnl(pnls)
    summary = shock.summarize(trades, daily, in_markets, INITIAL_CAPITAL, years, MULT,
                              ref_slip=0.02, horizon="daily")
    return summary, daily


def write_csv(all_trades):
    cols = ["structure", "label", "regime", "volState", "direction", "entryDate", "exitDate",
            "holdDays", "entrySpread", "exitSpread", "fairValue", "entryZ", "exitZ", "size",
            "entrySeverity", "pnl", "cost", "netPnl", "mae", "mfe", "exitReason", "histHitRate",
            "equityAfter"]
    path = OUT_DIR / "historical_trades.csv"
    with open(path, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); eq = INITIAL_CAPITAL
        for t in sorted(all_trades, key=lambda x: x["exitDate"]):
            eq += t["pnl"]; row = dict(t); row["equityAfter"] = round(eq, 2)
            w.writerow(row)


def main():
    global SLIP_PER_LEG
    ap = argparse.ArgumentParser()
    ap.add_argument("--slip", type=float, default=SLIP_PER_LEG,
                    help="per-leg slippage in price units (e.g. 0.02); reports net alongside gross")
    args = ap.parse_args()
    SLIP_PER_LEG = args.slip

    panel = pd.read_parquet(OUT_DIR / "panel.parquet")
    df = classify(panel)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    edges = phase2_edges()

    first, last = df.index.min(), df.index.max()
    years = max((last - first).days / 365.25, 1e-9)

    frames = {}
    for target, label, hitkey, active in CRUDE:
        if not active:
            continue
        fr = build_frame(df, target)
        if fr is not None:
            frames[target] = fr

    aware_trades, opens, a_pnls, a_inmkt = run_arm(frames, "aware", edges)
    blind_trades, _, b_pnls, b_inmkt = run_arm(frames, "blind", edges)

    aware_summary, aware_daily = arm_block(aware_trades, a_pnls, a_inmkt, years)
    blind_summary, _ = arm_block(blind_trades, b_pnls, b_inmkt, years)

    for target, label, hitkey, active in CRUDE:
        if not active or target not in frames:
            continue
        ts = [t for t in aware_trades if t["structure"] == target]
        if ts:
            print(f"  {target:14} trades={len(ts):3} pnl=${sum(t['pnl'] for t in ts):>8,.0f} "
                  f"win={sum(1 for t in ts if t['pnl']>0)/len(ts):.0%} PF={shock.pf(ts)}")

    structures = [(t, l) for t, l, _, a in CRUDE if a]
    feed = {
        "generatedAt": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "daily", "horizon": "daily",
        "span": {"first": first.strftime("%Y-%m-%d"), "last": last.strftime("%Y-%m-%d")},
        "years": round(years, 1), "days": int(len(df)),
        "strategy": {"name": STRATEGY_NAME, "desc": STRATEGY_DESC,
                     "params": {"zEntry": Z_ENTRY, "zExit": Z_EXIT, "zStop": Z_STOP,
                                "maxHoldDays": MAX_HOLD_DAYS, "mult": MULT, "slipPerLeg": SLIP_PER_LEG,
                                "shockAbsorption": True}},
        "summary": aware_summary,
        "blind": {"summary": blind_summary},
        "comparison": shock.head_to_head(aware_summary, blind_summary),
        "shock": shock.shock_summary(aware_trades),
        "byStructure": shock.per_structure(aware_trades, structures),
        "byRegime": shock.per_regime(aware_trades),
        "byVolState": shock.per_volstate(aware_trades),
        "equityCurve": shock.equity_from_daily(aware_daily, INITIAL_CAPITAL),
        "trades": sorted(aware_trades, key=lambda t: t["entryDate"], reverse=True),
        "openPositions": opens, "openCount": len(opens),
    }
    (DATA_DIR / "historical_backtest.json").write_text(json.dumps(feed, indent=1), encoding="utf8")
    write_csv(aware_trades)
    s = aware_summary
    net = f" | net ${s['netPnl']:,.0f}" if s["costs"] > 0 else ""
    print(f"\n{first.date()} -> {last.date()} ({years:.1f}y, {len(df)} days) | AWARE: "
          f"trades {s['trades']} | gross ${s['grossPnl']:,.0f}{net} | win {s['winRate']*100:.0f}% | "
          f"PF {s['profitFactor']} | Sharpe {s['sharpe']} | Calmar {s['calmar']} | "
          f"maxDD {s['maxDrawdownPct']*100:.0f}% (${s['maxDrawdown']:,.0f}) | CVaR ${s['cvar5']:,.0f}")
    b = blind_summary
    print(f"{'':>40}  BLIND: trades {b['trades']} | gross ${b['grossPnl']:,.0f} | "
          f"Sharpe {b['sharpe']} | Calmar {b['calmar']} | maxDD {b['maxDrawdownPct']*100:.0f}% "
          f"(${b['maxDrawdown']:,.0f}) | CVaR ${b['cvar5']:,.0f}")
    print(f"  -> {DATA_DIR / 'historical_backtest.json'}")


if __name__ == "__main__":
    main()
