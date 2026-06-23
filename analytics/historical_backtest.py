"""
historical_backtest.py — DAILY 5-year backtest, fully REGIME-DRIVEN.

The Phase-2 fundamentals regression is the FAIR VALUE (walk-forward, strictly
out-of-sample); the Phase-2 REGIME MODEL drives every decision on top of it:

  • Fair value  = the walk-forward fundamentals regression (analytics/models.py).
                  Dislocation = actual − fair value. A structure is traded ONLY where
                  that regression is a *validated* fair value (out-of-sample R² ≥ MIN_OOS)
                  — the negative-OOS butterflies/calendars are evaluated but not traded.
  • Signal      = a REGIME-CONDITIONED z: residual ÷ the EXPANDING std of residuals in
                  the SAME vol-state (no look-ahead).
  • Policy      = per vol-state (Low/Normal/High) zEntry/zExit/zStop and a max-hold set
                  to a multiple of the regime's TRAILING half-life.
  • Sizing      = vol-target — size ∝ (typical dispersion / this-state dispersion), so
                  each trade risks ~constant $ and high-vol regimes auto-get smaller size.
  • Shock layer = de-lever / stand-aside / confirmation-delay / flatten-on-regime-break,
                  driven by a severity∈[0,1] detector (vol jump, regime transition, z-breach).

Run alongside is a REGIME-BLIND control (fixed z=2, fixed 1 unit, global dispersion,
fixed hold, no shock layer) on the SAME fair value and SAME universe, so the head-to-head
isolates exactly what the regime model contributes. We lead with RISK (Sharpe, Calmar,
max drawdown, CVaR, % time in market), not gross PnL.

Reads  analytics/out/panel.parquet  +  server/data/backtest.json (Phase-2 hit-rates)
Writes server/data/historical_backtest.json  (+ out/historical_trades.csv)
Run:   python analytics/historical_backtest.py            # gross
       python analytics/historical_backtest.py --slip 0.02
"""
from __future__ import annotations

import argparse
import csv
import json

import numpy as np
import pandas as pd

from common import OUT_DIR, DATA_DIR
from regimes import classify
from models import FEATURES, walk_forward, MIN_TRAIN, r2
import regime_strategy as rs

INITIAL_CAPITAL = 250_000
MULT = 1000
REF_SLIP = 0.02            # reference per-leg cost for the always-shown after-cost number
# A structure is traded only where its regression FV beats the mean out-of-sample. NOTE: this
# gate uses the FULL-sample OOS R² (an in-sample UNIVERSE choice — "trade the structures whose
# model validates over the history"). The fair value itself is strictly walk-forward; only the
# membership decision is full-sample, and it is applied IDENTICALLY to the aware and blind arms,
# so it never biases the head-to-head — it only sets which structures both arms trade.
MIN_OOS = 0.05

# Daily universe (target column, display label). The whitelist is DATA-DRIVEN: each is
# kept only if its walk-forward OOS R² ≥ MIN_OOS — so the model, not a hand-set flag,
# decides the tradeable set. Cracks (strong OOS R²) lead; the negative-OOS butterflies
# (wti_fly, gasoil_fly) and ho_gasoil are evaluated and dropped.
UNIVERSE = [
    ("brent_wti",     "Brent-WTI arb"),
    ("ho_wti",        "HO crack (WTI)"),
    ("ho_brent",      "HO crack (Brent)"),
    ("rbob_ho",       "RBOB-HO"),
    ("crack_321_wti", "3:2:1 crack"),
    ("gasoil_brent",  "Gas Oil crack"),
    ("gasoil_m1m2",   "Gas Oil M1-M2"),
    ("wti_m1m2",      "WTI M1-M2"),
    ("brent_m1m2",    "Brent M1-M2"),
    ("wti_fly",       "WTI M1-M2-M3 fly"),
    ("gasoil_fly",    "Gas Oil fly"),
    ("ho_gasoil",     "HO-Gas Oil"),
]

STRATEGY_NAME = "Regime-driven fundamental RV mean-reversion (daily, 5y)"
STRATEGY_DESC = (
    "Fair value = the Phase-2 fundamentals regression (walk-forward, out-of-sample). The "
    "regime model DRIVES the book: a regime-conditioned z (residual vs same-vol-state expanding "
    "std), per-vol-state z-thresholds and max-hold (× the regime's trailing half-life), "
    "vol-target sizing (constant $-risk; high-vol regimes auto-sized down), and a shock layer "
    "(de-lever / stand-aside / flatten on a regime break). Universe = structures whose regression "
    "fair value is validated out-of-sample (R² ≥ 0.05). A regime-blind control runs head-to-head."
)


def phase2_edges() -> dict:
    try:
        return json.loads((DATA_DIR / "backtest.json").read_text(encoding="utf8")).get("spreads", {})
    except Exception:
        return {}


def hit_for(target: str, edges: dict):
    # exact key, then a sensible calendar fallback for keys absent from backtest.json
    fb = {"wti_m2m3": "wti_m1m2", "brent_m2m3": "brent_m1m2"}
    bt = edges.get(target) or edges.get(fb.get(target, ""), None)
    if bt and bt.get("sufficient"):
        return round(float(bt["hitRate"]), 3)
    return None


def regression_frame(df: pd.DataFrame, target: str):
    """Walk-forward regression fair value + OOS R², aligned to the dates where the
    out-of-sample fair value exists. Returns (frame, oos_r2) or (None, oos_r2)."""
    sub = df[FEATURES + [target]].dropna()
    if len(sub) < MIN_TRAIN + 60:
        return None, float("nan")
    fv = pd.Series(walk_forward(sub[FEATURES].values, sub[target].values), index=sub.index)
    oos = r2(sub[target][fv.notna()], fv.dropna())
    valid = fv.notna()
    sub, fv = sub[valid], fv[valid]
    if len(sub) < 60:
        return None, oos
    frame = pd.DataFrame({
        "spread": sub[target],
        "fv": fv,
        "vol_state": df["volatility"].reindex(sub.index),
        "regime_id": df["regimeId"].reindex(sub.index),
        "regime": df["regimeLabel"].reindex(sub.index),
        "bar_vol": df["wti_rvol20"].reindex(sub.index),
    })
    frame["seg"] = 1
    return frame, oos


def sizing_series(size_map: dict, sev_map: dict) -> list[dict]:
    """Portfolio sizing/severity strip: per-day mean intended size + mean severity across
    structures — the visual that shows the book de-levering through shocks."""
    if not size_map:
        return []
    sizes = pd.concat(size_map.values(), axis=1, sort=True).mean(axis=1)
    sevs = pd.concat(sev_map.values(), axis=1, sort=True).mean(axis=1)
    by_day_size = sizes.groupby(sizes.index.normalize()).mean()
    by_day_sev = sevs.groupby(sevs.index.normalize()).mean()
    out = []
    for ts in by_day_size.index:
        out.append({"t": ts.strftime("%Y-%m-%d"),
                    "size": round(float(by_day_size[ts]), 3),
                    "severity": round(float(by_day_sev.get(ts, 0.0)), 3)})
    return out


def comparison(aware_sum, blind_sum) -> dict:
    """The head-to-head that isolates the regime model's contribution (risk-led)."""
    def pair(key):
        return {"aware": aware_sum.get(key), "blind": blind_sum.get(key)}
    return {k: pair(k) for k in
            ["sharpe", "calmar", "maxDrawdown", "maxDrawdownPct", "cvar5", "volAnn",
             "netPnl", "grossPnl", "profitFactor", "trades", "pctTimeInMarket", "cagr"]}


def write_csv(all_trades):
    cols = ["structure", "label", "regime", "volState", "direction", "entryDate", "exitDate",
            "holdDays", "entrySpread", "exitSpread", "fairValue", "entryZ", "exitZ", "size",
            "entrySeverity", "pnl", "cost", "netPnl", "mae", "mfe", "exitReason", "histHitRate",
            "equityAfter"]
    with open(OUT_DIR / "historical_trades.csv", "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); eq = INITIAL_CAPITAL
        for t in sorted(all_trades, key=lambda x: x["exitDate"]):
            eq += t["pnl"]; row = dict(t); row["equityAfter"] = round(eq, 2)
            w.writerow(row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slip", type=float, default=0.0,
                    help="per-leg slippage in price units (e.g. 0.02); reports net alongside gross")
    args = ap.parse_args()

    cfg = rs.DAILY_CONFIG
    cfg.slip_per_leg = args.slip
    cfg.mult = MULT

    panel = pd.read_parquet(OUT_DIR / "panel.parquet")
    df = classify(panel)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    edges = phase2_edges()

    first, last = df.index.min(), df.index.max()
    years = max((last - first).days / 365.25, 1e-9)

    aware_trades, blind_trades = [], []
    aware_pnls, blind_pnls = [], []
    aware_inmkt, blind_inmkt = [], []
    size_map, sev_map = {}, {}
    open_positions = []
    traded, skipped = [], []

    for target, label in UNIVERSE:
        frame, oos = regression_frame(df, target)
        if frame is None:
            skipped.append((target, label, oos, "insufficient"))
            continue
        if not np.isfinite(oos) or oos < MIN_OOS:
            skipped.append((target, label, oos, "OOS R² below gate"))
            continue
        traded.append((target, label))
        hit = hit_for(target, edges)
        residual = (frame["spread"] - frame["fv"]).to_numpy(float)
        hl = rs.trailing_halflife(residual, frame["vol_state"].to_numpy(object),
                                  frame["seg"].to_numpy(), cfg)

        a = rs.simulate_structure(frame, cfg, mode="aware", legs_count=rs._legs_of({"structure": target}),
                                  structure=target, label=label, hit_rate=hit, halflife=hl)
        b = rs.simulate_structure(frame, cfg, mode="blind", legs_count=rs._legs_of({"structure": target}),
                                  structure=target, label=label, hit_rate=hit, halflife=hl)
        aware_trades += a["trades"]; blind_trades += b["trades"]
        aware_pnls.append(a["pnl"]); blind_pnls.append(b["pnl"])
        aware_inmkt.append(a["in_market"]); blind_inmkt.append(b["in_market"])
        size_map[target] = a["size"]; sev_map[target] = a["severity"]
        if a["open"]:
            open_positions.append(a["open"])
        print(f"  {target:14} OOS={oos:+.2f} aware n={len(a['trades']):3} "
              f"pnl=${sum(t['pnl'] for t in a['trades']):>9,.0f} | blind n={len(b['trades']):3} "
              f"pnl=${sum(t['pnl'] for t in b['trades']):>9,.0f}")

    for target, label, oos, why in skipped:
        print(f"  {target:14} OOS={oos:+.2f}  SKIP ({why})")

    aware_daily = rs.portfolio_daily_pnl(aware_pnls)
    blind_daily = rs.portfolio_daily_pnl(blind_pnls)
    aware_sum = rs.summarize(aware_trades, aware_daily, INITIAL_CAPITAL, years, MULT, REF_SLIP, "daily")
    blind_sum = rs.summarize(blind_trades, blind_daily, INITIAL_CAPITAL, years, MULT, REF_SLIP, "daily")
    aware_sum["pctTimeInMarket"] = rs.pct_time_in_market(aware_inmkt)
    blind_sum["pctTimeInMarket"] = rs.pct_time_in_market(blind_inmkt)

    curve = rs.equity_from_daily(aware_daily, INITIAL_CAPITAL)
    curve_blind = rs.equity_from_daily(blind_daily, INITIAL_CAPITAL)

    feed = {
        "generatedAt": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "daily", "horizon": "daily",
        "span": {"first": first.strftime("%Y-%m-%d"), "last": last.strftime("%Y-%m-%d")},
        "years": round(years, 1), "days": int(len(df)),
        "strategy": {"name": STRATEGY_NAME, "desc": STRATEGY_DESC,
                     "params": {"minOOS": MIN_OOS, "mult": MULT, "slipPerLeg": args.slip,
                                "volStateParams": {s: vars(p) for s, p in cfg.params.items()},
                                "sizing": "vol-target (constant $-risk, ×typical/state dispersion)",
                                "tradedStructures": [t for t, _ in traded]}},
        "summary": aware_sum,
        "blind": {"summary": blind_sum, "equityCurve": curve_blind},
        "comparison": comparison(aware_sum, blind_sum),
        "byStructure": rs.per_structure(aware_trades, traded),
        "byRegime": rs.per_regime(aware_trades),
        "byVolState": rs.per_volstate(aware_trades),
        "equityCurve": curve, "equityCurveBlind": curve_blind,
        "sizingSeries": sizing_series(size_map, sev_map),
        "trades": sorted(aware_trades, key=lambda t: t["entryDate"], reverse=True),
        "openPositions": open_positions, "openCount": len(open_positions),
    }
    (DATA_DIR / "historical_backtest.json").write_text(json.dumps(feed, indent=1), encoding="utf8")
    write_csv(aware_trades)

    print(f"\n{first.date()} -> {last.date()} ({years:.1f}y) | traded {len(traded)} structures")
    print(f"  AWARE  trades {aware_sum['trades']:4} | net ${aware_sum['netPnl']:>10,.0f} | "
          f"Sharpe {aware_sum['sharpe']:.2f} | Calmar {aware_sum['calmar']} | "
          f"maxDD ${aware_sum['maxDrawdown']:,.0f} ({aware_sum['maxDrawdownPct']*100:.1f}%) | "
          f"CVaR ${aware_sum['cvar5']:,.0f} | TIM {aware_sum['pctTimeInMarket']*100:.0f}%")
    print(f"  BLIND  trades {blind_sum['trades']:4} | net ${blind_sum['netPnl']:>10,.0f} | "
          f"Sharpe {blind_sum['sharpe']:.2f} | Calmar {blind_sum['calmar']} | "
          f"maxDD ${blind_sum['maxDrawdown']:,.0f} ({blind_sum['maxDrawdownPct']*100:.1f}%) | "
          f"CVaR ${blind_sum['cvar5']:,.0f}")
    print(f"  -> {DATA_DIR / 'historical_backtest.json'}")


if __name__ == "__main__":
    main()
