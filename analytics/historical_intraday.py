"""
historical_intraday.py — INTRADAY 5-year backtest, fully REGIME-DRIVEN, over 1-minute
WTI/Brent data resampled to 15-minute bars (Data/CL_data.csv, Data/LCO_data.csv).

Intraday the Phase-2 fundamentals regression cannot price the spread (its inputs are
daily/absent). The redesign replaces the old fixed rolling-mean fair value with a
REGIME-PARAMETERIZED ADAPTIVE LOCAL-LEVEL (EWMA) FILTER:

  • Fair value  = a one-sided EWMA whose half-life is the regime's MEASURED, TRAILING
                  reversion half-life (estimated per vol-state on a trailing window, refit
                  periodically — never full-sample). Faster reversion ⇒ a more responsive
                  fair value; slower ⇒ a smoother one. (See regime_strategy.adaptive_ewma.)
  • Signal      = a REGIME-CONDITIONED z: residual ÷ the EXPANDING std of residuals in the
                  SAME vol-state, with a regime volatility floor (no cent-sized churn).
  • Policy      = per vol-state zEntry/zExit/zStop and a max-hold = (× the regime half-life).
  • Sizing      = vol-target (constant $-risk; high-vol bars auto-sized down).
  • Shock layer = de-lever / stand-aside / confirmation-delay through vol-regime step-ups,
                  on top of the always-on session/roll flatten.

The daily vol-state and regime label per bar come from the Phase-2 regimes.json (built on
same-day / backward-looking inputs only). A REGIME-BLIND control (fixed-span EWMA fair
value, global dispersion, fixed z=2 / 1 unit, no shock layer) runs head-to-head on the same
universe so the comparison isolates the regime model's contribution. We lead with RISK.

Reads  Data/CL_data.csv + Data/LCO_data.csv (+ caches out/intraday_15min.parquet),
       server/data/regimes.json + backtest.json
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
import regime_strategy as rs

CL_CSV = ROOT / "Data" / "CL_data.csv"
LCO_CSV = ROOT / "Data" / "LCO_data.csv"
CACHE = OUT_DIR / "intraday_15min.parquet"
BAR = "15min"

INITIAL_CAPITAL = 250_000
MULT = 1000
REF_SLIP = 0.01            # reference per-leg cost for the always-shown after-cost number
MIN_EDGE = 0.15           # 1st gate: a validated daily Phase-2 reversion edge
TRAIN_FRAC = 0.60         # 2nd gate (OOS): trade only structures whose AWARE book is profitable on
                          # the first 60% of the history — drops structures with a daily edge but no
                          # intraday edge (e.g. the Brent calendars). Validated out-of-sample.
SLOW_HL = 96              # bars (~1 session) — the slow reference the half-life is measured against
# The fair value is the local EQUILIBRIUM the spread reverts TO. Its EWMA half-life is a
# modest multiple of the measured reversion half-life, kept in a tight band: too SLOW and the
# anchor lags into session trends (it would fade trends that keep running); too FAST and it
# chases the spread and erases the dislocation. Regime-adaptive within the band — faster-
# reverting regimes get a more responsive anchor, slower ones a smoother one.
FV_SPAN_MULT = 2.5
FV_MIN_HL, FV_MAX_HL = 16.0, 28.0   # never TIGHTER than the blind anchor; adapt slower in calm
SESSION_GAP_MIN = 90
DISPLAY = 600             # cap the trade list shipped to the dashboard (full stats use all)
BAR_VOL_WIN = 8          # short realized-vol window for the shock detector (bars)

# WTI & Brent crude only (the feed contains crude). legs = (product, cN, weight); the
# whitelist is data-driven (Phase-2 reversion edge ≥ MIN_EDGE — see backtest.json).
STRUCTURES = [
    ("WTI_M1M2",   "WTI M1-M2",          [("wti", "c1", 1), ("wti", "c2", -1)], "wti_m1m2"),
    ("WTI_M2M3",   "WTI M2-M3",          [("wti", "c2", 1), ("wti", "c3", -1)], "wti_m1m2"),
    ("WTI_FLY",    "WTI M1-M2-M3 fly",   [("wti", "c1", 1), ("wti", "c2", -2), ("wti", "c3", 1)], "wti_fly"),
    ("BRENT_M1M2", "Brent M1-M2",        [("brent", "c1", 1), ("brent", "c2", -1)], "brent_m1m2"),
    ("BRENT_M2M3", "Brent M2-M3",        [("brent", "c2", 1), ("brent", "c3", -1)], "brent_m1m2"),
    ("BRENT_FLY",  "Brent M1-M2-M3 fly", [("brent", "c1", 1), ("brent", "c2", -2), ("brent", "c3", 1)], "wti_fly"),
    ("BRENT_WTI",  "Brent-WTI arb",      [("brent", "c1", 1), ("wti", "c1", -1)], "brent_wti"),
]

STRATEGY_NAME = "Regime-driven intraday RV mean-reversion (15-min, 5y)"
STRATEGY_DESC = (
    "Fair value = a REGIME-PARAMETERIZED adaptive EWMA whose half-life is the regime's measured, "
    "trailing reversion speed (not a fixed window). The regime model drives a regime-conditioned z "
    "(residual vs same-vol-state expanding std + vol floor), per-vol-state z-thresholds and max-hold "
    "(× the regime half-life), vol-target sizing, a cost gate, and a shock layer (de-lever / "
    "stand-aside through vol-regime step-ups, plus the session/roll flatten). A regime-blind control "
    "(fixed-span EWMA, global dispersion, fixed z=2 / 1 unit, no shock layer) runs head-to-head."
)


# ============================================================================
# Data: 1-min CSV → cached 15-min curve (mids + contract codes per leg)
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
    df = wti.join(brent, how="outer").sort_index().dropna(how="all")
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
# Phase-2 context: daily vol-state + regime label per calendar date
# ============================================================================
def regime_by_date():
    try:
        hist = json.loads((DATA_DIR / "regimes.json").read_text(encoding="utf8")).get("history", [])
        return {h["date"]: {"vol": h.get("volatility"), "rid": h.get("regimeId"),
                            "label": h.get("regimeLabel")} for h in hist}
    except Exception:
        return {}


def edges_map():
    try:
        return json.loads((DATA_DIR / "backtest.json").read_text(encoding="utf8")).get("spreads", {})
    except Exception:
        return {}


def edge_for(hitkey, edges):
    bt = edges.get(hitkey)
    return (round(float(bt["hitRate"]), 3), float(bt.get("edge") or 0.0)) if bt and bt.get("sufficient") else (None, 0.0)


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


def prep_frames(df, legs, reg_map, cfg):
    """Build the aware (adaptive-EWMA FV) and blind (fixed-EWMA FV) frames + the trailing
    half-life array. Everything here is causal."""
    base = spread_frame(df, legs)
    if base.empty or len(base) < cfg.warmup + 20:
        return None
    spread = base["spread"]
    seg = base["seg"].to_numpy()
    dates = base.index.strftime("%Y-%m-%d")
    vol_state = np.array([reg_map.get(d, {}).get("vol") for d in dates], dtype=object)
    regime_id = np.array([reg_map.get(d, {}).get("rid") for d in dates], dtype=object)
    regime_lab = np.array([reg_map.get(d, {}).get("label") for d in dates], dtype=object)

    # measure the trailing per-vol-state reversion half-life off the deviation from a SLOW ref
    slow = rs.fixed_ewma(spread, SLOW_HL, seg)
    dev = (spread - slow).to_numpy(float)
    hl = rs.trailing_halflife(dev, vol_state, seg, cfg)        # reversion HL (drives maxHold)

    # adaptive fair value (aware): EWMA whose span is FV_SPAN_MULT × the reversion half-life
    # (the slow equilibrium) vs the blind fixed-span fair value
    fv_span = np.clip(FV_SPAN_MULT * hl, FV_MIN_HL, FV_MAX_HL)
    fv_aware = rs.adaptive_ewma(spread.to_numpy(float), fv_span, seg)
    fv_blind = rs.fixed_ewma(spread, rs.INTRADAY_BLIND_HL, seg).to_numpy(float)

    # short causal realized vol of the spread → the shock detector's per-bar vol proxy
    bar_vol = (base.groupby("seg")["spread"]
               .transform(lambda s: s.diff().abs().rolling(BAR_VOL_WIN, min_periods=2).mean())
               .to_numpy(float))

    common = {"vol_state": vol_state, "regime_id": regime_id, "regime": regime_lab,
              "bar_vol": bar_vol, "seg": seg}
    fa = pd.DataFrame({"spread": spread.to_numpy(float), "fv": fv_aware, **common}, index=base.index)
    fb = pd.DataFrame({"spread": spread.to_numpy(float), "fv": fv_blind, **common}, index=base.index)
    return fa, fb, hl


def comparison(aware_sum, blind_sum) -> dict:
    def pair(key):
        return {"aware": aware_sum.get(key), "blind": blind_sum.get(key)}
    return {k: pair(k) for k in
            ["sharpe", "calmar", "maxDrawdown", "maxDrawdownPct", "cvar5", "volAnn",
             "netPnl", "grossPnl", "profitFactor", "trades", "pctTimeInMarket", "cagr"]}


def sizing_series(size_map, sev_map):
    if not size_map:
        return []
    sizes = pd.concat(size_map.values(), axis=1, sort=True).mean(axis=1)
    sevs = pd.concat(sev_map.values(), axis=1, sort=True).mean(axis=1)
    bd_size = sizes.groupby(sizes.index.normalize()).mean()
    bd_sev = sevs.groupby(sevs.index.normalize()).mean()
    return [{"t": ts.strftime("%Y-%m-%d"), "size": round(float(bd_size[ts]), 3),
             "severity": round(float(bd_sev.get(ts, 0.0)), 3)} for ts in bd_size.index]


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--slip", type=float, default=0.0)
    ap.add_argument("--rebuild", action="store_true", help="force-rebuild the 15-min cache")
    args = ap.parse_args()

    cfg = rs.INTRADAY_CONFIG
    cfg.slip_per_leg = args.slip
    cfg.mult = MULT

    df = load_curve(rebuild=args.rebuild)
    reg_map = regime_by_date()
    edges = edges_map()

    first, last = df.index.min(), df.index.max()
    years = max((last - first).days / 365.25, 1e-9)

    aware_trades, blind_trades = [], []
    aware_pnls, blind_pnls = [], []
    aware_inmkt, blind_inmkt = [], []
    size_map, sev_map = {}, {}
    traded, skipped, deployable = [], [], []

    for key, label, legs, hitkey in STRUCTURES:
        hit, edge = edge_for(hitkey, edges)
        if hit is None or edge < MIN_EDGE:
            skipped.append((key, label, edge, "no validated reversion edge"))
            continue
        prepped = prep_frames(df, legs, reg_map, cfg)
        if prepped is None:
            skipped.append((key, label, edge, "insufficient bars"))
            continue
        fa, fb, hl = prepped
        legs_count = sum(abs(w) for _, _, w in legs)

        # Two OOS gates on the TRAIN window (brief's gross/net philosophy):
        #   • GROSS edge > 0  → the SIGNAL works → evaluated in the 5-year backtest.
        #   • AFTER-COST edge > 0 → cheap enough to actually trade → DEPLOYABLE (the live book
        #     trades only these). The calendar/fly structures are gross-positive but net-negative
        #     (high-frequency churn that stops out too often to clear costs).
        ntr = int(len(fa) * TRAIN_FRAC)
        at = rs.simulate_structure(fa.iloc[:ntr], cfg, mode="aware", legs_count=legs_count,
                                   structure=key, label=label, hit_rate=hit, halflife=hl[:ntr])
        train_gross = sum(t["pnl"] for t in at["trades"])
        if train_gross <= 0:
            skipped.append((key, label, edge, f"no intraday signal on train (${train_gross:,.0f})"))
            continue
        ref_cost = 2 * legs_count * REF_SLIP * MULT
        train_net = sum(t["pnl"] - ref_cost * t.get("size", 1.0) for t in at["trades"])
        if train_net > 0:
            deployable.append(key)
        traded.append((key, label))

        a = rs.simulate_structure(fa, cfg, mode="aware", legs_count=legs_count,
                                  structure=key, label=label, hit_rate=hit, halflife=hl)
        b = rs.simulate_structure(fb, cfg, mode="blind", legs_count=legs_count,
                                  structure=key, label=label, hit_rate=hit, halflife=hl)
        aware_trades += a["trades"]; blind_trades += b["trades"]
        aware_pnls.append(a["pnl"]); blind_pnls.append(b["pnl"])
        aware_inmkt.append(a["in_market"]); blind_inmkt.append(b["in_market"])
        size_map[key] = a["size"]; sev_map[key] = a["severity"]
        print(f"  {key:11} edge={edge:+.0%} aware n={len(a['trades']):5} "
              f"pnl=${sum(t['pnl'] for t in a['trades']):>10,.0f} | blind n={len(b['trades']):5} "
              f"pnl=${sum(t['pnl'] for t in b['trades']):>10,.0f}")

    for key, label, edge, why in skipped:
        print(f"  {key:11} edge={edge:+.0%}  SKIP ({why})")

    aware_daily = rs.portfolio_daily_pnl(aware_pnls)
    blind_daily = rs.portfolio_daily_pnl(blind_pnls)
    aware_sum = rs.summarize(aware_trades, aware_daily, INITIAL_CAPITAL, years, MULT, REF_SLIP, "intraday")
    blind_sum = rs.summarize(blind_trades, blind_daily, INITIAL_CAPITAL, years, MULT, REF_SLIP, "intraday")
    aware_sum["pctTimeInMarket"] = rs.pct_time_in_market(aware_inmkt)
    blind_sum["pctTimeInMarket"] = rs.pct_time_in_market(blind_inmkt)

    curve = rs.equity_from_daily(aware_daily, INITIAL_CAPITAL)
    curve_blind = rs.equity_from_daily(blind_daily, INITIAL_CAPITAL)
    shown = sorted(aware_trades, key=lambda t: t["entryDate"], reverse=True)[:DISPLAY]

    feed = {
        "generatedAt": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "intraday", "horizon": "15-min bars",
        "span": {"first": first.strftime("%Y-%m-%d"), "last": last.strftime("%Y-%m-%d")},
        "years": round(years, 1), "bars": int(len(df)),
        "strategy": {"name": STRATEGY_NAME, "desc": STRATEGY_DESC,
                     "params": {"slowHL": SLOW_HL, "blindHL": rs.INTRADAY_BLIND_HL, "mult": MULT,
                                "slipPerLeg": args.slip, "minEdge": MIN_EDGE, "trainFrac": TRAIN_FRAC,
                                "bookScale": cfg.size.book_scale,
                                "assumedSlip": cfg.assumed_slip, "edgeCostMult": cfg.edge_cost_mult,
                                "volStateParams": {s: vars(p) for s, p in cfg.params.items()},
                                "sizing": "vol-target (constant $-risk, ×typical/state dispersion)",
                                "tradedStructures": [t for t, _ in traded],
                                "deployableStructures": deployable}},
        "summary": aware_sum,
        "blind": {"summary": blind_sum, "equityCurve": curve_blind},
        "comparison": comparison(aware_sum, blind_sum),
        "byStructure": rs.per_structure(aware_trades, traded),
        "byRegime": rs.per_regime(aware_trades),
        "byVolState": rs.per_volstate(aware_trades),
        "equityCurve": curve, "equityCurveBlind": curve_blind,
        "sizingSeries": sizing_series(size_map, sev_map),
        "trades": shown, "tradesShown": len(shown),
        "openPositions": [], "openCount": 0,
    }
    (DATA_DIR / "historical_intraday.json").write_text(json.dumps(feed, indent=1), encoding="utf8")
    write_csv(aware_trades)

    print(f"\n{first.date()} -> {last.date()} ({years:.1f}y, {len(df):,} bars) | traded {len(traded)}")
    print(f"  AWARE  trades {aware_sum['trades']:5} | net ${aware_sum['netPnl']:>11,.0f} | "
          f"Sharpe {aware_sum['sharpe']:.2f} | Calmar {aware_sum['calmar']} | "
          f"maxDD ${aware_sum['maxDrawdown']:,.0f} ({aware_sum['maxDrawdownPct']*100:.1f}%) | "
          f"CVaR ${aware_sum['cvar5']:,.0f} | TIM {aware_sum['pctTimeInMarket']*100:.0f}%")
    print(f"  BLIND  trades {blind_sum['trades']:5} | net ${blind_sum['netPnl']:>11,.0f} | "
          f"Sharpe {blind_sum['sharpe']:.2f} | Calmar {blind_sum['calmar']} | "
          f"maxDD ${blind_sum['maxDrawdown']:,.0f} ({blind_sum['maxDrawdownPct']*100:.1f}%) | "
          f"CVaR ${blind_sum['cvar5']:,.0f}")
    print(f"  -> {DATA_DIR / 'historical_intraday.json'}")


if __name__ == "__main__":
    main()
