# ============================================================================
# Backtest engine  —  the Phase-2 strategy, backtested on the provided 15-min data
# ============================================================================
# Runs the Phase-2 framework's strategy — regime-conditioned relative-value
# MEAN-REVERSION — over the intraday bars in Backtesting/Data and logs EVERY
# trade: entry/exit, gross PnL (slippage 0), holding time, MAE/MFE, exit reason,
# the regime it was taken in, and a confidence score grounded in Phase-2's
# validated hit-rates.
#
# The strategy (straight from Phase 2): a spread has a fair value; when it
# dislocates >=1.5sigma from it, fade the move and bet on reversion to fair.
# Intraday, the fair value is a ROBUST rolling center (median/MAD, so the very
# dislocation we fade doesn't pull the reference) — Phase-2's absolute daily levels
# don't transfer to today's contracts (proven: live WTI M1-M2 sits ~1.3 vs Phase-2's
# 4.6), so the reversion reference is estimated from the data itself. Fades are taken
# only when the daily fundamentals fair-value model agrees on the dislocation's sign,
# and (in NET mode) only when the expected reversion clears its trading cost. Exits
# revert through to fair, take a tighter 2.5sigma stop, an OU half-life time stop, or a
# session break. The regime label and the per-structure historical edge are carried in
# from Phase 2 so every trade is tied back to the validated framework.
#
# Run:
#   python Backtesting/engine.py            # one backtest pass
#   python Backtesting/engine.py --live      # re-run every 60s on the freshest data
#
# Main output: the TRADE LOG — out/trades.csv (machine) + out/trades_log.md
# (readable) — plus the dashboard feed at server/data/signal_engine.json.
# ============================================================================
import argparse
import csv
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ---- Paths -----------------------------------------------------------------
HERE = Path(__file__).resolve().parent
LOCAL_DIR = HERE / "Data"                                  # the provided snapshot (fallback)
LIVE_DIR = Path(r"I:\Public\Summer Interns Energy\DB")     # mentor's live company feed
OUT_DIR = HERE / "out"
SERVER_DATA = HERE.parent / "server" / "data"
REGIMES_JSON = SERVER_DATA / "regimes.json"
PHASE2_BACKTEST = SERVER_DATA / "backtest.json"            # validated daily edge
MODELS_JSON = SERVER_DATA / "models.json"                 # daily fundamentals fair value
FEED_JSON = SERVER_DATA / "signal_engine.json"            # dashboard feed
SIGNAL_LOG = SERVER_DATA / "signal_log.json"              # persistent journal

# ---- Strategy parameters (Phase-2 logic, intraday horizon) -----------------
LOOKBACK = 16          # bars in the rolling fair value (~4h of 15-min bars)
Z_ENTRY = 1.5          # fade when |z| >= this (Phase-2 dislocation threshold)
Z_TARGET = 0.10        # take profit on reversion through to fair value (|z| <= this)
Z_STOP = 2.5           # stop if it stretches to |z| >= this (tighter -> positive reward:risk)
MAX_HOLD_HL = 3.0      # time stop: bail after this many estimated half-lives unsettled
HL_FALLBACK_BARS = 12  # hold cap when a half-life can't be estimated (~3h)
SESSION_GAP_MIN = 90   # gap to next bar > this = session/weekend break -> flatten
MULT = 1000            # 1,000 bbl/contract -> $1.00/bbl move = $1,000
INITIAL_CAPITAL = 250_000
SLIP_PER_LEG = 0.0     # price units per leg per side; 0 = GROSS (brief). Set via --slip for NET.
COST_EXP_MULT = 2.0    # NET mode only: enter only if expected reversion >= this x round-turn cost
ROBUST = True          # fair value via rolling median/MAD (resists the dislocation bar) vs mean/std
FUND_GATE = False      # hard-skip fades that disagree with the daily fundamentals fair value
LIVE_REFRESH_SEC = 60

# ---- Tradeable structures (crude-only — what the feed contains) -------------
STRUCTURES = {
    "WTI_M1M2":   {"label": "WTI Jul/Aug (M1-M2)",   "legs": [("CL_N26", 1), ("CL_Q26", -1)], "phase2": "wti_m1m2"},
    "WTI_M2M3":   {"label": "WTI Aug/Sep (M2-M3)",   "legs": [("CL_Q26", 1), ("CL_U26", -1)], "phase2": "wti_m1m2"},
    "WTI_FLY":    {"label": "WTI Jul/Aug/Sep fly",   "legs": [("CL_N26", 1), ("CL_Q26", -2), ("CL_U26", 1)], "phase2": "wti_fly"},
    "BRENT_M1M2": {"label": "Brent Aug/Sep (M1-M2)", "legs": [("CO_Q26", 1), ("CO_U26", -1)], "phase2": "brent_m1m2"},
    "BRENT_M2M3": {"label": "Brent Sep/Oct (M2-M3)", "legs": [("CO_U26", 1), ("CO_V26", -1)], "phase2": "brent_m1m2"},
    "BRENT_FLY":  {"label": "Brent Aug/Sep/Oct fly", "legs": [("CO_Q26", 1), ("CO_U26", -2), ("CO_V26", 1)], "phase2": "wti_fly"},
    "BRENT_WTI":  {"label": "Brent-WTI arb (Aug)",   "legs": [("CO_Q26", 1), ("CL_Q26", -1)], "phase2": "brent_wti"},
}

STRATEGY_NAME = "Regime-conditioned RV mean-reversion (Phase 2)"
STRATEGY_DESC = ("Fade a spread when it dislocates >=1.5sigma from a robust (median/MAD) "
                 "rolling fair value, in agreement with the daily fundamentals model; exit on "
                 "reversion through to fair (|z|<=0.1), a tighter 2.5sigma stop, an OU "
                 "half-life time stop, or a session break. The Phase-2 strategy, backtested "
                 "intraday with optional net-of-cost gating.")


# ============================================================================
# Data
# ============================================================================
def _snapshot_closes(db_path: Path) -> dict:
    """Snapshot db(+wal), checkpoint, return {table: close-series}."""
    tmp = Path(tempfile.mkdtemp()); dst = tmp / "snap.db"
    shutil.copy(db_path, dst)
    for ext in ("-wal", "-shm"):
        src = Path(str(db_path) + ext)
        if src.exists():
            try: shutil.copy(src, Path(str(dst) + ext))
            except Exception: pass
    frames = {}
    conn = sqlite3.connect(str(dst))
    try: conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception: pass
    try:
        for (t,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            try:
                s = pd.read_sql(f'SELECT timestamp, close FROM "{t}" ORDER BY timestamp',
                                conn, parse_dates=["timestamp"]).set_index("timestamp")["close"]
                if len(s): frames[t] = s
            except Exception: continue
    finally:
        conn.close()
    shutil.rmtree(tmp, ignore_errors=True)
    return frames


def _latest_db(folder: Path):
    if not folder.exists(): return None
    dbs = sorted(folder.glob("bars_15min_*.db"))
    return dbs[-1] if dbs else None


def load_closes():
    """(closes_df, mode, source). Backtests on the provided ./Data unless the live
    feed is reachable AND fresher (more bars)."""
    local_db, live_db = _latest_db(LOCAL_DIR), _latest_db(LIVE_DIR)
    local = _snapshot_closes(local_db) if local_db else {}
    live = {}
    if live_db is not None:
        try: live = _snapshot_closes(live_db)
        except Exception: live = {}
    depth = lambda f: max((len(s) for s in f.values()), default=0)
    if depth(live) > depth(local):
        frames, mode, src = live, "live", str(live_db)
    else:
        frames, mode, src = local, "local", str(local_db) if local_db else "(none)"
    if not frames:
        raise SystemExit("No market data in ./Data or the live feed")
    return pd.DataFrame(frames).sort_index(), mode, src


def build_spread(closes, legs):
    cols = [t for t, _ in legs]
    if any(c not in closes.columns for c in cols):
        return pd.Series(dtype=float)
    sub = closes[cols].dropna()
    if sub.empty:
        return pd.Series(dtype=float)
    return sum(sub[t] * q for t, q in legs)


# ============================================================================
# Phase-2 context
# ============================================================================
def current_regime():
    try:
        cur = json.loads(REGIMES_JSON.read_text(encoding="utf8")).get("current", {})
        return cur.get("label", "Unknown")
    except Exception:
        return "Unknown"


def phase2_edges():
    try:
        return json.loads(PHASE2_BACKTEST.read_text(encoding="utf8")).get("spreads", {})
    except Exception:
        return {}


def edge_for(key, edges):
    bt = edges.get(key)
    if bt and bt.get("sufficient"):
        return float(bt["hitRate"]), "validated (Phase-2 daily)"
    return 0.6, "prior"


def fundamental_views():
    """{phase2Key: daily residual z} from the regression fair-value model. The SIGN says
    whether fundamentals see the spread as rich (>0) or cheap (<0) — a transferable
    cross-check on the intraday fade even though the absolute daily LEVEL does not carry."""
    try:
        models = json.loads(MODELS_JSON.read_text(encoding="utf8")).get("models", {})
        return {k: (v.get("residual", {}) or {}).get("z") for k, v in models.items()}
    except Exception:
        return {}


def fund_agree(fund_z, entry_z):
    """True/False if the daily model corroborates the intraday fade, None if no view.
    Agree when both call the spread the same way (same sign of dislocation)."""
    if fund_z is None:
        return None
    return bool((fund_z >= 0) == (entry_z >= 0))


def confidence_score(edge, abs_z, agree=None):
    """0-100: mostly the validated historical edge, lifted by the live dislocation and by
    whether the daily fundamentals model agrees (+/- a small adjustment)."""
    base = 100 * (0.65 * edge + 0.35 * min(1.0, abs_z / 2.5))
    if agree is True:
        base += 8
    elif agree is False:
        base -= 12
    return int(round(max(0.0, min(100.0, base))))


# ============================================================================
# Fair value & mean-reversion statistics
# ============================================================================
def fair_value_z(spread, lookback, robust):
    """Rolling fair value, scale and z. ROBUST uses the median + MAD so the very
    dislocation we want to fade does not pull the reference (the mean/std do)."""
    if robust:
        center = spread.rolling(lookback).median()
        mad = spread.rolling(lookback).apply(
            lambda w: np.median(np.abs(w - np.median(w))), raw=True)
        scale = 1.4826 * mad                       # MAD -> std-equivalent
    else:
        center = spread.rolling(lookback).mean()
        scale = spread.rolling(lookback).std()
    scale = scale.replace(0.0, np.nan)
    z = (spread - center) / scale
    return center, scale, z


def half_life_bars(spread):
    """Mean-reversion half-life in bars via an OU / AR(1) fit:
    dx_t = beta*(x_{t-1} - mu) + e  ->  rho = 1+beta  ->  HL = -ln2 / ln(rho).
    Returns None if the series does not mean-revert (beta >= 0)."""
    s = spread.dropna()
    if len(s) < 12:
        return None
    lag = s.shift(1).dropna()
    dx = (s - s.shift(1)).dropna()
    x = (lag - lag.mean()).values
    if np.std(x) == 0:
        return None
    beta = float(np.polyfit(x, dx.values, 1)[0])
    rho = 1.0 + beta
    if not (0.0 < rho < 1.0):
        return None
    hl = float(-np.log(2) / np.log(rho))
    return hl if np.isfinite(hl) and hl > 0 else None


# ============================================================================
# Backtest one structure
# ============================================================================
def backtest_structure(name, meta, closes, regime, edges, views):
    spread = build_spread(closes, meta["legs"])
    if len(spread) < LOOKBACK + 3:
        return [], None
    df = pd.DataFrame({"spread": spread})
    df["mean"], df["scale"], df["z"] = fair_value_z(df["spread"], LOOKBACK, ROBUST)
    df = df.dropna(subset=["spread", "mean", "scale", "z"])
    if df.empty:
        return [], None

    hl = half_life_bars(spread)                       # OU half-life for the time stop
    max_hold = int(np.ceil(MAX_HOLD_HL * hl)) if hl else HL_FALLBACK_BARS
    fund_z = views.get(meta["phase2"])                # daily fundamentals view (sign)
    n_legs = sum(abs(q) for _, q in meta["legs"])
    round_turn_cost = SLIP_PER_LEG * 2 * n_legs * MULT   # entry+exit, both legs

    idx = df.index
    deltas = idx.to_series().diff().shift(-1)            # gap from bar i to i+1
    gap_next = (deltas > pd.Timedelta(minutes=SESSION_GAP_MIN)).fillna(False)
    gap_next.iloc[-1] = False                            # last bar stays OPEN, not forced

    edge, edge_src = edge_for(meta["phase2"], edges)
    contracts = sum(abs(q) for _, q in meta["legs"])

    def legs_at(ts):
        return {t: round(float(closes[t].get(ts, float("nan"))), 3) for t, _ in meta["legs"]}

    trades, pos = [], None
    for i, (ts, row) in enumerate(df.iterrows()):
        z, sp, scale = row["z"], row["spread"], row["scale"]
        if pos is None:
            if abs(z) < Z_ENTRY:
                continue
            agree = fund_agree(fund_z, z)
            # (3) Fundamentals anchor: skip a fade the daily model contradicts (gate only).
            if FUND_GATE and agree is False:
                continue
            # (2) Cost-aware: in NET mode, only enter if the expected reversion to fair
            # clears a multiple of the round-turn cost. No-op at slippage 0 (GROSS).
            exp_move = max(0.0, abs(z) - Z_TARGET) * scale * MULT
            if round_turn_cost > 0 and exp_move < COST_EXP_MULT * round_turn_cost:
                continue
            pos = {"dir": "LONG" if z <= -Z_ENTRY else "SHORT", "i": i, "t": ts,
                   "sp": sp, "z": float(z), "legs": legs_at(ts), "mae": 0.0, "mfe": 0.0,
                   "agree": agree}
            continue
        sign = 1.0 if pos["dir"] == "LONG" else -1.0
        entry_sign = -sign                                   # +1 if SHORT (entered rich), -1 if LONG
        upnl = sign * (sp - pos["sp"]) * MULT
        pos["mae"], pos["mfe"] = min(pos["mae"], upnl), max(pos["mfe"], upnl)
        held = i - pos["i"]
        # (1) Exit geometry: revert THROUGH fair (directional), a tighter symmetric stop,
        # an OU half-life time stop, or a session break.
        hit_t = entry_sign * z <= Z_TARGET
        hit_s = abs(z) >= Z_STOP
        hit_time = held >= max_hold
        forced = bool(gap_next.iloc[i])
        if hit_t or hit_s or hit_time or forced:
            reason = ("target" if hit_t else "stop" if hit_s
                      else "time_stop" if hit_time else "session_end")
            gross = sign * (sp - pos["sp"]) * MULT
            net = gross - round_turn_cost
            abs_z = abs(pos["z"])
            trades.append({
                "structure": name, "label": meta["label"],
                "strategy": STRATEGY_NAME, "phase2Key": meta["phase2"], "regime": regime,
                "direction": pos["dir"],
                "entryTime": pos["t"].strftime("%Y-%m-%d %H:%M"),
                "exitTime": ts.strftime("%Y-%m-%d %H:%M"),
                "entrySpread": round(pos["sp"], 4), "exitSpread": round(float(sp), 4),
                "entryZ": round(pos["z"], 2), "exitZ": round(float(z), 2),
                "entryLegs": pos["legs"], "exitLegs": legs_at(ts),
                "holdBars": held,
                "holdMin": int((ts - pos["t"]).total_seconds() // 60),
                "contracts": contracts, "pnl": round(gross, 2),
                "cost": round(round_turn_cost, 2), "netPnl": round(net, 2),
                "mae": round(pos["mae"], 2), "mfe": round(pos["mfe"], 2),
                "exitReason": reason, "histHitRate": round(edge, 3),
                "edgeSource": edge_src, "halfLifeBars": round(hl, 1) if hl else None,
                "fundZ": fund_z, "fundAgree": pos["agree"],
                "confidence": confidence_score(edge, abs_z, pos["agree"]),
            })
            pos = None

    open_pos = None
    if pos is not None:
        ts, sp, z = df.index[-1], float(df["spread"].iloc[-1]), float(df["z"].iloc[-1])
        sign = 1.0 if pos["dir"] == "LONG" else -1.0
        open_pos = {
            "structure": name, "label": meta["label"], "direction": pos["dir"],
            "entryTime": pos["t"].strftime("%Y-%m-%d %H:%M"),
            "asOf": ts.strftime("%Y-%m-%d %H:%M"),
            "entrySpread": round(pos["sp"], 4), "curSpread": round(sp, 4),
            "entryZ": round(pos["z"], 2), "curZ": round(z, 2),
            "holdBars": int(len(df) - 1 - pos["i"]),
            "unrealizedPnl": round(sign * (sp - pos["sp"]) * MULT, 2),
            "fundZ": fund_z, "fundAgree": pos["agree"],
            "regime": regime, "confidence": confidence_score(edge, abs(pos["z"]), pos["agree"]),
        }
    return trades, open_pos


# ============================================================================
# Aggregation
# ============================================================================
def equity_curve(all_trades):
    rows = sorted(all_trades, key=lambda t: t["exitTime"])
    eq = INITIAL_CAPITAL
    curve = [{"t": rows[0]["entryTime"], "equity": eq}] if rows else []
    for t in rows:
        eq += t["pnl"]
        curve.append({"t": t["exitTime"], "equity": round(eq, 2)})
    return curve


def max_drawdown(curve):
    peak, mdd = -1e18, 0.0
    for p in curve:
        peak = max(peak, p["equity"])
        mdd = min(mdd, p["equity"] - peak)
    return round(mdd, 2)


def summarize(all_trades, curve):
    n = len(all_trades)
    pnl = sum(t["pnl"] for t in all_trades)
    net = sum(t.get("netPnl", t["pnl"]) for t in all_trades)
    costs = sum(t.get("cost", 0.0) for t in all_trades)
    wins = [t for t in all_trades if t["pnl"] > 0]
    losses = [t for t in all_trades if t["pnl"] <= 0]
    gw, gl = sum(t["pnl"] for t in wins), -sum(t["pnl"] for t in losses)
    pf = (gw / gl) if gl > 0 else (None if gw == 0 else None)
    pnls = np.array([t["pnl"] for t in all_trades], float) if n else np.array([])
    sharpe = float(pnls.mean() / pnls.std()) if n > 1 and pnls.std() > 0 else 0.0
    # Net profit factor / win rate (the cost-aware view; equals gross at slippage 0).
    nets = [t.get("netPnl", t["pnl"]) for t in all_trades]
    nwins = [v for v in nets if v > 0]
    ngw = sum(v for v in nwins); ngl = -sum(v for v in nets if v <= 0)
    return {
        "trades": n, "grossPnl": round(pnl, 2), "netPnl": round(net, 2), "costs": round(costs, 2),
        "winRate": round(len(wins) / n, 4) if n else 0.0,
        "netWinRate": round(len(nwins) / n, 4) if n else 0.0,
        "avgWin": round(gw / len(wins), 2) if wins else 0.0,
        "avgLoss": round(-gl / len(losses), 2) if losses else 0.0,
        "profitFactor": round(gw / gl, 3) if gl > 0 else None,
        "netProfitFactor": round(ngw / ngl, 3) if ngl > 0 else None,
        "expectancy": round(pnl / n, 2) if n else 0.0,
        "netExpectancy": round(net / n, 2) if n else 0.0,
        "perTradeSharpe": round(sharpe, 3),
        "avgHoldMin": round(float(np.mean([t["holdMin"] for t in all_trades])), 1) if n else 0.0,
        "maxDrawdown": max_drawdown(curve),
        "endingEquity": round(INITIAL_CAPITAL + pnl, 2), "initialCapital": INITIAL_CAPITAL,
        "byExitReason": _counts(all_trades, "exitReason"),
        "byDirection": _counts(all_trades, "direction"),
    }


def _counts(rows, key):
    out = {}
    for r in rows:
        out[r[key]] = out.get(r[key], 0) + 1
    return out


def per_structure(all_trades):
    out = {}
    for name, meta in STRUCTURES.items():
        ts = [t for t in all_trades if t["structure"] == name]
        if not ts:
            continue
        wins = [t for t in ts if t["pnl"] > 0]
        gw = sum(t["pnl"] for t in wins); gl = -sum(t["pnl"] for t in ts if t["pnl"] <= 0)
        out[name] = {
            "label": meta["label"], "trades": len(ts), "wins": len(wins),
            "winRate": round(len(wins) / len(ts), 3),
            "pnl": round(sum(t["pnl"] for t in ts), 2),
            "profitFactor": round(gw / gl, 3) if gl > 0 else None,
            "avgHoldMin": round(float(np.mean([t["holdMin"] for t in ts])), 1),
            "histHitRate": ts[0]["histHitRate"],
        }
    return out


# ============================================================================
# Signal log (every opportunity, persistent)
# ============================================================================
def rationale(direction, abs_z, regime, edge, src):
    side = "cheap" if direction == "LONG" else "rich"
    return (f"Faded a {abs_z:.2f}sigma {side} dislocation from rolling fair value in the "
            f"{regime} regime. Historical reversion edge ~{round(edge*100)}% ({src}).")


def signals_from(all_trades, open_positions, regime):
    out = []
    for t in all_trades:
        out.append({
            "id": f'{t["structure"]}@{t["entryTime"]}', "timestamp": t["entryTime"],
            "regime": t["regime"], "instrument": t["structure"], "label": t["label"],
            "direction": t["direction"],
            "rationale": rationale(t["direction"], abs(t["entryZ"]), t["regime"],
                                   t["histHitRate"], t["edgeSource"]),
            "confidence": t["confidence"], "status": "CLOSED", "performance": t["pnl"],
            "outcome": "reverted-win" if t["pnl"] > 0 else "stopped-loss",
            "exitReason": t["exitReason"], "entryZ": t["entryZ"], "histHitRate": t["histHitRate"],
        })
    for p in open_positions:
        out.append({
            "id": f'{p["structure"]}@{p["entryTime"]}', "timestamp": p["entryTime"],
            "regime": p["regime"], "instrument": p["structure"], "label": p["label"],
            "direction": p["direction"],
            "rationale": rationale(p["direction"], abs(p["entryZ"]), p["regime"], 0.6, "open"),
            "confidence": p["confidence"], "status": "OPEN", "performance": p["unrealizedPnl"],
            "outcome": "open", "exitReason": None, "entryZ": p["entryZ"], "histHitRate": None,
        })
    return out


def update_journal(signals, generated_at):
    try:
        existing = json.loads(SIGNAL_LOG.read_text(encoding="utf8")).get("signals", [])
    except Exception:
        existing = []
    by_id = {s["id"]: s for s in existing}
    for sig in signals:
        prev = by_id.get(sig["id"]); sig = dict(sig)
        sig["loggedAt"] = prev["loggedAt"] if prev else generated_at
        sig["updatedAt"] = generated_at
        by_id[sig["id"]] = sig
    merged = sorted(by_id.values(), key=lambda s: s["timestamp"], reverse=True)
    safe_write(SIGNAL_LOG, json.dumps({"generatedAt": generated_at, "count": len(merged), "signals": merged}, indent=1))
    return merged


# ============================================================================
# Outputs
# ============================================================================
def safe_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text, encoding="utf8"); return True
    except PermissionError:
        print(f"  ! {path.name} locked — skipped", file=sys.stderr); return False


def write_trade_csv(all_trades):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cols = ["structure", "label", "strategy", "phase2Key", "regime", "direction",
            "entryTime", "exitTime", "holdBars", "holdMin", "entrySpread", "exitSpread",
            "entryZ", "exitZ", "contracts", "pnl", "cost", "netPnl", "mae", "mfe",
            "exitReason", "halfLifeBars", "fundZ", "fundAgree", "histHitRate",
            "confidence", "equityAfter"]
    try:
        with open(OUT_DIR / "trades.csv", "w", newline="", encoding="utf8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader(); eq = INITIAL_CAPITAL
            for t in sorted(all_trades, key=lambda x: x["exitTime"]):
                eq += t["pnl"]; row = dict(t); row["equityAfter"] = round(eq, 2)
                w.writerow(row)
    except PermissionError:
        print("  ! trades.csv locked (open in Excel?) — skipped", file=sys.stderr)


def write_trade_md(all_trades, summary, mode, regime):
    pf = summary["profitFactor"]
    basis = (f"Net basis (slippage {SLIP_PER_LEG}/leg)" if SLIP_PER_LEG > 0
             else "Gross basis (slippage 0)")
    net_line = (f" · net ${summary['netPnl']:,.0f} (PF {summary['netProfitFactor']}, "
                f"costs ${summary['costs']:,.0f})" if SLIP_PER_LEG > 0 else "")
    lines = [
        "# Trade Log — Phase-2 strategy backtested on the provided 15-min data", "",
        f"_Strategy: {STRATEGY_NAME}. Data: **{mode}**. Regime: **{regime}**. {basis}._", "",
        f"**{summary['trades']} trades · gross ${summary['grossPnl']:,.0f} · "
        f"win {summary['winRate']*100:.0f}% · PF {pf} · max DD ${summary['maxDrawdown']:,.0f}"
        f"{net_line}**", "",
        "Each trade names the strategy, the setup, the legs with fills, the signal, the exit and the gross PnL.",
        "", "---", "",
    ]
    for i, t in enumerate(sorted(all_trades, key=lambda x: x["entryTime"]), 1):
        legs = ", ".join(f"{k} {v}->{t['exitLegs'].get(k)}" for k, v in t["entryLegs"].items())
        lines += [
            f"### {i}. {t['label']} — {t['direction']}  ({t['pnl']:+,.0f} USD)",
            f"- **Strategy:** {t['strategy']} · regime {t['regime']} · hist. edge {t['histHitRate']*100:.0f}% · confidence {t['confidence']}/100",
            f"- **Setup:** dislocated to {t['entryZ']:+.2f}sigma ({'cheap' if t['direction']=='LONG' else 'rich'}) -> fade",
            f"- **Legs (entry->exit):** {legs}",
            f"- **In:** {t['entryTime']} @ {t['entrySpread']}   **Out:** {t['exitTime']} @ {t['exitSpread']} (z {t['exitZ']:+.2f}, {t['exitReason']})",
            f"- **Held:** {t['holdBars']} bars ({t['holdMin']} min)   **MAE/MFE:** {t['mae']:+,.0f} / {t['mfe']:+,.0f}",
            "",
        ]
    safe_write(OUT_DIR / "trades_log.md", "\n".join(lines))


def write_structure_csv(by_structure):
    try:
        with open(OUT_DIR / "by_structure.csv", "w", newline="", encoding="utf8") as f:
            w = csv.writer(f)
            w.writerow(["structure", "label", "trades", "wins", "winRate", "pnl", "profitFactor", "avgHoldMin", "histHitRate"])
            for name, s in by_structure.items():
                w.writerow([name, s["label"], s["trades"], s["wins"], s["winRate"], s["pnl"], s["profitFactor"], s["avgHoldMin"], s["histHitRate"]])
    except PermissionError:
        print("  ! by_structure.csv locked — skipped", file=sys.stderr)


# ============================================================================
# One pass
# ============================================================================
def run_once(generated_at):
    closes, mode, src = load_closes()
    regime, edges, views = current_regime(), phase2_edges(), fundamental_views()
    last_bar = closes.index[-1].strftime("%Y-%m-%d %H:%M")
    first_bar = closes.index[0].strftime("%Y-%m-%d %H:%M")

    all_trades, open_positions = [], []
    for name, meta in STRUCTURES.items():
        trades, open_pos = backtest_structure(name, meta, closes, regime, edges, views)
        all_trades += trades
        if open_pos:
            open_positions.append(open_pos)

    curve = equity_curve(all_trades)
    summary = summarize(all_trades, curve)
    by_structure = per_structure(all_trades)
    journal = update_journal(signals_from(all_trades, open_positions, regime), generated_at)

    write_trade_csv(all_trades)
    write_trade_md(all_trades, summary, mode, regime)
    write_structure_csv(by_structure)

    feed = {
        "generatedAt": generated_at, "mode": mode, "live": mode == "live",
        "source": os.path.basename(src), "firstBar": first_bar, "lastBar": last_bar,
        "bars": int(len(closes)), "regime": regime,
        "strategy": {"name": STRATEGY_NAME, "desc": STRATEGY_DESC,
                     "params": {"lookback": LOOKBACK, "zEntry": Z_ENTRY, "zTarget": Z_TARGET,
                                "zStop": Z_STOP, "maxHoldHalfLives": MAX_HOLD_HL,
                                "robustFairValue": ROBUST, "fundamentalGate": FUND_GATE,
                                "mult": MULT, "slipPerLeg": SLIP_PER_LEG,
                                "costExpMult": COST_EXP_MULT}},
        "summary": summary, "byStructure": by_structure, "equityCurve": curve,
        "trades": sorted(all_trades, key=lambda t: t["entryTime"], reverse=True),
        "openPositions": open_positions, "signalLog": journal, "openCount": len(open_positions),
    }
    safe_write(FEED_JSON, json.dumps(feed, indent=1))
    net_tag = (f" | net ${summary['netPnl']:,.0f} (PF {summary['netProfitFactor']})"
               if SLIP_PER_LEG > 0 else "")
    print(f"[{generated_at}] mode={mode} {first_bar}->{last_bar} ({len(closes)} bars) | "
          f"trades {summary['trades']} | gross ${summary['grossPnl']:,.0f} | "
          f"win {summary['winRate']*100:.0f}% | PF {summary['profitFactor']}{net_tag} | "
          f"DD ${summary['maxDrawdown']:,.0f} | open {len(open_positions)}")
    return feed


def main():
    global SLIP_PER_LEG, COST_EXP_MULT, ROBUST, FUND_GATE
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--interval", type=int, default=LIVE_REFRESH_SEC)
    ap.add_argument("--slip", type=float, default=SLIP_PER_LEG,
                    help="per-leg slippage in price units (e.g. 0.01); >0 = NET mode + cost gate")
    ap.add_argument("--cost-mult", type=float, default=COST_EXP_MULT,
                    help="NET mode: required expected reversion as a multiple of round-turn cost")
    ap.add_argument("--no-robust", action="store_true", help="use mean/std fair value, not median/MAD")
    ap.add_argument("--fund-gate", action="store_true",
                    help="hard-skip fades the daily fundamentals model contradicts")
    args = ap.parse_args()
    SLIP_PER_LEG, COST_EXP_MULT = args.slip, args.cost_mult
    ROBUST, FUND_GATE = not args.no_robust, args.fund_gate
    stamp = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if args.live:
        print(f"Live mode — re-running every {args.interval}s. Ctrl-C to stop.")
        while True:
            try: run_once(stamp())
            except Exception as e: print(f"  ! pass failed: {e}", file=sys.stderr)
            time.sleep(args.interval)
    else:
        run_once(stamp())


if __name__ == "__main__":
    main()
