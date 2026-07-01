# Does CFTC Positioning Predict WTI Crude Prices?

**Managed-Money net positioning vs WTI spot, weekly, 2016–2026**
Analysis folder: `CFTC_Analysis/` (standalone — not wired into the dashboard)
**Slide deck:** [`presentation.html`](presentation.html) (self-contained, dark dashboard theme)

---

## ⚠️ Data-source note (read first)

The file supplied in `Data/CFTC 2016-2026 CL.xlsx` (instrument `CFTC-D_F_CL_OR_NET_1W`)
is labelled in the assignment as *Managed Money*, but it is actually the CFTC
**Other Reportables** net series — verified value-for-value against the official CFTC
report (e.g. 2026-06-16: file = 28,255 = Other Reportables; Managed-Money net was 96,228).
`OR` in the code = **O**ther **R**eportables (Managed Money would be `MM`).

Because the assignment asks about **Managed Money**, this study pulls the real
Managed-Money series from the **official CFTC API** (WTI contract `067651`) as primary,
and keeps Other Reportables only as a contrast. Prices are EIA daily Cushing spot (`RWTC`).
The two categories trade **oppositely** (§1), so the label matters.

---

## Method

- **Positioning:** CFTC Disaggregated Futures-only, Managed-Money net = long − short, WTI, weekly, **547 weeks (2016-01-05 → 2026-06-23)**.
- **Price:** EIA daily Cushing WTI spot.
- **No look-ahead:** the COT report is *as-of Tuesday* but *published Friday*. Forward returns are entered at the **Friday release** (`as-of + 3d`).
- **Forward return:** `P(entry + 7·N days) / P(entry) − 1`, N = 1, 2, 4 weeks (NaN past data end). The lone −$36.98 spot print of 2020-04-20 is stepped over by Friday-to-Friday sampling.
- **Extremes:** (1) full-sample **decile** (top/bottom 10%; mild look-ahead) and (2) point-in-time **rolling-52w z-score**, `|z|>1.5` (tradeable).
- **Inference (refined):**
  - **Newey-West (HAC)** p-values on the predictive slope — honest under the autocorrelation that overlapping forward windows create.
  - **Hit-rate** (% positive) per bucket; **circular block-bootstrap** 95% CIs on bucket mean returns; **Mann-Whitney** medians vs the rest; **event-study** cumulative path (weeks 0–6).
- Reproduce: `python 01_prepare_data.py && python 02_analysis.py && python 03_build_deck.py`.

---

## 1. Relationship between positioning and price

| Measure | Managed Money | Other Reportables (supplied file) |
|---|---|---|
| Net **level** vs price level (Pearson) | −0.09 | −0.49 |
| **ΔPosition vs %ΔPrice, same week** | **+0.36** (p≈10⁻¹⁸) | **−0.29** (p≈10⁻¹²) |

Managed Money is **coincident and momentum-driven** — it *buys as price rises* (+0.36); a trend-follower, not a leading indicator. The **level** barely tracks price (−0.09): crowding is regime-dependent. (Other Reportables does the opposite — accumulating into weakness — which is why mislabelling the two inverts the story.)
→ `charts/01_timeseries.png`: extreme longs cluster at the 2018 & 2022 peaks, extreme shorts at the 2016 / 2019 / 2023–25 troughs.

## 2. Periods of extreme positioning

| Definition | Extreme long (n) | Extreme short (n) |
|---|---|---|
| Full-sample decile | 55 | 55 |
| Rolling-52w z > \|1.5\| | 54 | 73 |

## 3. Forward performance after extremes

**Predictive slope — Pearson r [Newey-West HAC p]** (all insignificant):

| Signal | 1-week | 2-week | 4-week |
|---|---|---|---|
| Rolling-52w z | +0.04 [0.34] | +0.06 [0.29] | +0.07 [0.39] |
| Full-sample z | +0.01 [0.68] | +0.02 [0.71] | +0.02 [0.81] |

**Extreme buckets** — median % | mean % | hit-rate | 95% boot-CI(mean) | Mann-Whitney p:

| Bucket (def) | horizon | median | mean | hit | 95% CI (mean) | p |
|---|---|---|---|---|---|---|
| Baseline (all) | 4-week | +0.84 | +1.56 | 54% | — | — |
| **Extreme short** (decile) | 4-week | **+2.55** | +5.85 | **60%** | **[+0.7, +11.9]** | **0.05** |
| Extreme long (decile) | 4-week | +1.92 | +1.05 | 62% | [−1.5, +3.5] | 0.91 |
| Extreme short (rolling-z) | 4-week | +0.38 | +0.95 | 53% | [−2.8, +4.7] | 0.85 |

→ `charts/`: `02_scatter_predictive` (flat fits + HAC p), `03_decile_returns` (non-monotonic), `04_extreme_buckets` (decile vs rolling-z), `05_event_study` (cumulative path), `06_hitrate`.

---

## Findings & conclusion

1. **Coincident momentum indicator, not leading.** Position *changes* track same-week price (+0.36); position *levels* have **no** linear predictive power — every Newey-West HAC p ≥ 0.29.
2. **The only edge is contrarian, at the short extreme.** After Managed Money is washed out (bottom decile), WTI's 4-week median is **+2.55% vs +0.84% baseline**, 60% win-rate, and the bootstrap CI of the *mean* excludes zero (p≈0.05). Crowded **longs** show **no** reliable reversal (p≈0.9).
3. **Fragile.** It is borderline, rests partly on big 2016/2020 rebounds (mean ≫ median), and **largely vanishes** under the point-in-time rolling-z definition (CI spans 0). Overlapping windows still flatter it.
4. **Non-monotonic** decile relationship — no clean "more long → worse" gradient.

**Bottom line:** CFTC Managed-Money positioning is a useful **coincident crowding/sentiment gauge** and a **weak contrarian tilt after extreme net-short capitulation** — **not** a standalone directional timing signal. Combine with inventories and term structure rather than trading it alone.

---

### Files
```
CFTC_Analysis/
  01_prepare_data.py   official CFTC (MM+OR) + EIA price -> weekly table
  02_analysis.py       refined stats (HAC, bootstrap, hit-rate, event study) + dark charts
  03_build_deck.py     assemble presentation.html (base64-embedded charts)
  REPORT.md            this report
  presentation.html    5-slide deck (open in any browser; ← → to navigate)
  data/                weekly_merged.csv, cftc_wti_official.csv, wti_spot_daily.csv, stats_summary.json
  charts/              01_timeseries .. 06_hitrate (dark dashboard theme)
```
