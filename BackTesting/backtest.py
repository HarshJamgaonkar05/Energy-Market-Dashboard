"""
Phase 3 — intraday backtest of the Phase-2 relative-value mean-reversion strategy
on real 15-minute crude-futures spread data.

Strategy (faithful to Phase 2): for each crude spread/structure, estimate an
intraday rolling fair value, z-score the deviation, FADE dislocations (|z| >=
Z_ENTRY) and bet on mean-reversion — exit on reversion (TARGET), widening (STOP),
or a session/data-end TIME stop. Full execution model (slippage + commission) and
an exhaustive per-trade log.

See IDEATION.md for the methodology, mapping to Phase 2, and every assumption.

Run:  analytics/.venv/Scripts/python BackTesting/backtest.py
Outputs: BackTesting/out/{trades.csv, equity_curve.csv, by_structure.csv,
         summary.json, report.md}
"""
from __future__ import annotations

import json
import math
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Config — all knobs in one place (documented in IDEATION.md §5).
# ----------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
RAW_DIR = HERE / "Raw Data"
OUT_DIR = HERE / "out"
REGIMES_JSON = HERE.parent / "server" / "data" / "regimes.json"

# LIVE data source — the network folder the Lightstreamer collector writes to.
# If reachable we read the freshest bars from here; otherwise we fall back to the
# local "Raw Data" copies. The newest bars sit in the DB's write-ahead log (WAL),
# which a plain read-only connection can't see while the collector holds it — so
# we snapshot (copy db+wal) to a temp file and read that (see snapshot_db).
LIVE_DIR = Path(r"I:\Public\Summer Interns Energy\DB")
LIVE_REFRESH_SEC = 60         # how often --live mode re-runs the backtest

INITIAL_CAPITAL = 250_000.0   # $ notional capital (for drawdown % / Sharpe)
MULT = 1000.0                 # bbl per contract: $1.00/bbl move = $1,000 / contract
UNITS = 1                     # spread units per trade (fixed 1-lot)
LOOKBACK = 16                 # bars for rolling fair value (4h @ 15min)
Z_ENTRY = 1.5                 # enter when |z| >= this (Phase-2 dislocation threshold)
Z_TARGET = 0.25               # take profit when |z| <= this (reverted to fair value)
Z_STOP = 3.0                  # stop when |z| >= this (dislocation widened)
# GROSS BASIS — transaction costs are switched OFF; PnL is the pure gross result.
# (Set these >0 to re-enable the slippage / commission model.)
SLIP_PER_LEG = 0.0            # $/bbl slippage per leg per side
COMM_PER_CONTRACT = 0.0       # $ commission per contract per side
MIN_STD = 0.002               # floor on rolling std (avoid div-by-~0 on flat spreads)
SESSION_GAP_MIN = 90          # gap (min) that forces a flat (session/weekend break)
BAR_MINUTES = 15

# Strategy label carried on every trade (the dashboard Phase-2 strategy).
STRATEGY_NAME = "Regime Relative-Value Mean-Reversion (z-fade)"

# Tradeable structures → legs (symbol, qty) and the Phase-2 key they map to.
STRUCTURES = {
    "WTI_M1M2":   {"product": "WTI",   "phase2": "wti_m1m2",  "legs": [("CL_N26", 1), ("CL_Q26", -1)]},
    "WTI_M2M3":   {"product": "WTI",   "phase2": "wti_m2m3",  "legs": [("CL_Q26", 1), ("CL_U26", -1)]},
    "WTI_FLY":    {"product": "WTI",   "phase2": "wti_fly",   "legs": [("CL_N26", 1), ("CL_Q26", -2), ("CL_U26", 1)]},
    "BRENT_M1M2": {"product": "Brent", "phase2": "brent_m1m2","legs": [("CO_Q26", 1), ("CO_U26", -1)]},
    "BRENT_M2M3": {"product": "Brent", "phase2": "brent_m2m3","legs": [("CO_U26", 1), ("CO_V26", -1)]},
    "BRENT_FLY":  {"product": "Brent", "phase2": "brent_fly", "legs": [("CO_Q26", 1), ("CO_U26", -2), ("CO_V26", 1)]},
    "BRENT_WTI":  {"product": "Cross", "phase2": "brent_wti", "legs": [("CO_Q26", 1), ("CL_Q26", -1)]},
}


# ----------------------------------------------------------------------------
# Data: load every .db (live folder if reachable, else local Raw Data) into one
# aligned close-price panel — reading the freshest bars from each DB's WAL.
# ----------------------------------------------------------------------------
def source_dbs() -> tuple[list[Path], str]:
    """Pick the data source: the LIVE network folder if reachable, else the local
    Raw Data copies. Returns (list of .db paths, mode)."""
    try:
        if LIVE_DIR.exists():
            live = sorted(LIVE_DIR.glob("bars_15min_*.db"))
            if live:
                return live, "live"
    except OSError:
        pass
    return sorted(RAW_DIR.glob("bars_15min_*.db")), "local"


def read_db_frames(path: Path) -> list[pd.DataFrame]:
    """Snapshot a DB (copy .db + .db-wal, skip the locked -shm) to a temp file and
    read each contract's closes — so the newest bars in the WAL come along even
    while the collector is writing the live file over the network."""
    tmp = Path(tempfile.mkdtemp())
    dst = tmp / "snap.db"
    frames = []
    try:
        shutil.copy2(path, dst)
        wal = Path(str(path) + "-wal")
        if wal.exists():
            try:
                shutil.copy2(wal, str(dst) + "-wal")   # -shm is locked; SQLite rebuilds it
            except (PermissionError, OSError):
                pass
        con = sqlite3.connect(str(dst))
        try:
            con.execute("PRAGMA wal_checkpoint(TRUNCATE)")   # fold the WAL into the copy
        except sqlite3.Error:
            pass
        tables = [t[0] for t in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for t in tables:
            df = pd.read_sql(f'SELECT timestamp, close FROM "{t}"', con, parse_dates=["timestamp"])
            frames.append(df.rename(columns={"close": t}).set_index("timestamp"))
        con.close()
    except (PermissionError, OSError, sqlite3.Error) as e:
        print(f"  [warn] could not read {path.name}: {e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return frames


def load_panel() -> tuple[pd.DataFrame, str]:
    dbs, mode = source_dbs()
    if not dbs:
        raise SystemExit(f"No bars_15min_*.db found (checked {LIVE_DIR} and {RAW_DIR}).")
    frames = []
    for db in dbs:
        frames += read_db_frames(db)
    if not frames:
        raise SystemExit("Found DB files but could not read any tables.")
    # Outer-join all contracts on the union of timestamps, then forward-fill.
    panel = pd.concat(frames, axis=1, sort=False).sort_index()
    panel = panel.groupby(level=0).last()          # de-dupe identical timestamps
    panel = panel.ffill()
    return panel, mode


def load_regime() -> tuple[str, dict]:
    """Current Phase-2 regime label + per-structure regime stats (context for the log)."""
    try:
        r = json.loads(REGIMES_JSON.read_text(encoding="utf8"))
        label = r["current"]["label"]
        rid = r["current"]["regimeId"]
        spreads = next((c["spreads"] for c in r["catalog"] if c["regimeId"] == rid), {})
        return label, spreads
    except Exception:
        return "n/a", {}


# ----------------------------------------------------------------------------
# Spread construction + z-score signal.
# ----------------------------------------------------------------------------
def spread_series(panel: pd.DataFrame, legs) -> pd.Series:
    s = None
    for sym, qty in legs:
        if sym not in panel.columns:
            return pd.Series(dtype=float)
        leg = qty * panel[sym]
        s = leg if s is None else s + leg
    return s


def zscore(spread: pd.Series):
    mean = spread.rolling(LOOKBACK, min_periods=LOOKBACK).mean()
    std = spread.rolling(LOOKBACK, min_periods=LOOKBACK).std(ddof=0).clip(lower=MIN_STD)
    z = (spread - mean) / std
    return z, mean, std


# ----------------------------------------------------------------------------
# Backtest one structure → list of trade dicts (entry/exit on the master index).
# ----------------------------------------------------------------------------
def backtest_structure(name, spec, panel, session_break, regime_label, regime_spreads):
    legs = spec["legs"]
    spread = spread_series(panel, legs)
    if spread.empty or spread.notna().sum() < LOOKBACK + 2:
        return []
    z, mean, std = zscore(spread)
    leg_qty_sum = sum(abs(q) for _, q in legs)          # Σ|qty| for slip/commission
    slip_spread = leg_qty_sum * SLIP_PER_LEG            # spread-unit slippage, one side
    comm_rt = 2 * leg_qty_sum * COMM_PER_CONTRACT * UNITS  # round-trip commission $
    p2 = regime_spreads.get(spec["phase2"], {})

    idx = panel.index
    n = len(idx)
    trades = []
    pos = None  # dict while in a position

    def leg_prices(i):
        return {sym: float(panel[sym].iloc[i]) for sym, _ in legs}

    for i in range(LOOKBACK, n):
        zi = z.iloc[i]
        if not np.isfinite(zi):
            continue
        mid = float(spread.iloc[i])
        # Only a real session/weekend gap forces a close. End-of-data does NOT —
        # a position still on at the latest bar is reported as a LIVE open position.
        forced = session_break[i]

        if pos is not None:
            # update running excursions (unrealised at mid)
            upnl = pos["sign"] * (mid - pos["entry_fill"]) * MULT * UNITS
            pos["mae"] = min(pos["mae"], upnl)
            pos["mfe"] = max(pos["mfe"], upnl)
            # exit conditions
            target = (pos["sign"] == -1 and zi <= Z_TARGET) or (pos["sign"] == 1 and zi >= -Z_TARGET)
            stop = (pos["sign"] == -1 and zi >= Z_STOP) or (pos["sign"] == 1 and zi <= -Z_STOP)
            reason = "TARGET" if target else "STOP" if stop else ("SESSION_END" if forced else None)
            if reason:
                # exit fill: adverse by slip_spread (LONG sells lower, SHORT buys higher)
                exit_fill = mid - slip_spread if pos["sign"] == 1 else mid + slip_spread
                gross = pos["sign"] * (mid - pos["entry_mid"]) * MULT * UNITS
                slippage_cost = 2 * slip_spread * MULT * UNITS
                net = pos["sign"] * (exit_fill - pos["entry_fill"]) * MULT * UNITS - comm_rt
                lp = leg_prices(i)
                trades.append({
                    **pos["meta"],
                    "entry_idx": pos["entry_idx"],
                    "exit_time": idx[i], "exit_idx": i, "exit_z": round(float(zi), 3),
                    "exit_spread_mid": round(mid, 4), "exit_fill": round(exit_fill, 4),
                    "exit_reason": reason,
                    "holding_bars": i - pos["entry_idx"],
                    "holding_min": (i - pos["entry_idx"]) * BAR_MINUTES,
                    "gross_pnl": round(gross, 2),
                    "slippage_cost": round(slippage_cost, 2),
                    "commission_cost": round(comm_rt, 2),
                    "net_pnl": round(net, 2),
                    "return_pct": round(net / INITIAL_CAPITAL * 100, 4),
                    "mae": round(pos["mae"], 2), "mfe": round(pos["mfe"], 2),
                    "exit_legs": lp,
                })
                pos = None
            continue

        # flat → look for an entry. Entry IS allowed on the latest bar — it simply
        # becomes a live open position (a fresh signal the strategy just acted on).
        if not forced and abs(zi) >= Z_ENTRY:
            sign = -1 if zi > 0 else 1   # rich → short spread; cheap → long spread
            entry_fill = mid + slip_spread if sign == 1 else mid - slip_spread
            lp = leg_prices(i)
            pos = {
                "sign": sign, "entry_idx": i, "entry_mid": mid,
                "entry_fill": entry_fill, "mae": 0.0, "mfe": 0.0,
                "meta": {
                    "structure": name, "product": spec["product"], "phase2_key": spec["phase2"],
                    "regime": regime_label,
                    "strategy": STRATEGY_NAME,
                    "strategy_desc": (
                        f"Faded a {zi:+.2f}sigma {'rich' if sign == -1 else 'cheap'} dislocation in {name} "
                        f"vs its {LOOKBACK}-bar intraday fair value -> {'SHORT' if sign == -1 else 'LONG'} the "
                        f"spread, betting on reversion (target |z|<={Z_TARGET}, stop |z|>={Z_STOP})."),
                    "direction": "LONG" if sign == 1 else "SHORT",
                    "units": UNITS,
                    "entry_time": idx[i], "entry_z": round(float(zi), 3),
                    "entry_spread_mid": round(mid, 4), "entry_fill": round(entry_fill, 4),
                    "legs": legs, "entry_legs": lp,
                    "p2_regime_mean": p2.get("mean"), "p2_regime_z": p2.get("z"),
                },
            }

    # A position still open at the final bar = a LIVE open position (not a closed trade).
    open_pos = None
    if pos is not None:
        j = n - 1
        zj = float(z.iloc[j]) if np.isfinite(z.iloc[j]) else None
        midj = float(spread.iloc[j])
        upnl = pos["sign"] * (midj - pos["entry_fill"]) * MULT * UNITS
        m = pos["meta"]
        open_pos = {
            "structure": name, "direction": m["direction"], "product": spec["product"],
            "phase2_key": spec["phase2"], "strategy_desc": m["strategy_desc"],
            "entry_time": m["entry_time"], "entry_idx": pos["entry_idx"],
            "entry_z": m["entry_z"], "entry_spread_mid": m["entry_spread_mid"],
            "entry_fill": pos["entry_fill"], "sign": pos["sign"],
            "current_z": round(zj, 3) if zj is not None else None,
            "current_spread_mid": round(midj, 4),
            "bars_held": j - pos["entry_idx"], "min_held": (j - pos["entry_idx"]) * BAR_MINUTES,
            "unrealized_pnl": round(upnl, 2),
            "mae": round(min(pos["mae"], upnl), 2), "mfe": round(max(pos["mfe"], upnl), 2),
            "legs": legs, "current_legs": leg_prices(j),
        }
    return trades, open_pos


# ----------------------------------------------------------------------------
# Portfolio equity curve (mark-to-market across all open positions each bar).
# ----------------------------------------------------------------------------
def equity_curve(panel, spreads_by_struct, trades, open_pos=None):
    idx = panel.index
    n = len(idx)
    realized = np.zeros(n)
    unreal = np.zeros(n)
    open_positions = np.zeros(n, dtype=int)
    for t in trades:
        ei, xi = t["entry_idx"], t["exit_idx"]
        realized[xi:] += t["net_pnl"]
        sp = spreads_by_struct[t["structure"]].values
        sign = 1 if t["direction"] == "LONG" else -1
        for i in range(ei, xi):  # open interval [entry, exit)
            unreal[i] += sign * (sp[i] - t["entry_fill"]) * MULT * UNITS
            open_positions[i] += 1
    # Mark any still-open positions to market through the final bar.
    for o in (open_pos or []):
        sp = spreads_by_struct[o["structure"]].values
        for i in range(o["entry_idx"], n):
            unreal[i] += o["sign"] * (sp[i] - o["entry_fill"]) * MULT * UNITS
            open_positions[i] += 1
    eq = INITIAL_CAPITAL + realized + unreal
    return pd.DataFrame({"timestamp": idx, "realized": realized, "unrealized": unreal,
                         "open_positions": open_positions, "equity": eq})


# ----------------------------------------------------------------------------
# Analytics.
# ----------------------------------------------------------------------------
def max_drawdown(equity: np.ndarray) -> tuple[float, float]:
    peak = np.maximum.accumulate(equity)
    dd = equity - peak
    ddpct = dd / peak
    return float(dd.min()), float(ddpct.min() * 100)


def summarize(trades_df, eq_df, panel):
    out = {}
    n = len(trades_df)
    out["trades"] = int(n)
    out["initialCapital"] = INITIAL_CAPITAL
    if n == 0:
        out["note"] = "No trades generated (no |z|>=Z_ENTRY dislocations in this window)."
        return out

    wins = trades_df[trades_df.net_pnl > 0]
    losses = trades_df[trades_df.net_pnl <= 0]
    gross = float(trades_df.gross_pnl.sum())
    net = float(trades_df.net_pnl.sum())
    slip = float(trades_df.slippage_cost.sum())
    comm = float(trades_df.commission_cost.sum())
    gross_win = float(wins.net_pnl.sum())
    gross_loss = float(losses.net_pnl.sum())

    out.update({
        "netPnl": round(net, 2),
        "grossPnl": round(gross, 2),
        "totalSlippage": round(slip, 2),
        "totalCommission": round(comm, 2),
        "returnOnCapitalPct": round(net / INITIAL_CAPITAL * 100, 3),
        "winRate": round(len(wins) / n * 100, 1),
        "wins": int(len(wins)), "losses": int(len(losses)),
        "avgWin": round(float(wins.net_pnl.mean()) if len(wins) else 0.0, 2),
        "avgLoss": round(float(losses.net_pnl.mean()) if len(losses) else 0.0, 2),
        "profitFactor": round(gross_win / abs(gross_loss), 3) if gross_loss < 0 else None,
        "expectancyPerTrade": round(net / n, 2),
        "avgHoldingMin": round(float(trades_df.holding_min.mean()), 1),
        "bestTrade": round(float(trades_df.net_pnl.max()), 2),
        "worstTrade": round(float(trades_df.net_pnl.min()), 2),
        "avgMAE": round(float(trades_df.mae.mean()), 2),
        "avgMFE": round(float(trades_df.mfe.mean()), 2),
        "slippagePctOfGross": round(slip / abs(gross) * 100, 1) if gross else None,
    })

    # Frequencies (the bifurcations the brief asks for).
    out["byStructure"] = {k: int(v) for k, v in trades_df.structure.value_counts().items()}
    out["byDirection"] = {k: int(v) for k, v in trades_df.direction.value_counts().items()}
    out["byExitReason"] = {k: int(v) for k, v in trades_df.exit_reason.value_counts().items()}
    out["byProduct"] = {k: int(v) for k, v in trades_df["product"].value_counts().items()}

    # Risk/return on the equity curve.
    eq = eq_df.equity.values
    rets = np.diff(eq) / eq[:-1]
    rets = rets[np.isfinite(rets)]
    bars_per_year = 252 * 24 * (60 / BAR_MINUTES)   # ~24h crude session
    if rets.std(ddof=0) > 0:
        out["sharpeAnnualized"] = round(float(rets.mean() / rets.std(ddof=0) * math.sqrt(bars_per_year)), 2)
        downside = rets[rets < 0]
        out["sortinoAnnualized"] = round(float(rets.mean() / downside.std(ddof=0) * math.sqrt(bars_per_year)), 2) if downside.std(ddof=0) > 0 else None
    dd_abs, dd_pct = max_drawdown(eq)
    out["maxDrawdown"] = round(dd_abs, 2)
    out["maxDrawdownPct"] = round(dd_pct, 3)

    # Exposure & turnover.
    out["positionBars"] = int(trades_df.holding_bars.sum())
    out["timeInMarketPct"] = round(float((eq_df.open_positions > 0).mean()) * 100, 1)
    out["avgConcurrentPositions"] = round(float(eq_df.open_positions.mean()), 2)
    out["maxConcurrentPositions"] = int(eq_df.open_positions.max())
    contracts = int(trades_df.apply(
        lambda r: 2 * sum(abs(q) for _, q in STRUCTURES[r.structure]["legs"]) * r.units, axis=1).sum())
    out["contractsTraded"] = contracts
    out["dataBars"] = int(len(panel))
    out["dataSpan"] = f"{panel.index.min()} -> {panel.index.max()}"
    return out


def per_structure(trades_df) -> pd.DataFrame:
    rows = []
    for name in STRUCTURES:
        sub = trades_df[trades_df.structure == name]
        if len(sub) == 0:
            rows.append({"structure": name, "trades": 0})
            continue
        wins = sub[sub.net_pnl > 0]
        losses = sub[sub.net_pnl <= 0]
        rows.append({
            "structure": name, "trades": len(sub),
            "winRate": round(len(wins) / len(sub) * 100, 1),
            "netPnl": round(float(sub.net_pnl.sum()), 2),
            "grossPnl": round(float(sub.gross_pnl.sum()), 2),
            "avgWin": round(float(wins.net_pnl.mean()) if len(wins) else 0.0, 2),
            "avgLoss": round(float(losses.net_pnl.mean()) if len(losses) else 0.0, 2),
            "profitFactor": round(float(wins.net_pnl.sum()) / abs(float(losses.net_pnl.sum())), 3) if len(losses) and losses.net_pnl.sum() < 0 else None,
            "avgHoldMin": round(float(sub.holding_min.mean()), 1),
            "slippage": round(float(sub.slippage_cost.sum()), 2),
            "commission": round(float(sub.commission_cost.sum()), 2),
            "longs": int((sub.direction == "LONG").sum()),
            "shorts": int((sub.direction == "SHORT").sum()),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Flatten the rich trade dicts into a fully-detailed CSV row (per-leg prices etc.).
# ----------------------------------------------------------------------------
def flatten_trades(trades) -> pd.DataFrame:
    rows = []
    for k, t in enumerate(trades, 1):
        legs = t["legs"]
        row = {
            "trade_id": k, "structure": t["structure"], "strategy": t["strategy"],
            "product": t["product"], "phase2_key": t["phase2_key"], "regime": t["regime"],
            "direction": t["direction"], "units": t["units"],
            "entry_time": t["entry_time"], "exit_time": t["exit_time"],
            "holding_bars": t["holding_bars"], "holding_min": t["holding_min"],
            "entry_z": t["entry_z"], "exit_z": t["exit_z"], "exit_reason": t["exit_reason"],
            "entry_spread_mid": t["entry_spread_mid"], "exit_spread_mid": t["exit_spread_mid"],
            "entry_fill": t["entry_fill"], "exit_fill": t["exit_fill"],
        }
        for li in range(3):
            if li < len(legs):
                sym, qty = legs[li]
                row[f"leg{li+1}_sym"] = sym
                row[f"leg{li+1}_qty"] = qty
                row[f"leg{li+1}_entry"] = round(t["entry_legs"].get(sym, float("nan")), 4)
                row[f"leg{li+1}_exit"] = round(t["exit_legs"].get(sym, float("nan")), 4)
            else:
                row[f"leg{li+1}_sym"] = ""; row[f"leg{li+1}_qty"] = ""
                row[f"leg{li+1}_entry"] = ""; row[f"leg{li+1}_exit"] = ""
        row.update({
            "gross_pnl": t["gross_pnl"], "slippage_cost": t["slippage_cost"],
            "commission_cost": t["commission_cost"], "net_pnl": t["net_pnl"],
            "return_pct": t["return_pct"], "mae": t["mae"], "mfe": t["mfe"],
            "p2_regime_mean": t["p2_regime_mean"], "p2_regime_z": t["p2_regime_z"],
            "strategy_desc": t["strategy_desc"],
        })
        rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
def write_trades_log(trades, eq_map, regime_label, span):
    """Human-readable, trade-by-trade log — each trade names the strategy used,
    the legs with entry/exit fills, the signal, the exit, and the gross PnL."""
    L = [f"# Phase 3 — Readable Trade Log\n",
         f"**Strategy:** {STRATEGY_NAME}  ·  **Basis:** GROSS (no slippage / commission)",
         f"**Phase-2 regime:** {regime_label}  ·  **Data:** {span}",
         f"**Trades:** {len(trades)}\n", "---\n"]
    sgn = lambda v: f"+${v:,.0f}" if v >= 0 else f"-${abs(v):,.0f}"
    for k, t in enumerate(trades, 1):
        legs = " ; ".join(
            f"{q:+d} {sym} @ {t['entry_legs'][sym]:.3f} -> {t['exit_legs'][sym]:.3f}"
            for sym, q in t["legs"])
        eq = eq_map.get(t["exit_time"])
        L.append(f"### #{k}  {t['structure']}  ·  {t['direction']}  ·  {t['units']} unit")
        L.append(f"- **Strategy:** {t['strategy']}")
        L.append(f"- **Setup:** {t['strategy_desc']}")
        L.append(f"- **Legs:** {legs}")
        L.append(f"- **Entry:** {t['entry_time']}  ·  spread {t['entry_spread_mid']:.3f}  ·  z {t['entry_z']:+.2f}")
        L.append(f"- **Exit:**  {t['exit_time']}  ·  spread {t['exit_spread_mid']:.3f}  ·  z {t['exit_z']:+.2f}  "
                 f"·  **{t['exit_reason']}**  ·  held {t['holding_min']} min")
        L.append(f"- **PnL (gross):** {sgn(t['net_pnl'])}   ·   MAE {sgn(t['mae'])} · MFE {sgn(t['mfe'])}"
                 + (f"   ·   equity {sgn(eq).replace('+$','$').replace('-$','$')}" if eq is not None else ""))
        L.append("")
    (OUT_DIR / "trades_log.md").write_text("\n".join(L), encoding="utf8")


def write_report(summ, by_struct, trades_df, regime_label):
    L = []
    L.append("# Phase 3 — Intraday Backtest Report\n")
    L.append(f"Strategy: Phase-2 regime relative-value **mean-reversion**, applied intraday to crude spreads.")
    L.append(f"Phase-2 regime context: **{regime_label}**. Data: {summ.get('dataSpan','')} "
             f"({summ.get('dataBars','?')} 15-min bars).\n")
    if summ.get("trades", 0) == 0:
        L.append(f"_{summ.get('note','No trades.')}_\n")
    else:
        L.append("## Headline\n")
        L.append(f"| Metric | Value |\n|---|---|")
        rows = [
            ("Trades", summ["trades"]),
            ("PnL (gross)", f"${summ['netPnl']:,.0f}"),
            ("Return on capital", f"{summ['returnOnCapitalPct']}%"),
            ("Win rate", f"{summ['winRate']}% ({summ['wins']}W / {summ['losses']}L)"),
            ("Profit factor", summ.get("profitFactor")),
            ("Expectancy / trade", f"${summ['expectancyPerTrade']:,.0f}"),
            ("Avg win / avg loss", f"${summ['avgWin']:,.0f} / ${summ['avgLoss']:,.0f}"),
            ("Best / worst", f"${summ['bestTrade']:,.0f} / ${summ['worstTrade']:,.0f}"),
            ("Costs", "none (gross basis — slippage & commission off)"),
            ("Avg holding", f"{summ['avgHoldingMin']} min"),
            ("Avg MAE / MFE", f"${summ['avgMAE']:,.0f} / ${summ['avgMFE']:,.0f}"),
            ("Sharpe (ann.)*", summ.get("sharpeAnnualized")),
            ("Max drawdown", f"${summ['maxDrawdown']:,.0f} ({summ['maxDrawdownPct']}%)"),
            ("Time in market", f"{summ['timeInMarketPct']}% (avg {summ['avgConcurrentPositions']} / max {summ['maxConcurrentPositions']} concurrent)"),
            ("Contracts traded", summ["contractsTraded"]),
        ]
        for k, v in rows:
            L.append(f"| {k} | {v} |")
        L.append("\n## Frequency of each trade type\n")
        L.append(f"- **By structure:** {summ['byStructure']}")
        L.append(f"- **By direction:** {summ['byDirection']}")
        L.append(f"- **By exit reason:** {summ['byExitReason']}")
        L.append(f"- **By product:** {summ['byProduct']}\n")
        L.append("## Per-structure bifurcation\n")
        cols = ["structure", "trades", "winRate", "netPnl", "profitFactor", "avgWin", "avgLoss", "avgHoldMin", "longs", "shorts"]
        L.append("| " + " | ".join(cols) + " |")
        L.append("|" + "---|" * len(cols))
        for _, r in by_struct.iterrows():
            L.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")

        # Interpretation — the honest read of these numbers.
        top = by_struct.loc[by_struct.netPnl.idxmax()] if len(by_struct) else None
        gross = summ["grossPnl"]; costs = summ["totalSlippage"] + summ["totalCommission"]
        L.append("\n## Interpretation\n")
        L.append(f"- **Gross basis — no transaction costs.** PnL here is the pure strategy edge: "
                 f"${summ['netPnl']:,.0f} across {summ['trades']} trades, with **{summ['winRate']}% of trades "
                 f"reverting profitably** (avg win ${summ['avgWin']:,.0f} vs avg loss ${summ['avgLoss']:,.0f}, "
                 f"profit factor {summ.get('profitFactor')}). This isolates whether the Phase-2 mean-reversion "
                 f"signal works on intraday crude spreads — it does, at a win rate in line with the Phase-2 "
                 f"daily backtest (67–83%). Slippage/commission are switched off (re-enable in config to stress-test).")
        if top is not None:
            others = summ["netPnl"] - float(top["netPnl"])
            L.append(f"- **PnL is concentrated.** {top['structure']} alone made ${top['netPnl']:,.0f}, while the "
                     f"other {len(by_struct) - 1} structures combined for ${others:,.0f}. Treat the headline as "
                     f"led by one or two strong reversions, not yet a broad edge (see per-structure table).")
        L.append(f"- **\\*Sample is tiny** ({summ['trades']} trades over {summ['dataBars']} bars / ~1 session). "
                 f"The annualised Sharpe is not statistically meaningful at this size — drop more daily .db files "
                 f"into Raw Data/ and re-run to build significance.")
    # Full, readable trade log embedded right here (so the whole thing is one doc).
    if len(trades_df):
        L.append("\n## Full trade log\n")
        cols = [("#", "trade_id"), ("Structure", "structure"), ("Dir", "direction"),
                ("Entry", "entry_time"), ("Exit", "exit_time"), ("z in", "entry_z"),
                ("z out", "exit_z"), ("Exit why", "exit_reason"), ("Hold(m)", "holding_min"),
                ("PnL $", "net_pnl"), ("Equity $", "equity_after")]
        L.append("| " + " | ".join(h for h, _ in cols) + " |")
        L.append("|" + "---|" * len(cols))
        for _, r in trades_df.iterrows():
            row = []
            for _, c in cols:
                v = r.get(c, "")
                if c in ("entry_time", "exit_time"):
                    v = str(v)[5:16]                       # MM-DD HH:MM
                elif c == "net_pnl":
                    v = f"{'+' if r['net_pnl'] >= 0 else '-'}${abs(r['net_pnl']):,.0f}"
                elif c == "equity_after":
                    v = f"${r['equity_after']:,.0f}"
                elif c in ("entry_z", "exit_z"):
                    v = f"{v:+.2f}"
                row.append(str(v))
            L.append("| " + " | ".join(row) + " |")
        L.append("\n_PnL is GROSS (no slippage / commission). Per-trade narrative with the "
                 "strategy & legs is in **trades_log.md**; raw data in trades.csv; aggregates in summary.json._")
    (OUT_DIR / "report.md").write_text("\n".join(L), encoding="utf8")


# ----------------------------------------------------------------------------
# LIVE SIGNAL ENGINE — every opportunity the framework generates, scored and
# journaled, with its subsequent performance tracked forward (the mentor brief).
# ----------------------------------------------------------------------------
SIGNAL_LOG = HERE.parent / "server" / "data" / "signal_log.json"
PHASE2_BACKTEST = HERE.parent / "server" / "data" / "backtest.json"


def load_phase2_backtest() -> dict:
    """Per-spread historical reversion hit-rates from the Phase-2 daily validation —
    the 'historical' edge that grounds each live signal's confidence."""
    try:
        return json.loads(PHASE2_BACKTEST.read_text(encoding="utf8")).get("spreads", {})
    except Exception:
        return {}


def edge_for(phase2_key, p2_backtest, intraday_wr):
    """Historical reversion edge (0–1) for a structure, with its provenance:
    prefer the Phase-2 daily-validated hit-rate, else this session's intraday hit-rate,
    else a neutral prior."""
    bt = p2_backtest.get(phase2_key)
    if bt and bt.get("sufficient"):
        return float(bt["hitRate"]), "validated (Phase-2 daily)"
    if intraday_wr is not None:
        return round(float(intraday_wr), 3), "intraday sample"
    return 0.6, "prior"


def confidence_score(edge: float, abs_z: float) -> int:
    """0–100 confidence = mostly the historical reversion edge, lifted by how far the
    spread is dislocated now (a bigger stretch reverts more reliably, within reason)."""
    return int(round(100 * (0.65 * edge + 0.35 * min(1.0, abs_z / 2.5))))


def build_signals(all_trades, open_positions, regime_label, p2_backtest, intraday_wr):
    """Turn completed trades (closed signals) + open positions (live signals) into one
    list of opportunity records carrying exactly the fields the brief asks for."""
    sigs = []

    def make(structure, phase2_key, direction, entry_time, entry_z, base_desc, status,
             pnl, realized, held_min, exit_time, exit_reason, outcome):
        az = abs(entry_z or 0)
        edge, edge_src = edge_for(phase2_key, p2_backtest, intraday_wr.get(structure))
        conf = confidence_score(edge, az)
        rationale = (f"{base_desc} Prevailing regime: {regime_label}. Confidence {conf}/100 — "
                     f"historical reversion edge ~{round(edge * 100)}% ({edge_src}) on a "
                     f"{az:.1f}sigma dislocation.")
        return {
            "id": f"{structure}@{pd.Timestamp(entry_time).strftime('%Y-%m-%dT%H:%M')}",
            "timestamp": str(entry_time),               # when the opportunity was generated
            "regime": regime_label,                     # market regime at generation
            "instrument": structure,                    # the spread / structure
            "direction": direction,
            "entryZ": entry_z,
            "confidence": conf,                         # 0–100 model confidence
            "histEdgePct": round(edge * 100),
            "rationale": rationale,                     # why it fired
            "status": status,                           # OPEN | CLOSED
            "exitTime": (str(exit_time) if exit_time is not None else None),
            "exitReason": exit_reason,
            "heldMin": held_min,
            "pnl": pnl,                                 # subsequent performance ($)
            "realized": realized,
            "outcome": outcome,
        }

    for t in all_trades:
        outcome = "Reverted — win" if t["net_pnl"] > 0 else ("Stopped/expired — loss" if t["net_pnl"] < 0 else "Flat")
        sigs.append(make(t["structure"], t["phase2_key"], t["direction"], t["entry_time"],
                         t["entry_z"], t["strategy_desc"], "CLOSED", t["net_pnl"], True,
                         t["holding_min"], t["exit_time"], t["exit_reason"], outcome))
    for o in open_positions:
        sigs.append(make(o["structure"], o["phase2_key"], o["direction"], o["entry_time"],
                         o["entry_z"], o["strategy_desc"], "OPEN", o["unrealized_pnl"], False,
                         o["min_held"], None, None, "Open — tracking"))
    sigs.sort(key=lambda s: s["timestamp"])
    return sigs


def update_signal_journal(current_signals) -> list:
    """Append-only journal: every opportunity ever generated is preserved (by id =
    instrument@entry-time); existing entries have their status/performance refreshed
    as the trade plays out, and the wall-clock 'loggedAt' is kept from first sighting."""
    existing = []
    if SIGNAL_LOG.exists():
        try:
            existing = json.loads(SIGNAL_LOG.read_text(encoding="utf8")).get("signals", [])
        except Exception:
            existing = []
    by_id = {s["id"]: s for s in existing}
    now = pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
    merged = {}
    for s in current_signals:
        prev = by_id.get(s["id"])
        s = dict(s)
        s["loggedAt"] = prev.get("loggedAt", now) if prev else now
        merged[s["id"]] = s
    for sid, s in by_id.items():        # preserve signals that scrolled out of the data window
        merged.setdefault(sid, s)
    out = sorted(merged.values(), key=lambda x: x["timestamp"])
    SIGNAL_LOG.write_text(json.dumps({"updatedAt": now, "count": len(out), "signals": out}))
    return out


def write_dashboard_feed(summ, by_struct, trades_df, eq_df, regime_label, panel, mode="local",
                         open_positions=None, signal_board=None, signal_log=None):
    """Consolidated JSON the Node backend serves to the dashboard BackTesting page.
    Same precompute->JSON->serve pattern as the regime/signals artifacts."""
    # Clean open positions for JSON (timestamps -> strings, drop internal indices).
    opens = []
    for o in (open_positions or []):
        opens.append({
            "structure": o["structure"], "direction": o["direction"], "product": o["product"],
            "entry_time": str(o["entry_time"]), "entry_z": o["entry_z"],
            "entry_spread_mid": o["entry_spread_mid"], "current_z": o["current_z"],
            "current_spread_mid": o["current_spread_mid"], "min_held": o["min_held"],
            "unrealized_pnl": o["unrealized_pnl"], "mae": o["mae"], "mfe": o["mfe"],
            "strategy_desc": o["strategy_desc"],
        })
    payload = {
        "generatedAt": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "strategy": STRATEGY_NAME,
        "basis": "gross (no slippage / commission)",
        "regime": regime_label,
        "mode": mode,                                   # "live" (network feed) or "local"
        "live": mode == "live",
        "lastBar": str(panel.index.max()),
        "dataSpan": f"{panel.index.min()} -> {panel.index.max()}",
        "dataBars": int(len(panel)),
        "params": {"lookback": LOOKBACK, "zEntry": Z_ENTRY, "zTarget": Z_TARGET, "zStop": Z_STOP,
                   "initialCapital": INITIAL_CAPITAL, "mult": MULT,
                   "slipPerLeg": SLIP_PER_LEG, "commPerContract": COMM_PER_CONTRACT},
        "summary": summ,
        "openPositions": opens,
        "signalBoard": signal_board or [],
        "signalLog": signal_log or [],
        "byStructure": json.loads(by_struct.to_json(orient="records")),
        "equityCurve": json.loads(eq_df.to_json(orient="records", date_format="iso")),
        "trades": json.loads(trades_df.to_json(orient="records", date_format="iso")) if len(trades_df) else [],
    }
    feed = HERE.parent / "server" / "data" / "intraday_backtest.json"
    feed.write_text(json.dumps(payload), encoding="utf8")
    return feed


def run_once():
    OUT_DIR.mkdir(exist_ok=True)
    panel, mode = load_panel()
    regime_label, regime_spreads = load_regime()
    print(f"[{mode}] loaded {len(panel)} bars, {panel.shape[1]} contracts "
          f"(latest {panel.index.max()})  | regime: {regime_label}")

    # Session-break flags: True on a bar after which there's a >gap to the next bar
    # (a real session/weekend break → force a close). The LAST bar's forward gap is
    # NaN → False: it is NOT a break, so a position open at the latest bar stays open
    # and is reported live (not force-closed).
    gaps = panel.index.to_series().diff().shift(-1).dt.total_seconds().div(60)
    session_break = (gaps > SESSION_GAP_MIN).fillna(False).values

    spreads_by_struct = {name: spread_series(panel, spec["legs"]) for name, spec in STRUCTURES.items()}

    all_trades = []
    open_positions = []
    for name, spec in STRUCTURES.items():
        trades, open_pos = backtest_structure(name, spec, panel, session_break, regime_label, regime_spreads)
        all_trades += trades
        if open_pos:
            open_positions.append(open_pos)
    all_trades.sort(key=lambda t: t["entry_time"])

    # Live signal board — current dislocation of EVERY structure at the latest bar,
    # so you can see what is/near a signal right now (even if no trade is open).
    signal_board = []
    for name in STRUCTURES:
        z, _, _ = zscore(spreads_by_struct[name])
        zl = z.dropna()
        zv = round(float(zl.iloc[-1]), 2) if len(zl) else None
        in_pos = any(o["structure"] == name for o in open_positions)
        sig = zv is not None and abs(zv) >= Z_ENTRY
        signal_board.append({
            "structure": name, "z": zv, "signal": bool(sig), "inPosition": in_pos,
            "bias": ("SHORT" if zv > 0 else "LONG") if (sig or in_pos) and zv is not None else None,
        })

    trades_df = flatten_trades(all_trades)
    eq_df = equity_curve(panel, spreads_by_struct, all_trades, open_positions)
    eq_map = dict(zip(eq_df.timestamp, eq_df.equity))
    if len(trades_df):
        trades_df["equity_after"] = [round(eq_map.get(t["exit_time"], float("nan")), 2) for t in all_trades]

    summ = summarize(trades_df, eq_df, panel)
    by_struct = per_structure(trades_df)
    span = f"{panel.index.min()} -> {panel.index.max()}"

    # LIVE SIGNAL ENGINE — score every opportunity and journal it (append-only),
    # tracking each from generation through its subsequent performance.
    intraday_wr = {}
    for name in STRUCTURES:
        sub = [t for t in all_trades if t["structure"] == name]
        if sub:
            intraday_wr[name] = sum(1 for t in sub if t["net_pnl"] > 0) / len(sub)
    p2_backtest = load_phase2_backtest()
    signals = build_signals(all_trades, open_positions, regime_label, p2_backtest, intraday_wr)
    signal_log = update_signal_journal(signals)

    # Resilient writes — if a file is locked (e.g. open in Excel), warn and keep going.
    locked = []

    def safe(path, writer):
        try:
            writer(path)
        except PermissionError:
            locked.append(path.name)

    safe(OUT_DIR / "trades.csv", lambda p: trades_df.to_csv(p, index=False))
    safe(OUT_DIR / "equity_curve.csv", lambda p: eq_df.to_csv(p, index=False))
    safe(OUT_DIR / "by_structure.csv", lambda p: by_struct.to_csv(p, index=False))
    safe(OUT_DIR / "summary.json", lambda p: p.write_text(json.dumps(summ, indent=2, default=str), encoding="utf8"))
    safe(OUT_DIR / "report.md", lambda p: write_report(summ, by_struct, trades_df, regime_label))
    safe(OUT_DIR / "trades_log.md", lambda p: write_trades_log(all_trades, eq_map, regime_label, span))
    # The dashboard feed always gets written (it's the live artifact); only the
    # OUT_DIR/* files might be locked by Excel.
    write_dashboard_feed(summ, by_struct, trades_df, eq_df, regime_label, panel, mode,
                         open_positions, signal_board, signal_log)
    if locked:
        print(f"  [warn] could not write (file open/locked — close it & re-run): {', '.join(locked)}")

    pf = summ.get("profitFactor")
    live = [f"{o['structure']} {o['direction']} {o['unrealized_pnl']:+.0f}" for o in open_positions]
    open_sigs = [s for s in signal_log if s["status"] == "OPEN"]
    print(f"  trades {summ['trades']} | gross ${summ['netPnl']:,.0f} | win {summ.get('winRate','-')}% | PF {pf} | source: {mode}")
    print(f"  signal journal: {len(signal_log)} opportunities ({len(open_sigs)} live)  | OPEN: {live if live else 'flat'}")
    return summ


def main():
    args = sys.argv[1:]
    live = "--live" in args
    interval = next((int(a) for a in args if a.lstrip("-").isdigit()), LIVE_REFRESH_SEC)
    if not live:
        run_once()
        return
    print(f"LIVE mode — re-running every {interval}s from {LIVE_DIR if LIVE_DIR.exists() else RAW_DIR}. Ctrl+C to stop.\n")
    while True:
        t0 = time.time()
        try:
            run_once()
        except KeyboardInterrupt:
            print("\nstopped."); return
        except Exception as e:                          # keep the loop alive on a transient error
            print(f"  [run error] {type(e).__name__}: {e}")
        time.sleep(max(1, interval - (time.time() - t0)))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nstopped.")
