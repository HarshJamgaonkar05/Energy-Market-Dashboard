"""
historical_backtest.py — the Phase-2 fundamental fair value, backtested as a daily
TRADE SIMULATION over the full 2021-2026 history.

This is the *correct* home for the Phase-2 model. Intraday (Phase 3) it could not be
used — the feed had no fundamentals, its level was stale, and it was flat over a few
days. On DAILY history with the fundamental features present, it is exactly the right
tool, and the sample is large enough to mean something (~5 years).

Method (honest, out-of-sample):
  • Fair value = the Phase-2 regression, produced WALK-FORWARD (expanding window,
    refit every 21 days) so a day's fair value never sees its own or future data —
    the same machinery models.py/backtest.py already validated.
  • Signal = residual z = (actual − fair value) / EXPANDING std  (no look-ahead).
  • Trade  = fade |z| ≥ 1.5 (rich → short the spread, cheap → long it); exit on
    reversion to fair (|z| ≤ 0.5), a 3σ stop, or a 20-trading-day time stop.
  • Size   = fixed 1 unit/trade, gross by default (the raw signal). --slip adds cost.

Reads  analytics/out/panel.parquet  +  server/data/backtest.json (Phase-2 hit-rates)
Writes server/data/historical_backtest.json  (+ out/historical_trades.csv)
Run:   python analytics/historical_backtest.py            # gross
       python analytics/historical_backtest.py --slip 0.02  # charge per-leg cost
"""
from __future__ import annotations

import argparse
import csv
import json

import numpy as np
import pandas as pd

from common import OUT_DIR, DATA_DIR
from regimes import classify
from models import FEATURES, walk_forward, MIN_TRAIN

# ---- Strategy parameters (daily horizon) -----------------------------------
Z_ENTRY = 1.5          # fade when |residual z| >= this (Phase-2 validated threshold)
Z_EXIT = 0.5           # take profit once reverted to within this of fair value
Z_STOP = 3.0           # stop if the dislocation widens to |z| >= this
MAX_HOLD_DAYS = 20     # time stop, in trading days (~1 month)
MULT = 1000            # $1.00/bbl move on a 1,000-bbl unit = $1,000
INITIAL_CAPITAL = 250_000
SLIP_PER_LEG = 0.0     # per-leg, per-side slippage in price units; 0 = gross

# WTI & Brent only — calendars, butterflies, and the Brent-WTI arb.
# (target panel column, display label, Phase-2 hit-rate key for confidence/context)
CRUDE = [
    ("wti_m1m2",   "WTI M1-M2",         "wti_m1m2"),
    ("wti_m2m3",   "WTI M2-M3",         "wti_m1m2"),
    ("wti_fly",    "WTI M1-M2-M3 fly",  "wti_fly"),
    ("brent_m1m2", "Brent M1-M2",       "brent_m1m2"),
    ("brent_m2m3", "Brent M2-M3",       "brent_m1m2"),
    ("brent_fly",  "Brent M1-M2-M3 fly","wti_fly"),
    ("brent_wti",  "Brent-WTI arb",     "brent_wti"),
]

STRATEGY_NAME = "Phase-2 fundamental RV mean-reversion (WTI & Brent, daily, 5y)"
STRATEGY_DESC = ("Fair value from the Phase-2 fundamentals regression (walk-forward, "
                 "out-of-sample); fade a >=1.5sigma residual dislocation; exit on reversion "
                 "to fair (|z|<=0.5), a 3sigma stop, or a 20-day time stop. WTI & Brent crude "
                 "structures only, 1 unit/trade.")


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
    all aligned on the dates where the out-of-sample fair value exists."""
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


# ============================================================================
# Trade simulation for one spread
# ============================================================================
def simulate(df: pd.DataFrame, target: str, label: str, hitkey: str, edges: dict):
    rz = residual_z(df, target)
    if rz is None:
        return [], None
    spread, fv, z = rz
    regimes = df["regimeLabel"]
    hit = edge_for(hitkey, edges)
    legs = legs_count(target)
    cost = SLIP_PER_LEG * 2 * legs * MULT
    dates = list(z.index)

    trades, pos = [], None
    for i, dt in enumerate(dates):
        zi, sp = float(z.iloc[i]), float(spread.iloc[i])
        if np.isnan(zi) or np.isnan(sp):
            continue
        if pos is None:
            if abs(zi) >= Z_ENTRY:
                pos = {"dir": "LONG" if zi <= -Z_ENTRY else "SHORT", "i": i, "t": dt,
                       "sp": sp, "z": zi, "fv": float(fv.iloc[i]),
                       "regime": regimes.get(dt), "mae": 0.0, "mfe": 0.0}
            continue
        sign = 1.0 if pos["dir"] == "LONG" else -1.0
        entry_sign = -sign
        upnl = sign * (sp - pos["sp"]) * MULT
        pos["mae"], pos["mfe"] = min(pos["mae"], upnl), max(pos["mfe"], upnl)
        held = i - pos["i"]

        hit_target = entry_sign * zi <= Z_EXIT          # reverted to fair
        hit_stop = abs(zi) >= Z_STOP                     # dislocation widened
        hit_time = held >= MAX_HOLD_DAYS
        if hit_target or hit_stop or hit_time:
            reason = "target" if hit_target else "stop" if hit_stop else "time_stop"
            gross = sign * (sp - pos["sp"]) * MULT
            trades.append({
                "structure": target, "label": label, "regime": pos["regime"],
                "direction": pos["dir"],
                "entryDate": pos["t"].strftime("%Y-%m-%d"), "exitDate": dt.strftime("%Y-%m-%d"),
                "entrySpread": round(pos["sp"], 3), "exitSpread": round(sp, 3),
                "fairValue": round(pos["fv"], 3),
                "entryZ": round(pos["z"], 2), "exitZ": round(zi, 2),
                "holdDays": held, "holdLabel": f"{held}d", "pnl": round(gross, 2),
                "cost": round(cost, 2), "netPnl": round(gross - cost, 2),
                "mae": round(pos["mae"], 2), "mfe": round(pos["mfe"], 2),
                "exitReason": reason, "histHitRate": hit,
            })
            pos = None

    open_pos = None
    if pos is not None:
        i = len(dates) - 1
        sp, zi = float(spread.iloc[i]), float(z.iloc[i])
        sign = 1.0 if pos["dir"] == "LONG" else -1.0
        open_pos = {
            "structure": target, "label": label, "direction": pos["dir"],
            "entryDate": pos["t"].strftime("%Y-%m-%d"), "asOf": dates[i].strftime("%Y-%m-%d"),
            "entrySpread": round(pos["sp"], 3), "curSpread": round(sp, 3),
            "entryZ": round(pos["z"], 2), "curZ": round(zi, 2),
            "holdDays": i - pos["i"], "regime": pos["regime"],
            "unrealizedPnl": round(sign * (sp - pos["sp"]) * MULT, 2),
        }
    return trades, open_pos


# ============================================================================
# Aggregation
# ============================================================================
def equity_curve(all_trades):
    rows = sorted(all_trades, key=lambda t: t["exitDate"])
    eq = INITIAL_CAPITAL
    curve = [{"t": rows[0]["entryDate"], "equity": eq}] if rows else []
    for t in rows:
        eq += t["pnl"]
        curve.append({"t": t["exitDate"], "equity": round(eq, 2)})
    return curve


def max_drawdown(curve):
    peak, mdd = -1e18, 0.0
    for p in curve:
        peak = max(peak, p["equity"])
        mdd = min(mdd, p["equity"] - peak)
    return round(mdd, 2)


def _counts(rows, key):
    out = {}
    for r in rows:
        out[r[key]] = out.get(r[key], 0) + 1
    return out


def pf(rows):
    gw = sum(t["pnl"] for t in rows if t["pnl"] > 0)
    gl = -sum(t["pnl"] for t in rows if t["pnl"] <= 0)
    return round(gw / gl, 3) if gl > 0 else None


def summarize(all_trades, curve, years):
    n = len(all_trades)
    gross = sum(t["pnl"] for t in all_trades)
    net = sum(t["netPnl"] for t in all_trades)
    costs = sum(t["cost"] for t in all_trades)
    wins = [t for t in all_trades if t["pnl"] > 0]
    losses = [t for t in all_trades if t["pnl"] <= 0]
    gw, gl = sum(t["pnl"] for t in wins), -sum(t["pnl"] for t in losses)
    nwins = [t for t in all_trades if t["netPnl"] > 0]
    nlosses = [t for t in all_trades if t["netPnl"] <= 0]
    pnls = np.array([t["pnl"] for t in all_trades], float) if n else np.array([])
    sharpe = float(pnls.mean() / pnls.std()) if n > 1 and pnls.std() > 0 else 0.0
    return {
        "trades": n, "grossPnl": round(gross, 2), "netPnl": round(net, 2), "costs": round(costs, 2),
        "winRate": round(len(wins) / n, 4) if n else 0.0,
        "avgWin": round(gw / len(wins), 2) if wins else 0.0,
        "avgLoss": round(-gl / len(losses), 2) if losses else 0.0,
        "avgNetWin": round(sum(t["netPnl"] for t in nwins) / len(nwins), 2) if nwins else 0.0,
        "avgNetLoss": round(sum(t["netPnl"] for t in nlosses) / len(nlosses), 2) if nlosses else 0.0,
        "profitFactor": pf(all_trades), "expectancy": round(gross / n, 2) if n else 0.0,
        "netExpectancy": round(net / n, 2) if n else 0.0,
        "perTradeSharpe": round(sharpe, 3),
        "avgHoldDays": round(float(np.mean([t["holdDays"] for t in all_trades])), 1) if n else 0.0,
        "tradesPerYear": round(n / years, 1) if years else 0.0,
        "maxDrawdown": max_drawdown(curve),
        "endingEquity": round(INITIAL_CAPITAL + gross, 2), "initialCapital": INITIAL_CAPITAL,
        "byExitReason": _counts(all_trades, "exitReason"), "byDirection": _counts(all_trades, "direction"),
    }


def per_structure(all_trades):
    out = {}
    for sp, label, _ in CRUDE:
        ts = [t for t in all_trades if t["structure"] == sp]
        if not ts:
            continue
        wins = [t for t in ts if t["pnl"] > 0]
        out[sp] = {
            "label": label, "trades": len(ts), "wins": len(wins),
            "winRate": round(len(wins) / len(ts), 3), "pnl": round(sum(t["pnl"] for t in ts), 2),
            "profitFactor": pf(ts), "avgHoldDays": round(float(np.mean([t["holdDays"] for t in ts])), 1),
            "histHitRate": ts[0]["histHitRate"],
        }
    return out


def per_regime(all_trades):
    out = {}
    labels = sorted({t["regime"] for t in all_trades if t["regime"]})
    for lab in labels:
        ts = [t for t in all_trades if t["regime"] == lab]
        wins = [t for t in ts if t["pnl"] > 0]
        out[lab] = {
            "trades": len(ts), "wins": len(wins),
            "winRate": round(len(wins) / len(ts), 3), "pnl": round(sum(t["pnl"] for t in ts), 2),
            "profitFactor": pf(ts),
        }
    return out


# ============================================================================
# Main
# ============================================================================
def write_csv(all_trades):
    cols = ["structure", "label", "regime", "direction", "entryDate", "exitDate", "holdDays",
            "entrySpread", "exitSpread", "fairValue", "entryZ", "exitZ", "pnl", "cost", "netPnl",
            "mae", "mfe", "exitReason", "histHitRate", "equityAfter"]
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

    all_trades, open_positions = [], []
    for sp, label, hitkey in CRUDE:
        trades, op = simulate(df, sp, label, hitkey, edges)
        all_trades += trades
        if op:
            open_positions.append(op)
        if trades:
            print(f"  {sp:14} trades={len(trades):3} pnl=${sum(t['pnl'] for t in trades):>8,.0f} "
                  f"win={sum(1 for t in trades if t['pnl']>0)/len(trades):.0%} PF={pf(trades)}")

    curve = equity_curve(all_trades)
    summary = summarize(all_trades, curve, years)
    feed = {
        "generatedAt": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "daily", "horizon": "daily",
        "span": {"first": first.strftime("%Y-%m-%d"), "last": last.strftime("%Y-%m-%d")},
        "years": round(years, 1), "days": int(len(df)),
        "strategy": {"name": STRATEGY_NAME, "desc": STRATEGY_DESC,
                     "params": {"zEntry": Z_ENTRY, "zExit": Z_EXIT, "zStop": Z_STOP,
                                "maxHoldDays": MAX_HOLD_DAYS, "mult": MULT, "slipPerLeg": SLIP_PER_LEG}},
        "summary": summary,
        "byStructure": per_structure(all_trades),
        "byRegime": per_regime(all_trades),
        "equityCurve": curve,
        "trades": sorted(all_trades, key=lambda t: t["entryDate"], reverse=True),
        "openPositions": open_positions, "openCount": len(open_positions),
    }
    (DATA_DIR / "historical_backtest.json").write_text(json.dumps(feed, indent=1), encoding="utf8")
    write_csv(all_trades)
    net = f" | net ${summary['netPnl']:,.0f}" if summary["costs"] > 0 else ""
    print(f"\n{first.date()} -> {last.date()} ({years:.1f}y, {len(df)} days) | "
          f"trades {summary['trades']} | gross ${summary['grossPnl']:,.0f}{net} | "
          f"win {summary['winRate']*100:.0f}% | PF {summary['profitFactor']} | "
          f"exp ${summary['netExpectancy' if summary['costs'] > 0 else 'expectancy']:,.0f} | "
          f"DD ${summary['maxDrawdown']:,.0f}")
    print(f"  -> {DATA_DIR / 'historical_backtest.json'}")


if __name__ == "__main__":
    main()
