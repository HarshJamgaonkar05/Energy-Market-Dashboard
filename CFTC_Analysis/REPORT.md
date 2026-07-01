# Does CFTC Positioning Predict WTI Crude Prices?

**Managed-Money net positioning vs WTI spot, weekly, 2016–2026**
Analysis folder: `CFTC_Analysis/` (standalone — not wired into the dashboard)
**Slide deck:** [`../public/cftc/presentation.html`](../public/cftc/presentation.html) (self-contained, dark dashboard theme; served in-app at `/cftc/presentation.html`)

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
  - **Deep-dive (§4):** cross-correlation lead/lag, **Granger causality** (both directions), **VAR + orthogonalized impulse response**, mean-reversion **half-life**, **quantile** & **logistic** regression, a **walk-forward out-of-sample backtest** with block-bootstrap Sharpe inference, and **Benjamini-Hochberg** multiple-testing correction.
- Reproduce: `python 01_prepare_data.py && python 02_analysis.py && python 04_deep_analysis.py && python 05_export_dashboard.py && python 03_build_deck.py`.

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

## 4. Mathematical deep-dive (`04_deep_analysis.py`)

The first pass measured *whether* a relationship exists. This pass interrogates its
**direction, dynamics, and tradeability** with proper time-series econometrics. Every
result below points the same way, and hardens the verdict.

### 4A · Direction — cross-correlation & Granger causality

**Cross-correlation** of Δposition against WTI return at leads/lags −8…+8 weeks
(Bartlett band ±1.96/√N = **±0.08**):

| Lag k | meaning | corr |
|---|---|---|
| k = 0 | same week | **+0.36** (only bar far outside the band) |
| k > 0 | position change *leads* return | max \|r\| = **0.08** (none clears the band) |
| k < 0 | return *leads* position change | max \|r\| = 0.09 |

The entire cross-correlation mass sits at **k = 0**. Formalised by **Granger causality**
(F-test, lags 1–4): Δposition → return **min p = 0.22**, return → Δposition **min p = 0.84**.
**Neither direction Granger-causes the other** — the +0.36 is contemporaneous comovement,
not lead/lag. → `charts/07_ccf.png`.

**VAR(3) orthogonalized impulse response** (Cholesky order position→price): a +1σ
Managed-Money position shock coincides with a **+2.7% same-week** WTI move that does *not*
build further (weeks 1–8 ≈ 0; cumulative +3.9%, 95% band [+2.6, +5.2]). The response is
entirely front-loaded — a picture of a **coincident**, not anticipatory, series. → `charts/08_irf.png`.

### 4B · Dynamics — how long crowding lasts

AR(1) on MM net: **ρ = 0.97**, Ornstein-Uhlenbeck **half-life ≈ 20 weeks** (ADF p = 0.016,
stationary). Positioning extremes **decay slowly (~5 months)** — crowding is a persistent
*state*, which is exactly why it works as a regime/context gauge but gives no crisp entry
timing. → `charts/09_halflife.png`.

### 4C · Tradeability — does any edge survive honest testing?

- **Quantile regression** (4-week return on the rolling-z, τ = 0.1…0.9): slopes are tiny
  and flip sign across the distribution (−1.0 to +0.7 %/σ), all CIs straddle 0 — positioning
  doesn't reliably move even the **tails**. → `charts/10_quantile.png`.
- **Logistic direction model** P(fwd_4w > 0) ~ z: β = −0.03 (p = 0.70), pseudo-R² ≈ 0,
  **AUC = 0.51** — indistinguishable from a coin flip.
- **Information horizon:** strongest \|corr\| of z with forward returns is at 3 weeks and only
  **r = +0.08 (p = 0.09)** — no horizon carries real predictive content.
- **Walk-forward out-of-sample backtest** of the one candidate edge (contrarian long when the
  point-in-time rolling-z ≤ −1; fixed a-priori threshold; weekly non-overlapping returns):

  | Strategy | Sharpe | Ann. return | Max DD | In-market | Boot p(Sharpe≤0) |
  |---|---|---|---|---|---|
  | Contrarian **long-only** | **0.18** | +1.5% | −52% | 28% | **0.29** |
  | Long-short (z≤−1 / z≥+1) | −0.19 | −9.4% | −89% | 44% | — |
  | **Buy & hold WTI** | **0.35** | +6.0% | −78% | 100% | — |

  The contrarian rule **underperforms buy-and-hold** on a risk-adjusted basis and its Sharpe
  is statistically indistinguishable from zero (circular block-bootstrap p = 0.29). Net of
  5 bps costs it is essentially unchanged (0.17) — costs aren't the problem, *there is no
  edge to erode.* → `charts/11_oos_equity.png`.

### 4D · Multiple testing — the capstone

The lone "significant" result in §3 (extreme-short decile, 4-week, p ≈ 0.05) was **one of 12**
extreme-bucket tests (2 definitions × 2 tails × 3 horizons). Under **Benjamini-Hochberg FDR
(q = 0.10)**, **0 of 12 survive** — the smallest p (0.050) needs to clear 0.008 at its rank
and doesn't. The apparent edge is fully consistent with **look-where-you-looked** noise.
→ `charts/12_fdr.png`.

### Deep-dive verdict

Every additional test agrees with the first pass and removes the last ambiguity:
Managed-Money positioning is a **contemporaneous, slow-moving crowding/sentiment state** with
**no lead/lag causal content, no distributional edge, no directional skill, and no
out-of-sample or multiple-testing-robust trading edge.** Use it as *context* (a regime
input alongside inventories & term structure) — **never as a standalone timing signal.**

---

### Files
```
CFTC_Analysis/
  01_prepare_data.py   official CFTC (MM+OR) + EIA price -> weekly table
  02_analysis.py       refined stats (HAC, bootstrap, hit-rate, event study) + dark charts
  04_deep_analysis.py  econometric deep-dive (CCF, Granger, VAR/IRF, half-life,
                       quantile & logit regression, OOS backtest, BH-FDR) + charts 07..12
  05_export_dashboard.py  distil stats_summary.json + deep_stats.json -> src/data/cftcStudy.json
  03_build_deck.py     assemble the deck → ../public/cftc/presentation.html (base64-embedded charts)
  REPORT.md            this report
  (deck output)        ../public/cftc/presentation.html — 8-slide deck, served in-app at /cftc/
  data/                weekly_merged.csv, cftc_wti_official.csv, wti_spot_daily.csv,
                       stats_summary.json, deep_stats.json
  charts/              01_timeseries .. 12_fdr (dark dashboard theme)
```

Reproduce end-to-end:
`python 01_prepare_data.py && python 02_analysis.py && python 04_deep_analysis.py && python 05_export_dashboard.py && python 03_build_deck.py`
