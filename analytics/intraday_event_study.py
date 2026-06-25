"""
intraday_event_study.py — HOW THE INVENTORY REACTION BUILDS MINUTE-BY-MINUTE.

The daily framework (inventory_lib) answers "how much does WTI move on the print?".
This answers the finer question: "how does that move unfold over the first two hours,
and at which horizon does the inventory surprise actually explain price?"

It reads the raw 1-minute WTI front-month tape (Data/CL_data.csv, 2021->2026, ~250
EIA releases), aligns every release to its 10:30 a.m. ET drop, and measures the
cumulative WTI return at +5 / +15 / +30 / +60 / +120 minutes. For each horizon it
regresses that reaction on the SURPRISE (actual - model-expected, from inventory_lib)
to get:
  * beta_h   — % WTI move per +1 MMbbl of surprise at horizon h,
  * r2_h     — how much of the move the surprise explains at h,
  * hit_h    — directional accuracy among material surprises at h,
  * rmse_h   — the residual std (the move NOT explained → the prediction band).
Computed overall and conditioned on the volatility regime.

This is the SLOW, OFFLINE step (it streams a ~550 MB CSV). It runs ONCE and writes a
tiny artifact, server/data/intraday_impact.json, which the live Release Lab button
(release_lab.py) reads to predict the per-horizon reaction without ever touching the
raw tape. The CSV stays git-ignored and out of the Docker image; only the JSON ships.

USAGE
  python analytics/intraday_event_study.py
  python analytics/intraday_event_study.py --csv Data/CL_data.csv --horizons 5,15,30,60,120
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import pandas as pd

from common import ROOT, DATA_DIR
import inventory_lib as lib

ET = ZoneInfo("America/New_York")
CSV_DEFAULT = ROOT / "Data" / "CL_data.csv"
OUT = DATA_DIR / "intraday_impact.json"
PRICE_COL = 2          # timestamp, c1||contract, c1||weighted_mid  -> index 2 is front-month price
MATCH_TOL_MIN = 4      # accept a bar within ±N minutes of the exact horizon


# ---------------------------------------------------------------------------
def release_windows(f: pd.DataFrame) -> dict:
    """Map each EIA release to its 10:30 a.m. ET datetime in UTC, plus the surprise
    and regime we condition on. Keyed by the UTC date (each release window — ref to
    +120 min — sits within one UTC date), so a single CSV pass can bucket bars."""
    out = {}
    sub = f.dropna(subset=["surprise"])
    for _, row in sub.iterrows():
        rel_date = lib.release_date(row["period"]).date()           # Wed (nominal)
        rel_et = datetime(rel_date.year, rel_date.month, rel_date.day, 10, 30, tzinfo=ET)
        rel_utc = rel_et.astimezone(timezone.utc)
        out[rel_utc.strftime("%Y-%m-%d")] = {
            "period": row["period"].strftime("%Y-%m-%d"),
            "release_utc": rel_utc,
            "surprise": float(row["surprise"]),
            "surprise_z": float(row["surprise_z"]) if row.get("surprise_z") == row.get("surprise_z") else 0.0,
            "vol_regime": row.get("vol_regime"),
        }
    return out


def collect_bars(csv: Path, want_dates: set) -> dict:
    """One streaming pass over the 1-min tape: keep only bars on release dates within
    14:00–18:00 UTC (covers the 10:30 ET window in both EST and EDT). Returns
    date_str -> list[(utc_datetime, price)] sorted by time."""
    bars: dict = {d: [] for d in want_dates}
    kept = 0
    with open(csv, "r") as fh:
        fh.readline()                # '#meta:1min...'
        fh.readline()                # header
        for line in fh:
            if len(line) < 20:
                continue
            d = line[:10]
            if d not in bars:
                continue
            hh = line[11:13]
            if hh < "14" or hh > "17":   # 14:00–17:59 UTC
                continue
            parts = line.split(",", PRICE_COL + 1)
            try:
                px = float(parts[PRICE_COL])
            except (ValueError, IndexError):
                continue
            ts = datetime(int(d[:4]), int(d[5:7]), int(d[8:10]),
                          int(line[11:13]), int(line[14:16]), tzinfo=timezone.utc)
            bars[d].append((ts, px))
            kept += 1
    for d in bars:
        bars[d].sort(key=lambda x: x[0])
    print(f"[intraday] kept {kept} bars across {sum(1 for v in bars.values() if v)} release days")
    return bars


def reaction_at(series, ref_dt, ref_px, minutes):
    """Cumulative return from the pre-release reference to the bar nearest ref+minutes
    (within MATCH_TOL_MIN). Returns None if no bar lands in the tolerance window."""
    target = ref_dt + timedelta(minutes=minutes)
    best, best_gap = None, timedelta(minutes=MATCH_TOL_MIN + 1)
    for ts, px in series:
        if ts < ref_dt:
            continue
        gap = abs(ts - target)
        if gap < best_gap:
            best, best_gap = px, gap
        if ts > target + timedelta(minutes=MATCH_TOL_MIN):
            break
    if best is None or ref_px in (0, None):
        return None
    return best / ref_px - 1.0


def build_reactions(windows, bars, horizons) -> pd.DataFrame:
    rows = []
    for d, info in windows.items():
        series = bars.get(d) or []
        if not series:
            continue
        rel = info["release_utc"]
        # reference = last bar at/just before the release (the pre-print price)
        ref = [(ts, px) for ts, px in series if ts <= rel]
        if not ref:
            continue
        ref_dt, ref_px = ref[-1]
        rec = {"period": info["period"], "surprise": info["surprise"],
               "surprise_z": info["surprise_z"], "vol_regime": info["vol_regime"]}
        any_h = False
        for h in horizons:
            r = reaction_at(series, ref_dt, ref_px, h)
            rec[f"r_{h}"] = r
            any_h = any_h or r is not None
        if any_h:
            rows.append(rec)
    return pd.DataFrame(rows)


def regress(x: pd.Series, y: pd.Series):
    m = pd.concat([x, y], axis=1).dropna()
    if len(m) < 10 or m.iloc[:, 0].std() == 0:
        return None
    xv, yv = m.iloc[:, 0].values, m.iloc[:, 1].values
    b, a = np.polyfit(xv, yv, 1)
    yhat = a + b * xv
    ss_res = float(np.sum((yv - yhat) ** 2))
    ss_tot = float(np.sum((yv - yv.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    rmse = float(np.sqrt(ss_res / max(len(m) - 2, 1)))
    sigma = float(np.std(xv))
    # directional hit-rate among material surprises (|z|>=0.5), draw beat -> up
    mm = m.copy()
    return {
        "n": int(len(m)),
        "beta_pct_per_mmbbl": round(b * 100, 4),
        "r2": round(float(r2), 4),
        "rmse_pct": round(rmse * 100, 3),
        "per_1sigma_pct": round(b * sigma * 100, 3),
    }


def hit_rate(df, hcol):
    m = df.dropna(subset=["surprise", "surprise_z", hcol])
    m = m[m["surprise_z"].abs() >= 0.5]
    if len(m) < 8:
        return None
    pred = -np.sign(m["surprise"])         # draw beat (neg surprise) -> up
    actual = np.sign(m[hcol])
    hit = (pred == actual) & (actual != 0)
    return round(float(hit.mean()), 3)


def horizon_stats(df, horizons):
    out = {}
    for h in horizons:
        col = f"r_{h}"
        fit = regress(df["surprise"], df[col])
        if not fit:
            continue
        fit["hit_rate"] = hit_rate(df, col)
        fit["avg_move_pct"] = round(float(df[col].dropna().mean()) * 100, 3)
        out[str(h)] = fit
    return out


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Intraday EIA reaction event study (1-min tape).")
    ap.add_argument("--csv", default=str(CSV_DEFAULT))
    ap.add_argument("--horizons", default="5,15,30,60,120")
    args = ap.parse_args()
    horizons = [int(x) for x in args.horizons.split(",")]
    csv = Path(args.csv)
    if not csv.exists():
        print(f"[intraday] {csv} not found — this offline step needs the raw 1-min tape "
              f"(git-ignored). Skipping; the live model JSON is left unchanged.")
        sys.exit(0)

    print("[intraday] loading weekly framework (surprises + regime) ...")
    weekly = lib.fetch_weekly(length=600, cache_hours=6.0)
    prices = lib.fetch_prices(cache_hours=6.0)
    panel = lib.load_panel()
    A = lib.analyze(weekly, prices, panel)
    f = A["frame"]

    windows = release_windows(f)
    print(f"[intraday] {len(windows)} candidate releases; streaming {csv.name} "
          f"({csv.stat().st_size/1e6:.0f} MB) ...")
    bars = collect_bars(csv, set(windows))
    df = build_reactions(windows, bars, horizons)
    print(f"[intraday] matched {len(df)} releases with intraday reactions")

    overall = horizon_stats(df, horizons)
    by_regime = {}
    for vol, sub in df.groupby("vol_regime"):
        if vol is None or (isinstance(vol, float) and pd.isna(vol)) or len(sub) < 12:
            continue
        st = horizon_stats(sub, horizons)
        if st:
            by_regime[str(vol)] = st

    # average reaction-path shape (mean cumulative move per horizon), for context
    path = {str(h): round(float(df[f"r_{h}"].dropna().mean()) * 100, 3)
            for h in horizons if f"r_{h}" in df}

    out = {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Data/CL_data.csv (1-min WTI front-month, weighted mid)",
        "horizons_min": horizons,
        "n_releases": int(len(df)),
        "sample_period": [df["period"].min(), df["period"].max()] if len(df) else [None, None],
        "match_tolerance_min": MATCH_TOL_MIN,
        "by_horizon": overall,
        "by_regime": by_regime,
        "avg_path_pct": path,
        "note": ("Per-horizon OLS of WTI cumulative return on the crude surprise. beta = %/MMbbl, "
                 "r2 = variance explained, rmse = unexplained move (prediction band), hit_rate = "
                 "directional accuracy among material surprises (|z|>=0.5)."),
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(f"[intraday] wrote {OUT}")
    print("\n  horizon |   beta%/MMbbl |   R2   | hit | n")
    for h in horizons:
        s = overall.get(str(h))
        if s:
            print(f"   {h:>4}m  | {s['beta_pct_per_mmbbl']:>12} | {s['r2']:>6} | "
                  f"{s.get('hit_rate')} | {s['n']}")


if __name__ == "__main__":
    main()
