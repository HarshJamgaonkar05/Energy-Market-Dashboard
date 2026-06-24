"""
run_inventory_analysis.py — run the crude-inventory framework end to end and emit the
artifacts the notebook, the PDF and the dashboard consume:

  deliverables/research/inventory_analysis.json   full results (tables + current read)
  deliverables/figures/*.png                       all charts (for the PDF & notebook)
  server/data/inventory_signal.json                the live verdict snapshot the
                                                    dashboard panel reads

Run:  python analytics/run_inventory_analysis.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from common import ROOT
import inventory_lib as lib

DELIV = ROOT / "deliverables"
FIGS = DELIV / "figures"
RESEARCH = DELIV / "research"
DATA_DIR = ROOT / "server" / "data"
for d in (FIGS, RESEARCH, DATA_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ---- chart styling: clean, light, readable in a PDF -------------------------
plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 130, "font.size": 10,
    "axes.titlesize": 12, "axes.titleweight": "bold", "axes.grid": True,
    "grid.alpha": 0.25, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
})
BULL, BEAR, NEU, ACCENT = "#16a34a", "#dc2626", "#64748b", "#2563eb"


def jdefault(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, (pd.Timestamp,)):
        return o.strftime("%Y-%m-%d")
    raise TypeError(str(type(o)))


def clean(o):
    """Recursively replace NaN/inf with None so the JSON is valid."""
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, float):
        return None if (np.isnan(o) or np.isinf(o)) else o
    return o


# ===========================================================================
def main():
    print("Loading data ...")
    weekly = lib.fetch_weekly(length=600)
    prices = lib.fetch_prices()
    panel = lib.load_panel()
    print(f"  EIA weeks: {len(weekly)} ({weekly.index.min().date()} -> {weekly.index.max().date()})")
    print(f"  prices: {list(prices.columns)}  ({prices.index.min().date()} -> {prices.index.max().date()})")
    print(f"  panel: {panel.shape if not panel.empty else 'MISSING'}")

    A = lib.analyze(weekly, prices, panel)
    f, es_df = A["frame"], A["es_df"]
    es, es_z, sens, hits = A["event_study"], A["event_study_z"], A["spread_sensitivity"], A["hit_rate"]
    print(f"  event-study sample: {len(es_df)} releases "
          f"({es_df['period'].min().date()} -> {es_df['period'].max().date()})")

    # ---- current read & verdict --------------------------------------------
    last = f.dropna(subset=["crude_wow"]).iloc[-1]
    cur_vol = last.get("vol_regime")
    cur_struct = last.get("wti_struct")
    cur_align = last.get("product_alignment")

    # Conditional reliability: R^2 of reaction~surprise in the current vol regime.
    rel_r2, rel_n, rel_beta = lib.reliability_for(es, cur_vol)

    # Products/spreads most likely affected = top sensitivities (drop raw wti/brent dupes).
    top_products = [k for k in sens.keys() if k not in ("panel_wti", "panel_brent")][:5]

    context = {"vol_regime": cur_vol, "wti_struct": cur_struct,
               "product_alignment": cur_align, "products": top_products}

    base = lib.forward_base_case(f, context, rel_r2, rel_n)

    # Days of supply, YoY.
    crude_now = float(last["crude"])
    crude_yr_ago = float(weekly["crude"].iloc[-53]) if len(weekly) >= 53 else None
    yoy_pct = round((crude_now - crude_yr_ago) / crude_yr_ago * 100, 1) if crude_yr_ago else None

    current = {
        "asOf_period": last["period"].strftime("%Y-%m-%d"),
        "next_release_est": lib.release_date(last["period"] + pd.Timedelta(days=7)).strftime("%Y-%m-%d"),
        "crude_stock": round(crude_now, 1),
        "crude_wow": round(float(last["crude_wow"]), 1),
        "crude_z": round(float(last["crude_z"]), 2) if last.get("crude_z") == last.get("crude_z") else None,
        "expected_next": round(float(last["expected"]), 1) if last.get("expected") == last.get("expected") else None,
        "cushing": round(float(last["cushing"]), 1) if "cushing" in last else None,
        "cushing_wow": round(float(last["cushing_wow"]), 1) if "cushing_wow" in last else None,
        "refutil": round(float(last["refutil"]), 1) if "refutil" in last else None,
        "days_supply": round(float(last["days_supply"]), 1) if last.get("days_supply") == last.get("days_supply") else None,
        "yoy_pct": yoy_pct, "season": last["season"],
        "vol_regime": cur_vol, "wti_struct": cur_struct, "product_alignment": cur_align,
        "reliability_r2": round(rel_r2, 3), "reliability_n": rel_n, "reliability_beta": rel_beta,
    }

    verdict = {
        "mode": "forward_base_case",
        "direction": base.direction, "score": base.score,
        "confidence": base.confidence, "headline": base.headline,
        "factors": base.factors, "products": base.products,
    }

    analysis = {
        "generatedAt": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "current": current, "verdict": verdict,
        "event_study": es, "event_study_z": es_z, "spread_sensitivity": sens,
        "hit_rate": hits,
        "expected_model_note": "expected = walk-forward OLS(seasonal_wow, lag1_wow, lag1_balance); leak-free.",
        "sample": {"n_releases": len(es_df),
                   "from": es_df["period"].min().strftime("%Y-%m-%d"),
                   "to": es_df["period"].max().strftime("%Y-%m-%d")},
        "recent_releases": clean(
            f.tail(14)[["period", "crude_wow", "expected", "surprise", "surprise_z",
                        "rxn_wti", "vol_regime", "season", "product_alignment"]]
            .assign(period=lambda d: d["period"].dt.strftime("%Y-%m-%d"))
            .to_dict("records")),
    }

    (RESEARCH / "inventory_analysis.json").write_text(json.dumps(clean(analysis), indent=2, default=jdefault))
    print(f"  -> {RESEARCH/'inventory_analysis.json'}")

    # Live verdict snapshot the dashboard reads (engine overwrites post-release).
    signal = {
        "generatedAt": analysis["generatedAt"], "stage": "pre-release",
        "asOf_period": current["asOf_period"], "next_release_est": current["next_release_est"],
        "verdict": verdict, "current": current, "crosscheck": None,
        "top_spreads": top_products,
    }
    (DATA_DIR / "inventory_signal.json").write_text(json.dumps(clean(signal), indent=2, default=jdefault))
    print(f"  -> {DATA_DIR/'inventory_signal.json'}")

    # Save the full frame for the notebook to re-load without re-fetching.
    f.assign(period=lambda d: d["period"].dt.strftime("%Y-%m-%d")).to_csv(RESEARCH / "weekly_frame.csv", index=False)

    make_figures(f, es_df, es, sens, weekly, current, base, hits)
    print("  figures ->", FIGS)

    # Console summary.
    print("\n==== CURRENT READ ====")
    print(f"  As of EIA week {current['asOf_period']} | next release ~{current['next_release_est']}")
    print(f"  Crude {current['crude_stock']} MMbbl ({current['crude_wow']:+.1f} WoW, "
          f"z={current['crude_z']}), Cushing {current['cushing']} ({current['cushing_wow']:+.1f}), "
          f"refutil {current['refutil']}%")
    print(f"  Regime: {cur_vol} vol / {cur_struct} / {current['season']} / align={cur_align}")
    print(f"  VERDICT: {base.direction}  (score {base.score}, confidence {base.confidence})")
    print(f"  {base.headline}")
    if es["overall"]:
        o = es["overall"]
        print(f"\n  Event study (n={o['n']}): WTI moves {o['beta']*1:.3%} per +1 MMbbl surprise, "
              f"R²={o['r2']:.2f}, corr={o['corr']:.2f}, t={o['t_stat']:.1f}")


# ===========================================================================
# FIGURES
# ===========================================================================
def make_figures(f, es_df, es, sens, weekly, current, base, hits):
    # --- Fig 1: crude stocks vs 5-year seasonal band (full 12 months) --------
    fig, ax = plt.subplots(figsize=(9, 4.2))
    crude = weekly["crude"].dropna()
    last_date = crude.index.max()
    yr = crude[crude.index >= last_date - pd.Timedelta(days=400)]
    # seasonal band by week-of-year over prior 5 years
    woy = lambda ts: (ts - pd.Timestamp(ts.year, 1, 1)).days // 7 + 1
    cur_year = last_date.year
    band = {}
    for ts, v in crude.items():
        if ts.year >= cur_year - 5 and ts.year < cur_year:
            band.setdefault(woy(ts), []).append(v)
    xs = list(yr.index)
    lo = [min(band.get(woy(ts), [np.nan])) for ts in xs]
    hi = [max(band.get(woy(ts), [np.nan])) for ts in xs]
    av = [np.mean(band.get(woy(ts), [np.nan])) for ts in xs]
    ax.fill_between(xs, lo, hi, color=ACCENT, alpha=0.12, label="5-yr range")
    ax.plot(xs, av, color=NEU, ls="--", lw=1, label="5-yr average")
    ax.plot(yr.index, yr.values, color="#f59e0b", lw=1.8, label="Current")
    # highlight last 3 months
    cut = last_date - pd.Timedelta(days=92)
    l3 = yr[yr.index >= cut]
    ax.plot(l3.index, l3.values, color="#dc2626", lw=2.6, label="Last 3 months")
    ax.set_title("U.S. Crude Stocks vs 5-Year Seasonal Band (MMbbl)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.legend(fontsize=8, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    fig.tight_layout(); fig.savefig(FIGS / "01_crude_seasonal_band.png", bbox_inches="tight"); plt.close(fig)

    # --- Fig 2: actual WoW vs expected + surprise (last ~6 months) -----------
    fig, ax = plt.subplots(figsize=(9, 4.2))
    recent = f.dropna(subset=["crude_wow"]).tail(26)
    x = recent["period"]
    ax.bar(x, recent["crude_wow"], width=4, color=[BULL if v < 0 else BEAR for v in recent["crude_wow"]],
           alpha=0.55, label="Actual WoW change")
    ax.plot(x, recent["expected"], color=ACCENT, marker="o", ms=3, lw=1.4, label="Model expected")
    ax.axhline(0, color="#94a3b8", lw=0.8)
    ax.set_title("Actual vs Expected Weekly Crude Change (MMbbl) — green=draw, red=build")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIGS / "02_actual_vs_expected.png", bbox_inches="tight"); plt.close(fig)

    # --- Fig 3: event study scatter (reaction vs surprise) -------------------
    fig, ax = plt.subplots(figsize=(7.5, 5))
    xv = es_df["surprise"].values
    yv = es_df["rxn_wti"].values * 100
    ax.scatter(xv, yv, s=18, alpha=0.5, color=ACCENT, edgecolor="none")
    if es["overall"]:
        b, a = es["overall"]["beta"] * 100, es["overall"]["intercept"] * 100
        xs = np.linspace(np.nanmin(xv), np.nanmax(xv), 50)
        ax.plot(xs, a + b * xs, color=BEAR, lw=2,
                label=f"slope {es['overall']['beta']*100:.3f}%/MMbbl · R²={es['overall']['r2']:.2f} · t={es['overall']['t_stat']:.1f}")
    ax.axhline(0, color="#cbd5e1", lw=0.7); ax.axvline(0, color="#cbd5e1", lw=0.7)
    ax.set_xlabel("Surprise = actual − expected  (MMbbl;  ◄ draw / build ►)")
    ax.set_ylabel("Release-day WTI return (%)")
    ax.set_title("Event Study: WTI Reaction vs Inventory Surprise")
    ax.legend(fontsize=9, loc="upper right")
    fig.tight_layout(); fig.savefig(FIGS / "03_event_study_scatter.png", bbox_inches="tight"); plt.close(fig)

    # --- Fig 4: conditioning — R^2 by state (when inventories mattered) ------
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    def bar_r2(ax, d, title, order=None):
        items = [(k, v["r2"], v["n"]) for k, v in d.items()]
        if order:
            items.sort(key=lambda kv: order.index(kv[0]) if kv[0] in order else 99)
        else:
            items.sort(key=lambda kv: -kv[1])
        labels = [k for k, _, _ in items]
        vals = [r for _, r, _ in items]
        ns = [n for _, _, n in items]
        bars = ax.bar(labels, vals, color=ACCENT, alpha=0.8)
        for b2, n in zip(bars, ns):
            ax.text(b2.get_x() + b2.get_width() / 2, b2.get_height() + 0.005, f"n={n}",
                    ha="center", va="bottom", fontsize=7, color=NEU)
        ax.set_title(title); ax.set_ylabel("R²  (share of move explained)")
        ax.tick_params(axis="x", labelrotation=20)
    bar_r2(axes[0], es["by_vol_regime"], "By Volatility Regime", order=["Low", "Normal", "High"])
    bar_r2(axes[1], es["by_season"], "By Season", order=["heating", "driving", "shoulder"])
    fig.suptitle("When Did Inventories Drive Price? (higher R² = stronger driver)", fontweight="bold")
    fig.tight_layout(); fig.savefig(FIGS / "04_conditioning_r2.png", bbox_inches="tight"); plt.close(fig)

    # --- Fig 5: spread sensitivity (|corr| with surprise) -------------------
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    items = [(k, v["corr"]) for k, v in sens.items() if k not in ("panel_wti", "panel_brent")][:8]
    labels = [k for k, _ in items]
    vals = [v for _, v in items]
    colors = [BEAR if v < 0 else BULL for v in vals]
    ax.barh(labels[::-1], vals[::-1], color=colors[::-1], alpha=0.8)
    ax.axvline(0, color="#94a3b8", lw=0.8)
    ax.set_xlabel("Correlation of release-day move with the surprise")
    ax.set_title("Which Products / Spreads React Most to a Crude Surprise")
    fig.tight_layout(); fig.savefig(FIGS / "05_spread_sensitivity.png", bbox_inches="tight"); plt.close(fig)

    # --- Fig 6: Cushing trend last 3 months ---------------------------------
    fig, ax = plt.subplots(figsize=(9, 3.8))
    cu = weekly["cushing"].dropna().tail(26)
    ax.plot(cu.index, cu.values, color="#f59e0b", lw=2, marker="o", ms=3)
    ax.axhspan(0, 22, color=BULL, alpha=0.08)
    ax.text(cu.index[1], 21.2, "operational low zone (~20-22 MMbbl)", fontsize=8, color=BULL)
    ax.set_title("Cushing, OK Crude Stocks — the WTI Delivery Hub (MMbbl)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.tight_layout(); fig.savefig(FIGS / "06_cushing_trend.png", bbox_inches="tight"); plt.close(fig)

    # --- Fig 7: directional hit-rate by state (on MATERIAL surprises) --------
    fig, ax = plt.subplots(figsize=(9, 4.4))
    rows = []
    for k, v in {**hits.get("by_season", {}), **{f"vol:{k}": x for k, x in hits.get("by_vol_regime", {}).items()},
                 **{f"align:{k}": x for k, x in hits.get("by_alignment", {}).items()}}.items():
        rows.append((k, v["hit_rate"], v["n_material"]))
    ov = hits.get("overall")
    if ov:
        rows = [("OVERALL", ov["hit_rate"], ov["n_material"])] + rows
    rows = [r for r in rows if r[2] >= 6]
    labels = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    ns = [r[2] for r in rows]
    colors = [BULL if v > 0.5 else BEAR for v in vals]
    bars = ax.bar(labels, vals, color=colors, alpha=0.82)
    for b2, n in zip(bars, ns):
        ax.text(b2.get_x() + b2.get_width() / 2, b2.get_height() + 0.01, f"n={n}", ha="center", fontsize=7, color=NEU)
    ax.axhline(0.5, color="#0f172a", lw=1, ls="--", label="coin-flip (50%)")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Directional hit-rate")
    ax.set_title("Did WTI Move the Way the Surprise Predicted?  (material surprises, |z|≥0.5)")
    ax.tick_params(axis="x", labelrotation=25)
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIGS / "07_hit_rate.png", bbox_inches="tight"); plt.close(fig)

    print("  saved 7 figures")


if __name__ == "__main__":
    main()
