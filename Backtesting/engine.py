# ============================================================================
# Phase 3 — LIVE regime-driven strategy engine (intraday SQLite feed)
# ============================================================================
# The SAME regime-driven core as the 5-year backtests (analytics/regime_strategy.py),
# run on the mentor's live 15-minute feed. The Phase-2 regime model DRIVES the book:
#   • Fair value = a regime-parameterized adaptive EWMA (the local equilibrium the spread
#     reverts to) — NOT a fixed rolling mean.
#   • Signal = a regime-conditioned z (residual vs same-vol-state expanding std + vol floor).
#   • Per-vol-state z-thresholds / max-hold (× the regime half-life), vol-target sizing,
#     a cost gate, and a shock layer (de-lever / stand-aside through vol-regime step-ups,
#     plus the always-on session flatten).
#   • A regime-BLIND control (fixed-span EWMA, global dispersion, fixed z=2 / 1 unit, no
#     shock layer) runs head-to-head so the panel shows the regime model's contribution.
#
# Over a SHORT live window the daily regime is ~constant, so the cross-regime conditioning is
# naturally dormant here (one vol-state present) — but it is the SAME engine the 5-year daily
# and intraday backtests validate. (This inverts the old design note "why we DON'T use the
# regime model intraday": we now do — see Backtesting/IDEATION.md.)
#
# Run:
#   python Backtesting/engine.py            # one pass (gross)
#   python Backtesting/engine.py --slip 0.01  # charge per-leg slippage (net too)
#   python Backtesting/engine.py --live       # re-run every 60s on the freshest data
#
# Outputs: out/trades.csv, out/trades_log.md, out/by_structure.csv, the dashboard feed
# server/data/signal_engine.json (+ persistent signal_log.json).
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

HERE = Path(__file__).resolve().parent
ANALYTICS = HERE.parent / "analytics"
sys.path.insert(0, str(ANALYTICS))
import regime_strategy as rs   # noqa: E402

# ---- Paths -----------------------------------------------------------------
LOCAL_DIR = HERE / "Data"                                  # committed snapshot (fallback)
LIVE_DIR = Path(r"I:\Public\Summer Interns Energy\DB")     # mentor's live company feed
OUT_DIR = HERE / "out"
SERVER_DATA = HERE.parent / "server" / "data"
REGIMES_JSON = SERVER_DATA / "regimes.json"
PHASE2_BACKTEST = SERVER_DATA / "backtest.json"
FEED_JSON = SERVER_DATA / "signal_engine.json"
SIGNAL_LOG = SERVER_DATA / "signal_log.json"

MULT = 1000
INITIAL_CAPITAL = 250_000
REF_SLIP = 0.01
MIN_EDGE = 0.15
LIVE_REFRESH_SEC = 60
SLOW_HL = 96
FV_SPAN_MULT, FV_MIN_HL, FV_MAX_HL = 2.5, 16.0, 28.0
BAR_VOL_WIN = 8

# Tradeable structures (crude-only — what the feed contains). M1/M2/M3 = 1st/2nd/3rd
# nearest contract in this June-2026 window. The whitelist is data-driven (validated
# Phase-2 reversion edge ≥ MIN_EDGE); the regime engine + cost gate manage the rest.
STRUCTURES = {
    "WTI_M1M2":   {"label": "WTI Jul/Aug (M1-M2)",   "legs": [("CL_N26", 1), ("CL_Q26", -1)], "phase2": "wti_m1m2"},
    "WTI_M2M3":   {"label": "WTI Aug/Sep (M2-M3)",   "legs": [("CL_Q26", 1), ("CL_U26", -1)], "phase2": "wti_m1m2"},
    "WTI_FLY":    {"label": "WTI Jul/Aug/Sep fly",   "legs": [("CL_N26", 1), ("CL_Q26", -2), ("CL_U26", 1)], "phase2": "wti_fly"},
    "BRENT_M1M2": {"label": "Brent Aug/Sep (M1-M2)", "legs": [("CO_Q26", 1), ("CO_U26", -1)], "phase2": "brent_m1m2"},
    "BRENT_M2M3": {"label": "Brent Sep/Oct (M2-M3)", "legs": [("CO_U26", 1), ("CO_V26", -1)], "phase2": "brent_m1m2"},
    "BRENT_FLY":  {"label": "Brent Aug/Sep/Oct fly", "legs": [("CO_Q26", 1), ("CO_U26", -2), ("CO_V26", 1)], "phase2": "wti_fly"},
    "BRENT_WTI":  {"label": "Brent-WTI arb (Aug)",   "legs": [("CO_Q26", 1), ("CL_Q26", -1)], "phase2": "brent_wti"},
}

STRATEGY_NAME = "Regime-driven RV mean-reversion (live, intraday)"
STRATEGY_DESC = (
    "The Phase-2 regime model drives an intraday relative-value book: fair value = a regime-"
    "parameterized adaptive EWMA, signal = a regime-conditioned z, with per-vol-state thresholds, "
    "vol-target sizing, a cost gate and a shock layer (de-lever / stand-aside through vol-regime "
    "step-ups). A regime-blind control runs alongside. Over a short live window the daily regime is "
    "constant, so the conditioning is dormant — but it is the same engine validated over 5 years."
)


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
        st = cur.get("states", {})
        return {"label": cur.get("label", "Unknown"), "rid": cur.get("regimeId", "unknown"),
                "vol": (st.get("volatility") or {}).get("state", "Normal")}
    except Exception:
        return {"label": "Unknown", "rid": "unknown", "vol": "Normal"}


def phase2_edges():
    try:
        return json.loads(PHASE2_BACKTEST.read_text(encoding="utf8")).get("spreads", {})
    except Exception:
        return {}


def validated_intraday_set():
    """The DEPLOYABLE structures from the 5-year INTRADAY backtest — those with a positive
    AFTER-COST edge on its out-of-sample train window. The live book trades only these, so it
    never trades a structure that is gross-positive but doesn't clear costs (the calendar/fly
    churn). Empty set (no backtest yet) → fall back to the daily-edge gate."""
    try:
        d = json.loads((SERVER_DATA / "historical_intraday.json").read_text(encoding="utf8"))
        p = d.get("strategy", {}).get("params", {})
        return set(p.get("deployableStructures") or p.get("tradedStructures", []))
    except Exception:
        return set()


def edge_for(key, edges):
    bt = edges.get(key)
    if bt and bt.get("sufficient"):
        return round(float(bt["hitRate"]), 3), float(bt.get("edge") or 0.0)
    return None, 0.0


def confidence_score(edge, abs_z, severity):
    """0-100: validated hit-rate, lifted by how stretched the spread is, cut by shock severity."""
    base = 0.6 * (edge or 0.6) + 0.4 * min(1.0, abs_z / 3.0)
    return int(round(100 * base * (1.0 - 0.5 * severity)))


# ============================================================================
# Build one structure's frame (segment-aware) + the aware/blind fair values
# ============================================================================
def build_frame(spread: pd.Series, regime: dict, cfg):
    if len(spread) < cfg.warmup + 10:
        return None
    idx = spread.index
    gap = idx.to_series().diff() > pd.Timedelta(minutes=90)
    seg = gap.fillna(True).cumsum().to_numpy()
    n = len(spread)
    vol_state = np.array([regime["vol"]] * n, dtype=object)
    regime_id = np.array([regime["rid"]] * n, dtype=object)
    regime_lab = np.array([regime["label"]] * n, dtype=object)

    slow = rs.fixed_ewma(spread, SLOW_HL, seg)
    dev = (spread - slow).to_numpy(float)
    hl = rs.trailing_halflife(dev, vol_state, seg, cfg)
    fv_span = np.clip(FV_SPAN_MULT * hl, FV_MIN_HL, FV_MAX_HL)
    fv_aware = rs.adaptive_ewma(spread.to_numpy(float), fv_span, seg)
    fv_blind = rs.fixed_ewma(spread, rs.INTRADAY_BLIND_HL, seg).to_numpy(float)
    bar_vol = (pd.Series(spread.to_numpy(float), index=idx).groupby(seg)
               .transform(lambda s: s.diff().abs().rolling(BAR_VOL_WIN, min_periods=2).mean())
               .to_numpy(float))

    common = {"vol_state": vol_state, "regime_id": regime_id, "regime": regime_lab,
              "bar_vol": bar_vol, "seg": seg}
    fa = pd.DataFrame({"spread": spread.to_numpy(float), "fv": fv_aware, **common}, index=idx)
    fb = pd.DataFrame({"spread": spread.to_numpy(float), "fv": fv_blind, **common}, index=idx)
    return fa, fb, hl


def enrich_trades(trades, closes, meta, edge):
    """Add the per-leg fills + strategy/confidence/contracts the dashboard detail shows."""
    contracts = sum(abs(q) for _, q in meta["legs"])
    out = []
    for t in trades:
        ti, to = pd.Timestamp(t["entryTime"]), pd.Timestamp(t["exitTime"])
        legs_in = {leg: round(float(closes[leg].asof(ti)), 3) if leg in closes else None for leg, _ in meta["legs"]}
        legs_out = {leg: round(float(closes[leg].asof(to)), 3) if leg in closes else None for leg, _ in meta["legs"]}
        t = dict(t)
        t.update({"strategy": STRATEGY_NAME, "phase2Key": meta["phase2"], "contracts": contracts,
                  "entryLegs": legs_in, "exitLegs": legs_out,
                  "confidence": confidence_score(edge, abs(t["entryZ"]), t.get("entrySeverity", 0.0))})
        out.append(t)
    return out


def comparison(aware_sum, blind_sum):
    return {k: {"aware": aware_sum.get(k), "blind": blind_sum.get(k)} for k in
            ["sharpe", "calmar", "maxDrawdown", "maxDrawdownPct", "cvar5", "netPnl", "grossPnl",
             "profitFactor", "trades", "pctTimeInMarket"]}


# ============================================================================
# Signal log (persistent opportunity journal)
# ============================================================================
def rationale(direction, abs_z, regime, edge):
    side = "cheap" if direction == "LONG" else "rich"
    return (f"Faded a {abs_z:.1f}sigma {side} dislocation from the regime-adaptive fair value in the "
            f"{regime} regime. Phase-2 reversion hit-rate ~{round((edge or 0.6)*100)}%.")


def signals_from(all_trades, open_positions, regime_label):
    out = []
    for t in all_trades:
        out.append({
            "id": f'{t["structure"]}@{t["entryTime"]}', "timestamp": t["entryTime"],
            "regime": t["regime"], "instrument": t["structure"], "label": t["label"],
            "direction": t["direction"],
            "rationale": rationale(t["direction"], abs(t["entryZ"]), t["regime"], t.get("histHitRate")),
            "confidence": t["confidence"], "status": "CLOSED", "performance": t["pnl"],
            "outcome": "reverted-win" if t["pnl"] > 0 else "stopped-loss",
            "exitReason": t["exitReason"], "entryZ": t["entryZ"], "histHitRate": t.get("histHitRate"),
        })
    for p in open_positions:
        out.append({
            "id": f'{p["structure"]}@{p["entryTime"]}', "timestamp": p["entryTime"],
            "regime": p["regime"], "instrument": p["structure"], "label": p["label"],
            "direction": p["direction"],
            "rationale": rationale(p["direction"], abs(p["entryZ"]), p["regime"], 0.6),
            "confidence": p.get("confidence", 60), "status": "OPEN", "performance": p["unrealizedPnl"],
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
    cols = ["structure", "label", "strategy", "phase2Key", "regime", "volState", "direction",
            "entryTime", "exitTime", "holdBars", "holdMin", "entrySpread", "exitSpread", "fairValue",
            "entryZ", "exitZ", "size", "contracts", "pnl", "cost", "netPnl", "mae", "mfe",
            "exitReason", "histHitRate", "confidence", "equityAfter"]
    try:
        with open(OUT_DIR / "trades.csv", "w", newline="", encoding="utf8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader(); eq = INITIAL_CAPITAL
            for t in sorted(all_trades, key=lambda x: x["exitTime"]):
                eq += t["pnl"]; row = dict(t); row["equityAfter"] = round(eq, 2)
                w.writerow(row)
    except PermissionError:
        print("  ! trades.csv locked — skipped", file=sys.stderr)


def write_trade_md(all_trades, summary, mode, regime_label):
    net = (f" · net ${summary['netPnl']:,.0f} (costs ${summary['costs']:,.0f})"
           if summary["costs"] > 0 else "")
    lines = [
        "# Trade Log — Phase-3 LIVE (regime-driven RV mean-reversion, intraday)", "",
        f"_Strategy: {STRATEGY_NAME}. Data: **{mode}**. Regime: **{regime_label}**. "
        f"Vol-target sizing, {'net of slippage' if summary['costs'] > 0 else 'gross (slippage 0)'}._", "",
        f"**{summary['trades']} trades · gross ${summary['grossPnl']:,.0f}{net} · "
        f"win {summary['winRate']*100:.0f}% · PF {summary['profitFactor']} · "
        f"Sharpe {summary['sharpe']} · max DD ${summary['maxDrawdown']:,.0f}**", "",
        "---", "",
    ]
    for i, t in enumerate(sorted(all_trades, key=lambda x: x["entryTime"]), 1):
        legs = ", ".join(f"{k} {v}->{t['exitLegs'].get(k)}" for k, v in t.get("entryLegs", {}).items())
        lines += [
            f"### {i}. {t['label']} — {t['direction']}  ({t['pnl']:+,.0f} USD)",
            f"- **Setup:** {t['entryZ']:+.2f}sigma ({'cheap' if t['direction']=='LONG' else 'rich'}) "
            f"-> fade · regime {t['regime']} · size {t.get('size')} · confidence {t['confidence']}/100",
            f"- **Legs (entry->exit):** {legs}",
            f"- **In:** {t['entryTime']} @ {t['entrySpread']}   **Out:** {t['exitTime']} @ {t['exitSpread']} "
            f"(z {t['exitZ']}, {t['exitReason']})",
            f"- **Held:** {t['holdBars']} bars ({t['holdMin']} min)   **MAE/MFE:** {t['mae']:+,.0f} / {t['mfe']:+,.0f}",
            "",
        ]
    safe_write(OUT_DIR / "trades_log.md", "\n".join(lines))


def write_structure_csv(by_structure):
    try:
        with open(OUT_DIR / "by_structure.csv", "w", newline="", encoding="utf8") as f:
            w = csv.writer(f)
            w.writerow(["structure", "label", "trades", "wins", "winRate", "pnl", "profitFactor", "avgSize", "histHitRate"])
            for name, s in by_structure.items():
                w.writerow([name, s["label"], s["trades"], s["wins"], s["winRate"], s["pnl"],
                            s["profitFactor"], s.get("avgSize"), s.get("histHitRate")])
    except PermissionError:
        print("  ! by_structure.csv locked — skipped", file=sys.stderr)


# ============================================================================
# One pass
# ============================================================================
def run_once(generated_at, cfg):
    closes, mode, src = load_closes()
    regime, edges = current_regime(), phase2_edges()
    validated = validated_intraday_set()
    first_bar = closes.index[0].strftime("%Y-%m-%d %H:%M")
    last_bar = closes.index[-1].strftime("%Y-%m-%d %H:%M")
    years = max((closes.index[-1] - closes.index[0]).days / 365.25, 1e-9)

    aware_trades, blind_trades, open_positions = [], [], []
    aware_pnls, blind_pnls, aware_inmkt, blind_inmkt = [], [], [], []
    size_map, sev_map, traded = {}, {}, []

    for name, meta in STRUCTURES.items():
        hit, edge = edge_for(meta["phase2"], edges)
        if hit is None or edge < MIN_EDGE:
            continue
        if validated and name not in validated:   # only trade structures with a validated intraday edge
            continue
        spread = build_spread(closes, meta["legs"])
        prepped = build_frame(spread, regime, cfg)
        if prepped is None:
            continue
        fa, fb, hl = prepped
        legs_count = sum(abs(q) for _, q in meta["legs"])
        traded.append((name, meta["label"]))

        a = rs.simulate_structure(fa, cfg, mode="aware", legs_count=legs_count,
                                  structure=name, label=meta["label"], hit_rate=hit, halflife=hl)
        b = rs.simulate_structure(fb, cfg, mode="blind", legs_count=legs_count,
                                  structure=name, label=meta["label"], hit_rate=hit, halflife=hl)
        aware_trades += enrich_trades(a["trades"], closes, meta, edge)
        blind_trades += b["trades"]
        aware_pnls.append(a["pnl"]); blind_pnls.append(b["pnl"])
        aware_inmkt.append(a["in_market"]); blind_inmkt.append(b["in_market"])
        size_map[name] = a["size"]; sev_map[name] = a["severity"]
        if a["open"]:
            op = dict(a["open"])
            op["confidence"] = confidence_score(edge, abs(op["entryZ"]), 0.0)
            open_positions.append(op)

    aware_daily = rs.portfolio_daily_pnl(aware_pnls)
    blind_daily = rs.portfolio_daily_pnl(blind_pnls)
    summary = rs.summarize(aware_trades, aware_daily, INITIAL_CAPITAL, years, MULT, REF_SLIP, "intraday")
    blind_sum = rs.summarize(blind_trades, blind_daily, INITIAL_CAPITAL, years, MULT, REF_SLIP, "intraday")
    summary["pctTimeInMarket"] = rs.pct_time_in_market(aware_inmkt)
    blind_sum["pctTimeInMarket"] = rs.pct_time_in_market(blind_inmkt)
    by_structure = rs.per_structure(aware_trades, traded)

    curve = rs.equity_from_daily(aware_daily, INITIAL_CAPITAL)
    curve_blind = rs.equity_from_daily(blind_daily, INITIAL_CAPITAL)
    journal = update_journal(signals_from(aware_trades, open_positions, regime["label"]), generated_at)

    write_trade_csv(aware_trades)
    write_trade_md(aware_trades, summary, mode, regime["label"])
    write_structure_csv(by_structure)

    sizes = (pd.concat(size_map.values(), axis=1, sort=True).mean(axis=1)
             if size_map else pd.Series(dtype=float))
    sevs = (pd.concat(sev_map.values(), axis=1, sort=True).mean(axis=1)
            if sev_map else pd.Series(dtype=float))
    sizing_series = [{"t": ts.strftime("%Y-%m-%d %H:%M"), "size": round(float(sizes[ts]), 3),
                      "severity": round(float(sevs.get(ts, 0.0)), 3)}
                     for ts in sizes.index[::4]] if len(sizes) else []

    feed = {
        "generatedAt": generated_at, "mode": mode, "live": mode == "live",
        "source": os.path.basename(src), "firstBar": first_bar, "lastBar": last_bar,
        "bars": int(len(closes)), "regime": regime["label"],
        "strategy": {"name": STRATEGY_NAME, "desc": STRATEGY_DESC,
                     "params": {"mult": MULT, "slipPerLeg": cfg.slip_per_leg, "minEdge": MIN_EDGE,
                                "bookScale": cfg.size.book_scale,
                                "assumedSlip": cfg.assumed_slip, "edgeCostMult": cfg.edge_cost_mult,
                                "blindHL": rs.INTRADAY_BLIND_HL,
                                "volStateParams": {s: vars(p) for s, p in cfg.params.items()},
                                "sizing": "vol-target (constant $-risk)",
                                "activeStructures": [t for t, _ in traded]}},
        "summary": summary,
        "blind": {"summary": blind_sum, "equityCurve": curve_blind},
        "comparison": comparison(summary, blind_sum),
        "byStructure": by_structure, "byRegime": rs.per_regime(aware_trades),
        "byVolState": rs.per_volstate(aware_trades),
        "equityCurve": curve, "equityCurveBlind": curve_blind, "sizingSeries": sizing_series,
        "trades": sorted(aware_trades, key=lambda t: t["entryTime"], reverse=True),
        "openPositions": open_positions, "signalLog": journal, "openCount": len(open_positions),
    }
    safe_write(FEED_JSON, json.dumps(feed, indent=1))
    net = f" | net ${summary['netPnl']:,.0f}" if summary["costs"] > 0 else ""
    print(f"[{generated_at}] mode={mode} {first_bar}->{last_bar} ({len(closes)} bars) | regime {regime['label']} | "
          f"aware trades {summary['trades']} gross ${summary['grossPnl']:,.0f}{net} Sharpe {summary['sharpe']} "
          f"DD ${summary['maxDrawdown']:,.0f} | blind ${blind_sum['grossPnl']:,.0f} DD ${blind_sum['maxDrawdown']:,.0f} "
          f"| open {len(open_positions)}")
    return feed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="re-run continuously on the freshest data")
    ap.add_argument("--interval", type=int, default=LIVE_REFRESH_SEC)
    ap.add_argument("--slip", type=float, default=0.0, help="per-leg slippage in price units (e.g. 0.01)")
    args = ap.parse_args()

    cfg = rs.INTRADAY_CONFIG
    cfg.slip_per_leg = args.slip
    cfg.mult = MULT
    stamp = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if args.live:
        print(f"Live mode — re-running every {args.interval}s. Ctrl-C to stop.")
        while True:
            try: run_once(stamp(), cfg)
            except Exception as e: print(f"  ! pass failed: {e}", file=sys.stderr)
            time.sleep(args.interval)
    else:
        run_once(stamp(), cfg)


if __name__ == "__main__":
    main()
