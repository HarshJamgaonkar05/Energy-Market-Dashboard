# ============================================================================
# Phase 3 — Strategy Backtest  (clean rebuild)
# ============================================================================
# Backtests the Phase-2 idea — relative-value MEAN-REVERSION on crude spreads —
# over the intraday 15-minute bars in the mentor's live feed. One simple, honest
# engine: estimate each spread's fair value from its own recent history, fade
# large dislocations, exit on reversion / stop / session break. Fixed one-unit
# sizing, gross PnL — the raw signal, not a leveraged book.
#
# ---- Why fair value is estimated from the data (not the Phase-2 model) ------
# The Phase-2 fair value is a DAILY regression on fundamentals (inventories,
# refinery utilisation, DXY, VIX, momentum, seasonality). It cannot price these
# intraday spreads, for three independent reasons:
#   1. Its INPUTS are absent — the feed holds only crude futures prices, none of
#      the fundamental features the regression needs, so it can't be evaluated.
#   2. Its OUTPUT level is stale — e.g. Phase-2 fair value for WTI M1-M2 ~2.18 vs
#      the live spread ~0.74; forcing it on would flag a permanent fake "cheap".
#   3. Fundamentals are daily, so over a few days the model is ~constant and can't
#      explain intraday moves (which are order-flow, not fundamentals).
# So fair value = a rolling mean of the spread itself. Phase 2 still contributes
# as CONTEXT: its validated per-structure hit-rates and the regime label are
# carried in as priors/labels (confidence + rationale), not as the price anchor.
#
# Run:
#   python Backtesting/engine.py            # one backtest pass (gross)
#   python Backtesting/engine.py --slip 0.01  # charge per-leg slippage (net too)
#   python Backtesting/engine.py --live       # re-run every 60s on the freshest data
#
# Outputs: out/trades.csv, out/trades_log.md, out/by_structure.csv, and the
# dashboard feed server/data/signal_engine.json (+ persistent signal_log.json).
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
LOCAL_DIR = HERE / "Data"                                  # committed snapshot (fallback)
LIVE_DIR = Path(r"I:\Public\Summer Interns Energy\DB")     # mentor's live company feed
OUT_DIR = HERE / "out"
SERVER_DATA = HERE.parent / "server" / "data"
REGIMES_JSON = SERVER_DATA / "regimes.json"                # current regime label (context)
PHASE2_BACKTEST = SERVER_DATA / "backtest.json"            # validated daily hit-rates (context)
FEED_JSON = SERVER_DATA / "signal_engine.json"             # dashboard feed
SIGNAL_LOG = SERVER_DATA / "signal_log.json"               # persistent journal

# ---- Strategy parameters (intentionally few) -------------------------------
LOOKBACK = 24          # bars in the rolling fair value (~6h of 15-min bars)
Z_ENTRY = 2.0          # fade when |z| >= this (a 2-sigma dislocation)
Z_EXIT = -1.5          # take profit after reverting THROUGH fair to ~1.5sigma the other side
                       #   (entry_sign*z <= this). Spreads overshoot, so exiting at fair leaves money on
                       #   the table; robustness testing (analytics/robustness.py) justified deepening
                       #   from -1.0 to -1.5 (+net every year, no extra drawdown). 5y-validated.
Z_STOP = 3.5           # stop if it stretches further to |z| >= this
MAX_HOLD_BARS = 48     # time stop: never hold a single trade longer than ~12h
SESSION_GAP_MIN = 90   # a gap to the next bar > this = session/weekend break -> flatten
MULT = 1000            # 1,000 bbl/contract -> a $1.00/bbl spread move = $1,000
INITIAL_CAPITAL = 250_000   # equity-curve baseline (display); size is fixed 1 unit
SLIP_PER_LEG = 0.0     # per-leg, per-side slippage in price units; 0 = GROSS (the brief)
# ---- Cost discipline (mirrors analytics/historical_intraday.py) -------------
# Only fade when the expected $ move back to fair (|spread-fair| x MULT) clears a
# realistic round-turn cost. ASSUMED_SLIP is a design-time cost that's ALWAYS on
# (even when reporting gross) so the trade set is one we'd actually trade — it skips
# the cent-sized, low-volatility dislocations that just bleed turnover. Validated on
# 5y of 15-min history: net@1c $50k -> $1.12M, net drawdown -$242k -> -$16k.
ASSUMED_SLIP = 0.01    # per-leg cost the entry gate must clear (independent of --slip reporting)
EDGE_COST_MULT = 2.0   # require expected capture >= this x round-turn cost
# ---- Position scaling (mirrors analytics/historical_intraday.py) ------------
# Add a 2nd unit on the deepest (>=2.75sigma) dislocations — the highest-conviction
# stretches. Validated on 5y: net $1.98M -> $2.62M, profitable every year. Toggle.
SCALE_IN = False
SCALE_ADD_Z = 2.75     # add a unit when |z| deepens past this (same side) while in a position
SCALE_MAX_UNITS = 2    # cap on total units per trade
# ---- LIVE panel display mode -----------------------------------------------
# True (default): live mirrors the DISCIPLINED, actually-tradeable strategy (cost gate
# + the 3 proven structures) that the 5-year historical backtest validates — a small
# but honestly-profitable demo on the few-day feed.
# False: the FULL ungated book (all 7 structures, every >=2sigma signal, no gate) —
# a bigger gross headline but a WORSE after-cost result (the extra trades lose money
# once you pay to trade them). Available on request; not the default.
LIVE_DISCIPLINED = True
LIVE_REFRESH_SEC = 60

# ---- Tradeable structures (crude-only — what the feed contains) -------------
# M1/M2/M3 = 1st/2nd/3rd nearest contract during this June-2026 window.
# `active` = traded. Over 5y of 15-min history the Brent calendars/fly and the WTI
# front calendar (M1-M2) had no persistent net edge after costs in either the 2021-23
# train or the 2024+ test half (PF ~0.9-1.2); only Brent-WTI arb, the WTI fly and WTI
# M2-M3 survive costs in both. We evaluate all seven but trade only those three.
STRUCTURES = {
    "WTI_M1M2":   {"label": "WTI Jul/Aug (M1-M2)",   "legs": [("CL_N26", 1), ("CL_Q26", -1)], "phase2": "wti_m1m2", "active": False},
    "WTI_M2M3":   {"label": "WTI Aug/Sep (M2-M3)",   "legs": [("CL_Q26", 1), ("CL_U26", -1)], "phase2": "wti_m1m2", "active": True},
    "WTI_FLY":    {"label": "WTI Jul/Aug/Sep fly",   "legs": [("CL_N26", 1), ("CL_Q26", -2), ("CL_U26", 1)], "phase2": "wti_fly", "active": True},
    "BRENT_M1M2": {"label": "Brent Aug/Sep (M1-M2)", "legs": [("CO_Q26", 1), ("CO_U26", -1)], "phase2": "brent_m1m2", "active": False},
    "BRENT_M2M3": {"label": "Brent Sep/Oct (M2-M3)", "legs": [("CO_U26", 1), ("CO_V26", -1)], "phase2": "brent_m1m2", "active": False},
    "BRENT_FLY":  {"label": "Brent Aug/Sep/Oct fly", "legs": [("CO_Q26", 1), ("CO_U26", -2), ("CO_V26", 1)], "phase2": "wti_fly", "active": False},
    "BRENT_WTI":  {"label": "Brent-WTI arb (Aug)",   "legs": [("CO_Q26", 1), ("CL_Q26", -1)], "phase2": "brent_wti", "active": True},
}

if LIVE_DISCIPLINED:
    STRATEGY_NAME = "RV mean-reversion + cost gate (Phase-2 idea, intraday)"
    STRATEGY_DESC = ("Estimate each crude spread's fair value as a rolling mean of its own recent "
                     "history; fade a >=2sigma dislocation ONLY when the expected $ move to fair clears "
                     "2x realistic cost (volatility-adaptive cost gate); ride the reversion through fair to "
                     "~1.5sigma overshoot (z<=-1.5), with a 3.5sigma stop, a 12h time stop, or a session break. "
                     "Universe pruned to the 3 structures with a persistent post-cost edge. 1 unit/trade "
                     "(optional 2-unit scaling on the deepest >=2.75sigma dislocations). Gross.")
else:
    STRATEGY_NAME = "RV mean-reversion — full live book (Phase-2 idea, intraday)"
    STRATEGY_DESC = ("Estimate each crude spread's fair value as a rolling mean of its own recent history; "
                     "fade EVERY >=2sigma dislocation across ALL 7 WTI & Brent crude structures (no cost "
                     "gate — full live book); ride the reversion through fair to ~1sigma overshoot (z<=-1.0), "
                     "with a 3.5sigma stop, a 12h time stop, or a session break. Fixed 1 unit/trade, gross. "
                     "(Bigger gross, but a worse after-cost result than the disciplined 3-structure strategy "
                     "proven over 5 years in the Historical BT panel.)")


# ============================================================================
# Data — snapshot the live SQLite (incl. WAL), checkpoint, read closes
# ============================================================================
def _snapshot_closes(db_path: Path) -> dict:
    """Copy db(+wal/shm), checkpoint, return {table: close-series}. The freshest
    bars live in the write-ahead log, so we must snapshot and checkpoint to see them."""
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
    """(closes_df, mode, source). Use the live company feed when reachable and at least
    as deep as the local snapshot; otherwise fall back to the committed ./Data copy."""
    local_db, live_db = _latest_db(LOCAL_DIR), _latest_db(LIVE_DIR)
    local = _snapshot_closes(local_db) if local_db else {}
    live = {}
    if live_db is not None:
        try: live = _snapshot_closes(live_db)
        except Exception: live = {}
    depth = lambda f: max((len(s) for s in f.values()), default=0)
    if depth(live) >= depth(local) and depth(live) > 0:
        frames, mode, src = live, "live", str(live_db)
    else:
        frames, mode, src = local, "local", str(local_db) if local_db else "(none)"
    if not frames:
        raise SystemExit("No market data in ./Data or the live feed")
    return pd.DataFrame(frames).sort_index(), mode, src


def build_spread(closes, legs):
    """Signed sum of leg closes (only on bars where every leg traded)."""
    cols = [t for t, _ in legs]
    if any(c not in closes.columns for c in cols):
        return pd.Series(dtype=float)
    sub = closes[cols].dropna()
    if sub.empty:
        return pd.Series(dtype=float)
    return sum(sub[t] * q for t, q in legs)


# ============================================================================
# Phase-2 context (labels & priors only — NOT the price reference)
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


def confidence_score(edge, abs_z):
    """0-100: mostly the validated historical hit-rate, lifted by how stretched the spread is."""
    return int(round(100 * (0.6 * edge + 0.4 * min(1.0, abs_z / 3.0))))


# ============================================================================
# Backtest one structure
# ============================================================================
def backtest_structure(name, meta, closes, regime, edges):
    spread = build_spread(closes, meta["legs"])
    if len(spread) < LOOKBACK + 3:
        return [], None
    df = pd.DataFrame({"spread": spread})
    df["mean"] = df["spread"].rolling(LOOKBACK).mean()        # fair value = rolling mean
    df["std"] = df["spread"].rolling(LOOKBACK).std()
    df["z"] = (df["spread"] - df["mean"]) / df["std"]         # dislocation in sigma
    df = df.dropna(subset=["mean", "std", "z"])
    df = df[df["std"] > 0]
    if df.empty:
        return [], None

    idx = df.index
    gap_next = (idx.to_series().diff().shift(-1) > pd.Timedelta(minutes=SESSION_GAP_MIN)).fillna(False)
    gap_next.iloc[-1] = False                                 # last bar stays OPEN, not forced flat

    edge, edge_src = edge_for(meta["phase2"], edges)
    contracts = sum(abs(q) for _, q in meta["legs"])
    cost = SLIP_PER_LEG * 2 * contracts * MULT                # round-turn slippage (0 in gross)
    # min $ capture to take a trade (0 = gate OFF, i.e. the full ungated live book)
    gate_cost = EDGE_COST_MULT * 2 * contracts * ASSUMED_SLIP * MULT if LIVE_DISCIPLINED else 0.0

    def legs_at(ts):
        return {t: round(float(closes[t].get(ts, float("nan"))), 3) for t, _ in meta["legs"]}

    trades, pos = [], None
    for i, (ts, row) in enumerate(df.iterrows()):
        z, sp, fv = float(row["z"]), float(row["spread"]), float(row["mean"])
        if pos is None:
            if abs(z) >= Z_ENTRY and abs(sp - fv) * MULT >= gate_cost:   # fade only if $ edge clears cost
                pos = {"dir": "LONG" if z <= -Z_ENTRY else "SHORT", "i": i, "t": ts,
                       "sp": sp, "entries": [sp], "z": z, "legs": legs_at(ts), "mae": 0.0, "mfe": 0.0}
            continue
        sign = 1.0 if pos["dir"] == "LONG" else -1.0
        entry_sign = -sign                                    # +1 if SHORT (entered rich), -1 if LONG
        # scale in: add a unit on a deeper, same-side dislocation (highest conviction)
        if (SCALE_IN and len(pos["entries"]) < SCALE_MAX_UNITS and abs(z) >= SCALE_ADD_Z
                and (z < 0) == (pos["dir"] == "LONG")):
            pos["entries"].append(sp)
        upnl = sign * sum(sp - e for e in pos["entries"]) * MULT
        pos["mae"], pos["mfe"] = min(pos["mae"], upnl), max(pos["mfe"], upnl)
        held = i - pos["i"]

        hit_target = entry_sign * z <= Z_EXIT                 # reverted through to fair
        hit_stop = abs(z) >= Z_STOP                           # stretched further -> wrong
        hit_time = held >= MAX_HOLD_BARS
        forced = bool(gap_next.iloc[i])
        if hit_target or hit_stop or hit_time or forced:
            reason = ("target" if hit_target else "stop" if hit_stop
                      else "time_stop" if hit_time else "session_end")
            units = len(pos["entries"])
            gross = sign * sum(sp - e for e in pos["entries"]) * MULT
            trade_cost = cost * units
            trades.append({
                "structure": name, "label": meta["label"], "strategy": STRATEGY_NAME,
                "phase2Key": meta["phase2"], "regime": regime, "direction": pos["dir"],
                "entryTime": pos["t"].strftime("%Y-%m-%d %H:%M"),
                "exitTime": ts.strftime("%Y-%m-%d %H:%M"),
                "entrySpread": round(pos["sp"], 4), "exitSpread": round(sp, 4),
                "entryZ": round(pos["z"], 2), "exitZ": round(z, 2),
                "entryLegs": pos["legs"], "exitLegs": legs_at(ts),
                "holdBars": held, "holdMin": int((ts - pos["t"]).total_seconds() // 60),
                "contracts": contracts, "units": units, "pnl": round(gross, 2),
                "cost": round(trade_cost, 2), "netPnl": round(gross - trade_cost, 2),
                "mae": round(pos["mae"], 2), "mfe": round(pos["mfe"], 2),
                "exitReason": reason, "histHitRate": round(edge, 3), "edgeSource": edge_src,
                "confidence": confidence_score(edge, abs(pos["z"])),
            })
            pos = None

    open_pos = None
    if pos is not None:
        ts, sp, z = df.index[-1], float(df["spread"].iloc[-1]), float(df["z"].iloc[-1])
        sign = 1.0 if pos["dir"] == "LONG" else -1.0
        open_pos = {
            "structure": name, "label": meta["label"], "direction": pos["dir"],
            "entryTime": pos["t"].strftime("%Y-%m-%d %H:%M"), "asOf": ts.strftime("%Y-%m-%d %H:%M"),
            "entrySpread": round(pos["sp"], 4), "curSpread": round(sp, 4),
            "entryZ": round(pos["z"], 2), "curZ": round(z, 2),
            "holdBars": int(len(df) - 1 - pos["i"]), "units": len(pos["entries"]),
            "unrealizedPnl": round(sign * sum(sp - e for e in pos["entries"]) * MULT, 2),
            "regime": regime, "confidence": confidence_score(edge, abs(pos["z"])),
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


def _counts(rows, key):
    out = {}
    for r in rows:
        out[r[key]] = out.get(r[key], 0) + 1
    return out


def summarize(all_trades, curve):
    n = len(all_trades)
    pnl = sum(t["pnl"] for t in all_trades)
    net = sum(t["netPnl"] for t in all_trades)
    costs = sum(t["cost"] for t in all_trades)
    wins = [t for t in all_trades if t["pnl"] > 0]
    losses = [t for t in all_trades if t["pnl"] <= 0]
    gw, gl = sum(t["pnl"] for t in wins), -sum(t["pnl"] for t in losses)
    # Net (after-cost) per-trade figures — equal the gross ones at slippage 0.
    nwins = [t for t in all_trades if t["netPnl"] > 0]
    nlosses = [t for t in all_trades if t["netPnl"] <= 0]
    pnls = np.array([t["pnl"] for t in all_trades], float) if n else np.array([])
    sharpe = float(pnls.mean() / pnls.std()) if n > 1 and pnls.std() > 0 else 0.0
    out = {
        "trades": n, "grossPnl": round(pnl, 2), "netPnl": round(net, 2), "costs": round(costs, 2),
        "winRate": round(len(wins) / n, 4) if n else 0.0,
        "avgWin": round(gw / len(wins), 2) if wins else 0.0,
        "avgLoss": round(-gl / len(losses), 2) if losses else 0.0,
        "avgNetWin": round(sum(t["netPnl"] for t in nwins) / len(nwins), 2) if nwins else 0.0,
        "avgNetLoss": round(sum(t["netPnl"] for t in nlosses) / len(nlosses), 2) if nlosses else 0.0,
        "profitFactor": round(gw / gl, 3) if gl > 0 else None,
        "expectancy": round(pnl / n, 2) if n else 0.0,
        "netExpectancy": round(net / n, 2) if n else 0.0,
        "perTradeSharpe": round(sharpe, 3),
        "avgHoldMin": round(float(np.mean([t["holdMin"] for t in all_trades])), 1) if n else 0.0,
        "maxDrawdown": max_drawdown(curve),
        "endingEquity": round(INITIAL_CAPITAL + pnl, 2), "initialCapital": INITIAL_CAPITAL,
        "byExitReason": _counts(all_trades, "exitReason"), "byDirection": _counts(all_trades, "direction"),
    }
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
            "winRate": round(len(wins) / len(ts), 3), "pnl": round(sum(t["pnl"] for t in ts), 2),
            "profitFactor": round(gw / gl, 3) if gl > 0 else None,
            "avgHoldMin": round(float(np.mean([t["holdMin"] for t in ts])), 1),
            "histHitRate": ts[0]["histHitRate"],
        }
    return out


# ============================================================================
# Signal log (persistent opportunity journal)
# ============================================================================
def rationale(direction, abs_z, regime, edge, src):
    side = "cheap" if direction == "LONG" else "rich"
    return (f"Faded a {abs_z:.1f}sigma {side} dislocation from the rolling fair value in the "
            f"{regime} regime. Phase-2 reversion hit-rate ~{round(edge*100)}% ({src}).")


def signals_from(all_trades, open_positions, regime):
    out = []
    for t in all_trades:
        out.append({
            "id": f'{t["structure"]}@{t["entryTime"]}', "timestamp": t["entryTime"],
            "regime": t["regime"], "instrument": t["structure"], "label": t["label"],
            "direction": t["direction"],
            "rationale": rationale(t["direction"], abs(t["entryZ"]), t["regime"], t["histHitRate"], t["edgeSource"]),
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
    cols = ["structure", "label", "strategy", "phase2Key", "regime", "direction", "entryTime",
            "exitTime", "holdBars", "holdMin", "entrySpread", "exitSpread", "entryZ", "exitZ",
            "contracts", "pnl", "cost", "netPnl", "mae", "mfe", "exitReason", "histHitRate",
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
    net = (f" · net ${summary['netPnl']:,.0f} (costs ${summary['costs']:,.0f})"
           if summary["costs"] > 0 else "")
    lines = [
        "# Trade Log — Phase-3 backtest (RV mean-reversion, intraday)", "",
        f"_Strategy: {STRATEGY_NAME}. Data: **{mode}**. Regime: **{regime}**. "
        f"Fixed 1 unit/trade, {'net of slippage' if summary['costs'] > 0 else 'gross (slippage 0)'}._", "",
        f"**{summary['trades']} trades · gross ${summary['grossPnl']:,.0f}{net} · "
        f"win {summary['winRate']*100:.0f}% · PF {summary['profitFactor']} · "
        f"exp ${summary['expectancy']:,.0f}/trade · max DD ${summary['maxDrawdown']:,.0f}**", "",
        "Each trade: the setup, the legs with fills, the signal, the exit and the gross PnL.", "",
        "---", "",
    ]
    for i, t in enumerate(sorted(all_trades, key=lambda x: x["entryTime"]), 1):
        legs = ", ".join(f"{k} {v}->{t['exitLegs'].get(k)}" for k, v in t["entryLegs"].items())
        lines += [
            f"### {i}. {t['label']} — {t['direction']}  ({t['pnl']:+,.0f} USD)",
            f"- **Setup:** dislocated to {t['entryZ']:+.2f}sigma "
            f"({'cheap' if t['direction']=='LONG' else 'rich'}) -> fade · regime {t['regime']} · "
            f"hist. edge {t['histHitRate']*100:.0f}% · confidence {t['confidence']}/100",
            f"- **Legs (entry->exit):** {legs}",
            f"- **In:** {t['entryTime']} @ {t['entrySpread']}   **Out:** {t['exitTime']} @ {t['exitSpread']} "
            f"(z {t['exitZ']:+.2f}, {t['exitReason']})",
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
    regime, edges = current_regime(), phase2_edges()
    first_bar = closes.index[0].strftime("%Y-%m-%d %H:%M")
    last_bar = closes.index[-1].strftime("%Y-%m-%d %H:%M")

    all_trades, open_positions = [], []
    for name, meta in STRUCTURES.items():
        if LIVE_DISCIPLINED and not meta.get("active", True):  # disciplined: trade only proven 3
            continue                                            # full-book mode: trade all 7
        trades, open_pos = backtest_structure(name, meta, closes, regime, edges)
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
                     "params": {"lookback": LOOKBACK, "zEntry": Z_ENTRY, "zExit": Z_EXIT,
                                "zStop": Z_STOP, "maxHoldBars": MAX_HOLD_BARS, "mult": MULT,
                                "slipPerLeg": SLIP_PER_LEG, "assumedSlip": ASSUMED_SLIP,
                                "edgeCostMult": EDGE_COST_MULT if LIVE_DISCIPLINED else 0.0,
                                "costGate": LIVE_DISCIPLINED, "scaleIn": SCALE_IN,
                                "scaleAddZ": SCALE_ADD_Z, "scaleMaxUnits": SCALE_MAX_UNITS,
                                "activeStructures": sorted(k for k, m in STRUCTURES.items()
                                                           if not LIVE_DISCIPLINED or m.get("active", True))}},
        "summary": summary, "byStructure": by_structure, "equityCurve": curve,
        "trades": sorted(all_trades, key=lambda t: t["entryTime"], reverse=True),
        "openPositions": open_positions, "signalLog": journal, "openCount": len(open_positions),
    }
    safe_write(FEED_JSON, json.dumps(feed, indent=1))
    net = f" | net ${summary['netPnl']:,.0f}" if summary["costs"] > 0 else ""
    print(f"[{generated_at}] mode={mode} {first_bar}->{last_bar} ({len(closes)} bars) | "
          f"trades {summary['trades']} | gross ${summary['grossPnl']:,.0f}{net} | "
          f"win {summary['winRate']*100:.0f}% | PF {summary['profitFactor']} | "
          f"exp ${summary['netExpectancy' if summary['costs'] > 0 else 'expectancy']:,.0f} | "
          f"DD ${summary['maxDrawdown']:,.0f} | open {len(open_positions)}")
    return feed


def main():
    global SLIP_PER_LEG
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="re-run continuously on the freshest data")
    ap.add_argument("--interval", type=int, default=LIVE_REFRESH_SEC)
    ap.add_argument("--slip", type=float, default=SLIP_PER_LEG,
                    help="per-leg slippage in price units (e.g. 0.01); reports net alongside gross")
    args = ap.parse_args()
    SLIP_PER_LEG = args.slip
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
