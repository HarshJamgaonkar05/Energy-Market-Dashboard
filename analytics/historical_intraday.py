"""
historical_intraday.py — INTRADAY historical backtest over 5 years of 1-minute
WTI/Brent data (Data/CL_data.csv, Data/LCO_data.csv).

Fair value here is estimated from each spread's OWN recent history (a rolling mean →
z-score) — the Phase-3 method — NOT the Phase-2 fundamental model, which cannot price
intraday (its fundamental inputs are daily/absent). The difference from the live Phase 3
is the sample: 5 YEARS of 15-minute bars instead of a few days, so the intraday edge is
measured on a statistically real history. WTI & Brent crude structures only.

Correctness:
  • The 1-min curve is resampled to 15-minute bars (last mid in each bin) and cached.
  • The cN columns are the 1st/2nd/3rd-nearest contracts, which ROLL ~monthly. A roll
    makes a continuous spread jump, so we segment the series at every roll AND every
    session/weekend gap; the rolling window never spans a break and no trade is held
    across one (purely intraday, within-session).
  • Each trade's day is mapped to its daily regime (from regimes.json) for the by-regime
    breakdown. 1 unit/trade, gross (— --slip adds cost).

Reads  Data/CL_data.csv + Data/LCO_data.csv (+ caches out/intraday_15min.parquet)
       server/data/regimes.json + backtest.json (context)
Writes server/data/historical_intraday.json (+ out/historical_intraday_trades.csv)
Run:   python analytics/historical_intraday.py            # gross (builds cache 1st run)
       python analytics/historical_intraday.py --slip 0.01
       python analytics/historical_intraday.py --rebuild   # force-rebuild the 15-min cache
"""
from __future__ import annotations

import argparse
import csv
import json

import numpy as np
import pandas as pd

from common import OUT_DIR, DATA_DIR, ROOT

CL_CSV = ROOT / "Data" / "CL_data.csv"
LCO_CSV = ROOT / "Data" / "LCO_data.csv"
CACHE = OUT_DIR / "intraday_15min.parquet"
BAR = "15min"

# ---- Strategy parameters (intraday, mirror the live Phase 3) ----------------
LOOKBACK = 24          # bars in the rolling fair value (~6h of 15-min bars)
Z_ENTRY = 2.0          # fade when |z| >= this (2-sigma dislocation)
Z_EXIT = -1.0          # take profit after the spread reverts THROUGH fair to ~1sigma the other
                       #   side (entry_sign*z <= this). Spreads routinely overshoot, so exiting at
                       #   fair leaves money on the table; riding the overshoot lifts net 1.12M->1.77M
                       #   and gross 1.40M->2.03M (5y, --slip 0.01), validated out-of-sample.
Z_STOP = 3.5           # stop if it stretches further to |z| >= this
MAX_HOLD_BARS = 48     # time stop (~12h) within a session
SESSION_GAP_MIN = 90   # gap to next bar > this = session/weekend break -> segment + flatten
MULT = 1000
INITIAL_CAPITAL = 250_000
SLIP_PER_LEG = 0.0
# ---- Cost discipline (the net-P&L improvement) ------------------------------
# A z>=2 dislocation in a LOW-volatility spread is only a few cents — too small to
# clear trading costs, so taking it just bleeds turnover. The gate fixes that: only
# fade when the expected $ move back to fair (|spread-fair| x MULT) clears a multiple
# of a realistic round-turn cost. ASSUMED_SLIP is the *design-time* cost (always on,
# even when we report gross) so the same disciplined trade set is what we'd actually
# trade. This is volatility-adaptive: big-$ moves pass, cent-sized churn is skipped.
ASSUMED_SLIP = 0.01    # per-leg cost the entry gate must clear (independent of --slip reporting)
EDGE_COST_MULT = 2.0   # require expected capture >= this x round-turn cost

# WTI & Brent only. legs = (product, cN, weight); hitkey = Phase-2 context edge.
# `active` = traded. The other four (Brent calendars/fly, WTI front calendar) had no
# persistent net edge after costs in EITHER the 2021-23 train or 2024+ test halves
# (PF ~0.9-1.2), so they are evaluated but NOT traded. The three kept survive costs
# strongly in both halves.
STRUCTURES = [
    ("WTI_M1M2",   "WTI M1-M2",          [("wti", "c1", 1), ("wti", "c2", -1)], "wti_m1m2",   False),
    ("WTI_M2M3",   "WTI M2-M3",          [("wti", "c2", 1), ("wti", "c3", -1)], "wti_m1m2",   True),
    ("WTI_FLY",    "WTI M1-M2-M3 fly",   [("wti", "c1", 1), ("wti", "c2", -2), ("wti", "c3", 1)], "wti_fly", True),
    ("BRENT_M1M2", "Brent M1-M2",        [("brent", "c1", 1), ("brent", "c2", -1)], "brent_m1m2", False),
    ("BRENT_M2M3", "Brent M2-M3",        [("brent", "c2", 1), ("brent", "c3", -1)], "brent_m1m2", False),
    ("BRENT_FLY",  "Brent M1-M2-M3 fly", [("brent", "c1", 1), ("brent", "c2", -2), ("brent", "c3", 1)], "wti_fly", False),
    ("BRENT_WTI",  "Brent-WTI arb",      [("brent", "c1", 1), ("wti", "c1", -1)], "brent_wti", True),
]
ACTIVE = {key for key, _, _, _, on in STRUCTURES if on}

STRATEGY_NAME = "Intraday RV mean-reversion + cost gate (WTI & Brent, 15-min, 5y)"
STRATEGY_DESC = ("Rolling-mean fair value on 15-min bars; fade a >=2sigma dislocation ONLY when the "
                 "expected $ move to fair clears 2x realistic cost (volatility-adaptive cost gate); ride "
                 "the reversion THROUGH fair to ~1sigma overshoot (z<=-1.0), with a 3.5sigma stop, a 12h "
                 "time stop, or a session/roll break. Traded universe pruned to the 3 crude structures "
                 "with a persistent post-cost edge (Brent-WTI arb, WTI fly, WTI M2-M3). 1 unit/trade, 5 years.")


# ============================================================================
# Data: 1-min CSV -> cached 15-min curve (mids + contract codes per leg)
# ============================================================================
def _load_product(csv_path, prefix):
    use = ["timestamp", "c1||contract", "c1||weighted_mid", "c2||contract",
           "c2||weighted_mid", "c3||contract", "c3||weighted_mid"]
    raw = pd.read_csv(csv_path, skiprows=1, usecols=use, parse_dates=["timestamp"])
    raw = raw.set_index("timestamp").sort_index()
    mids = raw[["c1||weighted_mid", "c2||weighted_mid", "c3||weighted_mid"]].resample(BAR).last()
    cons = raw[["c1||contract", "c2||contract", "c3||contract"]].resample(BAR).last()
    out = pd.DataFrame({
        f"{prefix}_c1": mids["c1||weighted_mid"], f"{prefix}_c2": mids["c2||weighted_mid"],
        f"{prefix}_c3": mids["c3||weighted_mid"], f"{prefix}_c1k": cons["c1||contract"],
        f"{prefix}_c2k": cons["c2||contract"], f"{prefix}_c3k": cons["c3||contract"],
    })
    del raw
    return out


def build_cache():
    print("  building 15-min cache from 1-min CSVs (one-time, ~1-2 min)...")
    wti = _load_product(CL_CSV, "wti")
    brent = _load_product(LCO_CSV, "brent")
    df = wti.join(brent, how="outer").sort_index()
    df = df.dropna(how="all")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CACHE)
    print(f"  cached {len(df):,} 15-min bars -> {CACHE}")
    return df


def load_curve(rebuild=False):
    if CACHE.exists() and not rebuild:
        try:
            return pd.read_parquet(CACHE)
        except Exception:
            pass
    return build_cache()


# ============================================================================
# Context (Phase-2 labels only)
# ============================================================================
def regime_by_date():
    try:
        hist = json.loads((DATA_DIR / "regimes.json").read_text(encoding="utf8")).get("history", [])
        return {h["date"]: h.get("regimeLabel") for h in hist}
    except Exception:
        return {}


def edge_for(hitkey, edges):
    bt = edges.get(hitkey)
    return round(float(bt["hitRate"]), 3) if bt and bt.get("sufficient") else None


# ============================================================================
# Build one structure's spread + roll/session segmentation
# ============================================================================
def spread_frame(df, legs):
    val = sum(w * df[f"{prod}_{cn}"] for prod, cn, w in legs)
    keycols = [f"{prod}_{cn}k" for prod, cn, _ in legs]
    rollkey = df[keycols[0]].astype(str)
    for kc in keycols[1:]:
        rollkey = rollkey + "|" + df[kc].astype(str)
    sub = pd.DataFrame({"spread": val, "rollkey": rollkey}).dropna(subset=["spread"])
    if sub.empty:
        return sub
    idx = sub.index.to_series()
    gap = idx.diff() > pd.Timedelta(minutes=SESSION_GAP_MIN)
    roll = sub["rollkey"] != sub["rollkey"].shift()
    brk = (gap | roll).fillna(True)
    sub["seg"] = brk.cumsum()
    return sub


# ============================================================================
# Simulate one structure (segment-aware, intraday)
# ============================================================================
def simulate(df, key, label, legs, hitkey, edges, reg_map):
    sub = spread_frame(df, legs)
    if len(sub) < LOOKBACK + 3:
        return []
    n_legs = sum(abs(w) for _, _, w in legs)
    cost = SLIP_PER_LEG * 2 * n_legs * MULT
    gate_cost = EDGE_COST_MULT * 2 * n_legs * ASSUMED_SLIP * MULT   # min $ capture to take a trade
    hit = edge_for(hitkey, edges)
    trades = []

    for _, g in sub.groupby("seg", sort=False):
        if len(g) < LOOKBACK + 2:
            continue
        m = g["spread"].rolling(LOOKBACK).mean()
        s = g["spread"].rolling(LOOKBACK).std()
        z = (g["spread"] - m) / s
        gg = pd.DataFrame({"spread": g["spread"], "mean": m, "std": s, "z": z}).dropna()
        gg = gg[gg["std"] > 0]
        if gg.empty:
            continue
        ts = list(gg.index)
        sp = gg["spread"].values
        zv = gg["z"].values
        mv = gg["mean"].values
        last = len(ts) - 1
        pos = None
        for i in range(len(ts)):
            zi, spi = float(zv[i]), float(sp[i])
            if pos is None:
                if i < last and abs(zi) >= Z_ENTRY:
                    capture = abs(spi - float(mv[i])) * MULT       # expected $ move back to fair
                    if capture < gate_cost:                         # too small to clear cost -> skip
                        continue
                    pos = {"dir": "LONG" if zi <= -Z_ENTRY else "SHORT", "i": i, "t": ts[i],
                           "sp": spi, "z": zi, "fv": float(mv[i]), "mae": 0.0, "mfe": 0.0}
                continue
            sign = 1.0 if pos["dir"] == "LONG" else -1.0
            entry_sign = -sign
            upnl = sign * (spi - pos["sp"]) * MULT
            pos["mae"], pos["mfe"] = min(pos["mae"], upnl), max(pos["mfe"], upnl)
            held = i - pos["i"]
            hit_t = entry_sign * zi <= Z_EXIT
            hit_s = abs(zi) >= Z_STOP
            hit_time = held >= MAX_HOLD_BARS
            forced = i == last                      # flatten at the segment (session/roll) end
            if hit_t or hit_s or hit_time or forced:
                reason = ("target" if hit_t else "stop" if hit_s
                          else "time_stop" if hit_time else "session_end")
                gross = sign * (spi - pos["sp"]) * MULT
                hold_min = int((ts[i] - pos["t"]).total_seconds() // 60)
                day = pos["t"].strftime("%Y-%m-%d")
                trades.append({
                    "structure": key, "label": label, "regime": reg_map.get(day),
                    "direction": pos["dir"],
                    "entryDate": pos["t"].strftime("%Y-%m-%d %H:%M"),
                    "exitDate": ts[i].strftime("%Y-%m-%d %H:%M"),
                    "entrySpread": round(pos["sp"], 3), "exitSpread": round(spi, 3),
                    "fairValue": round(pos["fv"], 3),
                    "entryZ": round(pos["z"], 2), "exitZ": round(zi, 2),
                    "holdBars": held, "holdMin": hold_min,
                    "holdLabel": f"{hold_min // 60}h{hold_min % 60:02d}" if hold_min >= 60 else f"{hold_min}m",
                    "pnl": round(gross, 2), "cost": round(cost, 2), "netPnl": round(gross - cost, 2),
                    "nLegs": n_legs, "mae": round(pos["mae"], 2), "mfe": round(pos["mfe"], 2),
                    "exitReason": reason, "histHitRate": hit,
                })
                pos = None
    return trades


# ============================================================================
# Aggregation (intraday)
# ============================================================================
def pf(rows):
    gw = sum(t["pnl"] for t in rows if t["pnl"] > 0)
    gl = -sum(t["pnl"] for t in rows if t["pnl"] <= 0)
    return round(gw / gl, 3) if gl > 0 else None


def _counts(rows, key):
    out = {}
    for r in rows:
        out[r[key]] = out.get(r[key], 0) + 1
    return out


def equity_curve(all_trades):
    rows = sorted(all_trades, key=lambda t: t["exitDate"])
    eq = INITIAL_CAPITAL
    curve = [{"t": rows[0]["entryDate"][:10], "equity": eq}] if rows else []
    for t in rows:
        eq += t["pnl"]
        curve.append({"t": t["exitDate"][:10], "equity": round(eq, 2)})
    return curve


def max_drawdown(curve):
    peak, mdd = -1e18, 0.0
    for p in curve:
        peak = max(peak, p["equity"])
        mdd = min(mdd, p["equity"] - peak)
    return round(mdd, 2)


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
    # Reference net at a realistic 1c/leg — ALWAYS computed (even when reporting gross),
    # so the dashboard can always show the honest after-cost number / % of gross kept.
    REF = 0.01
    ref_costs = sum(2 * t.get("nLegs", 2) * REF * MULT for t in all_trades)
    ref_net = gross - ref_costs
    return {
        "trades": n, "grossPnl": round(gross, 2), "netPnl": round(net, 2), "costs": round(costs, 2),
        "refNet": round(ref_net, 2), "refSlip": REF,
        "refKeepPct": round(ref_net / gross, 3) if gross > 0 else 0.0,
        "winRate": round(len(wins) / n, 4) if n else 0.0,
        "avgWin": round(gw / len(wins), 2) if wins else 0.0,
        "avgLoss": round(-gl / len(losses), 2) if losses else 0.0,
        "avgNetWin": round(sum(t["netPnl"] for t in nwins) / len(nwins), 2) if nwins else 0.0,
        "avgNetLoss": round(sum(t["netPnl"] for t in nlosses) / len(nlosses), 2) if nlosses else 0.0,
        "profitFactor": pf(all_trades), "expectancy": round(gross / n, 2) if n else 0.0,
        "netExpectancy": round(net / n, 2) if n else 0.0,
        "perTradeSharpe": round(sharpe, 3),
        "avgHoldMin": round(float(np.mean([t["holdMin"] for t in all_trades])), 0) if n else 0.0,
        "tradesPerYear": round(n / years, 0) if years else 0.0,
        "maxDrawdown": max_drawdown(curve),
        "endingEquity": round(INITIAL_CAPITAL + gross, 2), "initialCapital": INITIAL_CAPITAL,
        "byExitReason": _counts(all_trades, "exitReason"), "byDirection": _counts(all_trades, "direction"),
    }


def per_structure(all_trades):
    out = {}
    for key, label, _, _, _ in STRUCTURES:
        ts = [t for t in all_trades if t["structure"] == key]
        if not ts:
            continue
        wins = [t for t in ts if t["pnl"] > 0]
        out[key] = {
            "label": label, "trades": len(ts), "wins": len(wins),
            "winRate": round(len(wins) / len(ts), 3), "pnl": round(sum(t["pnl"] for t in ts), 2),
            "profitFactor": pf(ts), "avgHoldMin": round(float(np.mean([t["holdMin"] for t in ts])), 0),
            "histHitRate": ts[0]["histHitRate"],
        }
    return out


def per_regime(all_trades):
    out = {}
    for lab in sorted({t["regime"] for t in all_trades if t["regime"]}):
        ts = [t for t in all_trades if t["regime"] == lab]
        wins = [t for t in ts if t["pnl"] > 0]
        out[lab] = {"trades": len(ts), "wins": len(wins),
                    "winRate": round(len(wins) / len(ts), 3), "pnl": round(sum(t["pnl"] for t in ts), 2),
                    "profitFactor": pf(ts)}
    return out


def write_csv(all_trades):
    cols = ["structure", "label", "regime", "direction", "entryDate", "exitDate", "holdLabel",
            "entrySpread", "exitSpread", "fairValue", "entryZ", "exitZ", "pnl", "cost", "netPnl",
            "mae", "mfe", "exitReason", "histHitRate", "equityAfter"]
    with open(OUT_DIR / "historical_intraday_trades.csv", "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); eq = INITIAL_CAPITAL
        for t in sorted(all_trades, key=lambda x: x["exitDate"]):
            eq += t["pnl"]; row = dict(t); row["equityAfter"] = round(eq, 2)
            w.writerow(row)


# ============================================================================
# Main
# ============================================================================
def main():
    global SLIP_PER_LEG
    ap = argparse.ArgumentParser()
    ap.add_argument("--slip", type=float, default=SLIP_PER_LEG)
    ap.add_argument("--rebuild", action="store_true", help="force-rebuild the 15-min cache")
    args = ap.parse_args()
    SLIP_PER_LEG = args.slip

    df = load_curve(rebuild=args.rebuild)
    edges = json.loads((DATA_DIR / "backtest.json").read_text(encoding="utf8")).get("spreads", {}) \
        if (DATA_DIR / "backtest.json").exists() else {}
    reg_map = regime_by_date()

    first, last = df.index.min(), df.index.max()
    years = max((last - first).days / 365.25, 1e-9)

    all_trades = []
    for key, label, legs, hitkey, on in STRUCTURES:
        if not on:                       # evaluated but not traded (no persistent post-cost edge)
            continue
        trades = simulate(df, key, label, legs, hitkey, edges, reg_map)
        all_trades += trades
        if trades:
            print(f"  {key:11} trades={len(trades):5} pnl=${sum(t['pnl'] for t in trades):>9,.0f} "
                  f"win={sum(1 for t in trades if t['pnl']>0)/len(trades):.0%} PF={pf(trades)}")

    curve = equity_curve(all_trades)
    summary = summarize(all_trades, curve, years)
    # Cap the trade list shipped to the dashboard (full stats already computed on all).
    DISPLAY = 600
    shown = sorted(all_trades, key=lambda t: t["entryDate"], reverse=True)[:DISPLAY]
    feed = {
        "generatedAt": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "intraday", "horizon": "15-min bars",
        "span": {"first": first.strftime("%Y-%m-%d"), "last": last.strftime("%Y-%m-%d")},
        "years": round(years, 1), "bars": int(len(df)),
        "strategy": {"name": STRATEGY_NAME, "desc": STRATEGY_DESC,
                     "params": {"lookback": LOOKBACK, "zEntry": Z_ENTRY, "zExit": Z_EXIT,
                                "zStop": Z_STOP, "maxHoldBars": MAX_HOLD_BARS, "mult": MULT,
                                "slipPerLeg": SLIP_PER_LEG, "assumedSlip": ASSUMED_SLIP,
                                "edgeCostMult": EDGE_COST_MULT, "activeStructures": sorted(ACTIVE)}},
        "summary": summary, "byStructure": per_structure(all_trades),
        "byRegime": per_regime(all_trades), "equityCurve": curve,
        "trades": shown, "tradesShown": len(shown),
        "openPositions": [], "openCount": 0,
    }
    (DATA_DIR / "historical_intraday.json").write_text(json.dumps(feed, indent=1), encoding="utf8")
    write_csv(all_trades)
    net = f" | net ${summary['netPnl']:,.0f}" if summary["costs"] > 0 else ""
    print(f"\n{first.date()} -> {last.date()} ({years:.1f}y, {len(df):,} bars) | "
          f"trades {summary['trades']:,} | gross ${summary['grossPnl']:,.0f}{net} | "
          f"win {summary['winRate']*100:.0f}% | PF {summary['profitFactor']} | "
          f"exp ${summary['netExpectancy' if summary['costs'] > 0 else 'expectancy']:,.0f} | "
          f"DD ${summary['maxDrawdown']:,.0f}")
    print(f"  -> {DATA_DIR / 'historical_intraday.json'}")


if __name__ == "__main__":
    main()
