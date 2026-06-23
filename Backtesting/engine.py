# ============================================================================
# Phase 3 — Strategy Backtest  (rolling-mean fair value + shock absorption)
# ============================================================================
# Backtests the Phase-2 idea — relative-value MEAN-REVERSION on crude spreads —
# over the intraday 15-minute bars in the mentor's live feed. The SIGNAL is the
# rolling-mean fair value: estimate each spread's fair value from its own recent
# history, fade large dislocations, exit on reversion / stop / session break, with
# the volatility-adaptive cost gate. Base size one unit.
#
# What is layered on (shared with the daily & intraday books via analytics/shock.py):
#   • SHOCK ABSORPTION (aware arm) — de-lever / stand aside / flatten through a
#     measured shock (a vol jump, a step UP the vol-state ladder, a z-breach, or an
#     intraday vol spike).
#   • RISK-LED METRICS — Sharpe / Sortino / Calmar / drawdown / CVaR on mark-to-market
#     daily returns (a few-day live window is a freshness demo; the 5y historical
#     backtests carry the statistical weight).
#   • A regime-BLIND control — the SAME strategy with the shock layer off, so the
#     head-to-head isolates what shock absorption contributes.
#
# ---- Why fair value is estimated from the data (not the Phase-2 model) ------
# The Phase-2 fair value is a DAILY regression on fundamentals. It cannot price these
# intraday spreads: its inputs are absent from the feed, its output level is stale, and
# fundamentals are daily so it is ~constant over a few days. So fair value = a rolling
# mean of the spread itself; Phase 2 contributes as CONTEXT (per-structure hit-rates,
# the regime label and vol-state) — priors/labels, not the price anchor.
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
ANALYTICS_DIR = HERE.parent / "analytics"
sys.path.insert(0, str(ANALYTICS_DIR))                    # share the one shock core
import shock                                              # noqa: E402

LOCAL_DIR = HERE / "Data"                                  # committed snapshot (fallback)
LIVE_DIR = Path(r"I:\Public\Summer Interns Energy\DB")     # mentor's live company feed
OUT_DIR = HERE / "out"
SERVER_DATA = HERE.parent / "server" / "data"
REGIMES_JSON = SERVER_DATA / "regimes.json"                # current regime label (context)
PHASE2_BACKTEST = SERVER_DATA / "backtest.json"            # validated daily hit-rates (context)
FEED_JSON = SERVER_DATA / "signal_engine.json"             # dashboard feed
SIGNAL_LOG = SERVER_DATA / "signal_log.json"               # persistent journal

# ---- Strategy parameters (intentionally few) — UNCHANGED -------------------
LOOKBACK = 24          # bars in the rolling fair value (~6h of 15-min bars)
Z_ENTRY = 2.0          # fade when |z| >= this (a 2-sigma dislocation)
Z_EXIT = -1.5          # take profit after reverting THROUGH fair to ~1.5sigma the other side
Z_STOP = 3.5           # stop if it stretches further to |z| >= this
MAX_HOLD_BARS = 48     # time stop: never hold a single trade longer than ~12h
SESSION_GAP_MIN = 90   # a gap to the next bar > this = session/weekend break -> flatten
MULT = 1000            # 1,000 bbl/contract -> a $1.00/bbl spread move = $1,000
INITIAL_CAPITAL = 250_000   # equity-curve baseline (display); base size is 1 unit
SLIP_PER_LEG = 0.0     # per-leg, per-side slippage in price units; 0 = GROSS (the brief)
# ---- Cost discipline — UNCHANGED -------------------------------------------
ASSUMED_SLIP = 0.01    # per-leg cost the entry gate must clear (independent of --slip reporting)
EDGE_COST_MULT = 2.0   # require expected capture >= this x round-turn cost
# ---- LIVE panel display mode -----------------------------------------------
LIVE_DISCIPLINED = True
LIVE_REFRESH_SEC = 60

# The shock policy for the live feed (short window; z_stop in lock-step with Z_STOP).
from dataclasses import replace  # noqa: E402
LIVE_SHOCK = replace(shock.LIVE_SHOCK, z_stop=Z_STOP)

# ---- Tradeable structures (crude-only — what the feed contains) -------------
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
    STRATEGY_NAME = "RV mean-reversion + cost gate + shock absorption (Phase-2 idea, intraday)"
    STRATEGY_DESC = ("Estimate each crude spread's fair value as a rolling mean of its own recent "
                     "history; fade a >=2sigma dislocation ONLY when the expected $ move to fair clears "
                     "2x realistic cost (volatility-adaptive cost gate); ride the reversion through fair to "
                     "~1.5sigma overshoot (z<=-1.5), with a 3.5sigma stop, a 12h time stop, or a session break. "
                     "Universe pruned to the 3 structures with a persistent post-cost edge. 1 unit/trade. "
                     "SHOCK ABSORPTION (aware): de-lever / stand aside / flatten through a measured shock. "
                     "A regime-BLIND control (shock off) runs alongside. Gross.")
else:
    STRATEGY_NAME = "RV mean-reversion + shock absorption — full live book (Phase-2 idea, intraday)"
    STRATEGY_DESC = ("Estimate each crude spread's fair value as a rolling mean of its own recent history; "
                     "fade EVERY >=2sigma dislocation across ALL 7 WTI & Brent crude structures (no cost "
                     "gate — full live book); ride the reversion through fair to ~1.5sigma overshoot (z<=-1.5), "
                     "with a 3.5sigma stop, a 12h time stop, or a session break. 1 unit/trade. SHOCK "
                     "ABSORPTION (aware) + a regime-BLIND control run alongside. Gross.")


# ============================================================================
# Data — snapshot the live SQLite (incl. WAL), checkpoint, read closes
# ============================================================================
def _snapshot_closes(db_path: Path) -> dict:
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


def regime_maps():
    """date -> regimeLabel, date -> vol-state, and the current vol-state (fallback)."""
    try:
        data = json.loads(REGIMES_JSON.read_text(encoding="utf8"))
    except Exception:
        return {}, {}, None
    hist = data.get("history", [])
    reg = {h["date"]: h.get("regimeLabel") for h in hist}
    vol = {h["date"]: h.get("volatility") for h in hist}
    cur_vol = (data.get("current", {}).get("states", {}).get("volatility", {}) or {}).get("state")
    return reg, vol, cur_vol


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
# Build one structure's frame (rolling-mean FV + session segmentation)
# ============================================================================
def build_frame(closes, legs, regime, reg_map, vol_map, cur_vol):
    spread = build_spread(closes, legs)
    if len(spread) < LOOKBACK + 3:
        return None
    sub = pd.DataFrame({"spread": spread}).dropna()
    idx = sub.index.to_series()
    gap = idx.diff() > pd.Timedelta(minutes=SESSION_GAP_MIN)
    sub["seg"] = gap.fillna(True).cumsum()
    g = sub.groupby("seg", sort=False)["spread"]
    mean = g.transform(lambda s: s.rolling(LOOKBACK).mean())     # rolling-mean fair value
    std = g.transform(lambda s: s.rolling(LOOKBACK).std())
    z = ((sub["spread"] - mean) / std).where(std > 0)
    bar_vol = g.transform(lambda s: s.diff().abs())
    days = sub.index.strftime("%Y-%m-%d")
    vol_state = pd.Series([vol_map.get(d) or cur_vol or "Normal" for d in days], index=sub.index)
    reg_series = pd.Series([reg_map.get(d) or regime for d in days], index=sub.index)
    return pd.DataFrame({
        "spread": sub["spread"], "fv": mean, "z": z,
        "vol_state": vol_state, "regime": reg_series, "bar_vol": bar_vol, "seg": sub["seg"],
    })


def legs_at(closes, legs, ts_str):
    ts = pd.Timestamp(ts_str)
    return {t: round(float(closes[t].get(ts, float("nan"))), 3) for t, _ in legs}


def attach_live_fields(trades, opens, meta, closes, edge, edge_src):
    """Re-attach the live-only fields the journal / markdown consume (legs, strategy,
    confidence, contracts) onto the shock-core trade & open records."""
    contracts = sum(abs(q) for _, q in meta["legs"])
    for t in trades:
        t["strategy"] = STRATEGY_NAME
        t["phase2Key"] = meta["phase2"]
        t["contracts"] = contracts
        t["edgeSource"] = edge_src
        t["confidence"] = confidence_score(edge, abs(t["entryZ"]))
        t["entryLegs"] = legs_at(closes, meta["legs"], t["entryTime"])
        t["exitLegs"] = legs_at(closes, meta["legs"], t["exitTime"])
    for p in opens:
        p["strategy"] = STRATEGY_NAME
        p["contracts"] = contracts
        p["confidence"] = confidence_score(edge, abs(p["entryZ"]))


# ============================================================================
# One arm (aware | blind)
# ============================================================================
def run_arm(frames, metas, closes, mode, edges, regime):
    trades, opens, pnls, in_markets = [], [], [], []
    for name, meta in STRUCTURES.items():
        if LIVE_DISCIPLINED and not meta.get("active", True):
            continue
        if name not in frames:
            continue
        legs = meta["legs"]
        n_legs = sum(abs(q) for _, q in legs)
        gate_cost = (EDGE_COST_MULT * 2 * n_legs * ASSUMED_SLIP * MULT) if LIVE_DISCIPLINED else 0.0
        edge, edge_src = edge_for(meta["phase2"], edges)
        res = shock.simulate(
            frames[name], mode=mode, z_entry=Z_ENTRY, z_exit=Z_EXIT, z_stop=Z_STOP,
            max_hold=MAX_HOLD_BARS, shock=LIVE_SHOCK, legs_count=n_legs, structure=name,
            label=meta["label"], hit_rate=round(edge, 3), horizon="intraday", mult=MULT,
            slip_per_leg=SLIP_PER_LEG, gate_cost=gate_cost, warmup=0,
        )
        if mode == "aware":
            attach_live_fields(res["trades"], [res["open"]] if res["open"] else [],
                               meta, closes, edge, edge_src)
        trades += res["trades"]
        if res["open"]:
            opens.append(res["open"])
        pnls.append(res["pnl"])
        in_markets.append(res["in_market"])
    return trades, opens, pnls, in_markets


# ============================================================================
# Aggregation / display helpers
# ============================================================================
def equity_curve(all_trades):
    """Realized-PnL curve at trade resolution (finer than daily — for the live panel)."""
    rows = sorted(all_trades, key=lambda t: t["exitTime"])
    eq = INITIAL_CAPITAL
    curve = [{"t": rows[0]["entryTime"], "equity": eq}] if rows else []
    for t in rows:
        eq += t["pnl"]
        curve.append({"t": t["exitTime"], "equity": round(eq, 2)})
    return curve


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
            "rationale": rationale(t["direction"], abs(t["entryZ"]), t["regime"],
                                   t.get("histHitRate") or 0.6, t.get("edgeSource", "prior")),
            "confidence": t.get("confidence"), "status": "CLOSED", "performance": t["pnl"],
            "outcome": "reverted-win" if t["pnl"] > 0 else "stopped-loss",
            "exitReason": t["exitReason"], "entryZ": t["entryZ"], "histHitRate": t.get("histHitRate"),
        })
    for p in open_positions:
        out.append({
            "id": f'{p["structure"]}@{p["entryTime"]}', "timestamp": p["entryTime"],
            "regime": p["regime"], "instrument": p["structure"], "label": p["label"],
            "direction": p["direction"],
            "rationale": rationale(p["direction"], abs(p["entryZ"]), p["regime"], 0.6, "open"),
            "confidence": p.get("confidence"), "status": "OPEN", "performance": p["unrealizedPnl"],
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
    import csv
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cols = ["structure", "label", "strategy", "phase2Key", "regime", "volState", "direction",
            "entryTime", "exitTime", "holdBars", "holdMin", "entrySpread", "exitSpread", "entryZ",
            "exitZ", "contracts", "size", "entrySeverity", "pnl", "cost", "netPnl", "mae", "mfe",
            "exitReason", "histHitRate", "confidence", "equityAfter"]
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
        "# Trade Log — Phase-3 backtest (RV mean-reversion + shock absorption, intraday)", "",
        f"_Strategy: {STRATEGY_NAME}. Data: **{mode}**. Regime: **{regime}**. "
        f"Base 1 unit/trade (shock-aware sizing), {'net of slippage' if summary['costs'] > 0 else 'gross (slippage 0)'}._", "",
        f"**{summary['trades']} trades · gross ${summary['grossPnl']:,.0f}{net} · "
        f"win {summary['winRate']*100:.0f}% · PF {summary['profitFactor']} · "
        f"Sharpe {summary['sharpe']} · max DD ${summary['maxDrawdown']:,.0f}**", "",
        "Each trade: the setup, the legs with fills, the signal, the exit and the gross PnL.", "",
        "---", "",
    ]
    for i, t in enumerate(sorted(all_trades, key=lambda x: x["entryTime"]), 1):
        legs = ", ".join(f"{k} {v}->{t.get('exitLegs', {}).get(k)}" for k, v in t.get("entryLegs", {}).items())
        sev = f" · entry severity {t.get('entrySeverity', 0):.2f} · size {t.get('size', 1):.2f}u"
        exz = t.get("exitZ")
        exz_s = f"{exz:+.2f}" if exz is not None else "n/a"
        lines += [
            f"### {i}. {t['label']} — {t['direction']}  ({t['pnl']:+,.0f} USD)",
            f"- **Setup:** dislocated to {t['entryZ']:+.2f}sigma "
            f"({'cheap' if t['direction']=='LONG' else 'rich'}) -> fade · regime {t['regime']} · "
            f"hist. edge {(t.get('histHitRate') or 0)*100:.0f}% · confidence {t.get('confidence')}/100{sev}",
            f"- **Legs (entry->exit):** {legs}",
            f"- **In:** {t['entryTime']} @ {t['entrySpread']}   **Out:** {t['exitTime']} @ {t['exitSpread']} "
            f"(z {exz_s}, {t['exitReason']})",
            f"- **Held:** {t['holdBars']} bars ({t['holdMin']} min)   **MAE/MFE:** {t['mae']:+,.0f} / {t['mfe']:+,.0f}",
            "",
        ]
    safe_write(OUT_DIR / "trades_log.md", "\n".join(lines))


def write_structure_csv(by_structure):
    import csv
    try:
        with open(OUT_DIR / "by_structure.csv", "w", newline="", encoding="utf8") as f:
            w = csv.writer(f)
            w.writerow(["structure", "label", "trades", "wins", "winRate", "pnl", "profitFactor", "avgHoldMin", "histHitRate"])
            for name, s in by_structure.items():
                w.writerow([name, s["label"], s["trades"], s["wins"], s["winRate"], s["pnl"],
                            s["profitFactor"], s.get("avgHoldMin"), s.get("histHitRate")])
    except PermissionError:
        print("  ! by_structure.csv locked — skipped", file=sys.stderr)


# ============================================================================
# One pass
# ============================================================================
def run_once(generated_at):
    closes, mode, src = load_closes()
    regime, edges = current_regime(), phase2_edges()
    reg_map, vol_map, cur_vol = regime_maps()
    first_bar = closes.index[0].strftime("%Y-%m-%d %H:%M")
    last_bar = closes.index[-1].strftime("%Y-%m-%d %H:%M")
    years = max((closes.index[-1] - closes.index[0]).days / 365.25, 1e-9)

    frames, metas = {}, {}
    for name, meta in STRUCTURES.items():
        if LIVE_DISCIPLINED and not meta.get("active", True):
            continue
        fr = build_frame(closes, meta["legs"], regime, reg_map, vol_map, cur_vol)
        if fr is not None:
            frames[name] = fr
            metas[name] = meta

    aware_trades, opens, a_pnls, a_inmkt = run_arm(frames, metas, closes, "aware", edges, regime)
    blind_trades, _, b_pnls, b_inmkt = run_arm(frames, metas, closes, "blind", edges, regime)

    aware_daily = shock.portfolio_daily_pnl(a_pnls)
    blind_daily = shock.portfolio_daily_pnl(b_pnls)
    summary = shock.summarize(aware_trades, aware_daily, a_inmkt, INITIAL_CAPITAL, years, MULT,
                              ref_slip=0.01, horizon="intraday")
    blind_summary = shock.summarize(blind_trades, blind_daily, b_inmkt, INITIAL_CAPITAL, years, MULT,
                                    ref_slip=0.01, horizon="intraday")
    structures = [(n, m["label"]) for n, m in STRUCTURES.items()]
    by_structure = shock.per_structure(aware_trades, structures)
    journal = update_journal(signals_from(aware_trades, opens, regime), generated_at)

    write_trade_csv(aware_trades)
    write_trade_md(aware_trades, summary, mode, regime)
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
                                "costGate": LIVE_DISCIPLINED, "shockAbsorption": True,
                                "activeStructures": sorted(k for k, m in STRUCTURES.items()
                                                           if not LIVE_DISCIPLINED or m.get("active", True))}},
        "summary": summary,
        "blind": {"summary": blind_summary},
        "comparison": shock.head_to_head(summary, blind_summary),
        "shock": shock.shock_summary(aware_trades),
        "byStructure": by_structure,
        "byRegime": shock.per_regime(aware_trades),
        "byVolState": shock.per_volstate(aware_trades),
        "equityCurve": equity_curve(aware_trades),
        "trades": sorted(aware_trades, key=lambda t: t["entryTime"], reverse=True),
        "openPositions": opens, "signalLog": journal, "openCount": len(opens),
    }
    safe_write(FEED_JSON, json.dumps(feed, indent=1))
    net = f" | net ${summary['netPnl']:,.0f}" if summary["costs"] > 0 else ""
    print(f"[{generated_at}] mode={mode} {first_bar}->{last_bar} ({len(closes)} bars) | AWARE "
          f"trades {summary['trades']} | gross ${summary['grossPnl']:,.0f}{net} | "
          f"win {summary['winRate']*100:.0f}% | PF {summary['profitFactor']} | "
          f"DD ${summary['maxDrawdown']:,.0f} | open {len(opens)}  ||  BLIND gross "
          f"${blind_summary['grossPnl']:,.0f} | DD ${blind_summary['maxDrawdown']:,.0f}")
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
