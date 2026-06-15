"""
build_panel.py — assemble the unified daily FEATURE PANEL for Phase 2.

One row per trading day (2021→present), columns spanning prices, spreads, cracks,
calendar spreads, butterflies, realized vol, curve state, EIA inventory features,
seasonal flags and macro. This single table is the substrate for BOTH regime
classification (regimes.py) and the regression/signal models (models.py, signals.py).

Sources:
  • server/data/history.json — daily front closes + M1..M12 term strips for
    WTI / Brent / HO / Gas Oil (built by server/scripts/build-history.js).
  • Yahoo — RBOB (not in the dataset) + macro (DXY/VIX/SPX/UST10Y), ~5y daily.
  • EIA v2 — weekly crude/distillate/gasoline stocks + refinery utilization.

Output: analytics/out/panel.parquet (+ panel.csv for eyeballing).
Run:    python analytics/build_panel.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import (
    HISTORY_JSON, OUT_DIR, BBL_PER_MT_GASOIL, GAL_PER_BBL,
    load_env, yahoo_daily, eia_series,
)

# Dataset instruments and their native quote units (from build-history FILES).
UNITS = {"wti": "$/bbl", "brent": "$/bbl", "ho": "$/gal", "gasoil": "$/mt"}
TERM_K = 12

# Macro symbols (Yahoo) → panel column.
MACRO = {"DX-Y.NYB": "dxy", "^VIX": "vix", "^GSPC": "spx", "^TNX": "ust10y"}


# ----------------------------------------------------------------------------
# 1. Front-month closes + term strips from history.json → $/bbl frames.
# ----------------------------------------------------------------------------
def load_history() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    h = json.loads(HISTORY_JSON.read_text())
    fronts, terms = {}, {}
    for inst, unit in UNITS.items():
        node = h["instruments"].get(inst, {})
        # Term strip → DataFrame [date x M1..M12], converted to $/bbl.
        rows = {iso: mids for iso, mids in node.get("term", [])}
        tdf = pd.DataFrame.from_dict(rows, orient="index",
                                     columns=[f"m{i+1}" for i in range(TERM_K)])
        tdf.index = pd.to_datetime(tdf.index)
        tdf = tdf.sort_index()
        if unit == "$/gal":
            tdf *= GAL_PER_BBL
        elif unit == "$/mt":
            tdf /= BBL_PER_MT_GASOIL
        terms[inst] = tdf
        fronts[inst] = tdf["m1"].rename(inst)  # M1 in $/bbl == front close
    front_df = pd.concat(fronts.values(), axis=1, sort=False).sort_index()
    return front_df, terms


# ----------------------------------------------------------------------------
# 2. Spreads, cracks, calendar spreads, butterflies.
# ----------------------------------------------------------------------------
def add_spreads(panel: pd.DataFrame, terms: dict[str, pd.DataFrame]) -> pd.DataFrame:
    g = panel  # all fronts already $/bbl: wti, brent, ho, gasoil, rbob

    # Inter-commodity spreads ($/bbl)
    panel["brent_wti"] = g["brent"] - g["wti"]
    panel["ho_gasoil"] = g["ho"] - g["gasoil"]
    if "rbob" in g:
        panel["rbob_ho"] = g["rbob"] - g["ho"]
        panel["rbob_gasoil"] = g["rbob"] - g["gasoil"]

    # Crack spreads ($/bbl): product − crude
    panel["ho_wti"] = g["ho"] - g["wti"]
    panel["ho_brent"] = g["ho"] - g["brent"]
    panel["gasoil_brent"] = g["gasoil"] - g["brent"]
    panel["gasoil_wti"] = g["gasoil"] - g["wti"]
    if "rbob" in g:
        panel["rbob_wti"] = g["rbob"] - g["wti"]
        panel["crack_321_wti"] = (2 * g["rbob"] + g["ho"] - 3 * g["wti"]) / 3
        panel["crack_321_brent"] = (2 * g["rbob"] + g["ho"] - 3 * g["brent"]) / 3

    # Calendar spreads + butterflies per instrument (from the term strip, $/bbl).
    for inst, tdf in terms.items():
        t = tdf.reindex(panel.index)
        panel[f"{inst}_m1m2"] = t["m1"] - t["m2"]
        panel[f"{inst}_m2m3"] = t["m2"] - t["m3"]
        panel[f"{inst}_m1m6"] = t["m1"] - t["m6"]
        panel[f"{inst}_m1m12"] = t["m1"] - t["m12"]            # curve slope proxy
        panel[f"{inst}_fly"] = t["m1"] - 2 * t["m2"] + t["m3"]  # front calendar butterfly
    return panel


# ----------------------------------------------------------------------------
# 3. Realized volatility + curve state.
# ----------------------------------------------------------------------------
def add_vol_and_curve(panel: pd.DataFrame) -> pd.DataFrame:
    ANN = np.sqrt(252)
    for inst in UNITS:
        # Compute returns/vol on the instrument's OWN consecutive trading days —
        # the union index carries holiday rows (e.g. ICE-only days) where this
        # instrument is NaN, which would otherwise poison the rolling window.
        s = panel[inst].dropna()
        rvol = s.pct_change().rolling(20).std() * ANN
        panel[f"{inst}_rvol20"] = rvol.reindex(panel.index)
        # 20-day price momentum (a market-state driver — risk-on/off, demand
        # trend). Built from the UNDERLYING price, never from a spread/target, so
        # it adds explanatory power to the fair-value models without leakage.
        panel[f"{inst}_mom20"] = (s / s.shift(20) - 1.0).reindex(panel.index)
    # Curve state: backwardation when M1 > M12 (m1m12 > 0).
    for inst in UNITS:
        slope = panel[f"{inst}_m1m12"]
        panel[f"{inst}_struct"] = np.where(slope > 0.05, "backwardation",
                                   np.where(slope < -0.05, "contango", "flat"))
    return panel


# ----------------------------------------------------------------------------
# 4. EIA inventory features (weekly → forward-filled to the daily index).
#    crude/distillate/gasoline stocks (MMbbl), WoW change, refinery util, and a
#    z-score of crude stocks vs the 5 prior years for the same week-of-year.
# ----------------------------------------------------------------------------
def week_of_year(ts: pd.Timestamp) -> int:
    doy = (ts - pd.Timestamp(ts.year, 1, 1)).days
    return doy // 7 + 1


def seasonal_z(weekly: pd.Series) -> pd.Series:
    """z = (value − mean) / std of the 5 prior calendar years at the same week-of-year."""
    df = pd.DataFrame({"v": weekly})
    df["year"] = df.index.year
    df["woy"] = [week_of_year(ts) for ts in df.index]
    out = pd.Series(index=weekly.index, dtype=float)
    for ts, row in df.iterrows():
        prior = df[(df["woy"] == row["woy"]) & (df["year"] >= row["year"] - 5) & (df["year"] < row["year"])]["v"]
        if len(prior) >= 2 and prior.std(ddof=0) > 0:
            out[ts] = (row["v"] - prior.mean()) / prior.std(ddof=0)
    return out


def add_inventory(panel: pd.DataFrame, key: str) -> pd.DataFrame:
    def weekly(series_id, length=300):
        rows = eia_series(series_id, key, length=length)
        if not rows:
            return pd.Series(dtype=float)
        idx = pd.to_datetime([p for p, _ in rows])
        return pd.Series([v / 1000.0 for _, v in rows], index=idx).sort_index()  # kbbl→MMbbl

    # ~11y so a 2021 observation still has its 5 prior years for the seasonal z.
    crude = weekly("PET.WCESTUS1.W", 560)
    distillate = weekly("PET.WDISTUS1.W", 560)
    gasoline = weekly("PET.WGTSTUS1.W", 120)
    refutil = pd.Series(dtype=float)
    rows = eia_series("PET.WPULEUS3.W", key, length=560)  # full 2021->present
    if rows:
        refutil = pd.Series([v for _, v in rows],
                            index=pd.to_datetime([p for p, _ in rows])).sort_index()

    feats = {}
    if not crude.empty:
        feats["crude_stock"] = crude
        feats["crude_wow"] = crude.diff()
        feats["crude_z"] = seasonal_z(crude)
    if not distillate.empty:
        feats["distillate_stock"] = distillate
        feats["distillate_wow"] = distillate.diff()
        feats["distillate_z"] = seasonal_z(distillate)
    if not gasoline.empty:
        feats["gasoline_stock"] = gasoline
        feats["gasoline_wow"] = gasoline.diff()
    if not refutil.empty:
        feats["refinery_util"] = refutil

    # Forward-fill each weekly feature onto the daily panel index.
    for name, s in feats.items():
        panel[name] = s.reindex(panel.index.union(s.index)).sort_index().ffill().reindex(panel.index)
    return panel


# ----------------------------------------------------------------------------
# 5. Seasonal flags + macro.
# ----------------------------------------------------------------------------
def add_seasonal(panel: pd.DataFrame) -> pd.DataFrame:
    panel["month"] = panel.index.month
    # Heating: Oct–Mar · Driving: Apr–Aug · Shoulder: Sep.
    def season(m):
        if m in (10, 11, 12, 1, 2, 3):
            return "heating"
        if m in (4, 5, 6, 7, 8):
            return "driving"
        return "shoulder"
    panel["season"] = [season(m) for m in panel["month"]]
    return panel


def add_macro(panel: pd.DataFrame) -> pd.DataFrame:
    for sym, col in MACRO.items():
        daily = yahoo_daily(sym, "10y")
        if not daily:
            panel[col] = np.nan
            continue
        s = pd.Series(daily)
        s.index = pd.to_datetime(s.index)
        panel[col] = s.reindex(panel.index.union(s.index)).sort_index().ffill().reindex(panel.index)
    return panel


# ----------------------------------------------------------------------------
def main():
    print("Building feature panel ...")
    env = load_env()
    key = env.get("EIA_API_KEY", "")

    front, terms = load_history()
    panel = front.copy()

    # RBOB from Yahoo (the one instrument absent from the dataset), $/gal → $/bbl.
    rbob = yahoo_daily("RB=F", "10y")
    if rbob:
        s = pd.Series(rbob) * GAL_PER_BBL
        s.index = pd.to_datetime(s.index)
        panel["rbob"] = s.reindex(panel.index.union(s.index)).sort_index().ffill().reindex(panel.index)

    panel = add_spreads(panel, terms)
    panel = add_vol_and_curve(panel)
    panel = add_inventory(panel, key)
    panel = add_seasonal(panel)
    panel = add_macro(panel)

    panel.index.name = "date"
    panel = panel.sort_index()

    pq = OUT_DIR / "panel.parquet"
    panel.to_parquet(pq)
    panel.to_csv(OUT_DIR / "panel.csv")

    n_num = panel.select_dtypes("number").shape[1]
    print(f"  rows: {len(panel)}  ({panel.index.min().date()} -> {panel.index.max().date()})")
    print(f"  columns: {panel.shape[1]} ({n_num} numeric)")
    print(f"  coverage: brent {panel['brent'].notna().sum()}, rbob {panel.get('rbob', pd.Series(dtype=float)).notna().sum()}, "
          f"crude_z {panel.get('crude_z', pd.Series(dtype=float)).notna().sum()}, dxy {panel.get('dxy', pd.Series(dtype=float)).notna().sum()}")
    print(f"  -> {pq}")


if __name__ == "__main__":
    main()
