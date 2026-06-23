"""
shock.py — the shock-absorption layer, risk-led metrics, and the regime-blind
control, shared by the three rolling-mean engines (daily, intraday, live).

This deliberately KEEPS main's design — each engine supplies its own causal fair
value (a rolling mean intraday/live, the walk-forward regression daily), its own
z-score, FIXED entry/exit/stop thresholds, and a base size of 1 unit. What this
module adds, on top of that unchanged signal, is the three pieces asked for:

  1. SHOCK ABSORPTION (aware arm only). A severity ∈ [0,1] detector combining
       • a vol JUMP    — the spread's per-bar vol vs its trailing median;
       • a vol STEP-UP — a transition UP the Low→Normal→High vol ladder (decaying);
       • a z-BREACH    — the dislocation blowing past the stop;
       • an intraday SPIKE — short- vs long-window realized vol (intraday only),
     combined by probabilistic OR. The graded response:
       • DE-LEVER     — enter at size (1 − severity), floored at size_min;
       • STAND ASIDE  — block new entries when severity ≥ stand_aside_tau, or for
                        `confirm_bars` bars right after a vol step-up (confirmation delay);
       • FLATTEN      — exit an open position on a severe shock (severity ≥ flatten_tau)
                        or a step UP into the High-vol regime.

  2. RISK-LED METRICS, on a mark-to-market DAILY-return series (so drawdown includes
     OPEN-position risk — the honest measure for shock behaviour): Sharpe, Sortino,
     Calmar, max drawdown ($/%), CVaR 5%, annualized vol, % time in market.

  3. The REGIME-BLIND CONTROL. The blind arm is main's strategy EXACTLY (severity 0,
     size 1, a fixed max-hold, no stand-aside/flatten), so the aware-vs-blind
     head-to-head isolates precisely what shock absorption contributes.

Look-ahead discipline: severity uses only trailing/rolling-then-shifted inputs; the
vol-state is the Phase-2 daily classification (same-day / backward-looking inputs);
mark-to-market uses only the move since the prior bar. Pure (numpy/pandas) so the
standalone live engine in Backtesting/ can import it without the analytics package.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

VOL_STATES = ("Low", "Normal", "High")
_VOL_ORD = {"Low": 0, "Normal": 1, "High": 2}      # a "shock" is a step UP this ladder
ANN_DAYS = 252                                       # trading days / year, for annualizing
MULT_DEFAULT = 1000                                  # 1,000 bbl/contract → a $1/bbl move = $1,000


# ----------------------------------------------------------------------------
# Shock configuration (one per horizon)
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class ShockConfig:
    z_stop: float                  # the strategy's stop level — the z-breach severity is measured past it
    vol_ref_window: int            # trailing window for the median the vol jump is judged against
    vol_jump_scale: float          # (vol/median − 1) that maps to severity 1.0
    z_breach_scale: float          # (|z| − z_stop) that maps to severity 1.0
    transition_decay: int          # bars over which a vol step-up's severity decays to 0
    stand_aside_tau: float         # block NEW entries when severity >= this
    flatten_tau: float             # flatten an OPEN position when severity >= this
    confirm_bars: int              # block new entries for this many bars after a vol step-up
    size_min: float = 0.25         # floor on the de-levered entry size
    spike_short: int = 0           # intraday: short realized-vol window
    spike_long: int = 0            # intraday: baseline realized-vol window
    spike_scale: float = 0.0       # intraday: (short/long − 1) that maps to severity 1.0
    use_intraday_spike: bool = False
    flatten_on_regime_break: bool = True   # flatten on a step UP into the High-vol regime


# Defaults per horizon — calibrated as a TAIL-SHAVER for the rolling-mean engines:
# fire only on GENUINE shocks so normal mean-reversion trades through (high stand-aside
# / flatten thresholds, less trigger-happy vol-jump scales, short confirm delays). The
# response is mostly DE-LEVER + the occasional FLATTEN, rarely a full stand-aside —
# the point is to clamp exposure in turbulence, not to stop trading.
DAILY_SHOCK = ShockConfig(
    z_stop=3.0, vol_ref_window=63, vol_jump_scale=2.0, z_breach_scale=1.5,
    transition_decay=3, stand_aside_tau=0.97, flatten_tau=0.95, confirm_bars=0,
    size_min=0.40, use_intraday_spike=False, flatten_on_regime_break=True,
)
INTRADAY_SHOCK = ShockConfig(
    z_stop=3.5, vol_ref_window=1500, vol_jump_scale=2.0, z_breach_scale=1.5,
    transition_decay=4, stand_aside_tau=0.97, flatten_tau=0.95, confirm_bars=0,
    size_min=0.40, spike_short=8, spike_long=96, spike_scale=2.5,
    use_intraday_spike=True, flatten_on_regime_break=False,   # sessions already flatten
)
# Live runs on a short (few-day) feed — shrink the vol-reference windows so the jump/
# spike detectors actually have enough history to fire; step-up & z-breach still apply.
LIVE_SHOCK = ShockConfig(
    z_stop=3.5, vol_ref_window=120, vol_jump_scale=2.0, z_breach_scale=1.5,
    transition_decay=4, stand_aside_tau=0.97, flatten_tau=0.95, confirm_bars=0,
    size_min=0.40, spike_short=8, spike_long=48, spike_scale=2.5,
    use_intraday_spike=True, flatten_on_regime_break=False,
)


# ============================================================================
# Severity components — each ∈ [0,1], all causal
# ============================================================================
def _clip01(x):
    return np.clip(x, 0.0, 1.0)


def vol_jump_severity(bar_vol: np.ndarray, window: int, scale: float) -> np.ndarray:
    """Severity from the current vol vs its TRAILING median (a vol jump). Causal:
    the median uses the prior `window` bars only (shifted)."""
    s = pd.Series(bar_vol)
    med = s.rolling(window, min_periods=max(10, window // 5)).median().shift(1)
    ratio = s / med
    sev = _clip01((ratio - 1.0) / scale)
    return np.nan_to_num(sev.values, nan=0.0)


def intraday_spike_severity(bar_vol: np.ndarray, short: int, long: int, scale: float) -> np.ndarray:
    """Severity from a short-window vol spike vs a longer baseline (intraday). Causal."""
    s = pd.Series(bar_vol)
    sh = s.rolling(short, min_periods=2).mean()
    lo = s.rolling(long, min_periods=max(10, long // 5)).mean().shift(1)
    sev = _clip01((sh / lo - 1.0) / scale)
    return np.nan_to_num(sev.values, nan=0.0)


def combine_severity(*components) -> np.ndarray:
    """Probabilistic OR — independent shock signals compound toward 1 but never exceed
    it: sev = 1 − Π(1 − sᵢ). More interpretable than a sum, and additive shocks stack."""
    keep = 1.0
    for c in components:
        keep = keep * (1.0 - np.asarray(c, float))
    return _clip01(1.0 - keep)


# ============================================================================
# The simulation path — one structure, one arm ("aware" | "blind")
# ============================================================================
def simulate(frame: pd.DataFrame, *, mode: str, z_entry: float, z_exit: float,
             z_stop: float, max_hold: int, shock: ShockConfig, legs_count: int,
             structure: str, label: str, hit_rate, horizon: str,
             mult: float = MULT_DEFAULT, slip_per_leg: float = 0.0,
             gate_cost: float = 0.0, warmup: int = 0,
             extra: dict | None = None) -> dict:
    """Walk one structure's bars under FIXED thresholds and a base size of 1 unit.

    `frame` columns (aligned, sorted, segment-tagged by the caller):
      spread     — the actual spread ($/bbl)
      fv         — the engine's own causal fair value (rolling mean / regression)
      z          — the engine's own z-score (precomputed; this module never recomputes it)
      vol_state  — "Low"|"Normal"|"High" (Phase-2 vol dimension), or None
      regime     — the Phase-2 regime label (for the by-regime table)
      bar_vol    — a causal per-bar volatility proxy (for the shock detector)
      seg        — segment id (roll/session intraday; constant daily)

    mode="blind" reproduces main exactly. mode="aware" adds the shock layer.
    Returns trades, the open position, and per-bar pnl/size/severity/in_market series.
    """
    aware = mode == "aware"
    idx = frame.index
    n = len(frame)
    sp = frame["spread"].to_numpy(float)
    fv = frame["fv"].to_numpy(float)
    zv = frame["z"].to_numpy(float)
    state = frame["vol_state"].to_numpy(object)
    rlab = frame["regime"].to_numpy(object)
    seg = frame["seg"].to_numpy()
    bar_vol = frame["bar_vol"].to_numpy(float)
    extra = extra or {}

    cost_rt = slip_per_leg * 2 * legs_count * mult        # reporting round-turn $ (0 = gross)

    # vectorizable severity components (aware only)
    if aware:
        sev_vol = vol_jump_severity(bar_vol, shock.vol_ref_window, shock.vol_jump_scale)
        sev_spike = (intraday_spike_severity(bar_vol, shock.spike_short, shock.spike_long,
                                             shock.spike_scale)
                     if shock.use_intraday_spike else np.zeros(n))
    else:
        sev_vol = sev_spike = np.zeros(n)

    pnl = np.zeros(n)
    size_series = np.zeros(n)
    sev_series = np.zeros(n)
    in_market = np.zeros(n, dtype=bool)

    trades = []
    pos = None
    seg_start = 0
    bars_since_volup = 10 ** 9         # bars since the vol regime last stepped UP
    last_volup_step = 0
    prev_ord = None

    for i in range(n):
        # segment boundary → force-flatten any open position at the prior bar's price
        new_seg = i == 0 or seg[i] != seg[i - 1]
        if new_seg:
            if pos is not None:
                _close(trades, pos, i - 1, sp, idx, cost_rt, "session_end",
                       structure, label, hit_rate, mult, horizon, extra)
                pos = None
            seg_start = i

        # entry is only considered when FLAT coming into the bar (matches main: a bar
        # that closes a position does not also open a new one — no same-bar re-entry)
        was_flat = pos is None
        within_warmup = (i - seg_start) < warmup
        si = state[i] if isinstance(state[i], str) else "Normal"
        z = zv[i]

        # vol step-up bookkeeping (aware): a SHOCK is a step UP the vol ladder
        cur_ord = _VOL_ORD.get(si, 1)
        volup_now = False
        if aware:
            if prev_ord is not None and cur_ord > prev_ord:
                bars_since_volup, last_volup_step, volup_now = 0, cur_ord - prev_ord, True
            else:
                bars_since_volup += 1
            prev_ord = cur_ord

        # ---- severity ----
        sev_trans = 0.0
        if aware and shock.transition_decay > 0 and bars_since_volup < shock.transition_decay:
            peak = min(1.0, 0.6 * last_volup_step)
            sev_trans = peak * (1.0 - bars_since_volup / shock.transition_decay)
        sev_z = (_clip01((abs(z) - z_stop) / shock.z_breach_scale)
                 if (aware and np.isfinite(z)) else 0.0)
        severity = float(combine_severity(sev_vol[i], sev_spike[i], sev_trans, sev_z)) if aware else 0.0
        sev_series[i] = severity

        # ---- size: base 1 unit, de-levered by (1 − severity) when aware ----
        entry_size = max(1.0 - severity, shock.size_min) if aware else 1.0
        size_series[i] = entry_size if pos is None else pos["size"]

        # ---- manage an open position (mark-to-market this bar) ----
        if pos is not None:
            sign = 1.0 if pos["dir"] == "LONG" else -1.0
            entry_sign = -sign
            if i > pos["i"]:
                pnl[i] += pos["size"] * sign * (sp[i] - sp[i - 1]) * mult
            in_market[i] = True
            size_series[i] = pos["size"]
            upnl = pos["size"] * sign * (sp[i] - pos["sp"]) * mult
            pos["mae"], pos["mfe"] = min(pos["mae"], upnl), max(pos["mfe"], upnl)
            held = i - pos["i"]

            flat_shock = aware and severity >= shock.flatten_tau
            flat_break = (aware and shock.flatten_on_regime_break
                          and volup_now and cur_ord == _VOL_ORD["High"])
            hit_t = np.isfinite(z) and entry_sign * z <= z_exit
            hit_s = np.isfinite(z) and abs(z) >= z_stop
            hit_time = held >= max_hold
            if hit_t or hit_s or hit_time or flat_shock or flat_break:
                reason = ("target" if hit_t else "stop" if hit_s else "time_stop" if hit_time
                          else "shock_flat" if flat_shock else "vol_shock")
                _close(trades, pos, i, sp, idx, cost_rt, reason, structure, label,
                       hit_rate, mult, horizon, extra, exit_z=z)
                pos = None

        # ---- consider a new entry (only if flat coming into this bar) ----
        seg_last = (i == n - 1) or (seg[i + 1] != seg[i])   # never open on a segment's last bar
        if pos is None and was_flat and not within_warmup and np.isfinite(z) and not seg_last:
            block = aware and (severity >= shock.stand_aside_tau
                               or bars_since_volup < shock.confirm_bars)
            if (not block) and abs(z) >= z_entry:
                capture = abs(sp[i] - fv[i]) * mult              # expected $ move back to fair
                if (gate_cost <= 0) or (capture >= gate_cost):
                    pos = {
                        "dir": "LONG" if z <= -z_entry else "SHORT",
                        "i": i, "t": idx[i], "sp": sp[i], "fv": fv[i], "z": z,
                        "size": entry_size, "regime": rlab[i], "severity": severity,
                        "state": si, "mae": 0.0, "mfe": 0.0,
                    }
                    in_market[i] = True
                    size_series[i] = entry_size

    # open position at the last bar (left open, not force-closed)
    open_pos = None
    if pos is not None:
        i = n - 1
        sign = 1.0 if pos["dir"] == "LONG" else -1.0
        cur_z = float(zv[i]) if np.isfinite(zv[i]) else float(pos["z"])
        stamp = "%Y-%m-%d" if horizon == "daily" else "%Y-%m-%d %H:%M"
        open_pos = {
            "structure": structure, "label": label, "direction": pos["dir"],
            "entryDate": pos["t"].strftime(stamp), "entryTime": pos["t"].strftime(stamp),
            "asOf": idx[i].strftime(stamp),
            "entrySpread": round(pos["sp"], 4), "curSpread": round(float(sp[i]), 4),
            "entryZ": round(float(pos["z"]), 2), "curZ": round(cur_z, 2),
            "holdBars": int(i - pos["i"]), "holdDays": int(i - pos["i"]),
            "size": round(pos["size"], 2), "units": round(pos["size"], 2),
            "regime": pos["regime"], "volState": pos["state"],
            "unrealizedPnl": round(pos["size"] * sign * (sp[i] - pos["sp"]) * mult, 2),
            **{k: extra.get(k) for k in extra},
        }

    return {
        "trades": trades,
        "open": open_pos,
        "pnl": pd.Series(pnl, index=idx),
        "size": pd.Series(size_series, index=idx),
        "severity": pd.Series(sev_series, index=idx),
        "in_market": pd.Series(in_market, index=idx),
    }


def _close(trades, pos, i, sp, idx, cost_rt, reason, structure, label, hit_rate,
           mult, horizon, extra, exit_z=np.nan):
    sign = 1.0 if pos["dir"] == "LONG" else -1.0
    gross = pos["size"] * sign * (sp[i] - pos["sp"]) * mult
    cost = cost_rt * pos["size"]
    held = i - pos["i"]
    t_in, t_out = pos["t"], idx[i]
    rec = {
        "structure": structure, "label": label, "regime": pos["regime"],
        "direction": pos["dir"], "volState": pos["state"],
        "entrySpread": round(pos["sp"], 4), "exitSpread": round(float(sp[i]), 4),
        "fairValue": round(pos["fv"], 4),
        "entryZ": round(float(pos["z"]), 2),
        "exitZ": round(float(exit_z), 2) if np.isfinite(exit_z) else None,
        "size": round(pos["size"], 2), "units": round(pos["size"], 2),
        "entrySeverity": round(float(pos["severity"]), 2),
        "pnl": round(gross, 2), "cost": round(cost, 2), "netPnl": round(gross - cost, 2),
        "mae": round(pos["mae"], 2), "mfe": round(pos["mfe"], 2),
        "exitReason": reason, "histHitRate": hit_rate,
    }
    if horizon == "daily":
        rec["entryDate"] = t_in.strftime("%Y-%m-%d")
        rec["exitDate"] = t_out.strftime("%Y-%m-%d")
        rec["holdDays"] = held
        rec["holdLabel"] = f"{held}d"
    else:
        hold_min = int((t_out - t_in).total_seconds() // 60)
        rec["entryDate"] = t_in.strftime("%Y-%m-%d %H:%M")
        rec["exitDate"] = t_out.strftime("%Y-%m-%d %H:%M")
        rec["entryTime"] = rec["entryDate"]
        rec["exitTime"] = rec["exitDate"]
        rec["holdBars"] = held
        rec["holdMin"] = hold_min
        rec["holdLabel"] = f"{hold_min // 60}h{hold_min % 60:02d}" if hold_min >= 60 else f"{hold_min}m"
    rec.update(extra)
    trades.append(rec)


# ============================================================================
# Portfolio assembly + risk-led metrics (mark-to-market daily)
# ============================================================================
def portfolio_daily_pnl(bar_pnls: list) -> pd.Series:
    """Sum per-structure mark-to-market bar PnL into one portfolio series, resampled
    to a DAILY total (the substrate for Sharpe / Calmar / CVaR / drawdown)."""
    bar_pnls = [s for s in bar_pnls if s is not None and len(s)]
    if not bar_pnls:
        return pd.Series(dtype=float)
    total = pd.concat(bar_pnls, axis=1, sort=True).sum(axis=1)
    return total.groupby(total.index.normalize()).sum()


def pct_time_in_market(in_markets: list) -> float:
    """Fraction of DAYS on which the book held at least one position (portfolio-level)."""
    in_markets = [s for s in in_markets if s is not None and len(s)]
    if not in_markets:
        return 0.0
    any_open = pd.concat(in_markets, axis=1, sort=True).any(axis=1)
    by_day = any_open.groupby(any_open.index.normalize()).any()
    return round(float(by_day.mean()), 4) if len(by_day) else 0.0


def equity_from_daily(daily_pnl: pd.Series, initial: float) -> list:
    """Mark-to-market daily equity curve [{t, equity}] — drawdown therefore includes
    open-position risk (the honest measure for shock behaviour)."""
    if daily_pnl is None or not len(daily_pnl):
        return []
    eq = initial + daily_pnl.cumsum()
    return [{"t": ts.strftime("%Y-%m-%d"), "equity": round(float(v), 2)} for ts, v in eq.items()]


def max_drawdown_dollars(equity: np.ndarray) -> tuple:
    peak, mdd, mdd_pct = -1e18, 0.0, 0.0
    for v in equity:
        peak = max(peak, v)
        dd = v - peak
        if dd < mdd:
            mdd = dd
            mdd_pct = dd / peak if peak > 0 else 0.0
    return round(float(mdd), 2), round(float(mdd_pct), 4)


def risk_metrics(daily_pnl: pd.Series, initial: float, years: float,
                 in_markets: list | None = None) -> dict:
    """Sharpe (ann.), Sortino, Calmar (CAGR/|maxDD%|), max drawdown ($/%), CVaR 5%,
    annualized vol, % time in market — all on the mark-to-market daily-return series."""
    base = {"sharpe": 0.0, "sortino": None, "calmar": None, "cagr": 0.0,
            "maxDrawdown": 0.0, "maxDrawdownPct": 0.0, "cvar5": 0.0, "volAnn": 0.0,
            "downDevAnn": 0.0, "pctTimeInMarket": pct_time_in_market(in_markets or []),
            "days": int(len(daily_pnl) if daily_pnl is not None else 0)}
    if daily_pnl is None or len(daily_pnl) < 2:
        return base
    pnl = daily_pnl.to_numpy(float)
    eq = initial + np.cumsum(pnl)
    rets = pnl / initial                                  # additive PnL on a fixed capital base
    mu, sd = rets.mean(), rets.std(ddof=1)
    sharpe = float(mu / sd * np.sqrt(ANN_DAYS)) if sd > 0 else 0.0
    downside = rets[rets < 0]
    dd_dev = downside.std(ddof=1) if len(downside) > 1 else 0.0
    sortino = float(mu / dd_dev * np.sqrt(ANN_DAYS)) if dd_dev > 0 else None
    mdd, mdd_pct = max_drawdown_dollars(eq)
    end_eq = float(eq[-1])
    cagr = float((end_eq / initial) ** (1.0 / max(years, 1e-9)) - 1.0) if end_eq > 0 else -1.0
    calmar = float(cagr / abs(mdd_pct)) if mdd_pct < 0 else None
    k = max(1, int(np.ceil(0.05 * len(rets))))
    cvar = float(np.sort(rets)[:k].mean() * initial)     # mean $ of the worst 5% of days
    base.update({
        "sharpe": round(sharpe, 3),
        "sortino": None if sortino is None else round(sortino, 3),
        "calmar": None if calmar is None else round(calmar, 3),
        "cagr": round(cagr, 4),
        "maxDrawdown": mdd, "maxDrawdownPct": round(mdd_pct, 4),
        "cvar5": round(cvar, 2),
        "volAnn": round(float(sd * np.sqrt(ANN_DAYS)), 4),
        "downDevAnn": round(float(dd_dev * np.sqrt(ANN_DAYS)), 4),
        "days": int(len(pnl)),
    })
    return base


# ============================================================================
# Trade-level aggregation (keeps every field the dashboard already reads)
# ============================================================================
def pf(rows):
    gw = sum(t["pnl"] for t in rows if t["pnl"] > 0)
    gl = -sum(t["pnl"] for t in rows if t["pnl"] <= 0)
    return round(gw / gl, 3) if gl > 0 else None


def _counts(rows, key):
    out = {}
    for r in rows:
        out[r.get(key)] = out.get(r.get(key), 0) + 1
    return out


def _legs_of(t):
    s = (t.get("structure") or "").lower()
    return 4 if s.endswith("fly") else 2


def summarize(all_trades, daily_pnl, in_markets, initial, years, mult, ref_slip,
              horizon) -> dict:
    """Headline summary — keeps main's existing keys AND adds the risk-led block."""
    n = len(all_trades)
    gross = sum(t["pnl"] for t in all_trades)
    net = sum(t["netPnl"] for t in all_trades)
    costs = sum(t["cost"] for t in all_trades)
    wins = [t for t in all_trades if t["pnl"] > 0]
    losses = [t for t in all_trades if t["pnl"] <= 0]
    gw, gl = sum(t["pnl"] for t in wins), -sum(t["pnl"] for t in losses)
    nwins = [t for t in all_trades if t["netPnl"] > 0]
    nlosses = [t for t in all_trades if t["netPnl"] <= 0]
    pnls = np.array([t["pnl"] for t in all_trades], float) if n else np.array([])
    per_trade_sharpe = float(pnls.mean() / pnls.std()) if n > 1 and pnls.std() > 0 else 0.0
    ref_costs = sum(2 * _legs_of(t) * t.get("size", 1.0) * ref_slip * mult for t in all_trades)
    ref_net = gross - ref_costs
    risk = risk_metrics(daily_pnl, initial, years, in_markets)
    out = {
        "trades": n, "grossPnl": round(gross, 2), "netPnl": round(net, 2), "costs": round(costs, 2),
        "refNet": round(ref_net, 2), "refSlip": ref_slip,
        "refKeepPct": round(ref_net / gross, 3) if gross > 0 else 0.0,
        "winRate": round(len(wins) / n, 4) if n else 0.0,
        "avgWin": round(gw / len(wins), 2) if wins else 0.0,
        "avgLoss": round(-gl / len(losses), 2) if losses else 0.0,
        "avgNetWin": round(sum(t["netPnl"] for t in nwins) / len(nwins), 2) if nwins else 0.0,
        "avgNetLoss": round(sum(t["netPnl"] for t in nlosses) / len(nlosses), 2) if nlosses else 0.0,
        "profitFactor": pf(all_trades), "expectancy": round(gross / n, 2) if n else 0.0,
        "netExpectancy": round(net / n, 2) if n else 0.0,
        "perTradeSharpe": round(per_trade_sharpe, 3),
        "tradesPerYear": round(n / years, 1) if years else 0.0,
        "avgSize": round(float(np.mean([t.get("size", 1.0) for t in all_trades])), 2) if n else 0.0,
        "endingEquity": round(initial + gross, 2), "initialCapital": initial,
        "byExitReason": _counts(all_trades, "exitReason"), "byDirection": _counts(all_trades, "direction"),
        # risk-led block (lead with this)
        "sharpe": risk["sharpe"], "sortino": risk["sortino"], "calmar": risk["calmar"],
        "cagr": risk["cagr"], "maxDrawdown": risk["maxDrawdown"], "maxDrawdownPct": risk["maxDrawdownPct"],
        "cvar5": risk["cvar5"], "volAnn": risk["volAnn"], "pctTimeInMarket": risk["pctTimeInMarket"],
    }
    if horizon == "daily":
        out["avgHoldDays"] = round(float(np.mean([t["holdDays"] for t in all_trades])), 1) if n else 0.0
    else:
        out["avgHoldMin"] = round(float(np.mean([t["holdMin"] for t in all_trades])), 0) if n else 0.0
    return out


def per_structure(all_trades, structures):
    """structures: list of (key, label) to preserve order."""
    out = {}
    for key, label in structures:
        ts = [t for t in all_trades if t["structure"] == key]
        if not ts:
            continue
        wins = [t for t in ts if t["pnl"] > 0]
        rec = {
            "label": label, "trades": len(ts), "wins": len(wins),
            "winRate": round(len(wins) / len(ts), 3), "pnl": round(sum(t["pnl"] for t in ts), 2),
            "profitFactor": pf(ts), "histHitRate": ts[0].get("histHitRate"),
            "avgSize": round(float(np.mean([t.get("size", 1.0) for t in ts])), 2),
        }
        if "holdDays" in ts[0]:
            rec["avgHoldDays"] = round(float(np.mean([t["holdDays"] for t in ts])), 1)
        if "holdMin" in ts[0]:
            rec["avgHoldMin"] = round(float(np.mean([t["holdMin"] for t in ts])), 0)
        out[key] = rec
    return out


def per_regime(all_trades):
    out = {}
    for lab in sorted({t["regime"] for t in all_trades if t["regime"]}):
        ts = [t for t in all_trades if t["regime"] == lab]
        wins = [t for t in ts if t["pnl"] > 0]
        out[lab] = {
            "trades": len(ts), "wins": len(wins),
            "winRate": round(len(wins) / len(ts), 3), "pnl": round(sum(t["pnl"] for t in ts), 2),
            "profitFactor": pf(ts),
            "avgSize": round(float(np.mean([t.get("size", 1.0) for t in ts])), 2),
        }
    return out


def per_volstate(all_trades):
    out = {}
    for st in VOL_STATES:
        ts = [t for t in all_trades if t.get("volState") == st]
        if not ts:
            continue
        wins = [t for t in ts if t["pnl"] > 0]
        out[st] = {
            "trades": len(ts), "winRate": round(len(wins) / len(ts), 3),
            "pnl": round(sum(t["pnl"] for t in ts), 2), "profitFactor": pf(ts),
            "avgSize": round(float(np.mean([t.get("size", 1.0) for t in ts])), 2),
        }
    return out


def shock_summary(aware_trades) -> dict:
    """How the shock layer expressed itself in the aware arm — for the head-to-head."""
    n = len(aware_trades)
    flats = [t for t in aware_trades if t["exitReason"] in ("shock_flat", "vol_shock")]
    sev = [t.get("entrySeverity", 0.0) for t in aware_trades]
    de_levered = [t for t in aware_trades if t.get("size", 1.0) < 0.999]
    return {
        "shockFlattens": len(flats),
        "shockFlattenPnl": round(sum(t["pnl"] for t in flats), 2),
        "deLeveredTrades": len(de_levered),
        "avgEntrySeverity": round(float(np.mean(sev)), 3) if sev else 0.0,
        "maxEntrySeverity": round(float(np.max(sev)), 3) if sev else 0.0,
        "avgEntrySize": round(float(np.mean([t.get("size", 1.0) for t in aware_trades])), 3) if n else 0.0,
    }


def head_to_head(aware_summary: dict, blind_summary: dict) -> dict:
    """Aware-vs-blind deltas on the metrics the brief says to lead with (risk first)."""
    def d(key, pct=False):
        a, b = aware_summary.get(key), blind_summary.get(key)
        if a is None or b is None:
            return None
        return round(a - b, 4 if pct else 2)
    return {
        "sharpe": {"aware": aware_summary.get("sharpe"), "blind": blind_summary.get("sharpe"),
                   "delta": d("sharpe", pct=True)},
        "calmar": {"aware": aware_summary.get("calmar"), "blind": blind_summary.get("calmar")},
        "maxDrawdown": {"aware": aware_summary.get("maxDrawdown"), "blind": blind_summary.get("maxDrawdown"),
                        "delta": d("maxDrawdown")},
        "maxDrawdownPct": {"aware": aware_summary.get("maxDrawdownPct"),
                           "blind": blind_summary.get("maxDrawdownPct"), "delta": d("maxDrawdownPct", pct=True)},
        "cvar5": {"aware": aware_summary.get("cvar5"), "blind": blind_summary.get("cvar5"),
                  "delta": d("cvar5")},
        "grossPnl": {"aware": aware_summary.get("grossPnl"), "blind": blind_summary.get("grossPnl"),
                     "delta": d("grossPnl")},
        "netPnl": {"aware": aware_summary.get("netPnl"), "blind": blind_summary.get("netPnl"),
                   "delta": d("netPnl")},
        "winRate": {"aware": aware_summary.get("winRate"), "blind": blind_summary.get("winRate")},
        "trades": {"aware": aware_summary.get("trades"), "blind": blind_summary.get("trades")},
    }
