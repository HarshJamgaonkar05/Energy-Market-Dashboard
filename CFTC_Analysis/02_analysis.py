"""
02_analysis.py  —  refined
--------------------------
Does CFTC Managed-Money positioning have predictive value for WTI crude prices?

Reads  data/weekly_merged.csv + data/wti_spot_daily.csv  (from 01_prepare_data.py)
Writes data/stats_summary.json + console report + charts/*.png  (dark dashboard theme)

PRIMARY series : Managed Money net (official CFTC, WTI 067651).
SECONDARY      : Other Reportables net (= the supplied /Data Excel) — contrast only.

Refinements over the first pass:
  * Newey-West (HAC) p-values on the predictive slope — honest inference under the
    autocorrelation induced by OVERLAPPING forward windows.
  * Hit-rate (% positive) per extreme bucket.
  * Circular block-bootstrap 95% CIs on extreme-bucket mean forward returns.
  * Event-study: average cumulative WTI path for weeks 0..6 after each extreme.
Forward-return distributions are skewed, so MEDIANS accompany means throughout.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

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

# ---- dashboard dark palette -------------------------------------------------
BG = "#0e0f12"; PANEL = "#101115"; GRID = "#1c1d22"
INK = "#e4e4e7"; MUT = "#a1a1aa"
AMBER = "#f59e0b"; EMER = "#10b981"; RED = "#ef4444"; SKY = "#38bdf8"
SERIES3 = [SKY, AMBER, EMER]   # 1w / 2w / 4w
plt.rcParams.update({
    "figure.dpi": 140, "font.size": 9, "font.family": "DejaVu Sans",
    "figure.facecolor": BG, "savefig.facecolor": BG,
    "axes.facecolor": PANEL, "axes.edgecolor": GRID, "axes.labelcolor": INK,
    "axes.titlecolor": INK, "text.color": INK,
    "xtick.color": MUT, "ytick.color": MUT,
    "axes.grid": True, "grid.color": GRID, "grid.alpha": 0.6, "axes.axisbelow": True,
    "legend.facecolor": PANEL, "legend.edgecolor": GRID, "legend.framealpha": 0.9,
})

H = ["fwd_1w", "fwd_2w", "fwd_4w"]
LBL = {"fwd_1w": "1-week", "fwd_2w": "2-week", "fwd_4w": "4-week"}
NW_LAGS = {"fwd_1w": 1, "fwd_2w": 2, "fwd_4w": 4}
RNG = np.random.default_rng(7)


# ----------------------------------------------------------------- stats utils
def robust_stats(x):
    x = pd.Series(x).dropna()
    n = len(x)
    if n < 3:
        return {"mean": np.nan, "median": np.nan, "hit": np.nan, "t": np.nan, "p": np.nan, "n": n}
    t, p = stats.ttest_1samp(x, 0.0)
    return {"mean": float(x.mean()), "median": float(x.median()),
            "hit": float((x > 0).mean()), "t": float(t), "p": float(p), "n": n}


def block_bootstrap_ci(x, block=4, B=5000):
    """Circular block-bootstrap 95% CI for the MEAN (respects autocorrelation)."""
    x = np.asarray(pd.Series(x).dropna())
    n = len(x)
    if n < 5:
        return (np.nan, np.nan)
    nb = int(np.ceil(n / block))
    means = np.empty(B)
    for b in range(B):
        starts = RNG.integers(0, n, nb)
        idx = (starts[:, None] + np.arange(block)[None, :]).ravel() % n
        means[b] = x[idx[:n]].mean()
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def nw_slope_p(signal, ret, lags):
    """OLS ret ~ a + b*signal with Newey-West HAC SEs; return (beta, p, r)."""
    d = pd.DataFrame({"s": signal, "r": ret}).dropna()
    if len(d) < 10:
        return (np.nan, np.nan, np.nan)
    X = sm.add_constant(d["s"].values)
    m = sm.OLS(d["r"].values, X).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    r = float(np.corrcoef(d["s"], d["r"])[0, 1])
    return (float(m.params[1]), float(m.pvalues[1]), r)


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
                _, pu = stats.mannwhitneyu(xx, comp, alternative="two-sided")
            else:
                pu = np.nan
            rs["p_vs_rest_med"] = float(pu) if pu == pu else None
            lo, hi = block_bootstrap_ci(xx)
            rs["ci95_lo"], rs["ci95_hi"] = lo, hi
            out[b][h] = rs
    return out


def event_study(df, price, bcol, weeks=6):
    """Average cumulative WTI return for k=0..weeks after each extreme event."""
    pidx = price.index
    paths = {"extreme_long": [], "extreme_short": [], "mid": []}
    for _, row in df.iterrows():
        b = row[bcol]
        entry = row["release"]
        p0 = price.loc[:entry]
        if not len(p0):
            continue
        p0 = p0.iloc[-1]
        path = []
        ok = True
        for k in range(weeks + 1):
            tgt = entry + pd.Timedelta(days=7 * k)
            if tgt > pidx.max():
                ok = False; break
            path.append(price.loc[:tgt].iloc[-1] / p0 - 1.0)
        if ok:
            paths[b].append(path)
    res = {}
    for b, arr in paths.items():
        if not arr:
            continue
        a = np.array(arr) * 100
        res[b] = {"mean": a.mean(0).tolist(), "se": (a.std(0) / np.sqrt(len(a))).tolist(),
                  "n": len(a)}
    return res


def analyze_series(df, pfx):
    net, chg = f"{pfx}_net", f"{pfx}_chg"
    zf, zr = f"{pfx}_z_full", f"{pfx}_z_roll52"
    df = df.copy()
    df["wk_ret"] = df["price_asof"].pct_change()
    res = {}
    m = df.dropna(subset=[net, "price_asof"])
    c = df.dropna(subset=[chg, "wk_ret"])
    res["relationship"] = {
        "level_pearson": float(np.corrcoef(m[net], m["price_asof"])[0, 1]),
        "level_spearman": float(stats.spearmanr(m[net], m["price_asof"]).statistic),
        "chg_vs_ret_pearson": float(np.corrcoef(c[chg], c["wk_ret"])[0, 1]),
        "chg_vs_ret_p": float(stats.pearsonr(c[chg], c["wk_ret"])[1]),
        "predictive": {}}
    for sname, s in [("z_roll52", df[zr]), ("z_full", df[zf]), ("chg", df[chg])]:
        res["relationship"]["predictive"][sname] = {}
        for h in H:
            beta, pnw, r = nw_slope_p(s, df[h], NW_LAGS[h])
            res["relationship"]["predictive"][sname][h] = {
                "pearson": r, "beta": beta, "p_nw": pnw}

    res["baseline"] = {h: robust_stats(df[h]) for h in H}
    p10, p90 = df[net].quantile(0.10), df[net].quantile(0.90)
    df["bk_dec"] = np.where(df[net] >= p90, "extreme_long",
                   np.where(df[net] <= p10, "extreme_short", "mid"))
    Z = 1.5
    df["bk_z"] = np.where(df[zr] >= Z, "extreme_long",
                 np.where(df[zr] <= -Z, "extreme_short", "mid"))
    res["extremes_decile"] = {"p10": float(p10), "p90": float(p90), "stats": bucket_stats(df, "bk_dec")}
    res["extremes_rollz"] = {"z": Z, "stats": bucket_stats(df, "bk_z")}
    df["decile"] = pd.qcut(df[net], 10, labels=False) + 1
    dec_med = df.groupby("decile")[H].median()
    res["decile_median"] = {int(k): {h: float(v) for h, v in r.items()} for k, r in dec_med.iterrows()}
    return res, df, dec_med


# ----------------------------------------------------------------- charts
def style_ax(ax):
    for s in ax.spines.values():
        s.set_color(GRID)
    return ax


def charts(df, dec_med, res, price, ev):
    # 1 — time series + extremes
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.plot(df["asof"], df["price_asof"], color=SKY, lw=1.3, label="WTI spot ($/bbl)")
    ax.set_ylabel("WTI spot ($/bbl)", color=SKY)
    ax2 = ax.twinx()
    ax2.plot(df["asof"], df["mm_net"]/1e3, color=AMBER, lw=1.0, alpha=0.85, label="MM net (k)")
    ax2.set_ylabel("Managed-Money net (000s)", color=AMBER); ax2.grid(False)
    el = df[df["bk_dec"] == "extreme_long"]; es = df[df["bk_dec"] == "extreme_short"]
    ax2.scatter(el["asof"], el["mm_net"]/1e3, s=16, color=RED, zorder=5, ec=BG, lw=.4, label="extreme long")
    ax2.scatter(es["asof"], es["mm_net"]/1e3, s=16, color=EMER, zorder=5, ec=BG, lw=.4, label="extreme short")
    ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    for a in (ax, ax2): style_ax(a)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1+h2, l1+l2, fontsize=7.5, loc="upper left", ncol=2, labelcolor=INK)
    ax.set_title("WTI spot vs CFTC Managed-Money net positioning (2016–2026)", weight="bold")
    fig.tight_layout(); fig.savefig(CH/"01_timeseries.png"); plt.close(fig)

    # 2 — predictive scatter (HAC p)
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.9))
    for ax, h in zip(axes, H):
        d = df.dropna(subset=["mm_z_full", h])
        ax.scatter(d["mm_z_full"], (d[h]*100).clip(-40, 40), s=11, alpha=0.45, color=SKY, ec="none")
        b, a = np.polyfit(d["mm_z_full"], d[h]*100, 1)
        xs = np.linspace(d["mm_z_full"].min(), d["mm_z_full"].max(), 50)
        ax.plot(xs, a+b*xs, color=AMBER, lw=2)
        pr = res["relationship"]["predictive"]["z_full"][h]
        ax.set_title(f"{LBL[h]} fwd   r={pr['pearson']:+.2f}\nNewey-West p={pr['p_nw']:.2f}", fontsize=9)
        ax.set_xlabel("MM net z-score"); ax.axhline(0, color=MUT, lw=.6); ax.axvline(0, color=MUT, lw=.6)
        style_ax(ax)
    axes[0].set_ylabel("forward return (%, clipped)")
    fig.suptitle("Positioning z-score has ~no linear predictive power", y=1.02, weight="bold")
    fig.tight_layout(); fig.savefig(CH/"02_scatter_predictive.png", bbox_inches="tight"); plt.close(fig)

    # 3 — decile median forward returns
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(1, 11); w = 0.26
    for i, h in enumerate(H):
        ax.bar(x+(i-1)*w, dec_med[h]*100, width=w, label=LBL[h], color=SERIES3[i])
    ax.axhline(0, color=MUT, lw=.7); ax.set_xticks(x); style_ax(ax)
    ax.set_xlabel("Managed-Money net decile (1 = most short → 10 = most long)")
    ax.set_ylabel("MEDIAN forward return (%)")
    ax.set_title("Subsequent WTI return by positioning decile (non-monotonic)", weight="bold")
    ax.legend(labelcolor=INK); fig.tight_layout(); fig.savefig(CH/"03_decile_returns.png"); plt.close(fig)

    # 4 — extreme buckets (median) decile vs rolling-z
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, key, title in [(axes[0], "extremes_decile", "Top/Bottom decile (full-sample)"),
                           (axes[1], "extremes_rollz", "Rolling-52w z > |1.5| (point-in-time)")]:
        st = res[key]["stats"]; buckets = ["extreme_short", "mid", "extreme_long"]
        xx = np.arange(len(buckets)); w = 0.26
        for i, h in enumerate(H):
            ax.bar(xx+(i-1)*w, [st[b][h]["median"]*100 for b in buckets], width=w, label=LBL[h], color=SERIES3[i])
        ax.axhline(0, color=MUT, lw=.7); ax.set_xticks(xx); style_ax(ax)
        ax.set_xticklabels([f"{b.replace('extreme_','')}\n(n={st[b]['n']})" for b in buckets])
        ax.set_title(title, fontsize=9.5); ax.legend(fontsize=7, labelcolor=INK)
    axes[0].set_ylabel("MEDIAN forward return (%)")
    fig.suptitle("Forward WTI returns after extreme Managed-Money positioning", y=1.02, weight="bold")
    fig.tight_layout(); fig.savefig(CH/"04_extreme_buckets.png", bbox_inches="tight"); plt.close(fig)

    # 5 — event-study cumulative path
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ks = np.arange(len(ev["mid"]["mean"]))
    style = {"extreme_short": (EMER, "Extreme short (washed-out bears)"),
             "extreme_long": (RED, "Extreme long (crowded bulls)"),
             "mid": (MUT, "Baseline (mid)")}
    for b, (col, lab) in style.items():
        if b not in ev:
            continue
        mean = np.array(ev[b]["mean"]); se = np.array(ev[b]["se"])
        ax.plot(ks, mean, color=col, lw=2, marker="o", ms=4, label=f"{lab}  (n={ev[b]['n']})")
        ax.fill_between(ks, mean-se, mean+se, color=col, alpha=0.15)
    ax.axhline(0, color=MUT, lw=.7); style_ax(ax)
    ax.set_xlabel("weeks after CFTC release"); ax.set_ylabel("avg cumulative WTI return (%)")
    ax.set_title("Event study: WTI path after positioning extremes (decile, ±1 s.e.)", weight="bold")
    ax.legend(labelcolor=INK, fontsize=8); fig.tight_layout(); fig.savefig(CH/"05_event_study.png"); plt.close(fig)

    # 6 — hit-rate heat-ish bars for 4-week
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    st = res["extremes_decile"]["stats"]
    cats = ["extreme_short", "mid", "extreme_long"]
    cols = [EMER, MUT, RED]
    vals = [st[c]["fwd_4w"]["hit"]*100 for c in cats]
    bars = ax.bar([c.replace("extreme_", "") for c in cats], vals, color=cols, alpha=0.85)
    ax.axhline(50, color=AMBER, lw=1, ls="--", label="coin-flip (50%)")
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, v+1, f"{v:.0f}%", ha="center", color=INK, fontsize=9)
    ax.set_ylim(0, 80); style_ax(ax)
    ax.set_ylabel("% of weeks with positive 4-week return")
    ax.set_title("4-week win-rate by positioning extreme (decile)", weight="bold")
    ax.legend(labelcolor=INK, fontsize=8); fig.tight_layout(); fig.savefig(CH/"06_hitrate.png"); plt.close(fig)


# ----------------------------------------------------------------- report
def report(df, mm, dec_med):
    P = print
    P("="*74); P("CFTC MANAGED-MONEY POSITIONING vs WTI — REFINED SUMMARY"); P("="*74)
    P(f"Sample: {len(df)} weeks  {df['asof'].min().date()} -> {df['asof'].max().date()}")
    P(f"MM net mean {df['mm_net'].mean():,.0f}  range [{df['mm_net'].min():,.0f}, {df['mm_net'].max():,.0f}]")
    r = mm["relationship"]
    P("\n1) RELATIONSHIP")
    P(f"   level: Pearson {r['level_pearson']:+.2f} | Δnet vs %Δprice: {r['chg_vs_ret_pearson']:+.2f} (p={r['chg_vs_ret_p']:.1e})")
    P("   PREDICTIVE  Pearson r  [Newey-West HAC p]:")
    for s in r["predictive"]:
        row = r["predictive"][s]
        P(f"     {s:9s} " + "  ".join(f"{LBL[h]} {row[h]['pearson']:+.2f}[{row[h]['p_nw']:.2f}]" for h in H))
    P("\n2/3) FORWARD RETURNS AFTER EXTREMES  [median% | mean% | hit% | 95%CI(mean) | pMW]")
    b = mm["baseline"]
    P("   baseline: " + "  ".join(f"{LBL[h]} {b[h]['median']*100:+.2f}|{b[h]['mean']*100:+.2f}|{b[h]['hit']*100:.0f}%" for h in H))
    for key, name in [("extremes_decile", "DECILE"), ("extremes_rollz", "ROLLING-Z|1.5|")]:
        P(f"   --- {name} ---")
        st = mm[key]["stats"]
        for bk in ["extreme_long", "extreme_short"]:
            s = st[bk]
            P(f"     {bk:13s}(n={s['n']:3d}):")
            for h in H:
                d = s[h]
                P(f"        {LBL[h]}: {d['median']*100:+.2f}|{d['mean']*100:+.2f}|{d['hit']*100:.0f}%"
                  f"  CI[{d['ci95_lo']*100:+.1f},{d['ci95_hi']*100:+.1f}]  pMW={d['p_vs_rest_med']:.2f}")
    P("="*74)


def main():
    df = pd.read_csv(DATA/"weekly_merged.csv", parse_dates=["asof", "release"])
    price = pd.read_csv(DATA/"wti_spot_daily.csv", parse_dates=["date"]).set_index("date")["price"].sort_index()
    mm, dfm, dec_med = analyze_series(df, "mm")
    orr, _, _ = analyze_series(df, "or")
    ev = event_study(dfm, price, "bk_dec", weeks=6)
    summary = {
        "sample": {"weeks": int(len(df)), "start": str(df["asof"].min().date()), "end": str(df["asof"].max().date()),
                   "mm_net_mean": float(df["mm_net"].mean()), "mm_net_min": float(df["mm_net"].min()),
                   "mm_net_max": float(df["mm_net"].max())},
        "data_source_note": ("Supplied /Data Excel (CFTC-D_F_CL_OR_NET_1W) is CFTC OTHER REPORTABLES, "
                             "not Managed Money. MM pulled from official CFTC API (WTI 067651); "
                             "price = EIA daily Cushing spot RWTC."),
        "managed_money": mm, "other_reportables_compare": orr, "event_study_decile": ev}
    charts(dfm, dec_med, mm, price, ev)
    with open(DATA/"stats_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    report(dfm, mm, dec_med)
    print(f"\nΔpos vs %Δprice — OR: {orr['relationship']['chg_vs_ret_pearson']:+.2f} | MM: {mm['relationship']['chg_vs_ret_pearson']:+.2f}")
    print("charts/ (6) + data/stats_summary.json written.")


if __name__ == "__main__":
    main()
