"""
signals.py — rank explainable analytical opportunities under the CURRENT regime.

Two independent read-outs of "is this spread dislocated right now?":
  • regime z  — latest value vs the mean/std of the SAME spread within the current
                regime (from regimes.json) → conditioned on market state.
  • residual z — latest value vs the regression fair value (from models.json),
                produced walk-forward so it never sees its own data.

An opportunity is ranked by:
  magnitude   = how far the two read-outs say we are from normal,
  confidence  = the fair-value model's out-of-sample R² + regime sufficiency,
  robustness  = do the two read-outs AGREE (sign + size), and do residuals
                mean-revert (finite half-life)?

Only dislocations the two methods corroborate, under a model we trust, score high
— so the surfaced ideas are the ones we can actually explain.

Reads server/data/regimes.json + server/data/models.json
Writes server/data/signals.json   ·   Run: python analytics/signals.py
"""
from __future__ import annotations

import json

from common import DATA_DIR


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def confidence(r2_oos, n, sufficient, edge):
    """0–1 trust in the dislocation: model OOS R², regime sample size, AND the
    backtested edge of the signal (how far its historical reversion hit-rate beat
    the 50/50 baseline) — a signal that has actually worked is more trustworthy."""
    r2c = clamp(r2_oos)
    nfac = clamp(n / 250.0)
    edgef = clamp((edge or 0) / 0.25)   # +25pts over baseline → full marks
    c = 0.5 * r2c + 0.2 * nfac + 0.3 * edgef
    return round(c * (1.0 if sufficient else 0.6), 3)


def confidence_label(c):
    return "high" if c >= 0.4 else "medium" if c >= 0.2 else "low"


def main():
    regimes = json.loads((DATA_DIR / "regimes.json").read_text(encoding="utf8"))
    models = json.loads((DATA_DIR / "models.json").read_text(encoding="utf8"))
    bt_path = DATA_DIR / "backtest.json"
    bt_all = json.loads(bt_path.read_text(encoding="utf8")) if bt_path.exists() else {}
    backtest = bt_all.get("spreads", {})
    backtest_horizon = bt_all.get("horizonDays", 10)
    THRESHOLD_LABEL = f"{bt_all.get('thresholdSigma', 1.5):g}σ"

    rid = regimes["current"]["regimeId"]
    rlabel = regimes["current"]["label"]
    cat = next((c for c in regimes["catalog"] if c["regimeId"] == rid), None)
    regime_spreads = (cat or {}).get("spreads", {})
    regime_n = (cat or {}).get("n", 0)
    sufficient = (cat or {}).get("sufficient", False)

    opps = []
    for sp, m in models.get("models", {}).items():
        rs = regime_spreads.get(sp)          # regime-relative stats for this spread
        reg = m.get("residual", {})
        regime_z = rs.get("z") if rs else None
        resid_z = reg.get("z")
        if regime_z is None and resid_z is None:
            continue

        zs = [z for z in (regime_z, resid_z) if z is not None]
        agree = (regime_z is not None and resid_z is not None
                 and (regime_z >= 0) == (resid_z >= 0))
        # Combined magnitude: average when both agree; the more conservative
        # (smaller |z|, signed) when they conflict.
        if regime_z is not None and resid_z is not None:
            combined = (regime_z + resid_z) / 2 if agree else min(zs, key=abs)
        else:
            combined = zs[0]

        r2_oos = m["global"]["r2_oos"]
        hl = rs.get("halfLifeDays") if rs else None
        bt = backtest.get(sp) or {}
        edge = bt.get("edge") if bt.get("sufficient") else None
        conf = confidence(r2_oos, regime_n, sufficient, edge)

        # Robustness: agreement + both read-outs material + residuals mean-revert.
        both_material = all(abs(z) >= 1.0 for z in zs) and len(zs) == 2
        if agree and both_material and hl:
            robustness = "high"
        elif agree or len(zs) == 1:
            robustness = "medium"
        else:
            robustness = "low"
        rob_w = {"high": 1.0, "medium": 0.7, "low": 0.4}[robustness]

        score = round(abs(combined) * conf * rob_w, 3)
        direction = "rich" if combined > 0 else "cheap"

        cur = rs.get("current") if rs else m["global"]["coef"] and None
        fv = None
        if reg.get("latest") is not None and cur is not None:
            fv = round(cur - reg["latest"], 3)
        drivers = m["global"]["topDrivers"]

        # Plain-English rationale, generated from the model facts.
        parts = [f"In the current {rlabel} regime (n={regime_n}"
                 + (f", model OOS R²={r2_oos:.2f}" if r2_oos == r2_oos else "") + ")."]
        if rs:
            parts.append(f"{m['label']} averages {rs['mean']:.2f} here; it is now "
                         f"{rs['current']:.2f} ({regime_z:+.1f}σ {direction}).")
        if fv is not None and resid_z is not None:
            parts.append(f"The fair-value model (drivers: {', '.join(drivers[:3])}) expects "
                         f"{fv:.2f}, a residual of {reg['latest']:+.2f} ({resid_z:+.1f}σ).")
        if hl:
            parts.append(f"Such residuals mean-revert with a ~{hl:.0f}-day half-life.")
        if bt.get("sufficient"):
            parts.append(f"Backtest: past {THRESHOLD_LABEL} signals reverted "
                         f"{bt['hitRate']:.0%} of the time over {backtest_horizon}d "
                         f"(vs {bt['baselineHitRate']:.0%} baseline, {bt['edge']:+.0%} edge).")
        if not agree and len(zs) == 2:
            parts.append("Note: regime and model read-outs disagree — lower robustness.")

        opps.append({
            "spread": sp, "label": m["label"], "direction": direction,
            "current": cur, "regimeMean": rs["mean"] if rs else None, "fairValue": fv,
            "regimeZ": regime_z, "residualZ": resid_z, "combinedZ": round(combined, 2),
            "confidence": conf, "confidenceLabel": confidence_label(conf),
            "robustness": robustness, "r2_oos": r2_oos,
            "halfLifeDays": hl, "n": regime_n, "drivers": drivers,
            "backtest": ({"hitRate": bt["hitRate"], "baseline": bt["baselineHitRate"],
                          "edge": bt["edge"], "nSignals": bt["nSignals"], "avgFavMove": bt["avgFavMove"]}
                         if bt.get("sufficient") else None),
            "score": score, "rationale": " ".join(parts),
        })

    opps.sort(key=lambda o: -o["score"])

    out = {
        "generatedAt": regimes["generatedAt"],
        "asOf": regimes["asOf"],
        "regime": {"regimeId": rid, "label": rlabel},
        "opportunities": opps,
    }
    path = DATA_DIR / "signals.json"
    path.write_text(json.dumps(out))
    print(f"  regime: {rlabel}  | {len(opps)} opportunities ranked")
    for o in opps[:5]:
        print(f"   {o['spread']:14} {o['direction']:5} score={o['score']:.2f} "
              f"z={o['combinedZ']:+.1f} conf={o['confidenceLabel']:6} robust={o['robustness']}")
    print(f"  -> {path}  ({round(path.stat().st_size/1024)} KB)")


if __name__ == "__main__":
    main()
