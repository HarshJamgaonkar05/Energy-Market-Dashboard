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
def build(run_result: bool = True) -> dict:
    """Build the full Release-Lab snapshot. The PREDICTION half is always derived
    leak-free from data strictly before the target week; the RESULT half (the actual
    print, real surprise, verdict, cross-check) is added when run_result is True."""
    weekly = lib.fetch_weekly(length=600, cache_hours=0.0)
    prices = lib.fetch_prices(cache_hours=0.0)
    panel = lib.load_panel()

    if weekly.empty or "crude" not in weekly or weekly["crude"].dropna().empty:
        return {"generatedAt": now_iso(), "generatedAtET": now_et(), "status": "no-data",
                "error": "EIA returned no crude data (API outage or rate-limit?)."}

    A = lib.analyze(weekly, prices, panel)
    f, es = A["frame"], A["event_study"]

    # The TARGET = the most recent published week (the one the latest release covers).
    target = f.dropna(subset=["crude_wow"]).iloc[-1]
    t_period = target["period"]
    t_rel = lib.release_date(t_period)
    prior_cutoff = t_period - pd.Timedelta(days=7)

    # --- regime / catalyst strength the print landed in (drives verdict + curve) ---
    t_vol = target.get("vol_regime")
    r2, n, beta = lib.reliability_for(es, t_vol)          # conditional reaction-per-MMbbl
    ov = es.get("overall") or {}
    beta_ov, r2_ov, n_ov = ov.get("beta", 0.0), ov.get("r2", 0.0), ov.get("n", 0)
    sigma = float(es.get("surprise_sigma_mmbbl") or target.get("surprise_std") or 5.0)

    expected = float(target["expected"])                  # walk-forward, leak-free consensus
    expected_seasonal = _r(target.get("expected_seasonal"), 1)

    # ===================================================================
    # PREDICTION — what we knew BEFORE the print (rows strictly before target).
    # ===================================================================
    f_pre = f[f["period"] < t_period]
    prior = f_pre.dropna(subset=["crude_wow"]).iloc[-1]
    sens = A["spread_sensitivity"]
    products = [k for k in sens.keys() if k not in ("panel_wti", "panel_brent")][:5]
    ctx_pre = {"vol_regime": prior.get("vol_regime"), "wti_struct": prior.get("wti_struct"),
               "product_alignment": prior.get("product_alignment"), "products": products}
    r2_pre, n_pre, _ = lib.reliability_for(es, prior.get("vol_regime"))
    lean = lib.forward_base_case(f_pre, ctx_pre, r2_pre, n_pre)

    # The impact curve: predicted release-day WTI move = beta * surprise, drawn across a
    # +/- 2.5 sigma band, both in the current regime and over all history (the textbook line).
    span = [round(sigma * k, 2) for k in np.linspace(-2.5, 2.5, 21)]
    curve = [{"surprise": s,
              "regime_pct": round(beta * s * 100, 3),
              "overall_pct": round(beta_ov * s * 100, 3)} for s in span]

    # Expected-surprise scenarios (pre-release): a print in line = ~0 surprise = muted;
    # a 1-sigma beat / miss tells you the asymmetric payoff in THIS regime.
    def scen(label, surp):
        return {"label": label, "surprise": round(surp, 1),
                "pred_move_pct": round(beta * surp * 100, 3),
                "pred_move_pct_overall": round(beta_ov * surp * 100, 3),
                "dir": "Bullish" if surp < 0 else "Bearish" if surp > 0 else "Neutral"}

    prediction = {
        "asof": prior_cutoff.strftime("%Y-%m-%d"),
        "expected_wow": _r(expected, 2),
        "expected_seasonal": expected_seasonal,
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

    track = _track_record(f, A)

    snap = {
        "generatedAt": now_iso(), "generatedAtET": now_et(),
        "status": "complete" if run_result else "awaiting-release",
        "track_record": track,
        "target": {"period": t_period.strftime("%Y-%m-%d"),
                   "release_date": t_rel.strftime("%Y-%m-%d"),
                   "label": f"{t_rel.day} {t_rel.strftime('%B %Y')} EIA crude release"},
        "current": {
            "crude_stock": _r(target.get("crude"), 1), "cushing": _r(target.get("cushing"), 1),
            "cushing_wow": _r(target.get("cushing_wow"), 1), "refutil": _r(target.get("refutil"), 1),
            "crude_z": _r(target.get("crude_z"), 2), "days_supply": _r(target.get("days_supply"), 1),
            "season": target.get("season"), "vol_regime": t_vol,
            "wti_struct": target.get("wti_struct"), "product_alignment": target.get("product_alignment"),
        },
        "prediction": prediction,
        "impact_curve": {"beta_pct_per_mmbbl": round(beta * 100, 4),
                         "beta_overall_pct_per_mmbbl": round(beta_ov * 100, 4),
                         "sigma_mmbbl": round(sigma, 2), "points": curve},
        "result": None, "comparison": None, "scorecard": None,
        # pre-release: ship the intraday MODEL (per-horizon beta/r2) only; the predicted
        # path needs the surprise and the actual path needs the print, both added on run.
        "intraday": _intraday_block(t_vol, None, False, t_rel.strftime("%Y-%m-%d")),
    }

    if not run_result:
        return snap

    # ===================================================================
    # RESULT — the actual print, the REAL surprise, verdict and cross-check.
    # ===================================================================
    actual = float(target["crude_wow"])
    surprise = float(target["surprise"])
    sz = float(target["surprise_z"]) if target.get("surprise_z") == target.get("surprise_z") else 0.0
    ctx_t = {"vol_regime": t_vol, "wti_struct": target.get("wti_struct"),
             "product_alignment": target.get("product_alignment"), "products": products}
    verdict = lib.verdict_from_surprise(surprise, sz, ctx_t, r2, n, beta)
    cross = market_crosscheck(prices, target, surprise, beta, verdict.direction)
    actual_move = cross.get("wti_reaction_pct")          # % WTI move on the print
    pred_move = round(beta * surprise * 100, 3)           # regime-implied move at the real surprise
    pred_move_ov = round(beta_ov * surprise * 100, 3)

    snap["result"] = {
        "ran_at": now_iso(), "ran_at_et": now_et(),
        "actual_wow": _r(actual, 2), "actual_stock": _r(target.get("crude"), 1),
        "real_surprise": _r(surprise, 2), "real_surprise_z": _r(sz, 2),
        "real_surprise_dir": "bullish" if surprise < 0 else "bearish" if surprise > 0 else "neutral",
        "verdict": _vdict(verdict),
        "crosscheck": cross,
        "pred_move_pct": pred_move, "pred_move_pct_overall": pred_move_ov,
        "actual_move_pct": _r(actual_move, 2),
        # the realized dot for the impact-curve chart
        "realized_point": {"surprise": _r(surprise, 2),
                           "pred_regime_pct": pred_move, "pred_overall_pct": pred_move_ov,
                           "actual_pct": _r(actual_move, 2)},
    }
    snap["comparison"] = _comparison(expected, actual, surprise, sz, lean, verdict,
                                     cross, pred_move, actual_move, r2)
    snap["scorecard"] = _scorecard(expected, actual, surprise, sz, lean, cross,
                                   pred_move, actual_move, r2)
    # full intraday: predicted path at the REAL surprise + the live actual 5-min path.
    snap["intraday"] = _intraday_block(t_vol, surprise, True, t_rel.strftime("%Y-%m-%d"))
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
    t = snap["target"]; p = snap["prediction"]
    print(f"\n=== EIA RELEASE LAB — {t['label']} (week {t['period']}) ===")
    print(f"\n  PREDICTION (as of {p['asof']}):")
    print(f"    Expected {p['expected_wow']:+.1f} MMbbl  | expected surprise ~0  | lean {p['lean']} ({p['confidence']})")
    print(f"    Catalyst R²={p['catalyst_r2']} (n={p['catalyst_n']})  beta={p['beta_pct_per_mmbbl']}%/MMbbl")
    r = snap.get("result")
    if r:
        print(f"\n  RESULT:")
        print(f"    Actual {r['actual_wow']:+.1f} MMbbl  | REAL surprise {r['real_surprise']:+.1f} "
              f"({r['real_surprise_z']:+.1f}σ, {r['real_surprise_dir']})  | verdict {r['verdict']['direction']}")
        print(f"    Predicted move {r['pred_move_pct']:+.2f}%  | actual move {r['actual_move_pct']:+.2f}%  "
              f"-> {(r['crosscheck'] or {}).get('status','?').upper()}")
        print(f"\n  {snap['comparison']['narrative']}")


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
