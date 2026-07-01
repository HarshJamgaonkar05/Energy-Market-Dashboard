"""
04_deep_analysis.py  —  the mathematical deep-dive
--------------------------------------------------
Second, heavier pass on the CFTC Managed-Money vs WTI question. Where
02_analysis.py measured *whether* a relationship exists, this file interrogates
its DIRECTION, DYNAMICS, and TRADEABILITY with proper time-series econometrics:

  A. Cross-correlation function (CCF) — Δposition vs return at leads/lags −8..+8,
     with Bartlett ±1.96/√N bands. Pins down "coincident vs leading" numerically.
  B. Granger causality — both directions (Δpos→ret and ret→Δpos), lags 1..4.
  C. Reduced-form VAR + orthogonalized impulse response (IRF) with Monte-Carlo
     error bands: response of WTI return to a 1-SD Managed-Money position shock.
  D. Mean-reversion of positioning — AR(1) / Ornstein-Uhlenbeck half-life.
     How long does a crowding extreme actually persist (→ tradeability window)?
  E. Quantile regression — does positioning move the tails of the forward-return
     distribution even if it leaves the mean alone?
  F. Logistic regression — direction (P[fwd>0]) on the positioning z-score, with
     pseudo-R² and in-/out-of-sample AUC.
  G. Signal information horizon — |corr| of the z-score with forward returns at
     1..12 weeks: where, if anywhere, does predictive content live?
  H. Walk-forward OUT-OF-SAMPLE backtest of the one candidate edge (contrarian,
     long after net-short capitulation). Point-in-time rolling-z signal, fixed
     a-priori threshold. Equity curve vs buy&hold, Sharpe, max drawdown, exposure,
     turnover, transaction-cost sensitivity, and a circular block-bootstrap
     p-value on the Sharpe ratio.
  I. Multiple-testing correction — Benjamini-Hochberg FDR across the whole family
     of extreme-bucket tests. How many "edges" survive once you admit you looked
     many times?

Reads   data/weekly_merged.csv, data/wti_spot_daily.csv
Writes  data/deep_stats.json + charts/07..12*.png (dark dashboard theme)
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import statsmodels.api as sm
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
from statsmodels.regression.quantile_regression import QuantReg

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
CH = HERE / "charts"
CH.mkdir(exist_ok=True)

# ---- dashboard dark palette (identical to 02_analysis.py) -------------------
BG = "#0e0f12"; PANEL = "#101115"; GRID = "#1c1d22"
INK = "#e4e4e7"; MUT = "#a1a1aa"
AMBER = "#f59e0b"; EMER = "#10b981"; RED = "#ef4444"; SKY = "#38bdf8"; VIOLET = "#a78bfa"
plt.rcParams.update({
    "figure.dpi": 140, "font.size": 9, "font.family": "DejaVu Sans",
    "figure.facecolor": BG, "savefig.facecolor": BG,
    "axes.facecolor": PANEL, "axes.edgecolor": GRID, "axes.labelcolor": INK,
    "axes.titlecolor": INK, "text.color": INK,
    "xtick.color": MUT, "ytick.color": MUT,
    "axes.grid": True, "grid.color": GRID, "grid.alpha": 0.6, "axes.axisbelow": True,
    "legend.facecolor": PANEL, "legend.edgecolor": GRID, "legend.framealpha": 0.9,
})
WKS_YR = 52.0
RNG = np.random.default_rng(11)


def style_ax(ax):
    for s in ax.spines.values():
        s.set_color(GRID)
    return ax


# ============================================================ A. CCF lead/lag
def cross_correlation(dpos, ret, max_lag=8):
    """corr(dpos_{t-k}, ret_t): k>0 → position change LEADS the return."""
    d = pd.DataFrame({"dpos": dpos, "ret": ret}).dropna()
    x = (d["dpos"] - d["dpos"].mean()) / d["dpos"].std(ddof=0)
    y = (d["ret"] - d["ret"].mean()) / d["ret"].std(ddof=0)
    n = len(d)
    lags, corr = [], []
    for k in range(-max_lag, max_lag + 1):
        if k >= 0:
            a, b = x.iloc[:n - k].values, y.iloc[k:].values
        else:
            a, b = x.iloc[-k:].values, y.iloc[:n + k].values
        lags.append(k)
        corr.append(float(np.corrcoef(a, b)[0, 1]) if len(a) > 3 else np.nan)
    band = 1.96 / np.sqrt(n)               # Bartlett large-sample band
    return {"lags": lags, "corr": corr, "band": float(band), "n": int(n)}


# ============================================================ B. Granger
def granger(y, x, maxlag=4):
    """Does x Granger-cause y? Return per-lag p (ssr F-test) + min-p."""
    d = pd.DataFrame({"y": y, "x": x}).dropna()
    try:
        res = grangercausalitytests(d[["y", "x"]].values, maxlag=maxlag, verbose=False)
        pv = {int(L): float(res[L][0]["ssr_ftest"][1]) for L in res}
        best = min(pv, key=pv.get)
        return {"p_by_lag": pv, "min_p": pv[best], "best_lag": best}
    except Exception as e:
        return {"error": str(e)}


# ============================================================ C. VAR + IRF
def var_irf(ret, dpos_k, horizon=8):
    """Orthogonalized IRF (Cholesky order dpos→ret): response of ret to a
    +1-SD Managed-Money position shock, with Monte-Carlo 95% error bands."""
    d = pd.DataFrame({"dpos": dpos_k, "ret": ret}).dropna()
    try:
        model = VAR(d.values)
        sel = model.select_order(maxlags=6)
        p = int(sel.aic) if sel.aic and sel.aic > 0 else 2
        res = model.fit(maxlags=p)
        irf = res.irf(horizon)
        # column 0 = dpos, column 1 = ret; response of ret(1) to shock in dpos(0)
        pt = irf.orth_irfs[:, 1, 0]
        resp = pt.tolist()
        cum = np.cumsum(pt).tolist()
        try:                                   # analytic asymptotic 95% band
            se = irf.stderr(orth=True)[:, 1, 0]
            band_lo = (pt - 1.96 * se).tolist(); band_hi = (pt + 1.96 * se).tolist()
            cum_se = np.sqrt(np.cumsum(se ** 2))          # indep-approx cumulative SE
            cum_lo = (np.cumsum(pt) - 1.96 * cum_se).tolist()
            cum_hi = (np.cumsum(pt) + 1.96 * cum_se).tolist()
        except Exception:
            band_lo = band_hi = cum_lo = cum_hi = None
        return {"lag_order": p, "resp": resp, "cum": cum,
                "band_lo": band_lo, "band_hi": band_hi,
                "cum_lo": cum_lo, "cum_hi": cum_hi,
                "cum_total": float(cum[-1])}
    except Exception as e:
        return {"error": str(e)}


# ============================================================ D. half-life
def half_life(level):
    """AR(1): x_t = a + rho x_{t-1}; OU half-life = -ln2/ln(rho)."""
    x = pd.Series(level).dropna()
    x0, x1 = x.shift(1).dropna(), x.iloc[1:]
    X = sm.add_constant(x0.values)
    m = sm.OLS(x1.values, X).fit()
    rho = float(m.params[1])
    hl = float(-np.log(2) / np.log(rho)) if 0 < rho < 1 else np.nan
    # full autocorrelation profile for the chart
    acf = [float(x.autocorr(lag=k)) for k in range(0, 27)]
    return {"rho": rho, "half_life_wks": hl, "acf": acf,
            "adf_p": float(adfuller(x.values)[1])}


# ============================================================ E. quantile reg
def quantile_reg(z, ret, taus=(0.1, 0.25, 0.5, 0.75, 0.9)):
    d = pd.DataFrame({"z": z, "r": ret}).dropna()
    X = sm.add_constant(d["z"].values)
    out = {}
    for q in taus:
        try:
            m = QuantReg(d["r"].values, X).fit(q=q, max_iter=2000)
            out[str(q)] = {"slope": float(m.params[1]) * 100,
                           "p": float(m.pvalues[1]),
                           "lo": float(m.conf_int()[1, 0]) * 100,
                           "hi": float(m.conf_int()[1, 1]) * 100}
        except Exception:
            out[str(q)] = {"slope": np.nan, "p": np.nan, "lo": np.nan, "hi": np.nan}
    return out


# ============================================================ F. logistic
def logit_direction(z, ret):
    d = pd.DataFrame({"z": z, "r": ret}).dropna()
    d["up"] = (d["r"] > 0).astype(int)
    X = sm.add_constant(d["z"].values)
    try:
        m = sm.Logit(d["up"].values, X).fit(disp=0)
        # in-sample AUC (Mann-Whitney U identity)
        p_hat = m.predict(X)
        pos, neg = p_hat[d["up"].values == 1], p_hat[d["up"].values == 0]
        auc = float(stats.mannwhitneyu(pos, neg, alternative="greater").statistic / (len(pos) * len(neg)))
        return {"beta": float(m.params[1]), "p": float(m.pvalues[1]),
                "pseudo_r2": float(m.prsquared), "auc": auc, "n": int(len(d))}
    except Exception as e:
        return {"error": str(e)}


# ============================================================ G. info horizon
def info_horizon(price, df, zcol, weeks=12):
    """|corr| of the point-in-time z with the k-week forward return, k=1..weeks."""
    pidx = price.index
    out = {"k": [], "r": [], "p": []}
    for k in range(1, weeks + 1):
        fut = df["release"] + pd.Timedelta(days=7 * k)
        fr = fut.apply(lambda t: (price.loc[:t].iloc[-1] if t <= pidx.max() and len(price.loc[:t]) else np.nan))
        fret = fr.values / df["price_entry"].values - 1.0
        d = pd.DataFrame({"z": df[zcol].values, "r": fret}).dropna()
        if len(d) > 10:
            r, p = stats.pearsonr(d["z"], d["r"])
        else:
            r, p = np.nan, np.nan
        out["k"].append(k); out["r"].append(float(r)); out["p"].append(float(p))
    return out


# ============================================================ H. OOS backtest
def block_bootstrap_sharpe(r, block=8, B=5000):
    r = np.asarray(pd.Series(r).dropna())
    n = len(r)
    if n < 10:
        return {}
    nb = int(np.ceil(n / block))
    sh = np.empty(B)
    for b in range(B):
        st = RNG.integers(0, n, nb)
        idx = (st[:, None] + np.arange(block)[None, :]).ravel() % n
        s = r[idx[:n]]
        sh[b] = s.mean() / s.std(ddof=1) * np.sqrt(WKS_YR) if s.std(ddof=1) > 0 else 0.0
    return {"ci_lo": float(np.percentile(sh, 2.5)), "ci_hi": float(np.percentile(sh, 97.5)),
            "p_le_0": float((sh <= 0).mean())}


def perf(r):
    r = pd.Series(r).dropna()
    if len(r) < 5:
        return {}
    eq = (1 + r).cumprod()
    dd = (eq / eq.cummax() - 1.0)
    ann_ret = float((1 + r).prod() ** (WKS_YR / len(r)) - 1)
    ann_vol = float(r.std(ddof=1) * np.sqrt(WKS_YR))
    sharpe = float(r.mean() / r.std(ddof=1) * np.sqrt(WKS_YR)) if r.std(ddof=1) > 0 else np.nan
    return {"ann_ret": ann_ret, "ann_vol": ann_vol, "sharpe": sharpe,
            "max_dd": float(dd.min()), "hit": float((r > 0).mean()), "n": int(len(r))}


def backtest(df, z_lo=-1.0, z_hi=1.0, cost_bps=(0, 5, 10)):
    """Weekly-rebalanced, non-overlapping (uses fwd_1w). Point-in-time rolling-z
    signal, fixed a-priori thresholds → pseudo-OOS.
      long-only  : w=1 when z<=z_lo (net-short capitulation), else 0
      long-short : w=+1 when z<=z_lo, −1 when z>=z_hi, else 0
    """
    d = df.dropna(subset=["mm_z_roll52", "fwd_1w"]).copy().reset_index(drop=True)
    z, mkt = d["mm_z_roll52"].values, d["fwd_1w"].values
    w_lo = (z <= z_lo).astype(float)
    w_ls = np.where(z <= z_lo, 1.0, np.where(z >= z_hi, -1.0, 0.0))

    def with_costs(w, c_bps):
        turn = np.abs(np.diff(np.concatenate([[0.0], w])))
        gross = w * mkt
        net = gross - turn * (c_bps / 1e4)
        return net, float(turn.sum()), float(turn.mean())

    res = {"dates": [str(x.date()) for x in d["release"]],
           "buy_hold_equity": (1 + pd.Series(mkt)).cumprod().round(4).tolist(),
           "z": np.round(z, 2).tolist()}
    for name, w in [("long_only", w_lo), ("long_short", w_ls)]:
        net0, tot_turn, avg_turn = with_costs(w, 0)
        block = {"exposure": float((w != 0).mean()), "total_turnover": tot_turn,
                 "n_trades": int((np.abs(np.diff(np.concatenate([[0.0], w]))) > 0).sum()),
                 "equity": (1 + pd.Series(net0)).cumprod().round(4).tolist(),
                 "signal_weight": w.tolist()}
        for c in cost_bps:
            netc, _, _ = with_costs(w, c)
            block[f"perf_{c}bps"] = perf(netc)
        block["boot_sharpe"] = block_bootstrap_sharpe(net0)
        res[name] = block
    res["buy_hold_perf"] = perf(mkt)
    return res


# ============================================================ I. BH-FDR
def bh_fdr(pairs, q=0.10):
    """pairs: list of (label, p). Benjamini-Hochberg. Returns sorted + survivors."""
    valid = [(l, p) for l, p in pairs if p == p]
    m = len(valid)
    order = sorted(valid, key=lambda t: t[1])
    out, kmax = [], 0
    for i, (l, p) in enumerate(order, 1):
        thr = q * i / m
        passed = p <= thr
        if passed:
            kmax = i
        out.append({"label": l, "p": float(p), "rank": i, "bh_thr": float(thr)})
    for i, row in enumerate(out, 1):
        row["survives"] = i <= kmax
    return {"m": m, "q": q, "n_survivors": kmax, "tests": out}


# ============================================================ charts
def chart_ccf(ccf):
    fig, ax = plt.subplots(figsize=(9, 4.2))
    lags = np.array(ccf["lags"]); c = np.array(ccf["corr"]); b = ccf["band"]
    cols = [AMBER if k == 0 else (SKY if k < 0 else EMER) for k in lags]
    ax.bar(lags, c, color=cols, width=0.72, ec=BG, lw=.4)
    ax.axhspan(-b, b, color=MUT, alpha=0.12)
    ax.axhline(b, color=MUT, lw=.7, ls="--"); ax.axhline(-b, color=MUT, lw=.7, ls="--")
    ax.axhline(0, color=MUT, lw=.8); ax.axvline(0, color=AMBER, lw=.8, alpha=.5)
    ax.set_xlabel("lag k  (k<0: return leads · k=0: same week · k>0: position change leads)")
    ax.set_ylabel("cross-correlation")
    ax.text(0.02, 0.95, f"peak at k=0  (r={c[lags==0][0]:+.2f})\nno bar at k>0 clears the band → not leading",
            transform=ax.transAxes, va="top", fontsize=8.2, color=MUT)
    style_ax(ax); ax.set_title("Cross-correlation: Δ Managed-Money position vs WTI return", weight="bold")
    fig.tight_layout(); fig.savefig(CH / "07_ccf.png"); plt.close(fig)


def chart_irf(irf):
    fig, ax = plt.subplots(figsize=(9, 4.2))
    if "error" in irf:
        ax.text(0.5, 0.5, "IRF unavailable", ha="center");
    else:
        cum = np.array(irf["cum"]); ks = np.arange(len(cum))
        ax.plot(ks, cum * 100, color=VIOLET, lw=2, marker="o", ms=4, label="cumulative response of WTI return")
        if irf.get("cum_lo"):
            ax.fill_between(ks, np.array(irf["cum_lo"]) * 100, np.array(irf["cum_hi"]) * 100,
                            color=VIOLET, alpha=0.15, label="95% asymptotic band")
        ax.axhline(0, color=MUT, lw=.8)
    ax.set_xlabel("weeks after shock"); ax.set_ylabel("cumulative WTI return (%)")
    style_ax(ax); ax.legend(labelcolor=INK, fontsize=8)
    ax.set_title("Impulse response: WTI return to a +1σ Managed-Money position shock", weight="bold")
    fig.tight_layout(); fig.savefig(CH / "08_irf.png"); plt.close(fig)


def chart_halflife(hl):
    fig, ax = plt.subplots(figsize=(9, 4.2))
    acf = np.array(hl["acf"]); ks = np.arange(len(acf))
    ax.bar(ks, acf, color=SKY, width=0.7, ec=BG, lw=.4, label="autocorrelation of MM net")
    if hl["half_life_wks"] == hl["half_life_wks"]:
        ax.plot(ks, hl["rho"] ** ks, color=AMBER, lw=2, label=f"AR(1) fit  ρ={hl['rho']:.2f}")
        ax.axvline(hl["half_life_wks"], color=EMER, lw=1.4, ls="--",
                   label=f"half-life ≈ {hl['half_life_wks']:.0f} wks")
        ax.axhline(0.5, color=MUT, lw=.6)
    ax.axhline(0, color=MUT, lw=.8); ax.set_xlabel("lag (weeks)"); ax.set_ylabel("autocorrelation")
    style_ax(ax); ax.legend(labelcolor=INK, fontsize=8)
    ax.set_title("Positioning is persistent — mean-reversion half-life of MM net", weight="bold")
    fig.tight_layout(); fig.savefig(CH / "09_halflife.png"); plt.close(fig)


def chart_quantile(qr, horizon_lbl):
    fig, ax = plt.subplots(figsize=(9, 4.2))
    taus = sorted(float(k) for k in qr)
    sl = [qr[str(t)]["slope"] for t in taus]
    lo = [qr[str(t)]["lo"] for t in taus]; hi = [qr[str(t)]["hi"] for t in taus]
    ax.plot(taus, sl, color=AMBER, lw=2, marker="o", ms=5)
    ax.fill_between(taus, lo, hi, color=AMBER, alpha=0.15, label="95% CI")
    ax.axhline(0, color=MUT, lw=.8)
    ax.set_xlabel("forward-return quantile τ"); ax.set_ylabel("slope on MM net z-score (%/σ)")
    style_ax(ax); ax.legend(labelcolor=INK, fontsize=8)
    ax.set_title(f"Quantile regression — positioning barely moves the {horizon_lbl} return distribution", weight="bold")
    fig.tight_layout(); fig.savefig(CH / "10_quantile.png"); plt.close(fig)


def chart_equity(bt):
    fig, (ax, axd) = plt.subplots(2, 1, figsize=(10, 5.4), height_ratios=[2.4, 1], sharex=True)
    dates = pd.to_datetime(bt["dates"])
    ax.plot(dates, bt["buy_hold_equity"], color=MUT, lw=1.4, label="Buy & hold WTI")
    ax.plot(dates, bt["long_only"]["equity"], color=EMER, lw=1.8, label="Contrarian long-only (z≤−1)")
    ax.plot(dates, bt["long_short"]["equity"], color=AMBER, lw=1.4, alpha=.9, label="Long-short (z≤−1 / z≥+1)")
    ax.axhline(1, color=GRID, lw=.8); ax.set_ylabel("growth of $1 (weekly, non-overlap)")
    p = bt["long_only"]["perf_0bps"]
    ax.text(0.015, 0.96, f"long-only: Sharpe {p['sharpe']:.2f} · ann {p['ann_ret']*100:+.1f}% · "
            f"maxDD {p['max_dd']*100:.0f}% · in-mkt {bt['long_only']['exposure']*100:.0f}%",
            transform=ax.transAxes, va="top", fontsize=8, color=INK)
    style_ax(ax); ax.legend(labelcolor=INK, fontsize=8, loc="lower right")
    ax.set_title("Out-of-sample backtest of the one candidate edge (point-in-time signal)", weight="bold")
    # drawdown of long-only
    eq = pd.Series(bt["long_only"]["equity"]); dd = (eq / eq.cummax() - 1) * 100
    axd.fill_between(dates, dd, 0, color=RED, alpha=0.35)
    axd.set_ylabel("DD (%)"); axd.set_xlabel(""); style_ax(axd)
    fig.tight_layout(); fig.savefig(CH / "11_oos_equity.png"); plt.close(fig)


def chart_fdr(fdr):
    fig, ax = plt.subplots(figsize=(9, 4.2))
    t = fdr["tests"]; ranks = [r["rank"] for r in t]
    ps = [r["p"] for r in t]; thr = [r["bh_thr"] for r in t]
    cols = [EMER if r["survives"] else RED for r in t]
    ax.scatter(ranks, ps, color=cols, s=34, zorder=5, ec=BG, lw=.4)
    ax.plot(ranks, thr, color=AMBER, lw=1.6, ls="--", label=f"BH threshold (q={fdr['q']})")
    ax.axhline(0.05, color=MUT, lw=.7, ls=":", label="naive 0.05")
    ax.set_xlabel(f"rank of test (of {fdr['m']} extreme-bucket tests)"); ax.set_ylabel("p-value")
    ax.set_ylim(0, min(1.0, max(ps + [0.06]) * 1.1)); style_ax(ax)
    ax.legend(labelcolor=INK, fontsize=8)
    ax.set_title(f"Multiple-testing (Benjamini-Hochberg): {fdr['n_survivors']} of {fdr['m']} survive q={fdr['q']}", weight="bold")
    fig.tight_layout(); fig.savefig(CH / "12_fdr.png"); plt.close(fig)


# ============================================================ main
def main():
    df = pd.read_csv(DATA / "weekly_merged.csv", parse_dates=["asof", "release"])
    price = pd.read_csv(DATA / "wti_spot_daily.csv", parse_dates=["date"]).set_index("date")["price"].sort_index()
    df["ret"] = df["price_asof"].pct_change()

    P = print
    P("=" * 74); P("CFTC MANAGED-MONEY vs WTI — MATHEMATICAL DEEP-DIVE"); P("=" * 74)

    # A. CCF
    ccf = cross_correlation(df["mm_chg"], df["ret"], max_lag=8)
    k0 = ccf["corr"][ccf["lags"].index(0)]
    lead_max = max(abs(ccf["corr"][ccf["lags"].index(k)]) for k in range(1, 9))
    P(f"\nA. CROSS-CORRELATION  peak k=0 r={k0:+.2f} | max |lead (k>0)|={lead_max:.2f} | band=±{ccf['band']:.2f}")

    # B. Granger both directions
    g_pos_ret = granger(df["ret"], df["mm_chg"], maxlag=4)   # Δpos → ret
    g_ret_pos = granger(df["mm_chg"], df["ret"], maxlag=4)   # ret → Δpos
    P(f"B. GRANGER  Δpos→ret min-p={g_pos_ret.get('min_p', float('nan')):.3f} (lag {g_pos_ret.get('best_lag')}) | "
      f"ret→Δpos min-p={g_ret_pos.get('min_p', float('nan')):.3f} (lag {g_ret_pos.get('best_lag')})")

    # C. VAR + IRF  (position change in thousands of contracts)
    irf = var_irf(df["ret"], df["mm_chg"] / 1e3, horizon=8)
    P(f"C. VAR/IRF  order={irf.get('lag_order')} cum WTI response to +1σ pos shock = "
      f"{irf.get('cum_total', float('nan'))*100:+.2f}% over 8 wks")

    # D. half-life of positioning
    hl = half_life(df["mm_net"])
    P(f"D. HALF-LIFE  AR(1) ρ={hl['rho']:.2f} → half-life ≈ {hl['half_life_wks']:.0f} wks (ADF p={hl['adf_p']:.3f})")

    # E. quantile regression (4-week, tradeable rolling z)
    qr = quantile_reg(df["mm_z_roll52"], df["fwd_4w"])
    P("E. QUANTILE (4w) slope %/σ: " + " ".join(f"τ{t}={qr[t]['slope']:+.2f}" for t in qr))

    # F. logistic direction
    lg = logit_direction(df["mm_z_roll52"], df["fwd_4w"])
    P(f"F. LOGIT direction  β={lg.get('beta', float('nan')):+.3f} p={lg.get('p', float('nan')):.2f} "
      f"pseudoR²={lg.get('pseudo_r2', float('nan')):.3f} AUC={lg.get('auc', float('nan')):.2f}")

    # G. information horizon
    ih = info_horizon(price, df, "mm_z_roll52", weeks=12)
    kbest = int(np.nanargmax(np.abs(ih["r"]))) + 1
    P(f"G. INFO HORIZON  strongest |r| at {kbest}w (r={ih['r'][kbest-1]:+.2f}, p={ih['p'][kbest-1]:.2f})")

    # H. OOS backtest
    bt = backtest(df, z_lo=-1.0, z_hi=1.0)
    lo = bt["long_only"]; bh = bt["buy_hold_perf"]
    P(f"H. OOS BACKTEST  long-only Sharpe {lo['perf_0bps']['sharpe']:.2f} "
      f"(net 5bps {lo['perf_5bps']['sharpe']:.2f}) vs buy&hold {bh['sharpe']:.2f} | "
      f"exposure {lo['exposure']*100:.0f}% | maxDD {lo['perf_0bps']['max_dd']*100:.0f}% | "
      f"boot p(Sharpe≤0)={lo['boot_sharpe'].get('p_le_0', float('nan')):.2f}")

    # I. BH-FDR across all extreme-bucket tests (recompute the family)
    S = json.load(open(DATA / "stats_summary.json"))
    pairs = []
    for defn, key in [("decile", "extremes_decile"), ("rollz", "extremes_rollz")]:
        st = S["managed_money"][key]["stats"]
        for bk in ["extreme_long", "extreme_short"]:
            for h in ["fwd_1w", "fwd_2w", "fwd_4w"]:
                pv = st[bk][h].get("p_vs_rest_med")
                if pv is not None:
                    pairs.append((f"{defn} {bk.replace('extreme_','')} {h.replace('fwd_','')}", pv))
    fdr = bh_fdr(pairs, q=0.10)
    P(f"I. MULTIPLE-TESTING  {fdr['n_survivors']} of {fdr['m']} bucket tests survive BH q=0.10")
    P("=" * 74)

    # charts
    chart_ccf(ccf); chart_irf(irf); chart_halflife(hl)
    chart_quantile(qr, "4-week"); chart_equity(bt); chart_fdr(fdr)

    out = {
        "cross_correlation": ccf,
        "granger": {"dpos_to_ret": g_pos_ret, "ret_to_dpos": g_ret_pos},
        "var_irf": irf,
        "half_life": hl,
        "quantile_reg_4w": qr,
        "logit_direction_4w": lg,
        "info_horizon": ih,
        "backtest": bt,
        "fdr": fdr,
        "notes": ("Signals are point-in-time (rolling-52w z); backtest thresholds are fixed a-priori "
                  "(z_lo=-1, z_hi=+1) so the equity curve is pseudo-out-of-sample. Weekly non-overlapping "
                  "returns (fwd_1w) drive the curve; overlapping windows are used only for the descriptive "
                  "bucket stats, which is why HAC / bootstrap / BH-FDR accompany them."),
    }
    with open(DATA / "deep_stats.json", "w") as f:
        json.dump(out, f, indent=2)
    P("charts/ 07..12 + data/deep_stats.json written.")


if __name__ == "__main__":
    main()
