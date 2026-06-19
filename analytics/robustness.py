"""
robustness.py — does the intraday edge survive honest stress tests, and how much
extra profit can we safely take? Re-uses the EXACT production strategy params from
historical_intraday.py (so this always reflects the shipped engine) and reports:

  • Per-year P&L          — is the edge every year, or one lucky year?
  • Significance          — t-stat on per-trade net (>2 = real, not noise).
  • Monte-Carlo drawdown  — reshuffle trade order 2,000x -> drawdown distribution.
  • Walk-forward picks    — re-select structures each year on PAST data only; proves
                            the 3-structure pruning isn't hindsight cherry-picking.
  • Parameter sensitivity — net across the cost-gate x exit-depth grid (plateau, not spike).
  • Profit levers         — the same battery on candidate upgrades (deeper overshoot,
                            2-unit scaling) so we keep only what is robust, not just bigger.

Precomputes each structure's segmented rolling frames ONCE, then simulates every config
cheaply on top. Reads out/intraday_15min.parquet; writes server/data/robustness.json.
Run:  python analytics/robustness.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import DATA_DIR
from historical_intraday import (STRUCTURES, MULT, LOOKBACK, Z_ENTRY, Z_EXIT, Z_STOP,
                                 MAX_HOLD_BARS, ASSUMED_SLIP, EDGE_COST_MULT,
                                 SCALE_IN, SCALE_ADD_Z, SCALE_MAX_UNITS,
                                 spread_frame, load_curve)

PROD_ADD_Z = SCALE_ADD_Z if SCALE_IN else 0.0      # production scaling (or none)
PROD_MAX = SCALE_MAX_UNITS if SCALE_IN else 1

REPORT_SLIP = 0.01
ACTIVE = [k for k, _, _, _, on in STRUCTURES if on]      # the 3 traded
ALL = [k for k, _, _, _, _ in STRUCTURES]
RNG = np.random.default_rng(7)                            # fixed seed -> reproducible


# ---- Precompute per-structure segmented frames once ------------------------
def precompute(df):
    segs, nlegs = {}, {}
    for key, _, legs, _, _ in STRUCTURES:
        nlegs[key] = sum(abs(w) for _, _, w in legs)
        sub = spread_frame(df, legs)
        out = []
        if len(sub) >= LOOKBACK + 3:
            for _, g in sub.groupby("seg", sort=False):
                if len(g) < LOOKBACK + 2:
                    continue
                m = g["spread"].rolling(LOOKBACK).mean()
                s = g["spread"].rolling(LOOKBACK).std()
                z = (g["spread"] - m) / s
                gg = pd.DataFrame({"spread": g["spread"], "mean": m, "std": s, "z": z}).dropna()
                gg = gg[gg["std"] > 0]
                if not gg.empty:
                    out.append((list(gg.index), gg["spread"].values, gg["mean"].values, gg["z"].values))
        segs[key] = out
    return segs, nlegs


def sim_one(seglist, n_legs, gate_mult=EDGE_COST_MULT, z_exit=Z_EXIT, add_z=0.0, max_units=1):
    gate_cost = gate_mult * 2 * n_legs * ASSUMED_SLIP * MULT
    rt = 2 * n_legs * REPORT_SLIP * MULT
    out = []
    for idx, sp, mv, zv in seglist:
        last = len(sp) - 1
        pos = None
        for i in range(len(sp)):
            zi, spi = float(zv[i]), float(sp[i])
            if pos is None:
                if i < last and abs(zi) >= Z_ENTRY and abs(spi - float(mv[i])) * MULT >= gate_cost:
                    pos = {"dir": "L" if zi <= -Z_ENTRY else "S", "i": i, "entries": [spi]}
                continue
            sign = 1.0 if pos["dir"] == "L" else -1.0
            if add_z and len(pos["entries"]) < max_units and abs(zi) >= add_z and (zi < 0) == (pos["dir"] == "L"):
                pos["entries"].append(spi)
            held = i - pos["i"]
            if (-sign) * zi <= z_exit or abs(zi) >= Z_STOP or held >= MAX_HOLD_BARS or i == last:
                u = len(pos["entries"])
                g = sign * sum(spi - e for e in pos["entries"]) * MULT
                out.append((idx[i], g, g - rt * u))
                pos = None
    return out


def book(segs, nlegs, keys=ACTIVE, **kw):
    kw.setdefault("add_z", PROD_ADD_Z)             # default to the shipped scaling
    kw.setdefault("max_units", PROD_MAX)
    rows = []
    for k in keys:
        for (t, g, n) in sim_one(segs[k], nlegs[k], **kw):
            rows.append((t, g, n, t.year, k))
    return pd.DataFrame(rows, columns=["t", "gross", "net", "year", "structure"]).sort_values("t").reset_index(drop=True)


def pf(x):
    gw = float(x[x > 0].sum()); gl = -float(x[x <= 0].sum())
    return round(gw / gl, 3) if gl > 0 else None


def maxdd(net):
    eq = np.asarray(net).cumsum()
    if not len(eq):
        return 0.0
    return float((eq - np.maximum.accumulate(eq)).min())


def battery(bk, mc=2000):
    n = len(bk)
    nets = bk["net"].values
    tstat = float(nets.mean() / (nets.std(ddof=1) / np.sqrt(n))) if n > 1 and nets.std() > 0 else 0.0
    dds = [maxdd(RNG.permutation(nets)) for _ in range(mc)]
    p5, p50, p95 = (round(float(x)) for x in np.percentile(dds, [5, 50, 95]))
    per_year = [{"year": int(y), "trades": len(s), "gross": round(float(s["gross"].sum())),
                 "net": round(float(s["net"].sum())), "pf": pf(s["gross"])}
                for y, s in bk.groupby("year")]
    return {"trades": n, "gross": round(float(bk["gross"].sum())), "net": round(float(bk["net"].sum())),
            "pf": pf(bk["gross"]), "tStat": round(tstat, 1), "netDrawdown": round(maxdd(nets)),
            "mcDrawdown": {"p5": p5, "p50": p50, "p95": p95}, "perYear": per_year,
            "allYearsPositive": all(py["net"] > 0 for py in per_year)}


def walk_forward(segs, nlegs, **kw):
    full = book(segs, nlegs, keys=ALL, **kw)
    years = sorted(int(y) for y in full["year"].unique())
    picks, tot_net, tot_gross = [], 0.0, 0.0
    for y in years:
        if y == years[0]:
            keep = ALL
        else:
            per = full[full["year"] < y].groupby("structure")["net"].sum()
            keep = [k for k in ALL if per.get(k, 0) > 0]
        sub = full[(full["year"] == y) & (full["structure"].isin(keep))]
        picks.append({"year": y, "structures": sorted(keep), "net": round(float(sub["net"].sum()))})
        tot_net += float(sub["net"].sum()); tot_gross += float(sub["gross"].sum())
    fixed_net = round(float(book(segs, nlegs, keys=ACTIVE, **kw)["net"].sum()))
    return {"perYear": picks, "totalGross": round(tot_gross), "totalNet": round(tot_net),
            "fixedThreeNet": fixed_net}


def sensitivity(segs, nlegs):
    gates = [1.5, 2.0, 2.5]
    exits = [0.25, -0.5, -1.0, -1.5]
    grid = []
    for gm in gates:
        row = {"gate": gm}
        for ze in exits:
            row[str(ze)] = round(float(book(segs, nlegs, gate_mult=gm, z_exit=ze)["net"].sum()))
        grid.append(row)
    return {"gates": gates, "exits": exits, "grid": grid}


def main():
    df = load_curve()
    print(f"loaded {len(df):,} bars; precomputing frames...")
    segs, nlegs = precompute(df)

    base = battery(book(segs, nlegs))                                  # production: gate, prune, overshoot, scaling
    levers = {
        # opt-in upside vs the shipped default (whatever scaling state PROD_* reflect)
        "scaling_add2.75_max2": battery(book(segs, nlegs, add_z=2.75, max_units=2)),
        "overshoot_exit_-2.0": battery(book(segs, nlegs, z_exit=-2.0)),
    }
    wf = walk_forward(segs, nlegs)
    sens = sensitivity(segs, nlegs)

    out = {
        "generatedAt": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "strategy": {"zEntry": Z_ENTRY, "zExit": Z_EXIT, "gate": EDGE_COST_MULT,
                     "structures": ACTIVE, "reportSlip": REPORT_SLIP,
                     "scaleIn": SCALE_IN, "scaleAddZ": SCALE_ADD_Z, "scaleMaxUnits": SCALE_MAX_UNITS},
        "baseline": base, "profitLevers": levers, "walkForward": wf, "sensitivity": sens,
    }
    (DATA_DIR / "robustness.json").write_text(json.dumps(out, indent=1), encoding="utf8")

    b = base
    print(f"\nBASELINE  trades {b['trades']:,} | gross ${b['gross']:,} | net ${b['net']:,} | "
          f"PF {b['pf']} | t-stat {b['tStat']} | netDD ${b['netDrawdown']:,}")
    print(f"  MonteCarlo maxDD  p5 ${b['mcDrawdown']['p5']:,} / p50 ${b['mcDrawdown']['p50']:,} / p95 ${b['mcDrawdown']['p95']:,}")
    print(f"  all years positive: {b['allYearsPositive']}")
    for py in b["perYear"]:
        print(f"    {py['year']}  n={py['trades']:5,}  net ${py['net']:>9,}  PF {py['pf']}")
    print(f"\nWALK-FORWARD selection -> net ${wf['totalNet']:,}  (vs fixed-3 ${wf['fixedThreeNet']:,})")
    for p in wf["perYear"]:
        print(f"    {p['year']}: {p['structures']}")
    print("\nPROFIT LEVERS:")
    for k, v in levers.items():
        print(f"    {k:24} net ${v['net']:>10,}  netDD ${v['netDrawdown']:>9,}  allYrs+ {v['allYearsPositive']}")
    print(f"\n-> {DATA_DIR / 'robustness.json'}")


if __name__ == "__main__":
    main()
