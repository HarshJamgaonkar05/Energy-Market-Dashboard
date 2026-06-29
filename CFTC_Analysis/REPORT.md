# Does CFTC Positioning Predict WTI Crude Prices?

**Managed-Money net positioning vs WTI spot, weekly, 2016–2026**
Analysis folder: `CFTC_Analysis/` (standalone — not wired into the dashboard)

---

## ⚠️ Data-source correction (read first)

The file supplied in `Data/CFTC 2016-2026 CL.xlsx` (instrument `CFTC-D_F_CL_OR_NET_1W`)
is labelled in the assignment as *Managed Money*, but it is actually the CFTC
**Other Reportables** net series. Verified by matching it one-for-one against the
official CFTC Disaggregated report:

| Report date | Supplied file `actual` | Official **Managed Money** net | Official **Other Reportables** net |
|---|---|---|---|
| 2026-06-16 | 28,255 | 96,228 | **28,255** ✓ |
| 2026-06-02 | 65,109 | 90,765 | **65,109** ✓ |
| 2026-05-26 | 81,074 | 79,924 | **81,074** ✓ |

`OR` in the instrument code = **O**ther **R**eportables (Managed Money would be coded `MM`).
Because the assignment asks about **Managed Money**, this study pulls the real
Managed-Money series directly from the **official CFTC Socrata API** (free, no key,
WTI contract `067651`) and treats it as primary. The supplied Other-Reportables
series is kept only as a contrast. WTI prices are EIA daily Cushing spot (`RWTC`).

This relabelling matters: the two categories behave **oppositely** (see §1).

---

## Method

- **Positioning:** CFTC Disaggregated Futures-only, Managed-Money net = long − short, WTI, weekly, 547 weeks (2016-01-05 → 2026-06-23).
- **Price:** EIA daily Cushing WTI spot.
- **Look-ahead control:** the COT report is *as-of Tuesday* but *published Friday ~15:30 ET*. Forward returns are therefore entered at the **Friday release** (`as-of + 3 days`), never the Tuesday as-of date.
- **Forward return:** `P(entry + 7·N days) / P(entry) − 1`, for N = 1, 2, 4 weeks, using the last daily close on/before each calendar target (NaN past the data end).
- **Extremes, two definitions:**
  1. **Full-sample decile** — top/bottom 10% of net position (descriptive; uses whole-sample ranking, so mild look-ahead).
  2. **Rolling-52-week z-score** — `|z| > 1.5` (point-in-time, **tradeable**, no look-ahead).
- **Robustness:** EIA spot printed −$36.98 on Mon 2020-04-20; Friday-to-Friday sampling steps over that single daily print, so no forward return is contaminated. **Medians** are reported alongside means throughout because forward-return distributions are skewed.
- Reproduce: `python 01_prepare_data.py && python 02_analysis.py`.

---

## 1. Relationship between Managed-Money positioning and price

| Measure | Managed Money | Other Reportables (supplied file) |
|---|---|---|
| Net **level** vs price level (Pearson) | −0.09 | −0.49 |
| **ΔPosition vs %ΔPrice, same week** (Pearson) | **+0.36** (p≈10⁻¹⁸) | **−0.29** (p≈10⁻¹²) |

**Key insight:** Managed Money is **coincident and momentum-driven** — it *buys as price rises* (+0.36). It is a *trend-follower*, not a leading indicator. (Other Reportables does the opposite — accumulates into weakness — which is exactly why mislabelling the two would invert the story.)

The positioning **level** barely tracks the price **level** (−0.09): crowding is regime-dependent, not a price gauge.

→ *Chart:* `charts/01_timeseries.png` — extreme longs (red) cluster at the 2018 and 2022 price *peaks*; extreme shorts (green) cluster at the 2016, 2019 and 2023–25 *troughs*.

## 2. Periods of extreme positioning

| Definition | Extreme long (n) | Extreme short (n) |
|---|---|---|
| Full-sample decile (≤10% / ≥90%) | 55 | 55 |
| Rolling-52w z > \|1.5\| | 54 | 73 |

Extreme **longs**: late-2017→2018, early-2022 (post-invasion spike).
Extreme **shorts**: early-2016, late-2018/2019, and a sustained washout through 2023–2026.

## 3. Forward performance after extremes

Median | mean forward return (%), Mann-Whitney p vs all other weeks:

**Full-sample decile extremes**

| Bucket | 1-week | 2-week | 4-week |
|---|---|---|---|
| Baseline (all weeks) | +0.47 \| +0.40 | +0.85 \| +0.82 | +0.84 \| +1.56 |
| **Extreme long** (crowded bulls) | +0.24 \| +0.44 | +1.80 \| +0.68 | +1.92 \| +1.05 (p=0.91) |
| **Extreme short** (washed-out bears) | +0.75 \| +1.63 | +1.29 \| +2.91 | **+2.55 \| +5.85 (p=0.05)** |

**Rolling-52w z > |1.5| (tradeable, no look-ahead)**

| Bucket | 1-week | 2-week | 4-week |
|---|---|---|---|
| Extreme long | +0.51 \| +1.25 | +0.11 \| +1.59 | +0.39 \| +1.96 (p=0.30) |
| Extreme short | +0.44 \| +0.23 | +0.70 \| +0.34 | +0.38 \| +0.95 (p=0.85) |

**Predictive correlations (signal → forward return)** — all weak and statistically insignificant:

| Signal | 1-week | 2-week | 4-week |
|---|---|---|---|
| Rolling-52w z | +0.04 (p=0.36) | +0.06 (p=0.14) | +0.07 (p=0.10) |
| Full-sample z | +0.01 (p=0.73) | +0.02 (p=0.68) | +0.02 (p=0.72) |

→ *Charts:* `02_scatter_predictive.png` (flat regression lines), `03_decile_returns.png` (non-monotonic), `04_extreme_buckets.png`, `05_return_distributions.png`.

---

## Findings & conclusion

1. **Managed Money is a coincident momentum indicator, not a leading one.** Positioning *changes* correlate +0.36 with same-week price changes; positioning *levels* have ~0 linear predictive power for 1–4-week forward returns (all |r| ≤ 0.07, p > 0.10).

2. **The only signal with any edge is contrarian, and only at the short extreme.** After Managed Money is washed out into its **bottom decile**, WTI's 4-week forward median is **+2.55% vs +0.84% baseline** (Mann-Whitney p≈0.05) — a mild capitulation-bounce. Crowded **longs** show **no** reliable subsequent reversal (p≈0.9).

3. **The edge is fragile.** It is borderline-significant, appears only in the **full-sample decile** definition (which peeks at the whole sample), and **largely vanishes** under the realistic point-in-time **rolling-z** definition. Overlapping forward windows also inflate apparent significance, so the true p-value is weaker than reported.

4. **The decile relationship is non-monotonic** — there is no clean "more long → worse returns" gradient.

**Bottom line:** CFTC Managed-Money positioning has **limited, mostly contrarian** predictive value for WTI. It is best used as a *coincident sentiment/crowding gauge* and as a *weak contrarian tilt after extreme net-short capitulation* — **not** as a standalone directional timing signal. Any tradeable version of the short-extreme effect is marginal and should be combined with other drivers (inventories, term structure) rather than used alone.

---

### Files
```
CFTC_Analysis/
  01_prepare_data.py     fetch CFTC (official MM+OR) + EIA price, build weekly table
  02_analysis.py         stats + charts + JSON summary
  REPORT.md              this report
  data/
    weekly_merged.csv    one row per week: positions, z-scores, fwd returns
    cftc_wti_official.csv  official CFTC MM & OR net (WTI 067651)
    wti_spot_daily.csv   EIA daily Cushing WTI spot
    stats_summary.json   all computed statistics
  charts/                01–05 PNGs
```
