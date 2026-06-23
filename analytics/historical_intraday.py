"""
historical_intraday.py — INTRADAY historical backtest over 5 years of 1-minute
WTI/Brent data (Data/CL_data.csv, Data/LCO_data.csv), NOW with shock absorption,
risk-led metrics, and a regime-blind control.

Fair value here is estimated from each spread's OWN recent history (a rolling mean →
z-score) — the rolling-mean method — NOT the Phase-2 fundamental model, which cannot
price intraday (its fundamental inputs are daily/absent). The difference from the live
Phase 3 is the sample: 5 YEARS of 15-minute bars, so the intraday edge is measured on a
statistically real history. WTI & Brent crude structures only.

The SIGNAL is unchanged (rolling-mean fair value, the same fixed thresholds, the same
volatility-adaptive cost gate). What is new — shared with the daily book via
analytics/shock.py:
  • SHOCK ABSORPTION (aware arm): de-lever / stand aside / flatten through a measured
    shock (vol jump, vol-state step-up, z-breach, or an intraday vol spike).
  • RISK-LED METRICS on mark-to-market daily returns (Sharpe/Sortino/Calmar/DD/CVaR).
  • A regime-BLIND control (shock off = the old behaviour) for the head-to-head.

Correctness:
  • The 1-min curve is resampled to 15-minute bars (last mid in each bin) and cached.
  • The cN columns ROLL ~monthly; a roll makes a continuous spread jump, so we segment
    the series at every roll AND every session/weekend gap; the rolling fair value never
    spans a break and no trade is held across one (purely intraday, within-session).
  • Each bar's day is mapped to its daily regime + vol-state (from regimes.json).

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
from dataclasses import replace

import numpy as np
import pandas as pd

from common import OUT_DIR, DATA_DIR, ROOT
import shock

CL_CSV = ROOT / "Data" / "CL_data.csv"
LCO_CSV = ROOT / "Data" / "LCO_data.csv"
CACHE = OUT_DIR / "intraday_15min.parquet"
BAR = "15min"

# ---- Strategy parameters (intraday) — UNCHANGED ----------------------------
LOOKBACK = 24          # bars in the rolling fair value (~6h of 15-min bars)
Z_ENTRY = 2.0          # fade when |z| >= this (2-sigma dislocation)
Z_EXIT = -1.5          # ride the reversion THROUGH fair to ~1.5sigma overshoot
Z_STOP = 3.5           # stop if it stretches further to |z| >= this
MAX_HOLD_BARS = 48     # time stop (~12h) within a session
SESSION_GAP_MIN = 90   # gap to next bar > this = session/weekend break -> segment + flatten
MULT = 1000
INITIAL_CAPITAL = 250_000
SLIP_PER_LEG = 0.0
# ---- Cost discipline (the net-P&L improvement) — UNCHANGED ------------------
ASSUMED_SLIP = 0.01    # per-leg cost the entry gate must clear (independent of --slip reporting)
EDGE_COST_MULT = 2.0   # require expected capture >= this x round-turn cost

# The shock policy for the intraday horizon (z_stop kept in lock-step with Z_STOP).
INTRADAY_SHOCK = replace(shock.INTRADAY_SHOCK, z_stop=Z_STOP)

# WTI & Brent only. legs = (product, cN, weight); hitkey = Phase-2 context edge.
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

STRATEGY_NAME = "Intraday RV mean-reversion + cost gate + shock absorption (WTI & Brent, 15-min, 5y)"
STRATEGY_DESC = ("Rolling-mean fair value on 15-min bars; fade a >=2sigma dislocation ONLY when the "
                 "expected $ move to fair clears 2x realistic cost (volatility-adaptive cost gate); ride "
                 "the reversion THROUGH fair to ~1.5sigma overshoot (z<=-1.5), with a 3.5sigma stop, a 12h "
                 "time stop, or a session/roll break. 1 unit/trade. SHOCK ABSORPTION (aware arm): de-lever, "
                 "stand aside, and flatten through a measured shock (vol jump / vol-state step-up / z-breach / "
                 "intraday vol spike). A regime-BLIND control (shock off) runs alongside; read risk-first.")


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
# Context (Phase-2 labels: regime + vol-state by day)
# ============================================================================
def regime_maps():
    try:
        data = json.loads((DATA_DIR / "regimes.json").read_text(encoding="utf8"))
    except Exception:
        return {}, {}, None
    hist = data.get("history", [])
    reg = {h["date"]: h.get("regimeLabel") for h in hist}
    vol = {h["date"]: h.get("volatility") for h in hist}
    cur_vol = (data.get("current", {}).get("states", {}).get("volatility", {}) or {}).get("state")
    return reg, vol, cur_vol


def edge_for(hitkey, edges):
    bt = edges.get(hitkey)
    return round(float(bt["hitRate"]), 3) if bt and bt.get("sufficient") else None


# ============================================================================
# Build one structure's spread + roll/session segmentation + rolling FV
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


def build_frame(df, legs, reg_map, vol_map, cur_vol):
    sub = spread_frame(df, legs)
    if len(sub) < LOOKBACK + 3:
        return None
    g = sub.groupby("seg", sort=False)["spread"]
    mean = g.transform(lambda s: s.rolling(LOOKBACK).mean())     # rolling-mean fair value (per segment)
    std = g.transform(lambda s: s.rolling(LOOKBACK).std())
    z = (sub["spread"] - mean) / std
    z = z.where(std > 0)                                          # undefined where dispersion is 0
    bar_vol = sub.groupby("seg", sort=False)["spread"].transform(lambda s: s.diff().abs())
    days = sub.index.strftime("%Y-%m-%d")
    vol_state = pd.Series([vol_map.get(d) or cur_vol or "Normal" for d in days], index=sub.index)
    regime = pd.Series([reg_map.get(d) for d in days], index=sub.index)
    return pd.DataFrame({
        "spread": sub["spread"], "fv": mean, "z": z,
        "vol_state": vol_state, "regime": regime, "bar_vol": bar_vol, "seg": sub["seg"],
    })


def run_arm(frames, mode, edges):
    trades, opens, pnls, in_markets = [], [], [], []
    for key, label, legs, hitkey, on in STRUCTURES:
        if not on or key not in frames:
            continue
        n_legs = sum(abs(w) for _, _, w in legs)
        gate_cost = EDGE_COST_MULT * 2 * n_legs * ASSUMED_SLIP * MULT
        res = shock.simulate(
            frames[key], mode=mode, z_entry=Z_ENTRY, z_exit=Z_EXIT, z_stop=Z_STOP,
            max_hold=MAX_HOLD_BARS, shock=INTRADAY_SHOCK, legs_count=n_legs, structure=key,
            label=label, hit_rate=edge_for(hitkey, edges), horizon="intraday", mult=MULT,
            slip_per_leg=SLIP_PER_LEG, gate_cost=gate_cost, warmup=0,
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
                              ref_slip=0.01, horizon="intraday")
    return summary, daily


def write_csv(all_trades):
    cols = ["structure", "label", "regime", "volState", "direction", "entryDate", "exitDate",
            "holdLabel", "entrySpread", "exitSpread", "fairValue", "entryZ", "exitZ", "size",
            "entrySeverity", "pnl", "cost", "netPnl", "mae", "mfe", "exitReason", "histHitRate",
            "equityAfter"]
    with open(OUT_DIR / "historical_intraday_trades.csv", "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); eq = INITIAL_CAPITAL
        for t in sorted(all_trades, key=lambda x: x["exitDate"]):
            eq += t["pnl"]; row = dict(t); row["equityAfter"] = round(eq, 2)
            w.writerow(row)


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
    reg_map, vol_map, cur_vol = regime_maps()

    first, last = df.index.min(), df.index.max()
    years = max((last - first).days / 365.25, 1e-9)

    frames = {}
    for key, label, legs, hitkey, on in STRUCTURES:
        if not on:
            continue
        fr = build_frame(df, legs, reg_map, vol_map, cur_vol)
        if fr is not None:
            frames[key] = fr

    aware_trades, opens, a_pnls, a_inmkt = run_arm(frames, "aware", edges)
    blind_trades, _, b_pnls, b_inmkt = run_arm(frames, "blind", edges)

    aware_summary, aware_daily = arm_block(aware_trades, a_pnls, a_inmkt, years)
    blind_summary, _ = arm_block(blind_trades, b_pnls, b_inmkt, years)

    for key, label, legs, hitkey, on in STRUCTURES:
        if not on:
            continue
        ts = [t for t in aware_trades if t["structure"] == key]
        if ts:
            print(f"  {key:11} trades={len(ts):5} pnl=${sum(t['pnl'] for t in ts):>9,.0f} "
                  f"win={sum(1 for t in ts if t['pnl']>0)/len(ts):.0%} PF={shock.pf(ts)}")

    structures = [(k, l) for k, l, _, _, on in STRUCTURES if on]
    DISPLAY = 600
    shown = sorted(aware_trades, key=lambda t: t["entryDate"], reverse=True)[:DISPLAY]
    feed = {
        "generatedAt": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "intraday", "horizon": "15-min bars",
        "span": {"first": first.strftime("%Y-%m-%d"), "last": last.strftime("%Y-%m-%d")},
        "years": round(years, 1), "bars": int(len(df)),
        "strategy": {"name": STRATEGY_NAME, "desc": STRATEGY_DESC,
                     "params": {"lookback": LOOKBACK, "zEntry": Z_ENTRY, "zExit": Z_EXIT,
                                "zStop": Z_STOP, "maxHoldBars": MAX_HOLD_BARS, "mult": MULT,
                                "slipPerLeg": SLIP_PER_LEG, "assumedSlip": ASSUMED_SLIP,
                                "edgeCostMult": EDGE_COST_MULT, "activeStructures": sorted(ACTIVE),
                                "shockAbsorption": True}},
        "summary": aware_summary,
        "blind": {"summary": blind_summary},
        "comparison": shock.head_to_head(aware_summary, blind_summary),
        "shock": shock.shock_summary(aware_trades),
        "byStructure": shock.per_structure(aware_trades, structures),
        "byRegime": shock.per_regime(aware_trades),
        "byVolState": shock.per_volstate(aware_trades),
        "equityCurve": shock.equity_from_daily(aware_daily, INITIAL_CAPITAL),
        "trades": shown, "tradesShown": len(shown),
        "openPositions": opens, "openCount": len(opens),
    }
    (DATA_DIR / "historical_intraday.json").write_text(json.dumps(feed, indent=1), encoding="utf8")
    write_csv(aware_trades)
    s = aware_summary
    net = f" | net ${s['netPnl']:,.0f}" if s["costs"] > 0 else ""
    print(f"\n{first.date()} -> {last.date()} ({years:.1f}y, {len(df):,} bars) | AWARE: "
          f"trades {s['trades']:,} | gross ${s['grossPnl']:,.0f}{net} | win {s['winRate']*100:.0f}% | "
          f"PF {s['profitFactor']} | Sharpe {s['sharpe']} | Calmar {s['calmar']} | "
          f"maxDD {s['maxDrawdownPct']*100:.0f}% (${s['maxDrawdown']:,.0f}) | CVaR ${s['cvar5']:,.0f}")
    b = blind_summary
    print(f"{'':>40}  BLIND: trades {b['trades']:,} | gross ${b['grossPnl']:,.0f} | "
          f"Sharpe {b['sharpe']} | Calmar {b['calmar']} | maxDD {b['maxDrawdownPct']*100:.0f}% "
          f"(${b['maxDrawdown']:,.0f}) | CVaR ${b['cvar5']:,.0f}")
    print(f"  -> {DATA_DIR / 'historical_intraday.json'}")


if __name__ == "__main__":
    main()
