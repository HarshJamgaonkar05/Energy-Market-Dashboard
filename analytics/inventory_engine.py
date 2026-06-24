"""
inventory_engine.py — the LIVE crude-inventory cross-check engine.

WHAT IT DOES, IN PLAIN ENGLISH
------------------------------
The EIA publishes the weekly crude number every Wednesday at 10:30 a.m. ET. This
engine sits on top of the framework (inventory_lib.py) and, the moment a NEW print
lands on the EIA API, it:

  1. Reads the fresh number and computes the SURPRISE = actual − our model-expected
     build/draw (our leak-free stand-in for the analyst consensus).
  2. Turns that surprise into a VERDICT (Bullish / Bearish / Neutral) using how
     strongly inventories drive WTI in the *current* market regime.
  3. CROSS-CHECKS the verdict against the market: it pulls the live WTI price and
     measures how oil actually moved on the print, then reports whether the market
     CONFIRMED or CONTRADICTED the framework's call.
  4. Writes the result to server/data/inventory_signal.json (the dashboard panel
     reads this) and appends it to server/data/inventory_signal_log.json.

MODES
  python inventory_engine.py                 one-shot: assess the latest print (or, if
                                             nothing new, refresh the pre-release base case)
  python inventory_engine.py --watch         poll the EIA API until a NEW print appears
                                             (around Wed 10:30 ET), assess it, then exit
  python inventory_engine.py --watch --interval 60 --timeout 120
  python inventory_engine.py --crosscheck    re-run only the market cross-check on the
                                             most recent assessed release (e.g. end of day)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# Windows consoles default to cp1252, which can't encode σ/² etc. Force UTF-8 so the
# plain-English summaries print cleanly everywhere.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import pandas as pd

from common import ROOT
import inventory_lib as lib

DATA_DIR = ROOT / "server" / "data"
SIGNAL = DATA_DIR / "inventory_signal.json"
LOG = DATA_DIR / "inventory_signal_log.json"
ET = ZoneInfo("America/New_York")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def now_et() -> str:
    return datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S %Z")


def _read_json(p: Path, default):
    try:
        return json.loads(p.read_text())
    except Exception:
        return default


def latest_seen_period() -> str | None:
    """The most recent EIA crude week we've already assessed (from the log)."""
    log = _read_json(LOG, [])
    return log[-1]["period"] if log else None


# ---------------------------------------------------------------------------
def assess(fresh: bool = True) -> dict:
    """Run the framework on the freshest data and build the signal snapshot. It always
    carries BOTH:
      * forward  — the pre-release base case for the NEXT (not-yet-published) week
                   (the actionable read going into the release), and
      * last_print — the most recently PUBLISHED week assessed as a surprise + verdict
                   + live market cross-check (the framework's track record).
    `stage` flags whether THIS run newly detected a fresh print (for logging/alerting)."""
    ch = 0.0 if fresh else 6.0
    weekly = lib.fetch_weekly(length=600, cache_hours=ch)
    prices = lib.fetch_prices(cache_hours=ch)
    panel = lib.load_panel()

    # Graceful degradation if the EIA API is down (returns nothing): write a no-data
    # snapshot instead of crashing the scheduled run.
    if weekly.empty or "crude" not in weekly.columns or weekly["crude"].dropna().empty:
        return {"generatedAt": now_iso(), "generatedAtET": now_et(), "stage": "no-data",
                "error": "EIA returned no crude data (API outage or rate-limit?).",
                "verdict": None, "forward": None, "last_print": None, "crosscheck": None,
                "current": {}, "top_spreads": [],
                "framework_note": "No EIA data available this run; previous signal left unchanged on disk."}

    A = lib.analyze(weekly, prices, panel)
    f, es = A["frame"], A["event_study"]

    last = f.dropna(subset=["crude_wow"]).iloc[-1]
    period = last["period"].strftime("%Y-%m-%d")
    rel_date = lib.release_date(last["period"]).strftime("%Y-%m-%d")
    cur_vol, cur_struct, cur_align = last.get("vol_regime"), last.get("wti_struct"), last.get("product_alignment")
    rel_r2, rel_n, rel_beta = lib.reliability_for(es, cur_vol)

    sens = A["spread_sensitivity"]
    top_products = [k for k in sens.keys() if k not in ("panel_wti", "panel_brent")][:5]
    context = {"vol_regime": cur_vol, "wti_struct": cur_struct,
               "product_alignment": cur_align, "products": top_products}

    seen = latest_seen_period()
    is_new = (seen is None) or (period > seen)

    current = {
        "asOf_period": period, "release_date": rel_date,
        "crude_stock": round(float(last["crude"]), 1),
        "crude_wow": round(float(last["crude_wow"]), 1),
        "crude_z": _r(last.get("crude_z")),
        "cushing": _r(last.get("cushing")), "cushing_wow": _r(last.get("cushing_wow")),
        "refutil": _r(last.get("refutil")), "days_supply": _r(last.get("days_supply")),
        "season": last["season"], "vol_regime": cur_vol, "wti_struct": cur_struct,
        "product_alignment": cur_align,
        "expected": _r(last.get("expected")), "surprise": _r(last.get("surprise")),
        "surprise_z": _r(last.get("surprise_z")),
        "reliability_r2": round(rel_r2, 3), "reliability_n": rel_n,
    }

    # --- POST-release read on the latest published week (surprise + cross-check) ---
    last_print = None
    if last.get("surprise") == last.get("surprise"):
        surprise = float(last["surprise"])
        sz = float(last["surprise_z"]) if last.get("surprise_z") == last.get("surprise_z") else 0.0
        v_post = lib.verdict_from_surprise(surprise, sz, context, rel_r2, rel_n, rel_beta)
        cross = market_crosscheck(prices, last, surprise, rel_beta, v_post.direction)
        last_print = {"period": period, "release_date": rel_date, "verdict": _vdict(v_post),
                      "surprise": _r(surprise), "surprise_z": _r(sz), "crosscheck": cross}

    # --- PRE-release base case for the NEXT (unpublished) week ---
    v_fwd = lib.forward_base_case(f, context, rel_r2, rel_n)
    forward = _vdict(v_fwd)
    next_release = lib.release_date(last["period"] + pd.Timedelta(days=7)).strftime("%Y-%m-%d")

    snap = {
        "generatedAt": now_iso(), "generatedAtET": now_et(),
        "stage": "post-release" if is_new and last_print else "pre-release",
        "asOf_period": period, "release_date": rel_date, "next_release_est": next_release,
        # the dashboard headline = the forward base case into the upcoming release
        "verdict": forward, "forward": forward, "last_print": last_print,
        "crosscheck": last_print["crosscheck"] if last_print else None,
        "current": current, "top_spreads": top_products,
        "framework_note": ("Surprise = actual − model-expected (walk-forward seasonal + balance + "
                           "momentum). Verdict damped by how strongly inventories drive WTI in this "
                           "regime. Cross-check compares the post-release call to the live WTI move."),
    }
    return snap


def market_crosscheck(prices: pd.DataFrame, row, surprise: float, beta: float,
                      verdict_dir: str = "Neutral") -> dict:
    """Did the market move the way the inventory SURPRISE implied? We measure the
    RELEASE-DAY move only (prior close -> the first bar on/after the release), not the
    move-to-now, so the logged number is the print's own reaction and doesn't drift as
    days pass. The surprise direction (a draw beat -> up) is graded against that move;
    the framework's regime-aware verdict (which may be Neutral) is reported alongside,
    so a low-conviction call isn't mislabelled."""
    wti = prices.get("wti")
    if wti is None or wti.dropna().empty:
        return {"status": "no-price", "note": "WTI price unavailable."}
    s = wti.dropna()
    rel_when = lib.release_date(row["period"])
    before = s[s.index < rel_when]
    after = s[s.index >= rel_when]
    if before.empty or after.empty:
        return {"status": "pending", "note": "Price for the release day not in yet."}
    prior_close = float(before.iloc[-1])
    release_close = float(after.iloc[0])          # the RELEASE-DAY close (or the forming
    reaction = release_close / prior_close - 1.0  # bar if we're still on release day)
    preliminary = len(after) <= 1                 # only the release-day bar exists yet

    pred_dir = "up" if surprise < 0 else "down"   # a draw beat (surprise<0) implies up
    act_dir = "up" if reaction > 0.0005 else "down" if reaction < -0.0005 else "flat"
    status = "flat" if act_dir == "flat" else "confirmed" if act_dir == pred_dir else "contradicted"
    expected_move = beta * surprise               # fitted slope * surprise (beta<0): agrees w/ pred_dir

    kind = "larger-than-expected draw" if surprise < 0 else "larger-than-expected build"
    note = (f"The inventory surprise ({surprise:+.1f} MMbbl, a {kind}) implied WTI should trade "
            f"{pred_dir.upper()}; WTI moved {reaction*100:+.2f}% on the print -> {status.upper()}.")
    if verdict_dir == "Neutral":
        note += " The framework's regime-aware verdict was NEUTRAL — it made no firm directional bet here."
    if preliminary:
        note += " (Preliminary: release-day bar still forming until the close.)"
    return {
        "status": status, "predicted_dir": pred_dir, "actual_dir": act_dir,
        "verdict_dir": verdict_dir, "preliminary": preliminary,
        "wti_reaction_pct": round(reaction * 100, 3),
        "wti_prior_close": round(prior_close, 2), "wti_release_close": round(release_close, 2),
        "expected_move_pct": round(expected_move * 100, 3),
        "note": note,
    }


def _r(x):
    try:
        return None if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))) else round(float(x), 2)
    except Exception:
        return None


def _vdict(v: lib.Verdict) -> dict:
    return {"direction": v.direction, "score": v.score, "confidence": v.confidence,
            "headline": v.headline, "factors": v.factors, "products": v.products}


def write_signal(snap: dict):
    if snap.get("stage") == "no-data":
        # Don't clobber the last good signal on an EIA outage.
        print(f"[engine] {snap.get('error','no data')} — leaving {SIGNAL.name} unchanged.")
        return
    SIGNAL.write_text(json.dumps(snap, indent=2))
    # Append to the log only when a *new* print was detected this run.
    lp = snap.get("last_print")
    if snap["stage"] == "post-release" and lp:
        log = _read_json(LOG, [])
        if not log or log[-1]["period"] != lp["period"]:
            log.append({
                "period": lp["period"], "release_date": lp["release_date"],
                "assessedAt": snap["generatedAt"], "direction": lp["verdict"]["direction"],
                "surprise": lp["surprise"], "surprise_z": lp["surprise_z"],
                "crosscheck": lp["crosscheck"]["status"] if lp["crosscheck"] else None,
                "wti_reaction_pct": lp["crosscheck"]["wti_reaction_pct"] if lp["crosscheck"] else None,
            })
            LOG.write_text(json.dumps(log, indent=2))


def print_summary(snap: dict):
    if snap.get("stage") == "no-data":
        print(f"\n[NO-DATA]  {snap.get('error','EIA returned no data')}")
        return
    c = snap["current"]
    print(f"\n[{snap['stage'].upper()}]  latest EIA week {snap['asOf_period']}  (released {snap['release_date']})")
    print(f"  Crude {c['crude_stock']} MMbbl  ({c['crude_wow']:+.1f} WoW, z={c['crude_z']})  "
          f"Cushing {c['cushing']} ({c['cushing_wow']:+.1f})  refutil {c['refutil']}%")
    print(f"  Regime: {c['vol_regime']} vol / {c['wti_struct']} / {c['season']} / align={c['product_alignment']}  "
          f"(reliability R²={c['reliability_r2']}, n={c['reliability_n']})")
    lp = snap.get("last_print")
    if lp:
        print(f"\n  -- LAST PRINT ({lp['period']}) --")
        print(f"     Expected {c['expected']:+.1f} | Actual {c['crude_wow']:+.1f} | "
              f"SURPRISE {lp['surprise']:+.1f} MMbbl ({lp['surprise_z']:+.1f}σ) -> {lp['verdict']['direction']}")
        if lp["crosscheck"]:
            print(f"     CROSS-CHECK: {lp['crosscheck']['note']}")
    fwd = snap["forward"]
    print(f"\n  -- FORWARD base case (into {snap['next_release_est']}) --")
    print(f"     >>> {fwd['direction']}  (confidence {fwd['confidence']})")
    print(f"     {fwd['headline']}")


# ---------------------------------------------------------------------------
def watch(interval: int, timeout_min: int):
    """Poll the EIA API until a NEW crude week appears, then assess it and exit. Use
    around Wed 10:25-11:00 a.m. ET; it returns as soon as the print lands."""
    baseline = latest_seen_period()
    # If nothing logged yet, use the current freshest period as the baseline so we
    # only fire on the NEXT print.
    if baseline is None:
        weekly = lib.fetch_weekly(length=8, cache_hours=0.0)
        baseline = weekly["crude"].dropna().index.max().strftime("%Y-%m-%d")
    print(f"[watch] baseline EIA week = {baseline}. Polling every {interval}s up to {timeout_min} min.")
    print(f"[watch] now: {now_et()}")
    deadline = time.time() + timeout_min * 60
    while time.time() < deadline:
        weekly = lib.fetch_weekly(length=8, cache_hours=0.0)
        latest = weekly["crude"].dropna().index.max().strftime("%Y-%m-%d")
        if latest > baseline:
            print(f"[watch] NEW PRINT detected: {latest} (was {baseline}). Assessing ...")
            snap = assess(fresh=True)
            write_signal(snap)
            print_summary(snap)
            return snap
        print(f"[watch] {now_et()} — still {latest}; waiting ...")
        time.sleep(interval)
    print(f"[watch] timed out after {timeout_min} min with no new print. Refreshing base case.")
    snap = assess(fresh=True)
    write_signal(snap)
    print_summary(snap)
    return snap


def main():
    ap = argparse.ArgumentParser(description="Live EIA crude-inventory cross-check engine.")
    ap.add_argument("--watch", action="store_true", help="poll the EIA API until a new print lands")
    ap.add_argument("--interval", type=int, default=60, help="poll interval seconds (watch mode)")
    ap.add_argument("--timeout", type=int, default=90, help="max minutes to watch")
    ap.add_argument("--crosscheck", action="store_true", help="only re-run the market cross-check on the latest print")
    args = ap.parse_args()

    if args.watch:
        watch(args.interval, args.timeout)
    else:
        snap = assess(fresh=True)
        write_signal(snap)
        print_summary(snap)


if __name__ == "__main__":
    main()
