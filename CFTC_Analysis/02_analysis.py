"""
02_analysis.py
--------------
Does CFTC Managed-Money positioning have predictive value for WTI crude prices?

Reads  data/weekly_merged.csv  (from 01_prepare_data.py)
Writes data/stats_summary.json + console report + charts/*.png

PRIMARY series : Managed Money net (official CFTC, WTI 067651)  -> the speculative
                 "smart-money-chasing-momentum" crowd the assignment asks about.
SECONDARY      : Other Reportables net (= the series actually in the supplied
                 /Data Excel) -> reported for comparison only.

Robustness: WTI spot printed NEGATIVE on 2020-04-20. Any forward window that
straddles it produces a meaningless <-100% "return", so we report MEDIANS
alongside means and also a winsorized mean (1%/99%).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
CH = HERE / "charts"
CH.mkdir(exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "font.size": 9, "axes.grid": True,
                     "grid.alpha": 0.3, "axes.axisbelow": True})

H = ["fwd_1w", "fwd_2w", "fwd_4w"]
LBL = {"fwd_1w": "1-week", "fwd_2w": "2-week", "fwd_4w": "4-week"}


def robust_stats(x):
    """mean, median, winsorized-mean, t-test mean==0, n  (returns dict)."""
    x = pd.Series(x).dropna()
    n = len(x)
    if n < 3:
        return {"mean": np.nan, "median": np.nan, "wmean": np.nan,
                "t": np.nan, "p": np.nan, "n": n}
    w = x.clip(x.quantile(0.01), x.quantile(0.99))
    t, p = stats.ttest_1samp(x, 0.0)
    return {"mean": float(x.mean()), "median": float(x.median()),
            "wmean": float(w.mean()), "t": float(t), "p": float(p), "n": n}


def bucket_stats(df, bcol):
    out = {}
    for b in ["extreme_long", "extreme_short", "mid"]:
        sub = df[df[bcol] == b]
        out[b] = {"n": int(len(sub))}
        for h in H:
            rs = robust_stats(sub[h])
            comp = df[df[bcol] != b][h].dropna()
            xx = sub[h].dropna()
            if len(xx) >= 3 and len(comp) >= 3:
                # Mann-Whitney (median-based, robust) + Welch t (mean-based)
                uu, pu = stats.mannwhitneyu(xx, comp, alternative="two-sided")
                tt, pt = stats.ttest_ind(xx, comp, equal_var=False)
            else:
                pu = pt = np.nan
            rs["p_vs_rest_mean"] = float(pt) if pt == pt else None
            rs["p_vs_rest_med"] = float(pu) if pu == pu else None
            out[b][h] = rs
    return out


def analyze_series(df, pfx):
    """All stats for one positioning series (pfx in {'mm','or'})."""
    net, chg = f"{pfx}_net", f"{pfx}_chg"
    zf, zr = f"{pfx}_z_full", f"{pfx}_z_roll52"
    df = df.copy()
    df["wk_ret"] = df["price_asof"].pct_change()
    res = {}

    # --- relationship ---
    m = df.dropna(subset=[net, "price_asof"])
    c = df.dropna(subset=[chg, "wk_ret"])
    res["relationship"] = {
        "level_pearson": float(np.corrcoef(m[net], m["price_asof"])[0, 1]),
        "level_spearman": float(stats.spearmanr(m[net], m["price_asof"]).statistic),
        "chg_vs_ret_pearson": float(np.corrcoef(c[chg], c["wk_ret"])[0, 1]),
        "chg_vs_ret_p": float(stats.pearsonr(c[chg], c["wk_ret"])[1]),
        "predictive": {},
    }
    for sname, s in [("z_roll52", df[zr]), ("z_full", df[zf]), ("chg", df[chg])]:
        res["relationship"]["predictive"][sname] = {}
        for h in H:
            d = pd.DataFrame({"s": s, "r": df[h]}).dropna()
            r, p = stats.pearsonr(d["s"], d["r"])
            sr, sp = stats.spearmanr(d["s"], d["r"])
            res["relationship"]["predictive"][sname][h] = {
                "pearson": float(r), "p": float(p),
                "spearman": float(sr), "sp": float(sp), "n": int(len(d))}

    # --- baseline forward returns ---
    res["baseline"] = {h: robust_stats(df[h]) for h in H}

    # --- extremes: full-sample decile + point-in-time rolling z ---
    p10, p90 = df[net].quantile(0.10), df[net].quantile(0.90)
    df["bk_dec"] = np.where(df[net] >= p90, "extreme_long",
                   np.where(df[net] <= p10, "extreme_short", "mid"))
    Z = 1.5
    df["bk_z"] = np.where(df[zr] >= Z, "extreme_long",
                 np.where(df[zr] <= -Z, "extreme_short", "mid"))
    res["extremes_decile"] = {"p10": float(p10), "p90": float(p90),
                              "stats": bucket_stats(df, "bk_dec")}
    res["extremes_rollz"] = {"z": Z, "stats": bucket_stats(df, "bk_z")}

    # --- decile monotonicity (median forward return per net decile) ---
    df["decile"] = pd.qcut(df[net], 10, labels=False) + 1
    dec_mean = df.groupby("decile")[H].mean()
    dec_med = df.groupby("decile")[H].median()
    res["decile_mean"] = {int(k): {h: float(v) for h, v in r.items()} for k, r in dec_mean.iterrows()}
    res["decile_median"] = {int(k): {h: float(v) for h, v in r.items()} for k, r in dec_med.iterrows()}
    return res, df, dec_mean, dec_med


# ----------------------------------------------------------------- charts (MM)
def charts(df, dec_mean, dec_med, res):
    # 1 — time series with extremes marked
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.plot(df["asof"], df["price_asof"], color="#1f3b57", lw=1.3, label="WTI spot ($/bbl)")
    ax.set_ylabel("WTI spot ($/bbl)", color="#1f3b57")
    ax2 = ax.twinx()
    ax2.plot(df["asof"], df["mm_net"] / 1e3, color="#c0622d", lw=1.0, alpha=0.8,
             label="MM net (k contracts)")
    ax2.set_ylabel("Managed-Money net (000s)", color="#c0622d"); ax2.grid(False)
    el = df[df["bk_dec"] == "extreme_long"]; es = df[df["bk_dec"] == "extreme_short"]
    ax2.scatter(el["asof"], el["mm_net"]/1e3, s=14, color="#b00", zorder=5, label="extreme long (top decile)")
    ax2.scatter(es["asof"], es["mm_net"]/1e3, s=14, color="#0a7", zorder=5, label="extreme short (bottom decile)")
    ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1+h2, l1+l2, fontsize=7, loc="upper left", ncol=2)
    ax.set_title("WTI spot vs CFTC Managed-Money net positioning (2016–2026)")
    fig.tight_layout(); fig.savefig(CH/"01_timeseries.png"); plt.close(fig)

    # 2 — predictive scatter (z_full vs forward), clip y to ignore the 2020 neg-price tail visually
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, h in zip(axes, H):
        d = df.dropna(subset=["mm_z_full", h])
        y = (d[h]*100).clip(-40, 40)
        ax.scatter(d["mm_z_full"], y, s=10, alpha=0.4, color="#1f3b57")
        b, a = np.polyfit(d["mm_z_full"], d[h]*100, 1)
        xs = np.linspace(d["mm_z_full"].min(), d["mm_z_full"].max(), 50)
        ax.plot(xs, a+b*xs, color="#c0622d", lw=1.6)
        pr = res["relationship"]["predictive"]["z_full"][h]
        ax.set_title(f"{LBL[h]} fwd\nPearson r={pr['pearson']:+.2f} (p={pr['p']:.2f})")
        ax.set_xlabel("MM net z-score"); ax.axhline(0, color="k", lw=.6); ax.axvline(0, color="k", lw=.6)
    axes[0].set_ylabel("forward return (%, clipped ±40)")
    fig.suptitle("Managed-Money positioning z-score vs subsequent WTI return", y=1.02)
    fig.tight_layout(); fig.savefig(CH/"02_scatter_predictive.png", bbox_inches="tight"); plt.close(fig)

    # 3 — decile median forward returns (median = robust to 2020 outlier)
    fig, ax = plt.subplots(figsize=(9, 4.4))
    x = np.arange(1, 11); w = 0.26
    for i, h in enumerate(H):
        ax.bar(x+(i-1)*w, dec_med[h]*100, width=w, label=LBL[h])
    ax.axhline(0, color="k", lw=.7); ax.set_xticks(x)
    ax.set_xlabel("Managed-Money net decile (1 = most short, 10 = most long)")
    ax.set_ylabel("MEDIAN forward return (%)")
    ax.set_title("Median subsequent WTI return by Managed-Money positioning decile")
    ax.legend(); fig.tight_layout(); fig.savefig(CH/"03_decile_returns.png"); plt.close(fig)

    # 4 — extreme buckets (median) for decile and rolling-z definitions
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
    for ax, key, title in [(axes[0], "extremes_decile", "Top/Bottom decile (full sample)"),
                           (axes[1], "extremes_rollz", "Rolling-52w z > |1.5|")]:
        st = res[key]["stats"]; buckets = ["extreme_short", "mid", "extreme_long"]
        xx = np.arange(len(buckets)); w = 0.26
        for i, h in enumerate(H):
            ax.bar(xx+(i-1)*w, [st[b][h]["median"]*100 for b in buckets], width=w, label=LBL[h])
        ax.axhline(0, color="k", lw=.7); ax.set_xticks(xx)
        ax.set_xticklabels([f"{b}\n(n={st[b]['n']})" for b in buckets]); ax.set_title(title)
        ax.legend(fontsize=7)
    axes[0].set_ylabel("MEDIAN forward return (%)")
    fig.suptitle("Forward WTI returns after extreme Managed-Money positioning (medians)", y=1.02)
    fig.tight_layout(); fig.savefig(CH/"04_extreme_buckets.png", bbox_inches="tight"); plt.close(fig)

    # 5 — distribution boxplots (clip for display)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    order = ["extreme_short", "mid", "extreme_long"]; colors = ["#0a7", "#999", "#b00"]
    for ax, h in zip(axes, H):
        data = [(df[df["bk_dec"] == b][h].dropna()*100).clip(-40, 40) for b in order]
        bp = ax.boxplot(data, tick_labels=order, showmeans=True, patch_artist=True)
        for patch, cc in zip(bp["boxes"], colors): patch.set_facecolor(cc); patch.set_alpha(.35)
        ax.axhline(0, color="k", lw=.6); ax.set_title(f"{LBL[h]} fwd"); ax.tick_params(axis="x", labelsize=7)
    axes[0].set_ylabel("forward return (%, clipped ±40)")
    fig.suptitle("Distribution of forward returns by positioning extreme (decile buckets)", y=1.02)
    fig.tight_layout(); fig.savefig(CH/"05_return_distributions.png", bbox_inches="tight"); plt.close(fig)


def report(df, mm, dec_med):
    P = print
    P("="*72); P("CFTC MANAGED-MONEY POSITIONING vs WTI — ANALYSIS SUMMARY"); P("="*72)
    P(f"Sample: {len(df)} weeks  {df['asof'].min().date()} -> {df['asof'].max().date()}")
    P(f"MM net: mean {df['mm_net'].mean():,.0f}  std {df['mm_net'].std():,.0f}  "
      f"range [{df['mm_net'].min():,.0f}, {df['mm_net'].max():,.0f}]")
    P("NOTE: EIA WTI spot printed -$36.98 on Mon 2020-04-20; Friday-to-Friday release "
      "sampling steps over that single daily print, so no fwd return is contaminated. "
      "Medians reported alongside means for skew robustness.")
    P("")
    r = mm["relationship"]
    P("1) RELATIONSHIP")
    P(f"   MM net vs price LEVEL:   Pearson {r['level_pearson']:+.2f}  Spearman {r['level_spearman']:+.2f}")
    P(f"   ΔMM net vs %Δprice (same wk): {r['chg_vs_ret_pearson']:+.2f} (p={r['chg_vs_ret_p']:.1e})")
    P("   PREDICTIVE (signal -> forward return), Pearson r (p):")
    for s in r["predictive"]:
        row = r["predictive"][s]
        P(f"     {s:9s} " + "  ".join(f"{LBL[h]} {row[h]['pearson']:+.2f}({row[h]['p']:.2f})" for h in H))
    P("")
    P("2/3) FORWARD RETURNS AFTER EXTREMES  [median | mean | n]")
    b = mm["baseline"]
    P("   baseline(all): " + "  ".join(f"{LBL[h]} {b[h]['median']*100:+.2f}|{b[h]['mean']*100:+.2f}" for h in H))
    for key, name in [("extremes_decile", "DECILE extremes"), ("extremes_rollz", "ROLLING-Z |1.5|")]:
        P(f"   --- {name} ---")
        st = mm[key]["stats"]
        for bk in ["extreme_long", "extreme_short"]:
            P(f"     {bk:13s}(n={st[bk]['n']:3d}): " + "  ".join(
                f"{LBL[h]} {st[bk][h]['median']*100:+.2f}|{st[bk][h]['mean']*100:+.2f} "
                f"(pMW={st[bk][h]['p_vs_rest_med']:.2f})" for h in H))
    P("")
    P("   Decile MEDIAN fwd % (1=most short ... 10=most long):")
    for d, row in dec_med.iterrows():
        P(f"     dec {int(d):2d}: " + "  ".join(f"{LBL[h]} {row[h]*100:+.2f}" for h in H))
    P("="*72)


def main():
    df = pd.read_csv(DATA/"weekly_merged.csv", parse_dates=["asof", "release"])
    mm, dfm, dec_mean, dec_med = analyze_series(df, "mm")
    orr, _, _, _ = analyze_series(df, "or")
    summary = {
        "sample": {"weeks": int(len(df)), "start": str(df["asof"].min().date()),
                   "end": str(df["asof"].max().date()),
                   "mm_net_mean": float(df["mm_net"].mean()), "mm_net_std": float(df["mm_net"].std()),
                   "mm_net_min": float(df["mm_net"].min()), "mm_net_max": float(df["mm_net"].max())},
        "data_source_note": ("Supplied /Data Excel (CFTC-D_F_CL_OR_NET_1W) is CFTC "
                             "OTHER REPORTABLES, not Managed Money — verified vs official CFTC. "
                             "Managed Money pulled from official CFTC API (WTI 067651)."),
        "managed_money": mm, "other_reportables_compare": orr,
    }
    charts(dfm, dec_mean, dec_med, mm)
    with open(DATA/"stats_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    report(dfm, mm, dec_med)
    # quick OR-vs-MM contrast line
    P = print
    P("\nOTHER-REPORTABLES (supplied file) — contemporaneous Δpos vs %Δprice corr: "
      f"{orr['relationship']['chg_vs_ret_pearson']:+.2f}  | MM: {mm['relationship']['chg_vs_ret_pearson']:+.2f}")
    P("charts/ updated; data/stats_summary.json written.")


if __name__ == "__main__":
    main()
