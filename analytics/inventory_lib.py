"""
inventory_lib.py — the shared analytical core for the CRUDE INVENTORY market-impact
framework (Wednesday assignment).

WHAT THIS DOES, IN PLAIN ENGLISH
--------------------------------
Every Wednesday at 10:30 a.m. ET the U.S. Energy Information Administration (EIA)
publishes how much crude oil sits in U.S. tanks. The market does NOT react to the
raw number — it reacts to the SURPRISE: how far the print landed from what people
already expected. This module builds, end to end, the machinery to:

  1. Pull the EIA weekly data (crude + the supply/demand flows + Cushing, plus the
     two products gasoline & distillate so we can cross-check).
  2. Build a leak-free EXPECTED build/draw (our stand-in for the paywalled analyst
     consensus) from (a) the 5-year seasonal norm, (b) last week's supply/demand
     balance, and (c) recent momentum — fit walk-forward so it never sees the future.
  3. Define the SURPRISE = actual - expected, and standardise it (surprise_z).
  4. Run an EVENT STUDY: for every historical release, measure how WTI/Brent and the
     key spreads moved on release day, and regress that move on the surprise. The
     slope tells us "how many % oil moves per 1 MMbbl of surprise"; the R^2 tells us
     "how much of release-day's move inventories actually explain."
  5. CONDITION that relationship on market state (volatility regime, term structure,
     season, product alignment, surprise size) to answer the assignment's core
     question: WHEN did inventories matter, and when were they ignored?
  6. Produce a VERDICT (bullish / bearish / neutral) with confidence, the
     products/spreads most likely to move, and the top-3 driving factors — both as a
     forward base-case (pre-release) and as a post-release read for the live engine.

Everything here is deliberately interpretable: every number can be traced to the
exact driver that produced it.

Data sources (all free):
  * EIA Open Data API v2 (weekly petroleum status report) — via analytics/common.py.
  * analytics/out/panel.parquet — the pre-built daily price/spread panel (2021->),
    used for the multi-year spread reactions in the event study.
  * Yahoo Finance continuous front futures (CL=F, BZ=F, RB=F, HO=F) — fresh daily
    closes that extend the outright price reactions right up to today.

Run the analysis with:  python analytics/run_inventory_analysis.py
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from common import OUT_DIR, load_env, eia_series, yahoo_daily

# ---------------------------------------------------------------------------
# EIA series ids (legacy CATEGORY.SERIES.FREQ form the v2 /seriesid route wants).
# Stocks are reported in THOUSAND barrels; flows in THOUSAND barrels/day (kbd).
# ---------------------------------------------------------------------------
SERIES = {
    "crude":      "PET.WCESTUS1.W",            # U.S. commercial crude stocks ex-SPR (kbbl)
    "cushing":    "PET.W_EPC0_SAX_YCUOK_MBBL.W",  # Cushing, OK crude stocks (kbbl)
    "spr":        "PET.WCSSTUS1.W",            # Strategic Petroleum Reserve (kbbl)
    "gasoline":   "PET.WGTSTUS1.W",            # total motor gasoline stocks (kbbl)
    "distillate": "PET.WDISTUS1.W",            # distillate fuel oil stocks (kbbl)
    "refutil":    "PET.WPULEUS3.W",            # refinery utilization (% of capacity)
    "production": "PET.WCRFPUS2.W",            # crude field production (kbd)
    "imports":    "PET.WCEIMUS2.W",            # crude imports (kbd)
    "exports":    "PET.WCREXUS2.W",            # crude exports (kbd)
    "runs":       "PET.WCRRIUS2.W",            # refinery crude inputs / throughput (kbd)
}

# Yahoo continuous-front futures for fresh outright price reactions.
YAHOO = {"wti": "CL=F", "brent": "BZ=F", "rbob": "RB=F", "ho": "HO=F"}

# Spread/instrument columns in the panel we test for "which spreads react".
PANEL_REACTORS = [
    "wti", "brent", "brent_wti", "wti_m1m2", "crack_321_wti", "ho_wti", "gasoil_brent",
]

KBBL_TO_MM = 1.0 / 1000.0   # thousand bbl -> million bbl
DAYS_PER_WEEK = 7.0


# ===========================================================================
# 1. DATA LOADING
# ===========================================================================
def fetch_weekly(length: int = 600, cache_hours: float = 6.0) -> pd.DataFrame:
    """Pull every EIA weekly series we need into one weekly DataFrame indexed by the
    report week-ending FRIDAY. Stocks are converted to MMbbl; flows stay in kbd.

    `length` ~600 weeks ≈ 11.5 years so the 5-prior-year seasonal norm is always
    populated even for the oldest rows we keep. Set cache_hours=0 for the live engine."""
    key = load_env().get("EIA_API_KEY", "")
    cols = {}
    for name, sid in SERIES.items():
        rows = eia_series(sid, key, length=length, cache_hours=cache_hours)
        if not rows:
            continue
        idx = pd.to_datetime([p for p, _ in rows])
        vals = np.array([v for _, v in rows], dtype=float)
        if name in ("crude", "cushing", "spr", "gasoline", "distillate"):
            vals = vals * KBBL_TO_MM            # kbbl -> MMbbl
        cols[name] = pd.Series(vals, index=idx).sort_index()
    df = pd.DataFrame(cols).sort_index()
    df.index.name = "period"                    # the week-ending Friday
    return df


def fetch_prices(cache_hours: float = 6.0) -> pd.DataFrame:
    """Fresh daily continuous-front closes from Yahoo for WTI/Brent/RBOB/HO ($/bbl
    where natural; products left in their native units — we only use RETURNS, which
    are unit-free, so no conversion is needed for the event study)."""
    out = {}
    for name, sym in YAHOO.items():
        d = yahoo_daily(sym, "5y", cache_hours=cache_hours)
        if d:
            s = pd.Series(d)
            s.index = pd.to_datetime(s.index)
            out[name] = s.sort_index()
    px = pd.DataFrame(out).sort_index()
    px.index.name = "date"
    return px


def load_panel() -> pd.DataFrame:
    """The pre-built daily price/spread panel (2021->2026), our source for multi-year
    SPREAD reactions (calendar, cracks, brent_wti) that Yahoo fronts don't give us."""
    p = OUT_DIR / "panel.parquet"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_parquet(p)


# ===========================================================================
# 2. THE WEEKLY FRAME  (release calendar, WoW changes, balance, seasonality)
# ===========================================================================
def release_date(period: pd.Timestamp) -> pd.Timestamp:
    """Map a report week-ending FRIDAY to the day the market reacts. The EIA WPSR is
    released the following WEDNESDAY 10:30 a.m. ET — i.e. Friday + 5 days. (Federal
    holidays push it to Thursday; we later snap to the next available trading day, so
    a holiday simply shifts the measured reaction to Thu, which is what we want.)"""
    return period + pd.Timedelta(days=5)


def week_of_year(ts: pd.Timestamp) -> int:
    return (ts - pd.Timestamp(ts.year, 1, 1)).days // 7 + 1


def seasonal_norm(weekly: pd.Series, prior_years: int = 5) -> pd.Series:
    """For each week, the MEAN of the same week-of-year across the `prior_years`
    PREVIOUS calendar years (strictly earlier — leak-free). Used to seasonally judge
    a level (e.g. is crude high/low for the time of year)."""
    df = pd.DataFrame({"v": weekly})
    df["year"] = df.index.year
    df["woy"] = [week_of_year(ts) for ts in df.index]
    out = pd.Series(index=weekly.index, dtype=float)
    for ts, row in df.iterrows():
        pri = df[(df.woy == row.woy) & (df.year >= row.year - prior_years) & (df.year < row.year)]["v"]
        if len(pri) >= 2:
            out[ts] = pri.mean()
    return out


def seasonal_wow_norm(wow: pd.Series, prior_years: int = 5) -> pd.Series:
    """The seasonally-NORMAL weekly CHANGE: mean WoW change for this week-of-year over
    the prior years. This is the naive 'expected build/draw' a seasonal analyst uses."""
    return seasonal_norm(wow, prior_years)


def seasonal_z(weekly: pd.Series, prior_years: int = 5) -> pd.Series:
    """z-score of a level vs the prior-years seasonal mean/std (how unusual is today's
    stock level for this time of year). Negative = tighter than normal = bullish."""
    df = pd.DataFrame({"v": weekly})
    df["year"] = df.index.year
    df["woy"] = [week_of_year(ts) for ts in df.index]
    out = pd.Series(index=weekly.index, dtype=float)
    for ts, row in df.iterrows():
        pri = df[(df.woy == row.woy) & (df.year >= row.year - prior_years) & (df.year < row.year)]["v"]
        if len(pri) >= 2 and pri.std(ddof=0) > 0:
            out[ts] = (row.v - pri.mean()) / pri.std(ddof=0)
    return out


def build_frame(weekly: pd.DataFrame) -> pd.DataFrame:
    """Turn the raw weekly EIA series into the analysis frame: WoW changes, the
    implied supply/demand balance, the seasonal norms and z-scores, the release date,
    and the season label. One row per EIA report week."""
    f = pd.DataFrame(index=weekly.index)
    f["period"] = weekly.index
    f["release_date"] = [release_date(p) for p in weekly.index]

    # Levels (MMbbl).
    for c in ("crude", "cushing", "spr", "gasoline", "distillate", "refutil"):
        if c in weekly:
            f[c] = weekly[c]

    # Week-over-week changes (MMbbl). Negative = DRAW (bullish), positive = BUILD.
    for c in ("crude", "cushing", "gasoline", "distillate"):
        if c in weekly:
            f[f"{c}_wow"] = weekly[c].diff()

    # Implied weekly balance from the crude flows (MMbbl/week):
    #   (production + imports) - (refinery runs + exports), in kbd, * 7 days / 1000.
    if all(c in weekly for c in ("production", "imports", "runs", "exports")):
        supply = weekly["production"] + weekly["imports"]
        disp = weekly["runs"] + weekly["exports"]
        f["implied_balance"] = (supply - disp) * DAYS_PER_WEEK * KBBL_TO_MM
        for c in ("production", "imports", "runs", "exports"):
            f[c] = weekly[c]

    # Seasonal context for crude.
    f["crude_seasonal_wow"] = seasonal_wow_norm(f["crude_wow"])
    f["crude_z"] = seasonal_z(weekly["crude"]) if "crude" in weekly else np.nan

    # Days of supply = stocks / daily refinery runs.
    if "runs" in weekly:
        f["days_supply"] = weekly["crude"] / (weekly["runs"] * KBBL_TO_MM)

    # Season label (drives the seasonal expectation).
    def season(m):
        if m in (10, 11, 12, 1, 2, 3):
            return "heating"
        if m in (4, 5, 6, 7, 8):
            return "driving"
        return "shoulder"
    f["season"] = [season(p.month) for p in f["period"]]
    return f


# ===========================================================================
# 3. EXPECTED BUILD (consensus proxy)  +  SURPRISE
# ===========================================================================
def add_expected_and_surprise(f: pd.DataFrame, min_train: int = 78) -> pd.DataFrame:
    """Build a LEAK-FREE expected weekly crude change and the surprise around it.

    The analyst consensus is paywalled, so we reconstruct an ex-ante expectation from
    information available the DAY BEFORE the release:
        expected_wow_t = OLS( seasonal_wow_t , lag1_wow , lag1_balance )
    fit walk-forward on an EXPANDING window (only weeks strictly before t), so the
    model never peeks at the value it is predicting. Features:
      * seasonal_wow_t  — the normal change for this week-of-year (prior years only).
      * lag1_wow        — last week's actual change (known; persistence/momentum).
      * lag1_balance    — last week's implied supply/demand balance (known; flows are
                          sticky week to week, so last week's balance forecasts this
                          week's draw/build).
    surprise = actual_wow - expected_wow.  surprise_z standardises it by the expanding
    standard deviation of the model's own past errors, so "1 sigma" means a typically-
    sized miss. We also keep a simpler SEASONAL-NAIVE expectation (just seasonal_wow)
    for intuition/robustness."""
    f = f.copy()
    f["lag1_wow"] = f["crude_wow"].shift(1)
    f["lag1_balance"] = f["implied_balance"].shift(1) if "implied_balance" in f else np.nan

    # Seasonal-naive expectation & its surprise (baseline).
    f["expected_seasonal"] = f["crude_seasonal_wow"]
    f["surprise_seasonal"] = f["crude_wow"] - f["expected_seasonal"]

    feats = ["crude_seasonal_wow", "lag1_wow", "lag1_balance"]
    have = [c for c in feats if c in f and f[c].notna().any()]
    y = f["crude_wow"]

    exp_model = pd.Series(index=f.index, dtype=float)
    rows = f.reset_index(drop=True)
    for i in range(len(rows)):
        train = rows.iloc[:i]                              # strictly earlier weeks
        train = train.dropna(subset=have + ["crude_wow"])
        cur = rows.iloc[i]
        if len(train) < min_train or any(pd.isna(cur[c]) for c in have):
            continue
        X = np.column_stack([np.ones(len(train))] + [train[c].values for c in have])
        b, *_ = np.linalg.lstsq(X, train["crude_wow"].values, rcond=None)
        xrow = np.array([1.0] + [cur[c] for c in have])
        exp_model.iloc[i] = float(xrow @ b)

    f["expected_model"] = exp_model.values
    # Primary expectation: the model where available, else the seasonal naive.
    f["expected"] = f["expected_model"].fillna(f["expected_seasonal"])
    f["surprise"] = f["crude_wow"] - f["expected"]

    # Standardise by the EXPANDING std of past surprises (leak-free).
    s = f["surprise"]
    exp_std = s.shift(1).expanding(min_periods=26).std()
    f["surprise_z"] = s / exp_std
    f["surprise_std"] = exp_std
    return f


# ===========================================================================
# 4. MARKET-STATE CONTEXT  (volatility regime, term structure, alignment)
# ===========================================================================
def add_market_state(f: pd.DataFrame, panel: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """Attach the market backdrop KNOWN GOING INTO each release (so it can condition
    the reaction without look-ahead): realized-vol regime, WTI term structure, and a
    product-alignment flag. We read these as of the trading day BEFORE the release."""
    f = f.copy()
    # Build a daily reference of vol & structure from the panel (falls back to NaN).
    idx = panel.index.union(prices.index) if not panel.empty else prices.index
    ref = pd.DataFrame(index=idx).sort_index()
    panel_rvol = panel["wti_rvol20"].reindex(idx) if (not panel.empty and "wti_rvol20" in panel) else pd.Series(index=idx, dtype=float)
    # The prebuilt panel can lag the live release by weeks; extend realized vol with a
    # FRESH estimate from the live WTI price so the current regime label isn't stale.
    if "wti" in prices and not prices["wti"].dropna().empty:
        fresh_rvol = (prices["wti"].pct_change().rolling(20).std() * np.sqrt(252)).reindex(idx)
        ref["rvol20"] = panel_rvol.combine_first(fresh_rvol)   # panel where present, fresh after
    else:
        ref["rvol20"] = panel_rvol
    # Term structure has no free fresh source here, so it stays panel-derived (it moves
    # slowly; the asof read still returns the last known curve state).
    ref["m1m2"] = panel["wti_m1m2"].reindex(idx) if (not panel.empty and "wti_m1m2" in panel) else pd.Series(index=idx, dtype=float)
    ref["m1m12"] = panel["wti_m1m12"].reindex(idx) if (not panel.empty and "wti_m1m12" in panel) else pd.Series(index=idx, dtype=float)

    def asof(series, when):
        if series is None or series.dropna().empty:
            return np.nan
        s = series.dropna()
        s = s[s.index < when]            # strictly before the release -> no leak
        return float(s.iloc[-1]) if len(s) else np.nan

    vols, structs, m1m2s = [], [], []
    for _, row in f.iterrows():
        when = row["release_date"]
        rv = asof(ref.get("rvol20"), when)
        m12 = asof(ref.get("m1m12"), when)
        m2 = asof(ref.get("m1m2"), when)
        vols.append("Low" if rv < 0.30 else "High" if rv > 0.50 else "Normal" if rv == rv else None)
        structs.append("Backwardation" if m12 > 0.5 else "Contango" if m12 < -0.5 else "Flat" if m12 == m12 else None)
        m1m2s.append(m2)
    f["vol_regime"] = vols
    f["wti_struct"] = structs
    f["wti_m1m2"] = m1m2s

    # Product alignment: do crude & products tell the same story this week?
    #   A crude DRAW that comes with product DRAWS is a clean bullish signal; a crude
    #   draw with product BUILDS is muddier. We score agreement of the three WoW signs
    #   relative to their seasonal norms (here, simple signs of the WoW changes).
    def align(row):
        signs = [np.sign(row.get(f"{c}_wow", np.nan)) for c in ("crude", "gasoline", "distillate")]
        signs = [s for s in signs if s == s and s != 0]
        if len(signs) < 2:
            return "n/a"
        if all(s < 0 for s in signs):
            return "all-draw"
        if all(s > 0 for s in signs):
            return "all-build"
        return "mixed"
    f["product_alignment"] = f.apply(align, axis=1)
    return f


# ===========================================================================
# 5. EVENT STUDY  (release-day reactions + reaction-vs-surprise regression)
# ===========================================================================
def _reaction(series: pd.Series, when: pd.Timestamp) -> float:
    """Release-day return of a price series: close on the first trading day >= release
    date divided by the previous trading day's close, minus 1. Captures the Tue->Wed
    move (or Wed->Thu on a holiday week)."""
    s = series.dropna()
    if s.empty:
        return np.nan
    after = s[s.index >= when]
    before = s[s.index < when]
    if after.empty or before.empty:
        return np.nan
    return float(after.iloc[0] / before.iloc[-1] - 1.0)


def _reaction_diff(series: pd.Series, when: pd.Timestamp) -> float:
    """Release-day CHANGE (level difference, for spreads where a return is meaningless,
    e.g. brent_wti or a calendar spread): value on/after release minus value before."""
    s = series.dropna()
    if s.empty:
        return np.nan
    after = s[s.index >= when]
    before = s[s.index < when]
    if after.empty or before.empty:
        return np.nan
    return float(after.iloc[0] - before.iloc[-1])


def add_reactions(f: pd.DataFrame, panel: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """For each release, the WTI & Brent outright % reactions (fresh Yahoo fronts) and
    the level-change reactions of the key spreads (from the panel)."""
    f = f.copy()
    for name in ("wti", "brent"):
        if name in prices:
            f[f"rxn_{name}"] = [_reaction(prices[name], w) for w in f["release_date"]]
    # Spread reactions from the panel (level changes; brent_wti/cracks/calendar).
    for col in PANEL_REACTORS:
        if not panel.empty and col in panel:
            if col in ("wti", "brent"):
                f[f"rxn_panel_{col}"] = [_reaction(panel[col], w) for w in f["release_date"]]
            else:
                f[f"rxn_{col}"] = [_reaction_diff(panel[col], w) for w in f["release_date"]]
    return f


@dataclass
class Fit:
    n: int
    beta: float            # slope: reaction per unit surprise
    intercept: float
    r2: float
    corr: float
    t_stat: float
    per_1mm: float         # reaction (in the y units) per +1 MMbbl surprise
    per_1sigma: float      # reaction per +1 sigma surprise


def regress(x: pd.Series, y: pd.Series, sigma: float | None = None) -> Fit | None:
    """OLS y = a + b*x with R^2, correlation and a t-stat on the slope. `sigma` (the
    surprise std) lets us also express the slope as 'move per 1 sigma surprise'."""
    m = pd.concat([x, y], axis=1).dropna()
    if len(m) < 8:
        return None
    xv, yv = m.iloc[:, 0].values, m.iloc[:, 1].values
    if np.std(xv) == 0:
        return None
    b, a = np.polyfit(xv, yv, 1)
    yhat = a + b * xv
    ss_res = float(np.sum((yv - yhat) ** 2))
    ss_tot = float(np.sum((yv - yv.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    corr = float(np.corrcoef(xv, yv)[0, 1])
    n = len(m)
    se = np.sqrt(ss_res / max(n - 2, 1)) / (np.std(xv) * np.sqrt(n)) if n > 2 else np.nan
    t_stat = float(b / se) if se and se == se and se > 0 else np.nan
    return Fit(n=n, beta=float(b), intercept=float(a), r2=float(r2), corr=corr,
               t_stat=t_stat, per_1mm=float(b),
               per_1sigma=float(b * sigma) if sigma else np.nan)


def event_study(f: pd.DataFrame, y_col: str = "rxn_wti", x_col: str = "surprise") -> dict:
    """The headline relationship: how release-day WTI move depends on the surprise,
    overall AND conditioned on market state. Returns a dict ready to serialise."""
    sigma = float(f[x_col].std())
    overall = regress(f[x_col], f[y_col], sigma)

    def by(col):
        out = {}
        for key, sub in f.groupby(col):
            if key is None or (isinstance(key, float) and pd.isna(key)):
                continue
            fit = regress(sub[x_col], sub[y_col], sigma)
            if fit:
                out[str(key)] = fit.__dict__
        return out

    # Magnitude buckets: small vs large surprises (|z| <> 1).
    f = f.copy()
    f["surp_bucket"] = np.where(f["surprise_z"].abs() >= 1.0, "large |z|>=1", "small |z|<1")

    return {
        "x": x_col, "y": y_col, "surprise_sigma_mmbbl": round(sigma, 3),
        "overall": overall.__dict__ if overall else None,
        "by_vol_regime": by("vol_regime"),
        "by_season": by("season"),
        "by_structure": by("wti_struct"),
        "by_alignment": by("product_alignment"),
        "by_surprise_size": by("surp_bucket"),
    }


def hit_rate(sub: pd.DataFrame, x_col: str = "surprise", y_col: str = "rxn_wti",
             material_z: float = 0.5) -> dict | None:
    """DIRECTIONAL accuracy — more robust than R² on noisy daily returns and what a
    trader actually cares about: among releases with a MATERIAL surprise (|z| >=
    material_z), how often did WTI move the way the surprise predicted (a draw-beat ->
    up, a build-miss -> down)? Also the average FAVOURABLE move (return signed by the
    predicted direction) and how often it was the right sign."""
    m = sub.dropna(subset=[x_col, y_col, "surprise_z"]).copy()
    m = m[m["surprise_z"].abs() >= material_z]
    if len(m) < 6:
        return None
    pred = -np.sign(m[x_col])                      # draw beat (neg surprise) -> up
    actual = np.sign(m[y_col])
    hit = (pred == actual) & (actual != 0)
    fav = (m[y_col] * pred)                         # favourable move (signed return)
    return {
        "n_material": int(len(m)),
        "hit_rate": round(float(hit.mean()), 3),
        "avg_fav_move": round(float(fav.mean()), 5),     # mean signed return
        "avg_fav_move_pct": round(float(fav.mean()) * 100, 3),
        "edge_vs_coinflip": round(float(hit.mean()) - 0.5, 3),
    }


def hit_rate_table(f: pd.DataFrame, x_col: str = "surprise", y_col: str = "rxn_wti") -> dict:
    """Directional hit-rate overall and conditioned on market state."""
    out = {"overall": hit_rate(f, x_col, y_col)}
    for dim, col in [("by_vol_regime", "vol_regime"), ("by_season", "season"),
                     ("by_structure", "wti_struct"), ("by_alignment", "product_alignment")]:
        d = {}
        for key, sub in f.groupby(col):
            if key is None or (isinstance(key, float) and pd.isna(key)):
                continue
            hr = hit_rate(sub, x_col, y_col)
            if hr:
                d[str(key)] = hr
        out[dim] = d
    return out


def spread_sensitivity(f: pd.DataFrame, x_col: str = "surprise") -> dict:
    """Which instruments/spreads react most to a crude surprise (the 'products/spreads
    most likely to be affected' deliverable). Ranks by |correlation| with the surprise."""
    sigma = float(f[x_col].std())
    out = {}
    for col in [c for c in f.columns if c.startswith("rxn_")]:
        fit = regress(f[x_col], f[col], sigma)
        if fit:
            out[col.replace("rxn_", "")] = {
                "n": fit.n, "beta": round(fit.beta, 5), "corr": round(fit.corr, 3),
                "r2": round(fit.r2, 3), "t_stat": round(fit.t_stat, 2) if fit.t_stat == fit.t_stat else None,
                "per_1sigma": round(fit.per_1sigma, 4) if fit.per_1sigma == fit.per_1sigma else None,
            }
    return dict(sorted(out.items(), key=lambda kv: -abs(kv[1]["corr"])))


# ===========================================================================
# 6. VERDICT  (bullish / bearish / neutral)
# ===========================================================================
def analyze(weekly: pd.DataFrame, prices: pd.DataFrame, panel: pd.DataFrame) -> dict:
    """One call that runs the whole pipeline: frame -> expected/surprise -> market
    state -> reactions -> event study + spread sensitivity + hit-rate. Shared by the
    batch runner, the notebook and the live engine so they can never diverge."""
    f = build_frame(weekly)
    f = add_expected_and_surprise(f)
    f = add_market_state(f, panel, prices)
    f = add_reactions(f, panel, prices)
    es_df = f.dropna(subset=["surprise", "rxn_wti"]).copy()
    es = event_study(es_df, y_col="rxn_wti", x_col="surprise")
    es_z = event_study(es_df, y_col="rxn_wti", x_col="surprise_z")
    sens = spread_sensitivity(es_df, x_col="surprise")
    hits = hit_rate_table(es_df, x_col="surprise", y_col="rxn_wti")
    return {"frame": f, "es_df": es_df, "event_study": es, "event_study_z": es_z,
            "spread_sensitivity": sens, "hit_rate": hits}


def reliability_for(es: dict, vol_regime: str | None) -> tuple[float, int, float]:
    """How reliably inventories drive WTI in this vol regime: (R^2, n, beta). Falls
    back to the all-history fit when the regime bucket is empty."""
    rel = es["by_vol_regime"].get(str(vol_regime)) if vol_regime else None
    if not rel:
        rel = es.get("overall") or {}
    return rel.get("r2", 0.0), rel.get("n", 0), rel.get("beta", 0.0)


@dataclass
class Verdict:
    direction: str                 # "Bullish" | "Bearish" | "Neutral"
    score: float                   # signed, roughly in surprise-sigma units
    confidence: str                # "low" | "medium" | "high"
    headline: str
    factors: list = field(default_factory=list)
    products: list = field(default_factory=list)


def _confidence(reliability_r2: float, n: int) -> str:
    """How much to trust the verdict: how strongly inventories drive price in THIS
    market state (the conditional R^2) and how many observations back that bucket."""
    score = 0.6 * min(max(reliability_r2, 0), 1) + 0.4 * min(n / 60.0, 1)
    return "high" if score >= 0.5 else "medium" if score >= 0.25 else "low"


def verdict_from_surprise(surprise: float, surprise_z: float, context: dict,
                          reliability_r2: float, n: int, beta: float) -> Verdict:
    """POST-release read (used by the live engine). A bigger-than-expected BUILD
    (positive surprise) is BEARISH; a bigger-than-expected DRAW (negative surprise) is
    BULLISH — so the directional signal is the SIGN OF -surprise, scaled by how far it
    missed (|z|) and how strongly the current regime reacts (reliability)."""
    raw = -surprise_z                       # bullish if draw beat expectations
    # Damp by how reliably inventories move price in this state.
    signal = raw * (0.4 + 0.6 * min(max(reliability_r2, 0), 1))
    direction = "Bullish" if signal > 0.35 else "Bearish" if signal < -0.35 else "Neutral"
    conf = _confidence(reliability_r2, n)

    factors = []
    draw = surprise < 0
    factors.append(
        f"Surprise = {surprise:+.1f} MMbbl ({surprise_z:+.1f}σ) vs expected — a "
        f"{'larger draw / smaller build' if draw else 'larger build / smaller draw'} than priced in "
        f"({'bullish' if draw else 'bearish'})."
    )
    factors.append(
        f"In the current {context.get('vol_regime','?')}-vol / {context.get('wti_struct','?')} regime, "
        f"release-day WTI moves about {abs(beta)*1.0:.2%} per 1 MMbbl of surprise "
        f"(conditional R² {reliability_r2:.2f}, n={n}) — "
        f"{'inventories drive price here' if reliability_r2>=0.2 else 'inventories are a weak driver here'}."
    )
    align = context.get("product_alignment", "n/a")
    factors.append(
        f"Product alignment: {align}" +
        ("  — crude and products agree, a clean signal." if align in ("all-draw", "all-build")
         else "  — crude and products diverge, so the read is muddier." if align == "mixed"
         else "."))

    # Expected WTI move = the fitted slope times the surprise. beta is the empirical
    # reaction-per-MMbbl and is NEGATIVE (a bigger build pushes price down), so for a
    # draw beat (surprise < 0) beta*surprise is POSITIVE = up = bullish — consistent
    # with the verdict's sign. (Do NOT add an extra minus here.)
    pred_move = beta * surprise
    sign = "higher" if pred_move > 0 else "lower"
    head = (f"{direction} — model expects WTI to trade {sign} on the print "
            f"(~{abs(pred_move):.2%} on the surprise alone), confidence {conf}.")
    return Verdict(direction=direction, score=round(signal, 2), confidence=conf,
                   headline=head, factors=factors,
                   products=context.get("products", []))


def forward_base_case(f: pd.DataFrame, context: dict, reliability_r2: float, n: int) -> Verdict:
    """PRE-release base case (for the assignment's Thursday deliverable). Before the
    number lands we don't have a surprise, so the lean comes from the structural
    backdrop: where stocks sit vs the seasonal norm (crude_z), the recent draw/build
    momentum, the Cushing trend, the seasonal expectation, and product alignment.
    The model's *expected* build/draw is the base case the market is positioned for —
    if it prints near expected, the reaction is neutral; the asymmetry is the story."""
    last = f.dropna(subset=["crude_wow"]).iloc[-1]
    z = last.get("crude_z", np.nan)
    exp = last.get("expected", np.nan)
    mom = f["crude_wow"].tail(4).mean()
    cush = f["cushing_wow"].tail(4).sum() if "cushing_wow" in f else np.nan

    lean = 0.0
    factors = []
    # 1) Structural tightness vs seasonal norm.
    if z == z:
        lean += -np.tanh(z)                 # low stocks vs norm (z<0) -> bullish
        factors.append(
            f"U.S. crude stocks are {abs(z):.1f}σ {'below' if z < 0 else 'above'} the 5-year "
            f"seasonal norm — structurally {'tight (bullish)' if z < 0 else 'loose (bearish)'}.")
    # 2) Recent momentum.
    if mom == mom:
        lean += -np.tanh(mom / 4.0)
        factors.append(
            f"Last 4 weeks averaged a {abs(mom):.1f} MMbbl/week {'draw' if mom < 0 else 'build'} "
            f"— {'bullish' if mom < 0 else 'bearish'} momentum into the print.")
    # 3) Cushing (WTI delivery hub).
    if cush == cush:
        lean += -np.tanh(cush / 6.0)
        factors.append(
            f"Cushing has {'drawn' if cush < 0 else 'built'} {abs(cush):.1f} MMbbl over 4 weeks "
            f"({last.get('cushing', np.nan):.1f} MMbbl now) — "
            f"{'draining toward tank lows, very bullish for WTI structure' if cush < 0 else 'refilling, bearish for WTI structure'}.")
    # 4) Seasonal expectation.
    sw = last.get("crude_seasonal_wow", np.nan)
    if sw == sw:
        factors.append(
            f"Seasonally this week normally {'draws' if sw < 0 else 'builds'} ~{abs(sw):.1f} MMbbl "
            f"({last['season']} season); the model's expected change is {exp:+.1f} MMbbl.")
    # 5) Alignment.
    align = context.get("product_alignment", "n/a")
    factors.append(
        f"Product alignment is '{align}'" +
        (" — crude and products agree, so a surprise is a cleaner signal." if align in ("all-draw", "all-build")
         else " — crude and products diverge, so the day-of read is muddier." if align == "mixed" else "."))

    # 6) Release-day CATALYST STRENGTH (separate from the structural lean): how much
    #    does the market actually move on the inventory surprise in THIS state?
    catalyst = ("a strong" if reliability_r2 >= 0.05 else "a weak")
    factors.append(
        f"Release-day catalyst strength is {catalyst} one: in the current "
        f"{context.get('vol_regime','?')}-vol / {context.get('wti_struct','?')} / "
        f"{last['season']} regime, the crude surprise has historically explained only "
        f"R²={reliability_r2:.2f} of the day's WTI move (n={n}) — other drivers (macro, OPEC, "
        f"positioning) usually dominate the day.")

    # 7) RISK SKEW: if a big draw is already the base case, the asymmetric risk is a
    #    bearish surprise (a build vs an expected draw), and vice-versa.
    if exp == exp:
        if exp < -1:
            factors.append(
                f"Asymmetry: a sizeable DRAW (~{exp:+.1f} MMbbl) is the base case and largely priced, "
                f"so the bigger surprise risk is a BUILD (bearish). A draw merely in line confirms but "
                f"adds little; a draw far bigger than {exp:+.1f} is the bullish tail.")
        elif exp > 1:
            factors.append(
                f"Asymmetry: a BUILD (~{exp:+.1f} MMbbl) is the base case and largely priced, so the "
                f"bigger surprise risk is a DRAW (bullish).")

    direction = "Bullish" if lean > 0.4 else "Bearish" if lean < -0.4 else "Neutral"
    conf = _confidence(reliability_r2, n)
    head = (f"Structural lean {direction.upper()} (score {lean:+.2f}), but the RELEASE itself is "
            f"{catalyst} same-day catalyst (conditional R²={reliability_r2:.2f}). Base case: the market "
            f"is positioned for ~{exp:+.1f} MMbbl — the day's move hinges on the surprise vs that, and "
            f"in this regime inventories are {'a' if reliability_r2>=0.05 else 'rarely the'} decisive driver.")
    return Verdict(direction=direction, score=round(float(lean), 2), confidence=conf,
                   headline=head, factors=factors, products=context.get("products", []))
