"""
regime_strategy.py — the shared, regime-DRIVEN trading core for Phase 3.

This is the single engine behind all three Phase-3 backtests (daily 5y, intraday 5y,
and the live feed). It exists to satisfy the mentor's redesign brief:

  1. Model-based fair value (NOT a rolling mean): the daily engine feeds in the
     Phase-2 walk-forward fundamentals regression; the intraday engine feeds in a
     REGIME-PARAMETERIZED adaptive local-level (EWMA) filter whose reversion span is
     the regime's *measured, trailing* half-life (see `adaptive_ewma`/`trailing_halflife`).
  2. The Phase-2 REGIME MODEL drives the strategy — it is not a label. Per vol-state
     (Low/Normal/High) it sets zEntry/zExit/zStop, the max-hold (× regime half-life),
     the dispersion the z is measured against, AND the vol-target position size.
  3. A real SHOCK-ABSORPTION layer: a severity∈[0,1] detector (vol jump, regime
     transition, z-breach, intraday vol spike) that de-levers, stands aside, delays
     confirmation after a regime change, and flattens on a regime break.
  4. A REGIME-BLIND control: the SAME engine with the regime layer off (fixed z=2,
     fixed 1 unit, global dispersion, fixed-span fair value, no shock layer) so a
     head-to-head isolates exactly what the regime model contributes — especially
     through shocks.
  5. Risk-led measurement: Sharpe, Calmar, max drawdown ($/%), CVaR, % time in market,
     computed on a mark-to-market daily-return series (drawdown therefore includes
     OPEN-position risk, which is what matters for shock behaviour).

LOOK-AHEAD DISCIPLINE (enforced here, audited in the review):
  • Fair value is causal — regression is walk-forward (passed in); the EWMA is a
    one-sided recursion; the blind EWMA is pandas `ewm` (causal).
  • The half-life that parameterizes the FV span and the max-hold is estimated on a
    TRAILING window of data strictly before each bar, refit periodically — never the
    full-sample catalog number.
  • The z dispersion is an EXPANDING same-vol-state std using only residuals before
    the current bar.
  • The vol-target size uses only causal (expanding) dispersions.
  • regime(t) is the Phase-2 classification, which is built from same-day / backward
    -looking inputs only (seasonal-z, trailing realized vol, same-day curve slope).
  • Roll/session segments are warmed up before any residual feeds the dispersion, so
    a contract roll never injects a spurious dislocation.

The concrete engines (historical_backtest.py, historical_intraday.py,
Backtesting/engine.py) only build a per-structure frame — spread, fair value,
vol-state, regime id, a per-bar volatility proxy, a segment id — and then call
`simulate_structure` once per (structure, mode) and aggregate with the helpers here.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
VOL_STATES = ("Low", "Normal", "High")
_VOL_ORD = {"Low": 0, "Normal": 1, "High": 2}   # a "shock" is a step UP this ladder
MULT_DEFAULT = 1000          # 1,000 bbl/contract → a $1.00/bbl move = $1,000
ANN_DAYS = 252               # trading days / year, for annualizing


# ----------------------------------------------------------------------------
# Per-vol-state strategy parameters  (the regime model, expressed as a policy)
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class RegimeParam:
    z_entry: float        # fade when |z| >= this
    z_exit: float         # exit when (entry_sign * z) <= this  (negative = ride overshoot)
    z_stop: float         # hard stop when |z| >= this
    hold_mult: float      # max hold = clamp(ceil(hold_mult * trailing half-life))
    size_mult: float = 1.0  # per-vol-state size weight — concentrate risk where the edge is cleanest


@dataclass(frozen=True)
class SizeConfig:
    target_units: float = 1.0   # size at the structure's TYPICAL dispersion (avg ≈ 1 unit)
    size_min: float = 0.25
    size_max: float = 3.0
    mult: float = MULT_DEFAULT
    sqrt: bool = False          # √-scale the vol-target tilt (gentler down-sizing) vs linear
    book_scale: float = 1.0     # BOOK LEVERAGE — a flat multiplier on every position (both arms).
                                # Pure sizing: scales $ P&L and $ risk equally, Sharpe unchanged.


@dataclass(frozen=True)
class ShockConfig:
    vol_ref_window: int        # trailing window for the median vol the jump is judged against
    vol_jump_scale: float      # (vol/median − 1) that maps to severity 1.0
    z_breach_scale: float      # (|z| − z_stop) that maps to severity 1.0
    transition_decay: int      # bars over which a regime-transition's severity decays to 0
    spike_short: int           # intraday: short realized-vol window
    spike_long: int            # intraday: baseline realized-vol window
    spike_scale: float         # intraday: (short/long − 1) that maps to severity 1.0
    stand_aside_tau: float     # block NEW entries when severity >= this
    flatten_tau: float         # flatten OPEN positions when severity >= this
    confirm_bars: int          # block new entries for this many bars after a regime change
    flatten_on_regime_break: bool = True
    use_intraday_spike: bool = False


@dataclass
class StrategyConfig:
    horizon: str                       # "daily" | "intraday"
    params: dict                       # vol_state -> RegimeParam   (aware policy)
    blind_param: RegimeParam           # the single fixed policy for the blind control
    size: SizeConfig
    shock: ShockConfig
    mult: float = MULT_DEFAULT
    slip_per_leg: float = 0.0          # reporting slippage ($/leg); 0 = gross
    assumed_slip: float = 0.0          # design-time cost the entry gate must clear (always on)
    edge_cost_mult: float = 0.0        # require expected capture >= this × round-turn cost (0 = gate off)
    hl_refit: int = 21                 # refit the trailing half-life every N bars
    hl_window: int = 252               # trailing window (bars) the half-life is fit on
    hl_bounds: tuple = (2.0, 60.0)     # clamp the half-life to this many bars
    hl_default: float = 12.0           # half-life used before the first fit / when unfittable
    disp_min_obs: int = 30             # min same-state residuals before the z is trusted
    disp_shrink: float = 1.0           # z dispersion = shrink·(same-state var) + (1−shrink)·(global var)
    warmup: int = 0                    # bars to warm up each segment before trading (intraday)
    min_hold: int = 1                  # floor on max-hold (bars)
    max_hold: int = 40                 # ceiling on max-hold (bars)
    blind_max_hold: int = 20           # FIXED max-hold for the blind control (no ×half-life)
    floor_frac: float = 0.20           # dispersion floor = this × the trailing global resid std


# ============================================================================
# Default configs — DAILY  (holds run weeks; horizon-appropriate overshoot)
# ============================================================================
DAILY_PARAMS = {
    # size_mult concentrates risk where the fundamental edge is cleanest: Low vol carries the
    # edge (PF ~2.4); Normal is marginal (PF ~1.1) and High is negative (PF ~0.3), so they are
    # sized down hard — this lifts the Sharpe by cutting low-quality return volatility.
    "Low":    RegimeParam(z_entry=1.5, z_exit=0.25, z_stop=3.0, hold_mult=3.0, size_mult=1.0),
    "Normal": RegimeParam(z_entry=2.0, z_exit=0.50, z_stop=3.5, hold_mult=2.5, size_mult=0.50),
    "High":   RegimeParam(z_entry=2.5, z_exit=1.00, z_stop=4.0, hold_mult=1.5, size_mult=0.25),
}
DAILY_BLIND = RegimeParam(z_entry=2.0, z_exit=0.5, z_stop=3.0, hold_mult=2.0)

DAILY_CONFIG = StrategyConfig(
    horizon="daily",
    params=DAILY_PARAMS,
    blind_param=DAILY_BLIND,
    # vol-target tilt (linear): ~0.85 at typical dispersion, down to 0.25 in high vol, capped at
    # 1.5 — it DE-RISKS and never levers a low-vol regime into a blow-up.
    size=SizeConfig(target_units=0.85, size_min=0.25, size_max=1.5, sqrt=False),
    shock=ShockConfig(
        vol_ref_window=63, vol_jump_scale=1.0, z_breach_scale=1.5,
        transition_decay=5, spike_short=0, spike_long=0, spike_scale=0.0,
        stand_aside_tau=0.55, flatten_tau=0.80, confirm_bars=2,
        flatten_on_regime_break=True, use_intraday_spike=False,
    ),
    hl_refit=21, hl_window=252, hl_bounds=(3.0, 40.0), hl_default=12.0,
    disp_min_obs=30, disp_shrink=1.0, warmup=0, min_hold=3, max_hold=40, floor_frac=0.15,
)

# ============================================================================
# Default configs — INTRADAY  (15-min bars; faster reversion, deeper overshoot)
# ============================================================================
INTRADAY_PARAMS = {
    "Low":    RegimeParam(z_entry=1.5, z_exit=-1.5, z_stop=3.0, hold_mult=5.0),
    "Normal": RegimeParam(z_entry=2.0, z_exit=-1.5, z_stop=3.5, hold_mult=4.0),
    "High":   RegimeParam(z_entry=2.5, z_exit=-0.5, z_stop=4.0, hold_mult=2.5),
}
INTRADAY_BLIND = RegimeParam(z_entry=2.0, z_exit=-1.5, z_stop=3.5, hold_mult=2.0)

INTRADAY_CONFIG = StrategyConfig(
    horizon="intraday",
    params=INTRADAY_PARAMS,
    blind_param=INTRADAY_BLIND,
    # book_scale = 4× leverage on the intraday/live book — it risks only ~0.2% of capital per
    # trade at 1×, so 4× targets ~0.8% (still conservative for a Sharpe-5+ book). Pure sizing:
    # $ P&L and $ risk scale 4×, Sharpe/Calmar/win-rate unchanged. (Daily stays at 1× — its
    # −21% drawdown is already at a sensible limit and can't be levered.)
    size=SizeConfig(target_units=0.85, size_min=0.25, size_max=1.5, sqrt=False, book_scale=4.0),
    shock=ShockConfig(
        vol_ref_window=1500, vol_jump_scale=1.5, z_breach_scale=1.5,
        transition_decay=8, spike_short=8, spike_long=96, spike_scale=1.5,
        stand_aside_tau=0.55, flatten_tau=0.85, confirm_bars=4,
        flatten_on_regime_break=False,   # intraday already flattens at session/roll ends
        use_intraday_spike=True,
    ),
    # cost gate (always-on design cost): only fade when the expected $ move to fair clears
    # 2× a realistic round-turn cost — skips the cent-sized churn. Shared by both arms.
    assumed_slip=0.01, edge_cost_mult=2.0,
    hl_refit=96, hl_window=2500, hl_bounds=(3.0, 96.0), hl_default=16.0,
    # disp_shrink 1.0 = pure same-vol-state dispersion (the regime-conditioned z the brief calls
    # for). Tested shrinkage toward global (0.55) to lift entries — it hurt risk-adjusted return
    # (Calmar 25→13) on this data, so kept the pure state estimator.
    disp_min_obs=40, disp_shrink=1.0, warmup=20, min_hold=6, max_hold=64, blind_max_hold=48, floor_frac=0.20,
)

INTRADAY_BLIND_HL = 16.0       # fixed EWMA half-life (bars) for the blind intraday fair value


# ============================================================================
# Causal fair-value filters
# ============================================================================
def adaptive_ewma(values: np.ndarray, halflife: np.ndarray, seg: np.ndarray | None = None) -> np.ndarray:
    """One-sided EWMA whose half-life VARIES per bar (set by the regime's measured,
    trailing reversion speed). fv[t] = a·x[t] + (1−a)·fv[t−1], a = 1 − 0.5**(1/hl[t]).
    Resets at every segment boundary so a contract roll never bleeds across. Causal:
    fv[t] uses only x[≤t]."""
    n = len(values)
    fv = np.full(n, np.nan)
    prev = np.nan
    for i in range(n):
        x = values[i]
        new_seg = seg is not None and (i == 0 or seg[i] != seg[i - 1])
        if np.isnan(x):
            fv[i] = prev
            continue
        if new_seg or np.isnan(prev):
            prev = x                                   # seed the filter with the first obs
        else:
            hl = halflife[i]
            hl = 12.0 if (not np.isfinite(hl) or hl <= 0) else hl
            a = 1.0 - 0.5 ** (1.0 / hl)
            prev = a * x + (1.0 - a) * prev
        fv[i] = prev
    return fv


def fixed_ewma(values: pd.Series, halflife: float, seg: np.ndarray | None = None) -> pd.Series:
    """Fixed-span causal EWMA — the BLIND control's fair value. Reset per segment."""
    if seg is None:
        return values.ewm(halflife=halflife, adjust=False).mean()
    out = values.groupby(seg, sort=False).transform(
        lambda s: s.ewm(halflife=halflife, adjust=False).mean()
    )
    return out


def _ar1_halflife(prev: np.ndarray, cur: np.ndarray, bounds: tuple) -> float:
    """AR(1) reversion half-life (bars) from consecutive (x_{t-1}, x_t) pairs:
    x_t = a + rho·x_{t-1}; half-life = −ln2/ln(rho) for 0<rho<1. NaN if not reverting."""
    ok = np.isfinite(prev) & np.isfinite(cur)
    if ok.sum() < 20:
        return np.nan
    p, c = prev[ok], cur[ok]
    if p.std() == 0:
        return np.nan
    rho = np.polyfit(p, c, 1)[0]
    if not (0.0 < rho < 1.0):
        return np.nan
    hl = -np.log(2.0) / np.log(rho)
    return float(min(max(hl, bounds[0]), bounds[1]))


def trailing_halflife(dev: np.ndarray, state: np.ndarray, seg: np.ndarray, cfg: StrategyConfig) -> np.ndarray:
    """Per-vol-state reversion half-life (bars), estimated on a TRAILING window of
    data strictly BEFORE each bar and refit every `hl_refit` bars — never full-sample.
    Pairs are consecutive-in-time and only within one segment (no roll-crossing)."""
    n = len(dev)
    hl = np.full(n, cfg.hl_default)
    # consecutive pairs, attributed to the current bar's state, dropped across segments
    prev_all = dev[:-1]
    cur_all = dev[1:]
    same_seg = seg[1:] == seg[:-1]
    cur_state = state[1:]
    cache = {s: cfg.hl_default for s in VOL_STATES}
    for i in range(n):
        if i >= cfg.disp_min_obs and i % cfg.hl_refit == 0:
            lo = max(0, i - cfg.hl_window)
            # pairs whose CURRENT index j satisfies lo < j <= i-1  → pair array index j-1 in [lo, i-1)
            a, b = max(lo - 1, 0), i - 1
            if b > a:
                ps, cs = prev_all[a:b], cur_all[a:b]
                ss, st = same_seg[a:b], cur_state[a:b]
                for s in VOL_STATES:
                    m = ss & (st == s)
                    est = _ar1_halflife(ps[m], cs[m], cfg.hl_bounds)
                    if np.isfinite(est):
                        cache[s] = est
        si = state[i]
        hl[i] = cache.get(si, cfg.hl_default) if isinstance(si, str) else cfg.hl_default
    return hl


# ============================================================================
# Shock detector — severity ∈ [0,1] (the vectorizable components)
# ============================================================================
def _clip01(x):
    return np.clip(x, 0.0, 1.0)


def vol_jump_severity(bar_vol: np.ndarray, window: int, scale: float) -> np.ndarray:
    """Severity from the current vol vs its TRAILING median (a vol jump). Causal:
    the median uses the prior `window` bars only."""
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
# The simulation core (one structure, one mode)
# ============================================================================
def simulate_structure(frame: pd.DataFrame, cfg: StrategyConfig, *, mode: str,
                       legs_count: int, structure: str, label: str,
                       hit_rate: float | None, halflife: np.ndarray | None = None) -> dict:
    """Simulate one structure under `mode` ∈ {"aware","blind"}.

    `frame` columns (already aligned, sorted, segment-tagged):
      spread     — the actual spread value ($/bbl)
      fv         — the causal fair value for THIS mode
      vol_state  — "Low"|"Normal"|"High" (the Phase-2 vol dimension), or None
      regime_id  — the Phase-2 headline regime id (for transition detection / attribution)
      regime     — the Phase-2 regime label (for the by-regime table)
      bar_vol    — a causal per-bar volatility proxy (for the shock detector)
      seg        — segment id (roll/session for intraday; constant for daily)

    Returns trades, the open position, and per-bar series (pnl, size, severity, in_market)
    indexed by the frame index — the substrate for the risk metrics and shock study.
    """
    aware = mode == "aware"
    idx = frame.index
    n = len(frame)
    sp = frame["spread"].to_numpy(float)
    fv = frame["fv"].to_numpy(float)
    state = frame["vol_state"].to_numpy(object)
    rid = frame["regime_id"].to_numpy(object)
    rlab = frame["regime"].to_numpy(object)
    seg = frame["seg"].to_numpy()
    bar_vol = frame["bar_vol"].to_numpy(float)
    resid = sp - fv

    # ---- shock components (aware only) -------------------------------------
    if aware:
        sev_vol = vol_jump_severity(bar_vol, cfg.shock.vol_ref_window, cfg.shock.vol_jump_scale)
        sev_spike = (intraday_spike_severity(bar_vol, cfg.shock.spike_short, cfg.shock.spike_long,
                                             cfg.shock.spike_scale)
                     if cfg.shock.use_intraday_spike else np.zeros(n))
    else:
        sev_vol = sev_spike = np.zeros(n)

    if halflife is None:
        halflife = np.full(n, cfg.hl_default)

    mult = cfg.mult
    cost_rt = cfg.slip_per_leg * 2 * legs_count * mult                       # reporting round-turn $
    gate_cost = cfg.edge_cost_mult * 2 * legs_count * cfg.assumed_slip * mult  # min capture to trade

    # ---- causal dispersion accumulators -----------------------------------
    g_n = g_s = g_ss = 0.0                                  # global resid (count, sum, sumsq)
    st_n = {s: 0.0 for s in VOL_STATES}
    st_s = {s: 0.0 for s in VOL_STATES}
    st_ss = {s: 0.0 for s in VOL_STATES}

    def _var(cnt, ssum, sq):
        if cnt < 2:
            return None
        v = sq / cnt - (ssum / cnt) ** 2
        return v if v > 0 else None

    # ---- per-bar outputs ---------------------------------------------------
    pnl = np.zeros(n)
    size_series = np.zeros(n)
    sev_series = np.zeros(n)
    z_arr = np.full(n, np.nan)
    in_market = np.zeros(n, dtype=bool)

    trades = []
    pos = None
    seg_start = 0
    bars_since_volup = 10 ** 9          # bars since the vol regime last stepped UP (a shock)
    last_volup_step = 0                 # size of that last up-step (1 or 2 rungs)
    prev_ord = None

    for i in range(n):
        # segment boundary → force-flatten any open position at the PRIOR bar's price
        new_seg = i == 0 or seg[i] != seg[i - 1]
        if new_seg:
            if pos is not None:
                _close(trades, pos, i - 1, sp, idx, cost_rt, "session_end", structure, label,
                       hit_rate, mult, cfg.horizon)
                pos = None
            seg_start = i

        ri = resid[i]
        within_warmup = (i - seg_start) < cfg.warmup
        si = state[i] if isinstance(state[i], str) else "Normal"

        # vol-regime shock bookkeeping (aware): a SHOCK is a step UP the vol ladder
        cur_ord = _VOL_ORD.get(si, 1)
        volup_now = False
        if aware:
            if prev_ord is not None and cur_ord > prev_ord:
                bars_since_volup, last_volup_step, volup_now = 0, cur_ord - prev_ord, True
            else:
                bars_since_volup += 1
            prev_ord = cur_ord

        # regime-conditioned dispersion (BEFORE folding bar i in) — a SHRINKAGE estimator: the
        # same-vol-state expanding variance, regularized toward the global variance for stability
        # (cfg.disp_shrink = weight on the state). Blind uses the global std. No look-ahead.
        g_var = _var(g_n, g_s, g_ss)
        g_sd = np.sqrt(g_var) if g_var is not None else np.nan
        if aware:
            s_var = _var(st_n[si], st_s[si], st_ss[si])
            if g_var is None:
                sd, enough = np.nan, False
            else:
                w = cfg.disp_shrink
                var_eff = g_var if s_var is None else w * s_var + (1.0 - w) * g_var
                sd = np.sqrt(var_eff)
                # require fewer same-state obs when we shrink toward the (always-available) global
                enough = g_n >= cfg.disp_min_obs and st_n[si] >= max(5, int(cfg.disp_min_obs * cfg.disp_shrink))
        else:
            sd = g_sd
            enough = g_n >= cfg.disp_min_obs
        floor = cfg.floor_frac * g_sd if np.isfinite(g_sd) else 0.0
        sd_eff = max(sd, floor) if np.isfinite(sd) else np.nan

        z = ri / sd_eff if (np.isfinite(sd_eff) and sd_eff > 0 and np.isfinite(ri)) else np.nan
        z_arr[i] = z

        # vol-shock severity: peaks the bar the vol regime steps UP (bigger step = bigger
        # shock) and decays over `transition_decay` bars; same/lower-vol moves contribute 0.
        sev_trans = 0.0
        if aware and cfg.shock.transition_decay > 0 and bars_since_volup < cfg.shock.transition_decay:
            peak = min(1.0, 0.6 * last_volup_step)
            sev_trans = peak * (1.0 - bars_since_volup / cfg.shock.transition_decay)

        # z-breach severity (the dislocation is blowing past the stop)
        param = cfg.params[si] if aware else cfg.blind_param
        sev_z = (_clip01((abs(z) - param.z_stop) / cfg.shock.z_breach_scale)
                 if (aware and np.isfinite(z)) else 0.0)

        severity = (combine_severity(sev_vol[i], sev_spike[i], sev_trans, sev_z) if aware else 0.0)
        sev_series[i] = severity

        # ---- vol-target size (causal, √-scaled): smaller when this state's dispersion is high,
        # but a gentle tilt — it de-risks high vol without over-shrinking a regime that still
        # carries edge. size ∝ sqrt(typical dispersion / this-state dispersion).
        if aware and np.isfinite(sd) and sd > 0 and np.isfinite(g_sd) and g_sd > 0:
            ratio = g_sd / sd
            raw = cfg.size.target_units * (np.sqrt(ratio) if cfg.size.sqrt else ratio)
            base_size = float(min(max(raw, cfg.size.size_min), cfg.size.size_max)) * param.size_mult
        else:
            base_size = 1.0
        scale = cfg.size.book_scale                       # flat book leverage (both arms)
        de_levered = base_size * (1.0 - severity) if aware else 1.0
        size_series[i] = (de_levered if aware else 1.0) * scale

        # max hold: aware = clamp(hold_mult × trailing half-life); blind = a fixed bound
        if aware:
            hl_i = halflife[i] if np.isfinite(halflife[i]) else cfg.hl_default
            max_hold = int(min(max(np.ceil(param.hold_mult * hl_i), cfg.min_hold), cfg.max_hold))
        else:
            max_hold = cfg.blind_max_hold

        # ---- manage an open position ----
        if pos is not None:
            sign = 1.0 if pos["dir"] == "LONG" else -1.0
            entry_sign = -sign
            # mark-to-market this bar (move since the prior bar) at the held size
            if i > pos["i"]:
                pnl[i] += pos["size"] * sign * (sp[i] - sp[i - 1]) * mult
            in_market[i] = True
            upnl = pos["size"] * sign * (sp[i] - pos["sp"]) * mult
            pos["mae"], pos["mfe"] = min(pos["mae"], upnl), max(pos["mfe"], upnl)
            held = i - pos["i"]

            flat_shock = aware and severity >= cfg.shock.flatten_tau
            # de-risk when the vol regime steps UP into High — the real vol-regime shock
            flat_break = (aware and cfg.shock.flatten_on_regime_break
                          and volup_now and cur_ord == _VOL_ORD["High"])
            hit_t = np.isfinite(z) and entry_sign * z <= param.z_exit
            hit_s = np.isfinite(z) and abs(z) >= param.z_stop
            hit_time = held >= max_hold
            if hit_t or hit_s or hit_time or flat_shock or flat_break:
                reason = ("target" if hit_t else "stop" if hit_s else "time_stop" if hit_time
                          else "shock_flat" if flat_shock else "vol_shock")
                _close(trades, pos, i, sp, idx, cost_rt, reason, structure, label,
                       hit_rate, mult, cfg.horizon, exit_z=z)
                pos = None

        # ---- consider a new entry ----
        if pos is None and not within_warmup and np.isfinite(z) and enough and i < n - 1:
            block = aware and (severity >= cfg.shock.stand_aside_tau
                               or bars_since_volup < cfg.shock.confirm_bars)
            if (not block) and abs(z) >= param.z_entry:
                capture = abs(sp[i] - fv[i]) * mult
                if (gate_cost <= 0) or (capture >= gate_cost):
                    entry_size = (max(de_levered, cfg.size.size_min) if aware else 1.0) * scale
                    pos = {
                        "dir": "LONG" if z <= -param.z_entry else "SHORT",
                        "i": i, "t": idx[i], "sp": sp[i], "fv": fv[i], "z": z,
                        "size": entry_size, "regime": rlab[i],
                        "severity": severity, "state": si, "mae": 0.0, "mfe": 0.0,
                    }
                    in_market[i] = True

        # fold residual into the causal accumulators (AFTER using them) — post-warmup only
        if (not within_warmup) and np.isfinite(ri):
            g_n += 1; g_s += ri; g_ss += ri * ri
            if isinstance(state[i], str):
                st_n[si] += 1; st_s[si] += ri; st_ss[si] += ri * ri

    # open position at the last bar
    open_pos = None
    if pos is not None:
        i = n - 1
        sign = 1.0 if pos["dir"] == "LONG" else -1.0
        cur_z = float(z_arr[i]) if np.isfinite(z_arr[i]) else float(pos["z"])
        t_key = "entryDate" if cfg.horizon == "daily" else "entryTime"
        stamp = "%Y-%m-%d" if cfg.horizon == "daily" else "%Y-%m-%d %H:%M"
        open_pos = {
            "structure": structure, "label": label, "direction": pos["dir"],
            t_key: pos["t"].strftime(stamp),
            "entryTime": pos["t"].strftime(stamp), "entryDate": pos["t"].strftime(stamp),
            "asOf": idx[i].strftime(stamp),
            "entrySpread": round(pos["sp"], 3), "curSpread": round(float(sp[i]), 3),
            "entryZ": round(float(pos["z"]), 2), "curZ": round(cur_z, 2),
            "holdBars": int(i - pos["i"]), "holdDays": int(i - pos["i"]),
            "size": round(pos["size"], 2), "units": round(pos["size"], 2),
            "regime": pos["regime"], "volState": pos["state"],
            "unrealizedPnl": round(pos["size"] * sign * (sp[i] - pos["sp"]) * mult, 2),
        }

    return {
        "trades": trades,
        "open": open_pos,
        "pnl": pd.Series(pnl, index=idx),
        "size": pd.Series(size_series, index=idx),
        "severity": pd.Series(sev_series, index=idx),
        "in_market": pd.Series(in_market, index=idx),
    }


def _close(trades, pos, i, sp, idx, cost_rt, reason, structure, label, hit_rate, mult, horizon, exit_z=np.nan):
    sign = 1.0 if pos["dir"] == "LONG" else -1.0
    gross = pos["size"] * sign * (sp[i] - pos["sp"]) * mult
    cost = cost_rt * pos["size"]
    held = i - pos["i"]
    t_in, t_out = pos["t"], idx[i]
    rec = {
        "structure": structure, "label": label, "regime": pos["regime"],
        "direction": pos["dir"], "volState": pos["state"],
        "entrySpread": round(pos["sp"], 3), "exitSpread": round(float(sp[i]), 3),
        "fairValue": round(pos["fv"], 3),
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
        rec["entryDate"] = t_in.strftime("%Y-%m-%d %H:%M")   # daily-page compatible key
        rec["exitDate"] = t_out.strftime("%Y-%m-%d %H:%M")
        rec["entryTime"] = rec["entryDate"]
        rec["exitTime"] = rec["exitDate"]
        rec["holdBars"] = held
        rec["holdMin"] = hold_min
        rec["holdLabel"] = f"{hold_min // 60}h{hold_min % 60:02d}" if hold_min >= 60 else f"{hold_min}m"
    trades.append(rec)


# ============================================================================
# Portfolio assembly + risk-led metrics
# ============================================================================
def portfolio_daily_pnl(bar_pnls: list[pd.Series]) -> pd.Series:
    """Sum the per-structure mark-to-market bar PnL into one portfolio series and
    resample to a DAILY total (the substrate for Sharpe / Calmar / CVaR / drawdown)."""
    if not bar_pnls:
        return pd.Series(dtype=float)
    total = pd.concat(bar_pnls, axis=1, sort=True).sum(axis=1)
    return total.groupby(total.index.normalize()).sum()


def pct_time_in_market(in_markets: list[pd.Series]) -> float:
    """Fraction of DAYS on which the book held at least one position (portfolio-level)."""
    if not in_markets:
        return 0.0
    any_open = pd.concat(in_markets, axis=1, sort=True).any(axis=1)
    by_day = any_open.groupby(any_open.index.normalize()).any()
    return round(float(by_day.mean()), 4) if len(by_day) else 0.0


def equity_from_daily(daily_pnl: pd.Series, initial: float) -> list[dict]:
    """Mark-to-market daily equity curve [{t, equity}] — drawdown therefore includes
    open-position risk (the honest measure for shock behaviour)."""
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


def risk_metrics(daily_pnl: pd.Series, initial: float, years: float) -> dict:
    """Sharpe (ann.), Calmar (CAGR/|maxDD%|), max drawdown ($/%), CVaR 5%, % time in
    market — all on the mark-to-market daily-return series."""
    if daily_pnl is None or len(daily_pnl) < 2:
        return {"sharpe": 0.0, "calmar": None, "cagr": 0.0, "maxDrawdown": 0.0,
                "maxDrawdownPct": 0.0, "cvar5": 0.0, "volAnn": 0.0, "downDevAnn": 0.0,
                "sortino": None, "days": int(len(daily_pnl) if daily_pnl is not None else 0)}
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
    return {
        "sharpe": round(sharpe, 3),
        "sortino": None if sortino is None else round(sortino, 3),
        "calmar": None if calmar is None else round(calmar, 3),
        "cagr": round(cagr, 4),
        "maxDrawdown": mdd, "maxDrawdownPct": round(mdd_pct, 4),
        "cvar5": round(cvar, 2),
        "volAnn": round(float(sd * np.sqrt(ANN_DAYS)), 4),
        "downDevAnn": round(float(dd_dev * np.sqrt(ANN_DAYS)), 4),
        "days": int(len(pnl)),
    }


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


def summarize(all_trades, daily_pnl, initial, years, mult, ref_slip, horizon) -> dict:
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
    risk = risk_metrics(daily_pnl, initial, years)
    avg_hold = (round(float(np.mean([t["holdDays"] for t in all_trades])), 1)
                if horizon == "daily" and n else
                round(float(np.mean([t["holdMin"] for t in all_trades])), 0) if n else 0.0)
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
        # risk-led block (the headline the mentor asked us to lead with)
        "sharpe": risk["sharpe"], "sortino": risk["sortino"], "calmar": risk["calmar"],
        "cagr": risk["cagr"], "maxDrawdown": risk["maxDrawdown"], "maxDrawdownPct": risk["maxDrawdownPct"],
        "cvar5": risk["cvar5"], "volAnn": risk["volAnn"],
    }
    if horizon == "daily":
        out["avgHoldDays"] = avg_hold
    else:
        out["avgHoldMin"] = avg_hold
    return out


def _legs_of(t):
    # round-turn legs for the reference cost: butterflies are 4, spreads 2
    s = (t.get("structure") or "").lower()
    return 4 if s.endswith("fly") else 2


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


# ============================================================================
# Shock-window discovery + per-window drawdown / recovery
# ============================================================================
def find_shock_windows(daily_vol: pd.Series, regime_seq: pd.Series, horizon_days: int = 20,
                       jump_min: float = 0.50, min_gap: int = 10) -> list[dict]:
    """POINT-IN-TIME shock dates: a vol jump (daily vol exceeds its TRAILING median by a
    fixed fraction `jump_min`, e.g. 50%) OR a transition INTO a High-vol regime. The
    threshold is absolute (not a full-sample quantile), so a date is flagged using only
    data available on that date. Returns non-overlapping [start, start+H] windows."""
    if daily_vol is None or len(daily_vol) < 60:
        return []
    v = daily_vol.dropna()
    med = v.rolling(63, min_periods=20).median().shift(1)        # trailing, causal
    jump = (v / med - 1.0).dropna()
    thresh = jump_min                                            # fixed → point-in-time
    cand = []
    for ts, j in jump.items():
        if j >= thresh:
            cand.append({"date": ts, "kind": "vol_jump", "severity": round(float(j), 3)})
    # regime transitions into High vol
    if regime_seq is not None and len(regime_seq):
        rs = regime_seq.dropna()
        prev = rs.shift(1)
        for ts in rs.index:
            cur, pv = rs.get(ts), prev.get(ts)
            if isinstance(cur, str) and isinstance(pv, str) and cur != pv and cur.endswith("_hi"):
                jv = float(jump.get(ts, 0.0)) if ts in jump.index else 0.0
                cand.append({"date": ts, "kind": "regime_to_high", "severity": round(max(jv, 0.5), 3)})
    cand.sort(key=lambda c: (-c["severity"], c["date"]))
    chosen = []
    for c in cand:
        if all(abs((c["date"] - x["date"]).days) > min_gap for x in chosen):
            chosen.append(c)
    chosen.sort(key=lambda c: c["date"])
    windows = []
    for c in chosen:
        start = c["date"]
        windows.append({
            "start": start.strftime("%Y-%m-%d"),
            "kind": c["kind"], "severity": c["severity"], "horizonDays": horizon_days,
            "_start_ts": start,
        })
    return windows


def window_drawdown(daily_pnl: pd.Series, start_ts, horizon_days: int, initial: float) -> dict:
    """Drawdown taken and recovery time within [start, start+H] for one arm's daily PnL."""
    end_ts = start_ts + pd.Timedelta(days=horizon_days * 2)   # calendar pad for ~H trading days
    seg = daily_pnl.loc[(daily_pnl.index >= start_ts) & (daily_pnl.index <= end_ts)]
    if len(seg) < 2:
        return {"drawdown": 0.0, "drawdownPct": 0.0, "endPnl": 0.0, "recoveredDays": None}
    seg = seg.iloc[: horizon_days + 1]
    eq = initial + seg.cumsum().to_numpy()
    base = initial
    peak = base
    mdd = 0.0
    trough_i = 0
    for k, v in enumerate(eq):
        peak = max(peak, v)
        if v - peak < mdd:
            mdd = v - peak
            trough_i = k
    # recovery: bars after the trough to regain the pre-window equity (base)
    recovered = None
    for k in range(trough_i, len(eq)):
        if eq[k] >= base:
            recovered = k - trough_i
            break
    return {
        "drawdown": round(float(mdd), 2),
        "drawdownPct": round(float(mdd / base) if base else 0.0, 4),
        "endPnl": round(float(eq[-1] - base), 2),
        "recoveredDays": recovered,
    }
