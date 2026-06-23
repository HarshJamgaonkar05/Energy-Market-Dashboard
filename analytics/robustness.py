"""
robustness.py — does the intraday edge survive honest stress tests? Re-uses the EXACT
production engine (regime_strategy + historical_intraday) so this always reflects the
shipped strategy, and compares the regime-AWARE book against the regime-BLIND control:

  • Per-year P&L          — is the edge every year, or one lucky year? (aware vs blind)
  • Significance          — t-stat on per-trade net (>2 ≈ real, not noise).
  • Monte-Carlo drawdown  — reshuffle trade order 2,000× → drawdown distribution (p50/p95/worst).

Reads out/intraday_15min.parquet (built by historical_intraday); writes server/data/robustness.json.
Run:  python analytics/robustness.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import DATA_DIR
import regime_strategy as rs
import historical_intraday as hi

REPORT_SLIP = 0.01
RNG = np.random.default_rng(7)          # fixed seed → reproducible
N_MC = 2000


def ref_net(trades):
    """Per-trade net at a realistic 1c/leg (round-turn), respecting each trade's size."""
    out = []
    for t in trades:
        legs = 4 if (t.get("structure", "").lower().endswith("fly")) else 2
        cost = 2 * legs * REPORT_SLIP * t.get("size", 1.0) * hi.MULT
        out.append(t["pnl"] - cost)
    return np.array(out, float)


def per_year(trades):
    out = {}
    for t in trades:
        yr = t["exitDate"][:4]
        out[yr] = out.get(yr, 0.0) + t["pnl"]
    return {k: round(v, 2) for k, v in sorted(out.items())}


def mc_drawdown(pnls):
    """Distribution of max drawdown over 2,000 reshuffles of the trade ORDER."""
    if len(pnls) < 10:
        return {"p50": 0.0, "p95": 0.0, "worst": 0.0}
    dds = np.empty(N_MC)
    for i in range(N_MC):
        eq = hi.INITIAL_CAPITAL + np.cumsum(RNG.permutation(pnls))
        peak = np.maximum.accumulate(eq)
        dds[i] = (eq - peak).min()
    return {"p50": round(float(np.percentile(dds, 50)), 2),
            "p95": round(float(np.percentile(dds, 5)), 2),     # 5th pct = a bad (deep) drawdown
            "worst": round(float(dds.min()), 2)}


def main():
    df = hi.load_curve()
    reg_map = hi.regime_by_date()
    edges = hi.edges_map()
    cfg = rs.INTRADAY_CONFIG
    cfg.mult = hi.MULT
    cfg.slip_per_leg = 0.0

    # mirror the intraday engine's traded universe (its OOS train gate), so the per-year / t-stat
    # / Monte-Carlo numbers reconcile with the backtest.
    try:
        traded = set(json.loads((DATA_DIR / "historical_intraday.json").read_text(encoding="utf8"))
                     .get("strategy", {}).get("params", {}).get("tradedStructures", []))
    except Exception:
        traded = set()

    aware_trades, blind_trades = [], []
    for key, label, legs, hitkey in hi.STRUCTURES:
        hit, edge = hi.edge_for(hitkey, edges)
        if hit is None or edge < hi.MIN_EDGE:
            continue
        if traded and key not in traded:
            continue
        prepped = hi.prep_frames(df, legs, reg_map, cfg)
        if prepped is None:
            continue
        fa, fb, hl = prepped
        lc = sum(abs(w) for _, _, w in legs)
        a = rs.simulate_structure(fa, cfg, mode="aware", legs_count=lc, structure=key,
                                  label=label, hit_rate=hit, halflife=hl)
        b = rs.simulate_structure(fb, cfg, mode="blind", legs_count=lc, structure=key,
                                  label=label, hit_rate=hit, halflife=hl)
        aware_trades += a["trades"]; blind_trades += b["trades"]

    aware_pnl = np.array([t["pnl"] for t in aware_trades], float)
    net = ref_net(aware_trades)
    n = len(net)
    tstat = float(net.mean() / (net.std(ddof=1) / np.sqrt(n))) if n > 1 and net.std(ddof=1) > 0 else 0.0

    ay, by = per_year(aware_trades), per_year(blind_trades)
    years = sorted(set(ay) | set(by))
    per_year_rows = [{"year": y, "aware": ay.get(y, 0.0), "blind": by.get(y, 0.0)} for y in years]
    aware_profitable_years = sum(1 for r in per_year_rows if r["aware"] > 0)

    out = {
        "generatedAt": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "horizon": "intraday", "reportSlip": REPORT_SLIP,
        "perYear": per_year_rows,
        "perYearSummary": {"years": len(years), "awareProfitableYears": aware_profitable_years},
        "significance": {
            "nTrades": n,
            "meanNetPerTrade": round(float(net.mean()), 2) if n else 0.0,
            "tStat": round(tstat, 2),
            "interpretation": "t>2 ≈ a real edge, not noise" if tstat > 2 else "below the t>2 significance bar",
        },
        "monteCarlo": {
            "reshuffles": N_MC,
            "awareDrawdown": mc_drawdown(aware_pnl),
            "blindDrawdown": mc_drawdown(np.array([t["pnl"] for t in blind_trades], float)),
        },
    }
    path = DATA_DIR / "robustness.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf8")
    print(f"  per-year aware profitable in {aware_profitable_years}/{len(years)} years | "
          f"t-stat {tstat:.2f} (n={n}) | MC p95 DD ${out['monteCarlo']['awareDrawdown']['p95']:,.0f}")
    print(f"  -> {path}")


if __name__ == "__main__":
    main()
