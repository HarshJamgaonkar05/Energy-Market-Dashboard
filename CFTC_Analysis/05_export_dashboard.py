"""
05_export_dashboard.py
----------------------
Distil the two heavy result files (data/stats_summary.json + data/deep_stats.json)
into ONE compact bundle the dashboard React page imports:  src/data/cftcStudy.json

Keeps the web bundle small and guarantees the in-app numbers never drift from the
analysis — the page renders only what this exporter selects.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE.parent / "src" / "data" / "cftcStudy.json"

S = json.load(open(DATA / "stats_summary.json"))
D = json.load(open(DATA / "deep_stats.json"))
mm = S["managed_money"]
H = ["fwd_1w", "fwd_2w", "fwd_4w"]
HL = {"fwd_1w": "1w", "fwd_2w": "2w", "fwd_4w": "4w"}


def r3(x):
    return round(x, 4) if isinstance(x, (int, float)) else x


def bucket(defkey):
    st = mm[defkey]["stats"]
    out = {}
    for bk in ["extreme_long", "extreme_short", "mid"]:
        out[bk] = {"n": st[bk]["n"]}
        for h in H:
            d = st[bk][h]
            out[bk][HL[h]] = {"median": r3(d["median"]), "mean": r3(d["mean"]),
                              "hit": r3(d["hit"]), "ci_lo": r3(d["ci95_lo"]),
                              "ci_hi": r3(d["ci95_hi"]), "p": d.get("p_vs_rest_med")}
    return out


rel = mm["relationship"]
bt = D["backtest"]

# --- backtest equity: keep full weekly curve but round hard to shrink bytes ---
def curve(name):
    return [round(v, 3) for v in bt[name]["equity"]]


bundle = {
    "meta": {
        "start": S["sample"]["start"], "end": S["sample"]["end"], "weeks": S["sample"]["weeks"],
        "mm_mean": round(S["sample"]["mm_net_mean"]), "mm_min": round(S["sample"]["mm_net_min"]),
        "mm_max": round(S["sample"]["mm_net_max"]),
        "note": S["data_source_note"],
    },
    "relationship": {
        "level_pearson": r3(rel["level_pearson"]),
        "chg_ret_mm": r3(rel["chg_vs_ret_pearson"]),
        "chg_ret_or": r3(S["other_reportables_compare"]["relationship"]["chg_vs_ret_pearson"]),
        "predictive": {sig: {HL[h]: {"r": r3(rel["predictive"][sig][h]["pearson"]),
                                     "p": r3(rel["predictive"][sig][h]["p_nw"])} for h in H}
                       for sig in ["z_roll52", "z_full"]},
    },
    "baseline": {HL[h]: {"median": r3(mm["baseline"][h]["median"]),
                         "mean": r3(mm["baseline"][h]["mean"]),
                         "hit": r3(mm["baseline"][h]["hit"])} for h in H},
    "decile_median": {str(k): {HL[h]: r3(v[h]) for h in H} for k, v in mm["decile_median"].items()},
    "extremes_decile": bucket("extremes_decile"),
    "extremes_rollz": bucket("extremes_rollz"),
    "event_study": {b: {"mean": [round(x, 3) for x in v["mean"]],
                        "se": [round(x, 3) for x in v["se"]], "n": v["n"]}
                    for b, v in S["event_study_decile"].items()},
    # ---------- deep-dive ----------
    "ccf": {"lags": D["cross_correlation"]["lags"],
            "corr": [r3(x) for x in D["cross_correlation"]["corr"]],
            "band": r3(D["cross_correlation"]["band"])},
    "granger": {"dpos_ret_p": r3(D["granger"]["dpos_to_ret"].get("min_p")),
                "dpos_ret_lag": D["granger"]["dpos_to_ret"].get("best_lag"),
                "ret_dpos_p": r3(D["granger"]["ret_to_dpos"].get("min_p")),
                "ret_dpos_lag": D["granger"]["ret_to_dpos"].get("best_lag")},
    "irf": {"cum": [r3(x) for x in D["var_irf"]["cum"]],
            "cum_lo": [r3(x) for x in D["var_irf"].get("cum_lo", [])],
            "cum_hi": [r3(x) for x in D["var_irf"].get("cum_hi", [])],
            "cum_total": r3(D["var_irf"]["cum_total"]), "order": D["var_irf"].get("lag_order")},
    "half_life": {"rho": r3(D["half_life"]["rho"]), "wks": round(D["half_life"]["half_life_wks"], 1),
                  "acf": [r3(x) for x in D["half_life"]["acf"]], "adf_p": r3(D["half_life"]["adf_p"])},
    "quantile": {"taus": [float(t) for t in D["quantile_reg_4w"]],
                 "slope": [r3(D["quantile_reg_4w"][t]["slope"]) for t in D["quantile_reg_4w"]],
                 "lo": [r3(D["quantile_reg_4w"][t]["lo"]) for t in D["quantile_reg_4w"]],
                 "hi": [r3(D["quantile_reg_4w"][t]["hi"]) for t in D["quantile_reg_4w"]]},
    "logit": {"beta": r3(D["logit_direction_4w"].get("beta")), "p": r3(D["logit_direction_4w"].get("p")),
              "auc": r3(D["logit_direction_4w"].get("auc")), "pseudo_r2": r3(D["logit_direction_4w"].get("pseudo_r2"))},
    "info_horizon": {"k": D["info_horizon"]["k"], "r": [r3(x) for x in D["info_horizon"]["r"]],
                     "p": [r3(x) for x in D["info_horizon"]["p"]]},
    "backtest": {
        "dates": bt["dates"],
        "buy_hold": [round(v, 3) for v in bt["buy_hold_equity"]],
        "long_only": curve("long_only"), "long_short": curve("long_short"),
        "perf": {
            "long_only": {"sharpe": r3(bt["long_only"]["perf_0bps"]["sharpe"]),
                          "ann": r3(bt["long_only"]["perf_0bps"]["ann_ret"]),
                          "dd": r3(bt["long_only"]["perf_0bps"]["max_dd"]),
                          "sharpe_5bps": r3(bt["long_only"]["perf_5bps"]["sharpe"]),
                          "exposure": r3(bt["long_only"]["exposure"]),
                          "boot_p": r3(bt["long_only"]["boot_sharpe"].get("p_le_0"))},
            "long_short": {"sharpe": r3(bt["long_short"]["perf_0bps"]["sharpe"]),
                           "ann": r3(bt["long_short"]["perf_0bps"]["ann_ret"]),
                           "dd": r3(bt["long_short"]["perf_0bps"]["max_dd"]),
                           "exposure": r3(bt["long_short"]["exposure"])},
            "buy_hold": {"sharpe": r3(bt["buy_hold_perf"]["sharpe"]),
                         "ann": r3(bt["buy_hold_perf"]["ann_ret"]),
                         "dd": r3(bt["buy_hold_perf"]["max_dd"])},
        },
    },
    "fdr": {"m": D["fdr"]["m"], "q": D["fdr"]["q"], "n_survivors": D["fdr"]["n_survivors"],
            "tests": [{"label": t["label"], "p": r3(t["p"]), "rank": t["rank"],
                       "thr": r3(t["bh_thr"]), "survives": t["survives"]} for t in D["fdr"]["tests"]]},
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(bundle, indent=None, separators=(",", ":")), encoding="utf-8")
print(f"wrote {OUT}  ({OUT.stat().st_size/1024:.1f} KB)")
