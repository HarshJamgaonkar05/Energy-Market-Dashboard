"""
release_lab.py — the "EIA Release Lab": EXPECTED vs REAL surprise for one release.

WHAT THIS IS, IN ONE BREATH
---------------------------
The rest of Phase 4 (inventory_lib.py + inventory_engine.py) is a rolling live signal.
This module freezes a single experiment around ONE EIA crude release so a human can see,
side by side:

  1. THE PREDICTION (built from everything we knew BEFORE the release) —
       * the model's EXPECTED build/draw (our leak-free consensus proxy),
       * the structural lean (bullish / bearish / neutral) and why,
       * how hard the market actually moves per unit of surprise in this regime
         (the "impact curve": predicted WTI move = beta x surprise),
       * an EXPECTED SURPRISE of ~0 — by construction the model expects the print to
         land on its own consensus, so the only thing that moves price is the miss.

  2. THE RESULT (computed AFTER the number lands, when you press the button) —
       * the ACTUAL build/draw,
       * the REAL SURPRISE = actual - expected, standardised (sigma),
       * the regime-aware verdict,
       * the market cross-check: where the REAL surprise + the REAL WTI move landed
         relative to the predicted impact curve (did reality follow the line?).

  3. THE DIFFERENCE — expected vs real, in plain English: did the surprise break the way
       we leaned, did price move the way the surprise implied, and was the call right?

Everything reuses inventory_lib.analyze() (the single source of truth), and every number
is leak-free: the EXPECTED for the target week is the walk-forward one-step-ahead forecast
(it never sees the actual it predicts), and the structural lean is computed only from rows
strictly before the target week.

USAGE
  python release_lab.py --predict   build & freeze the prediction only (result = null).
                                     Run this BEFORE the release to lock in the call.
  python release_lab.py --run        the dashboard button: re-derive the prediction, fetch
                                     the freshest EIA print, compute the real surprise +
                                     verdict + cross-check, and write the full comparison.
  python release_lab.py              same as --run.

Writes server/data/release_lab.json (the /api/release-lab panel reads it).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# Windows consoles default to cp1252, which can't encode sigma/squared etc.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import pandas as pd

from datetime import datetime as _dt, timedelta

from common import ROOT, yahoo_intraday
import inventory_lib as lib
from inventory_engine import market_crosscheck   # reuse the live cross-check

DATA_DIR = ROOT / "server" / "data"
OUT = DATA_DIR / "release_lab.json"
IMPACT = DATA_DIR / "intraday_impact.json"
ET = ZoneInfo("America/New_York")
HEADLINE_HORIZONS = [5, 30, 60]      # the three the dashboard features


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def now_et() -> str:
    return datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S %Z")


def _r(x, nd=2):
    try:
        if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
            return None
        return round(float(x), nd)
    except Exception:
        return None


def _vdict(v: lib.Verdict) -> dict:
    return {"direction": v.direction, "score": v.score, "confidence": v.confidence,
            "headline": v.headline, "factors": v.factors, "products": v.products}


# ---------------------------------------------------------------------------
# Live track record: persist each frozen FORWARD forecast, then grade it once the
# week actually publishes — a genuine out-of-sample record of real pre-release calls
# (distinct from the backtested track_record). Survives across runs via a JSON log.
HISTORY = DATA_DIR / "release_lab_history.json"


def _load_history() -> list:
    try:
        h = json.loads(HISTORY.read_text())
        return h if isinstance(h, list) else []
    except Exception:
        return []


def _write_history(hist: list):
    try:
        HISTORY.write_text(json.dumps(hist[-260:], indent=2))
    except Exception as e:
        print(f"[release-lab] could not write history: {e}")


def _freeze_history(period, u_rel, pred: dict):
    """Upsert the current forward call for `period` (keeps it fresh until it publishes)."""
    hist = _load_history()
    key = period.strftime("%Y-%m-%d")
    idx = next((i for i, e in enumerate(hist) if e.get("period") == key), None)
    if idx is not None and hist[idx].get("graded_at"):
        return                                   # already graded — never overwrite the record
    entry = {"period": key, "release_date": u_rel.strftime("%Y-%m-%d"),
             "frozen_at": now_iso(),
             "expected_wow": pred.get("expected_wow"), "expected_seasonal": pred.get("expected_seasonal"),
             "lean": pred.get("lean"), "lean_score": pred.get("lean_score"),
             "catalyst_r2": pred.get("catalyst_r2"),
             "actual_wow": None, "surprise": None, "lean_hit": None, "graded_at": None}
    if idx is None:
        hist.append(entry)
    else:
        entry["frozen_at"] = hist[idx].get("frozen_at") or entry["frozen_at"]   # keep first freeze
        hist[idx] = entry
    _write_history(hist)


def _grade_history(published: pd.DataFrame):
    """Fill in the actual + surprise for any frozen call whose week has now published."""
    hist = _load_history()
    if not hist:
        return
    idx = {r["period"].strftime("%Y-%m-%d"): r for _, r in published.iterrows()}
    changed = False
    for e in hist:
        if e.get("graded_at") or e.get("period") not in idx:
            continue
        r = idx[e["period"]]
        actual, surprise = r.get("crude_wow"), r.get("surprise")
        if actual != actual:
            continue
        e["actual_wow"] = round(float(actual), 2)
        e["surprise"] = round(float(surprise), 2) if surprise == surprise else None
        if e.get("lean") and surprise == surprise:
            e["lean_hit"] = bool((e["lean"] == "Bullish" and surprise < 0) or
                                 (e["lean"] == "Bearish" and surprise > 0))
        e["graded_at"] = now_iso()
        changed = True
    if changed:
        _write_history(hist)


def _live_record() -> dict:
    """Summarise the engine's ACTUAL forward calls: how many graded, forecast accuracy
    vs the seasonal-naive guess, and how often the pre-release lean called the surprise."""
    hist = _load_history()
    graded = [e for e in hist if e.get("graded_at") and e.get("actual_wow") is not None]
    pending = [e for e in hist if not e.get("graded_at")]
    out = {"n": len(graded), "pending": len(pending),
           "recent": [{"period": e["period"], "expected_wow": e.get("expected_wow"),
                       "actual_wow": e.get("actual_wow"), "lean": e.get("lean"),
                       "lean_hit": e.get("lean_hit")} for e in graded[-6:]]}
    if len(graded) >= 3:
        me = [abs(e["actual_wow"] - e["expected_wow"]) for e in graded if e.get("expected_wow") is not None]
        se = [abs(e["actual_wow"] - e["expected_seasonal"]) for e in graded if e.get("expected_seasonal") is not None]
        lh = [e["lean_hit"] for e in graded if isinstance(e.get("lean_hit"), bool)]
        out["mae"] = round(float(np.mean(me)), 2) if me else None
        out["mae_seasonal"] = round(float(np.mean(se)), 2) if se else None
        out["lean_hit_rate"] = round(float(np.mean(lh)), 3) if lh else None
    return out


# ---------------------------------------------------------------------------
def _impact_curve(beta, beta_ov, sigma):
    """predicted release-day WTI move = beta * surprise across +/- 2.5 sigma."""
    span = [round(sigma * k, 2) for k in np.linspace(-2.5, 2.5, 21)]
    return [{"surprise": s, "regime_pct": round(beta * s * 100, 3),
             "overall_pct": round(beta_ov * s * 100, 3)} for s in span]


def _prediction(expected, expected_seasonal, lean, r2, n, beta, beta_ov, r2_ov, n_ov,
                sigma, asof, products):
    """The pre-release PREDICTION half, shared by the upcoming (forward) and the last
    (retrospective, leak-free) blocks so the two can never diverge in construction."""
    def scen(label, surp):
        return {"label": label, "surprise": round(surp, 1),
                "pred_move_pct": round(beta * surp * 100, 3),
                "pred_move_pct_overall": round(beta_ov * surp * 100, 3),
                "dir": "Bullish" if surp < 0 else "Bearish" if surp > 0 else "Neutral"}
    return {
        "asof": asof,
        "expected_wow": _r(expected, 2),
        "expected_seasonal": _r(expected_seasonal, 1),
        "expected_surprise": 0.0,            # by construction the model expects to be right
        "lean": lean.direction, "lean_score": lean.score, "confidence": lean.confidence,
        "headline": lean.headline, "factors": lean.factors, "products": products,
        "catalyst_r2": round(r2, 4), "catalyst_n": n,
        "beta_pct_per_mmbbl": round(beta * 100, 4),
        "beta_overall_pct_per_mmbbl": round(beta_ov * 100, 4),
        "overall_r2": round(r2_ov, 4), "overall_n": n_ov,
        "sigma_mmbbl": round(sigma, 2),
        "scenarios": [scen("Big draw beat (-1σ)", -sigma),
                      scen("In line (0)", 0.0),
                      scen("Big build miss (+1σ)", sigma)],
        "narrative": _predict_narrative(expected, lean, r2, beta_ov, sigma),
    }


def _levels(row, vol):
    return {
        "crude_stock": _r(row.get("crude"), 1), "cushing": _r(row.get("cushing"), 1),
        "cushing_wow": _r(row.get("cushing_wow"), 1), "refutil": _r(row.get("refutil"), 1),
        "crude_z": _r(row.get("crude_z"), 2), "days_supply": _r(row.get("days_supply"), 1),
        "season": row.get("season"), "vol_regime": vol,
        "wti_struct": row.get("wti_struct"), "product_alignment": row.get("product_alignment"),
    }


def build(run_result: bool = True) -> dict:
    """Build the full Release-Lab snapshot with TWO experiments:

      * UPCOMING — a live, forward, leak-free forecast for the NEXT (not-yet-released)
        week: the model's one-step-ahead expected build/draw, the structural lean into
        the print, the regime catalyst strength and the impact curve. Refreshed every
        run so it always describes the next release; graded automatically once it lands.

      * LAST — the most recent PUBLISHED week: the same pre-release prediction (derived
        leak-free from rows strictly before that week) PLUS the result (actual print,
        real surprise, verdict, cross-check, scorecard) when run_result is True.

    Implementation: we append one synthetic future week to the EIA series and run the
    single analyze() pipeline once. The future row picks up the walk-forward `expected`
    (its features are all lagged/seasonal, known pre-release) and the CURRENT regime
    context (vol/structure read as-of its release date), while its NaN reaction simply
    drops out of the event study — so both experiments come from one consistent frame."""
    weekly = lib.fetch_weekly(length=600, cache_hours=0.0)
    prices = lib.fetch_prices(cache_hours=0.0)
    panel = lib.load_panel()

    if weekly.empty or "crude" not in weekly or weekly["crude"].dropna().empty:
        return {"generatedAt": now_iso(), "generatedAtET": now_et(), "status": "no-data",
                "error": "EIA returned no crude data (API outage or rate-limit?)."}

    # Append the NEXT week (all-NaN) so the pipeline produces a forward forecast for it.
    next_period = weekly.index.max() + pd.Timedelta(days=7)
    weekly_ext = weekly.copy()
    weekly_ext.loc[next_period] = np.nan
    weekly_ext = weekly_ext.sort_index()

    A = lib.analyze(weekly_ext, prices, panel)
    f, es = A["frame"], A["event_study"]
    sens = A["spread_sensitivity"]
    products = [k for k in sens.keys() if k not in ("panel_wti", "panel_brent")][:5]
    ov = es.get("overall") or {}
    beta_ov, r2_ov, n_ov = ov.get("beta", 0.0), ov.get("r2", 0.0), ov.get("n", 0)
    sigma = float(es.get("surprise_sigma_mmbbl") or 5.0)
    track = _track_record(f, A)

    published = f.dropna(subset=["crude_wow"])
    last_pub = published.iloc[-1]
    _grade_history(published)                 # grade any frozen calls that have now published

    # ===================================================================
    # UPCOMING — forward, leak-free forecast for the next unreleased week.
    # ===================================================================
    up_row = f.iloc[-1]                                    # the synthetic future row
    upcoming = None
    if up_row["period"] == next_period:
        u_rel = lib.release_date(next_period)
        u_vol = up_row.get("vol_regime")
        ur2, un, ubeta = lib.reliability_for(es, u_vol)
        u_exp = float(up_row["expected"]) if up_row.get("expected") == up_row.get("expected") else float(last_pub["expected"])
        u_seasonal = up_row.get("expected_seasonal")
        u_sigma = float(up_row.get("surprise_std") or sigma)
        ctx_now = {"vol_regime": u_vol, "wti_struct": up_row.get("wti_struct"),
                   "product_alignment": up_row.get("product_alignment"), "products": products}
        u_lean = lib.forward_base_case(f, ctx_now, ur2, un, expected_override=u_exp,
                                       seasonal_override=(u_seasonal if u_seasonal == u_seasonal else None),
                                       season_override=up_row.get("season"))
        today = datetime.now(ET).date()
        days_until = (u_rel.date() - today).days
        upcoming = {
            "status": "awaiting-release",
            "target": {"period": next_period.strftime("%Y-%m-%d"),
                       "release_date": u_rel.strftime("%Y-%m-%d"),
                       "days_until": days_until,
                       "label": f"{u_rel.day} {u_rel.strftime('%B %Y')} EIA crude release"},
            "current": _levels(last_pub, last_pub.get("vol_regime")),   # stocks going INTO the print
            "prediction": _prediction(u_exp, u_seasonal, u_lean, ur2, un, ubeta, beta_ov,
                                      r2_ov, n_ov, u_sigma, now_et(), products),
            "impact_curve": {"beta_pct_per_mmbbl": round(ubeta * 100, 4),
                             "beta_overall_pct_per_mmbbl": round(beta_ov * 100, 4),
                             "sigma_mmbbl": round(u_sigma, 2),
                             "points": _impact_curve(ubeta, beta_ov, u_sigma)},
            "intraday": _intraday_block(u_vol, None, False, u_rel.strftime("%Y-%m-%d")),
            "result": None,
        }
        _freeze_history(next_period, u_rel, upcoming["prediction"])

    # ===================================================================
    # LAST — the most recent PUBLISHED week (prediction + graded result).
    # ===================================================================
    target = last_pub
    t_period = target["period"]
    t_rel = lib.release_date(t_period)
    prior_cutoff = t_period - pd.Timedelta(days=7)
    t_vol = target.get("vol_regime")
    r2, n, beta = lib.reliability_for(es, t_vol)
    expected = float(target["expected"])
    expected_seasonal = target.get("expected_seasonal")

    # leak-free retrospective lean: rows strictly before the target week.
    f_pre = f[f["period"] < t_period]
    prior = f_pre.dropna(subset=["crude_wow"]).iloc[-1]
    ctx_pre = {"vol_regime": prior.get("vol_regime"), "wti_struct": prior.get("wti_struct"),
               "product_alignment": prior.get("product_alignment"), "products": products}
    r2_pre, n_pre, _ = lib.reliability_for(es, prior.get("vol_regime"))
    lean = lib.forward_base_case(f_pre, ctx_pre, r2_pre, n_pre)

    last_block = {
        "target": {"period": t_period.strftime("%Y-%m-%d"),
                   "release_date": t_rel.strftime("%Y-%m-%d"),
                   "label": f"{t_rel.day} {t_rel.strftime('%B %Y')} EIA crude release"},
        "current": _levels(target, t_vol),
        "prediction": _prediction(expected, expected_seasonal, lean, r2, n, beta, beta_ov,
                                  r2_ov, n_ov, sigma, prior_cutoff.strftime("%Y-%m-%d"), products),
        "impact_curve": {"beta_pct_per_mmbbl": round(beta * 100, 4),
                         "beta_overall_pct_per_mmbbl": round(beta_ov * 100, 4),
                         "sigma_mmbbl": round(sigma, 2), "points": _impact_curve(beta, beta_ov, sigma)},
        "intraday": _intraday_block(t_vol, None, False, t_rel.strftime("%Y-%m-%d")),
        "result": None, "comparison": None, "scorecard": None,
    }

    snap = {
        "generatedAt": now_iso(), "generatedAtET": now_et(),
        "status": "complete" if run_result else "awaiting-release",
        "track_record": track,
        "live_record": _live_record(),
        "upcoming": upcoming,
        "last": last_block,
    }

    if not run_result:
        return snap

    # ---- grade the LAST release ----
    actual = float(target["crude_wow"])
    surprise = float(target["surprise"])
    sz = float(target["surprise_z"]) if target.get("surprise_z") == target.get("surprise_z") else 0.0
    ctx_t = {"vol_regime": t_vol, "wti_struct": target.get("wti_struct"),
             "product_alignment": target.get("product_alignment"), "products": products}
    verdict = lib.verdict_from_surprise(surprise, sz, ctx_t, r2, n, beta)
    cross = market_crosscheck(prices, target, surprise, beta, verdict.direction)
    actual_move = cross.get("wti_reaction_pct")
    pred_move = round(beta * surprise * 100, 3)
    pred_move_ov = round(beta_ov * surprise * 100, 3)

    last_block["result"] = {
        "ran_at": now_iso(), "ran_at_et": now_et(),
        "actual_wow": _r(actual, 2), "actual_stock": _r(target.get("crude"), 1),
        "real_surprise": _r(surprise, 2), "real_surprise_z": _r(sz, 2),
        "real_surprise_dir": "bullish" if surprise < 0 else "bearish" if surprise > 0 else "neutral",
        "verdict": _vdict(verdict), "crosscheck": cross,
        "pred_move_pct": pred_move, "pred_move_pct_overall": pred_move_ov,
        "actual_move_pct": _r(actual_move, 2),
        "realized_point": {"surprise": _r(surprise, 2),
                           "pred_regime_pct": pred_move, "pred_overall_pct": pred_move_ov,
                           "actual_pct": _r(actual_move, 2)},
        "attribution": lib.decompose_move(A.get("impact_decomp", {}), target),
    }
    last_block["comparison"] = _comparison(expected, actual, surprise, sz, lean, verdict,
                                           cross, pred_move, actual_move, r2)
    last_block["scorecard"] = _scorecard(expected, actual, surprise, sz, lean, cross,
                                         pred_move, actual_move, r2)
    last_block["intraday"] = _intraday_block(t_vol, surprise, True, t_rel.strftime("%Y-%m-%d"))
    return snap


# ---------------------------------------------------------------------------
def _predict_narrative(expected, lean, r2, beta_ov, sigma) -> str:
    exp_kind = "draw" if expected < 0 else "build"
    cat = "a strong" if r2 >= 0.05 else "a weak"
    return (
        f"Before the print, the model expects a {abs(expected):.1f} MMbbl {exp_kind} — that is the "
        f"number the market is positioned for, so the EXPECTED SURPRISE is ~0 and a print in line "
        f"should barely move WTI. Our structural lean is {lean.direction.upper()}. Crucially, the "
        f"release is {cat} same-day catalyst here (regime R²={r2:.2f}): even a 1σ miss "
        f"(~{sigma:.1f} MMbbl) maps to only a small WTI move on the inventory number alone. The real "
        f"test is whether the print beats or misses that {abs(expected):.1f} MMbbl base case."
    )


def _comparison(expected, actual, surprise, sz, lean, verdict, cross, pred_move, actual_move, r2) -> dict:
    surp_dir = "a bigger draw than expected (bullish)" if surprise < 0 else \
               "a bigger build than expected (bearish)" if surprise > 0 else "right in line"
    lean_bull = lean.direction == "Bullish"
    lean_bear = lean.direction == "Bearish"
    surp_bull = surprise < 0
    lean_matched = (lean_bull and surp_bull) or (lean_bear and not surp_bull) or \
                   (lean.direction == "Neutral" and abs(sz) < 0.5)
    status = (cross or {}).get("status")
    am = actual_move if actual_move is not None else float("nan")

    parts = [
        f"We expected a {abs(expected):.1f} MMbbl {'draw' if expected < 0 else 'build'}; the EIA "
        f"reported {abs(actual):.1f} MMbbl {'draw' if actual < 0 else 'build'}. That is a REAL "
        f"SURPRISE of {surprise:+.1f} MMbbl ({sz:+.1f}σ) — {surp_dir}.",
        f"Our pre-release lean was {lean.direction.upper()}; the surprise broke "
        f"{'the SAME way' if lean_matched else 'the OTHER way'}.",
    ]
    if actual_move is not None:
        on_line = abs(am - pred_move) <= max(0.4, abs(pred_move) * 1.5)
        parts.append(
            f"On the inventory surprise alone the regime model implied WTI ~{pred_move:+.2f}%; WTI "
            f"actually moved {am:+.2f}% on the print — the surprise was "
            f"{status.upper() if status else 'n/a'} by the market, and the realized move sat "
            f"{'ON' if on_line else 'WELL OFF'} the predicted impact line.")
        if not on_line and abs(r2) < 0.05:
            parts.append(
                "That gap is the headline lesson, not a model failure: in this regime inventories "
                "explain almost none of release-day WTI (R²≈" f"{r2:.2f}), so the day was "
                "driven by other forces (macro / OPEC / geopolitics / positioning) — exactly the "
                "low-catalyst read the framework flagged going in.")
    return {
        "expected_wow": _r(expected, 2), "actual_wow": _r(actual, 2),
        "expected_surprise": 0.0, "real_surprise": _r(surprise, 2), "real_surprise_z": _r(sz, 2),
        "lean": lean.direction, "verdict": verdict.direction,
        "lean_matched_surprise": bool(lean_matched),
        "pred_move_pct": pred_move, "actual_move_pct": _r(actual_move, 2),
        "crosscheck_status": status,
        "narrative": " ".join(parts),
    }


# ---------------------------------------------------------------------------
def _track_record(f: pd.DataFrame, A: dict) -> dict:
    """Backtest the FRAMEWORK on history so a single experiment isn't read as luck.
    Three honest, leak-free questions over all releases and the last 52:
      1. SURPRISE -> PRICE: among material surprises, how often did WTI move the way
         the surprise implied? (the framework's core empirical claim)
      2. LEAN: a per-release structural lean built only from data BEFORE the week
         (prior z, prior 4w momentum, prior 4w Cushing) — did it call the surprise
         direction? (tests our pre-release bias, not just the math identity)
      3. FORECAST SKILL: the model's mean absolute error on the weekly change vs the
         naive seasonal guess — is the consensus proxy actually better than season?"""
    es_df = A["es_df"]
    overall_hit = A["hit_rate"].get("overall") or {}
    recent_hit = lib.hit_rate(es_df.tail(52)) or {}

    # Leak-free structural lean per release (mirrors forward_base_case, shifted by 1).
    g = f.copy()
    g["lz"] = g["crude_z"].shift(1)
    g["lmom"] = g["crude_wow"].shift(1).rolling(4).mean()
    g["lcush"] = (g["cushing_wow"].shift(1).rolling(4).sum() if "cushing_wow" in g else np.nan)
    g["lean_score"] = -np.tanh(g["lz"]) - np.tanh(g["lmom"] / 4.0) - np.tanh(g["lcush"] / 6.0)

    def lean_hit(sub):
        d = sub.dropna(subset=["lean_score", "surprise", "surprise_z"])
        d = d[(d["lean_score"].abs() > 0.4) & (d["surprise_z"].abs() >= 0.5)]
        if len(d) < 6:
            return None
        hit = (d["lean_score"] > 0) == (d["surprise"] < 0)   # bullish lean -> draw beat
        return {"hit_rate": round(float(hit.mean()), 3), "n": int(len(d))}

    def mae(sub):
        d = sub.dropna(subset=["crude_wow", "expected", "expected_seasonal", "expected_model"])
        if d.empty:
            return None
        return {"model": round(float((d["crude_wow"] - d["expected"]).abs().mean()), 2),
                "seasonal": round(float((d["crude_wow"] - d["expected_seasonal"]).abs().mean()), 2),
                "n": int(len(d))}

    def window(es_sub, g_sub, hit_obj):
        return {
            "surprise_hit_rate": hit_obj.get("hit_rate"),
            "surprise_hit_n": hit_obj.get("n_material"),
            "avg_fav_move_pct": hit_obj.get("avg_fav_move_pct"),
            "lean": lean_hit(g_sub),
            "mae": mae(g_sub),
        }

    return {
        "all": window(es_df, g, overall_hit),
        "recent": window(es_df.tail(52), g.tail(52), recent_hit),
        "note": ("Surprise->price = directional accuracy among material surprises (|z|>=0.5). "
                 "Lean = our pre-release bias calling the surprise sign. MAE = avg miss of the "
                 "model's expected weekly change vs the naive seasonal guess (lower is better)."),
    }


def _scorecard(expected, actual, surprise, sz, lean, cross, pred_move, actual_move, r2) -> dict:
    """Three traffic lights + one net verdict — the at-a-glance 'did it work?'.
       ok = True (green) / None (amber) / False (red)."""
    a_sz = abs(sz)
    fc_ok = True if a_sz < 0.5 else None if a_sz < 1.0 else False
    fc_grade = "GOOD" if fc_ok is True else "FAIR" if fc_ok is None else "OFF"

    lean_bull, lean_bear = lean.direction == "Bullish", lean.direction == "Bearish"
    surp_bull = surprise < 0
    matched = (lean_bull and surp_bull) or (lean_bear and not surp_bull) or \
              (lean.direction == "Neutral" and a_sz < 0.5)

    status = (cross or {}).get("status")
    price_ok = True if status == "confirmed" else None if status in ("flat", "pending") else False

    weak_cat = abs(r2) < 0.05
    if price_ok is True:
        net = ("The call paid off end to end: the surprise broke the way we leaned AND price "
               "followed it.")
    elif price_ok is False and weak_cat:
        net = ("Framework worked as designed: it flagged inventories as a WEAK same-day catalyst "
               f"(R²≈{r2:.2f}), and sure enough WTI ignored the surprise and moved on other forces "
               "(macro / OPEC / geopolitics).")
    elif price_ok is False:
        net = ("A genuine miss: inventories usually drive price in this regime, but WTI moved "
               "against the surprise this time.")
    else:
        net = "Price reaction was flat / still forming — no clear grade on the move yet."

    return {
        "lights": [
            {"key": "forecast", "label": "Forecast the number", "grade": fc_grade, "ok": fc_ok,
             "detail": f"off by {abs(surprise):.1f} MMbbl ({sz:+.1f}σ)"},
            {"key": "surprise", "label": "Surprise broke our way", "grade": "YES" if matched else "NO",
             "ok": bool(matched),
             "detail": f"lean {lean.direction} vs a {'bullish' if surp_bull else 'bearish'} "
                       f"{'beat' if surp_bull else 'miss'}"},
            {"key": "price", "label": "Price followed the surprise",
             "grade": "YES" if price_ok is True else "FLAT" if price_ok is None else "NO",
             "ok": price_ok,
             "detail": (f"WTI {actual_move:+.1f}% vs {pred_move:+.1f}% implied"
                        if actual_move is not None else "pending")},
        ],
        "net": net,
    }


# ---------------------------------------------------------------------------
def _load_impact():
    try:
        return json.loads(IMPACT.read_text())
    except Exception:
        return None


def _actual_path(t_rel_str: str, max_min: int = 120):
    """The live release-day WTI reaction path from Yahoo 5-min bars: cumulative % move
    from the last pre-print bar, sampled every 5 min. Returns (path_list, {h: frac})."""
    bars = yahoo_intraday("CL=F", "5m", "60d", cache_hours=1.0)
    if not bars:
        return None, {}
    ser = [(_dt.fromtimestamp(ep, tz=timezone.utc).astimezone(ET), px) for ep, px in bars]
    rel = _dt.strptime(t_rel_str, "%Y-%m-%d")
    release = _dt(rel.year, rel.month, rel.day, 10, 30, tzinfo=ET)
    pre = [(d, p) for d, p in ser if d < release]
    post = [(d, p) for d, p in ser if release <= d <= release + timedelta(minutes=max_min + 10)]
    if not pre or len(post) < 2:
        return None, {}
    ref_px = pre[-1][1]

    def at(minutes):
        target = release + timedelta(minutes=minutes)
        best, gap = None, timedelta(minutes=6)
        for d, p in post:
            g = abs(d - target)
            if g < gap:
                best, gap = p, g
        return None if best is None or ref_px in (0, None) else best / ref_px - 1.0

    path = [{"min": 0, "pct": 0.0}]
    for m in range(5, max_min + 1, 5):
        v = at(m)
        if v is not None:
            path.append({"min": m, "pct": round(v * 100, 3)})
    return path, {h: at(h) for h in (5, 15, 30, 60, 120)}


def _intraday_block(t_vol, surprise, with_actual: bool, t_rel_str: str) -> dict | None:
    """Per-horizon predicted vs actual reaction. The MODEL (beta/r2/rmse per horizon)
    comes from the precomputed intraday_impact.json; the PREDICTED move = beta x the
    real surprise; the ACTUAL path is the live Yahoo 5-min reaction on the print day."""
    model = _load_impact()
    if not model:
        return None
    horizons = model.get("horizons_min", [5, 15, 30, 60, 120])
    by_h, by_reg = model.get("by_horizon", {}), model.get("by_regime", {})

    def pick(h):
        reg = (by_reg.get(str(t_vol)) or {}).get(str(h)) if t_vol else None
        return reg if (reg and reg.get("n", 0) >= 12) else by_h.get(str(h))

    path_actual, actual_by_h = (_actual_path(t_rel_str) if with_actual else (None, {}))

    rows, pred_path = [], [{"min": 0, "pct": 0.0, "lo": 0.0, "hi": 0.0}]
    for h in horizons:
        s = pick(h)
        if not s:
            continue
        beta = s["beta_pct_per_mmbbl"]
        rmse = s.get("rmse_pct")
        pred = round(beta * surprise, 3) if surprise is not None else None
        lo = round(pred - rmse, 3) if (pred is not None and rmse is not None) else None
        hi = round(pred + rmse, 3) if (pred is not None and rmse is not None) else None
        af = actual_by_h.get(h)
        actual = round(af * 100, 3) if af is not None else None
        hit = None
        if actual is not None and surprise not in (None, 0):
            hit = (actual > 0) if surprise < 0 else (actual < 0)
        rows.append({"min": h, "beta_pct_per_mmbbl": beta, "r2": s.get("r2"),
                     "rmse_pct": rmse, "n": s.get("n"), "predicted_pct": pred,
                     "lo": lo, "hi": hi, "actual_pct": actual, "hit": hit})
        if pred is not None:
            pred_path.append({"min": h, "pct": pred, "lo": lo, "hi": hi})

    best_r2 = max((r["r2"] for r in rows if r.get("r2") is not None), default=0.0)
    return {
        "model_source": model.get("source"), "model_n": model.get("n_releases"),
        "sample_period": model.get("sample_period"),
        "vol_regime_used": t_vol or "overall",
        "headline_min": HEADLINE_HORIZONS,
        "horizons": rows,
        "path": {"predicted": pred_path if surprise is not None else None, "actual": path_actual},
        "max_r2": round(float(best_r2), 4),
        "narrative": _intraday_narrative(rows, best_r2, with_actual),
    }


def _intraday_narrative(rows, best_r2, with_actual) -> str:
    head = ("Minute-by-minute, the crude surprise explains almost none of WTI — the best "
            f"any horizon reaches is R²≈{best_r2:.2f}. ") if best_r2 < 0.05 else \
           (f"The surprise's intraday signal peaks at R²≈{best_r2:.2f}. ")
    if not with_actual:
        return head + "Press run to overlay the actual release-day path on the prediction."
    feat = [r for r in rows if r["min"] in HEADLINE_HORIZONS and r.get("actual_pct") is not None]
    if not feat:
        return head + "Live 5-min reaction path unavailable for this release."
    parts = ", ".join(f"+{r['min']}m {r['actual_pct']:+.2f}% (vs predicted {r['predicted_pct']:+.2f}%)"
                      for r in feat)
    misses = sum(1 for r in feat if r.get("hit") is False)
    tail = (" — the realized path runs far from the near-zero prediction at every horizon, so "
            "the move came from other flows, not the inventory number."
            if misses >= len(feat) - 1 else
            " — the early reaction tracked the surprise before other flows took over.")
    return head + "Realized: " + parts + tail


# ---------------------------------------------------------------------------
def write(snap: dict):
    if snap.get("status") == "no-data":
        print(f"[release-lab] {snap.get('error')} — leaving {OUT.name} unchanged.")
        return
    OUT.write_text(json.dumps(snap, indent=2))
    print(f"[release-lab] wrote {OUT}")


def print_summary(snap: dict):
    if snap.get("status") == "no-data":
        print("[NO-DATA]", snap.get("error"));  return
    u = snap.get("upcoming")
    if u:
        ut, up = u["target"], u["prediction"]
        print(f"\n=== UPCOMING (live forecast) — {ut['label']} · in {ut['days_until']}d (week {ut['period']}) ===")
        print(f"    Expected {up['expected_wow']:+.1f} MMbbl  | lean {up['lean']} ({up['confidence']})  "
              f"| catalyst R²={up['catalyst_r2']} (n={up['catalyst_n']})")
    last = snap.get("last") or {}
    t, p = last.get("target", {}), last.get("prediction", {})
    print(f"\n=== LAST (graded) — {t.get('label')} (week {t.get('period')}) ===")
    print(f"    Expected {p.get('expected_wow'):+.1f} MMbbl (as of {p.get('asof')})  | lean {p.get('lean')} ({p.get('confidence')})")
    r = last.get("result")
    if r:
        print(f"    Actual {r['actual_wow']:+.1f} MMbbl  | REAL surprise {r['real_surprise']:+.1f} "
              f"({r['real_surprise_z']:+.1f}σ, {r['real_surprise_dir']})  | verdict {r['verdict']['direction']}")
        print(f"    Predicted move {r['pred_move_pct']:+.2f}%  | actual move {r['actual_move_pct']:+.2f}%  "
              f"-> {(r['crosscheck'] or {}).get('status','?').upper()}")
        print(f"\n  {last['comparison']['narrative']}")
    lr = snap.get("live_record") or {}
    print(f"\n  LIVE RECORD: {lr.get('n',0)} graded · {lr.get('pending',0)} pending"
          + (f" · MAE {lr.get('mae')} vs seasonal {lr.get('mae_seasonal')} · lean hit {lr.get('lean_hit_rate')}"
             if lr.get('n',0) >= 3 else ""))


def main():
    ap = argparse.ArgumentParser(description="EIA Release Lab — expected vs real surprise.")
    ap.add_argument("--predict", action="store_true",
                    help="freeze the prediction only (result=null); run BEFORE the release")
    ap.add_argument("--run", action="store_true", help="run the full pipeline on the latest print (default)")
    args = ap.parse_args()
    snap = build(run_result=not args.predict)
    write(snap)
    print_summary(snap)


if __name__ == "__main__":
    main()
