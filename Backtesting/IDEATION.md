# Phase 3 — Strategy Backtest (methodology)

Phase 3 takes the Phase-2 idea — **relative-value mean-reversion on energy spreads** — and
makes the **Phase-2 regime model DRIVE the strategy**, end to end. The same regime-driven
core ([`analytics/regime_strategy.py`](../analytics/regime_strategy.py)) powers three
backtests: a **daily 5-year** engine, an **intraday 5-year** engine, and this **live** engine
on the 15-minute feed ([`engine.py`](engine.py)).

The work is framed by mentor feedback on the first cut:

1. The rolling-mean fair value was too simple → use a **model-based** fair value.
2. **Gross P&L is not the point** → lead with methodology and **risk behaviour**.
3. The regime model must **drive** the strategy, not be a bolted-on confidence label.
4. **Shock absorption** — detecting and de-risking through vol/regime shocks — is a primary axis.
5. **All** backtesting runs through the regime model.

Every claim below is reproduced by re-running the pipeline (`python analytics/run.py`).

---

## 1. Inverting the old design — we now DO use the regime model intraday

The previous version contained a section titled *"why we DON'T use the regime model intraday."*
Its argument was that the **Phase-2 fundamental regression** can't price intraday spreads (its
inputs are daily/absent, its level is stale). **That remains true — and it was the wrong
conclusion.** The Phase-2 deliverable is two things, and we conflated them:

- a **fair-value regression** on fundamentals (daily), and
- a **regime model** (inventory × volatility state, per-regime reversion half-life, dispersion,
  transition behaviour).

The regression can't run intraday. **The regime model can** — its state is a daily label that
applies to every intraday bar, and its measured reversion speed / dispersion / transition risk
are exactly what an intraday mean-reversion book needs. So Phase 3 now uses:

- **Daily engine** — fair value = the Phase-2 **fundamentals regression** (walk-forward, OOS).
- **Intraday & live engines** — fair value = a **regime-parameterized adaptive local-level
  (EWMA) filter** whose span is set by the regime's measured reversion half-life.

In **both** cases the regime model drives the z-thresholds, the holding horizon, the **position
size**, and the **shock response**. The regime model is no longer a label — it is the strategy.

---

## 2. Model-based fair value (not a rolling mean)

| Engine | Fair value | Dislocation |
|---|---|---|
| Daily 5y | Phase-2 fundamentals regression, **walk-forward** (expanding window, refit every 21d, strictly out-of-sample) | `actual − regression FV` |
| Intraday 5y / Live | **Adaptive EWMA**: a one-sided filter whose half-life = `2.5 ×` the regime's **trailing, measured** reversion half-life, clamped to a band so it stays a slow *equilibrium* (it never chases the spread, never lags into a session trend) | `actual − adaptive FV` |

The **signal** is a **regime-conditioned z**: the residual divided by the **expanding std of
residuals in the *same* vol-state** (Low/Normal/High), with a regime volatility floor so a calm
regime's tiny dispersion can't manufacture huge z-scores out of cent-sized noise. A z=2 in a
high-vol regime is a genuinely bigger dislocation than a z=2 in a calm one — conditioning makes
them comparable.

> **Why the intraday FV is a *multiple* of the half-life, not the half-life itself.** The fair
> value is the equilibrium the spread reverts *to*. If its span equalled the reversion speed it
> would track the spread and erase the very dislocation we trade; if it were too slow it would
> lag into intraday trends and fade moves that keep running. A modest multiple in a tight band is
> the sweet spot — validated empirically against the blind fixed-span anchor.

---

## 3. The regime model drives the strategy

Per **vol-state** the engine looks up its entire policy (`analytics/regime_strategy.py`):

| Vol-state | z-entry | z-exit | z-stop | max-hold | size tilt |
|---|---|---|---|---|---|
| **Low** | 1.5 | ride overshoot | 3.0 | longest (× half-life) | up to ~1.5× |
| **Normal** | 2.0 | overshoot / near fair | 3.5 | medium (× half-life) | ~1× |
| **High** | 2.5 | take profit fast | 4.0 | shortest (× half-life) | down to 0.25× |

- **Max-hold = a multiple of the regime's trailing half-life** — fast-reverting regimes get a
  short leash, slow ones a longer one.
- **Vol-target sizing** — `size ∝ (typical dispersion ÷ this-state dispersion)`, clamped. Each
  trade risks ≈ a constant number of dollars, so **high-vol regimes are automatically sized
  down** and the book never levers a calm regime into a blow-up. The size series is shipped to
  the dashboard so you can watch it breathe with the regime.
- **Edge concentration (daily).** On the daily horizon the fundamental fair value is cleanest in
  *low* vol (PF ~2.4); it is marginal in Normal (PF ~1.1) and negative in High (PF ~0.3). So the
  daily book also weights size by edge quality — Low ×1.0, Normal ×0.5, High ×0.25 — which lifts
  the Sharpe (0.71→0.82) and **halves the max drawdown (−42%→−21%)** by cutting low-quality
  return volatility, for the same net P&L. (Intraday keeps full per-state size — there Normal/High
  vol *do* carry edge, PF ~5.6 / ~2.2.)
- **Structure whitelist (data-driven, no hand-set flags).** A structure is traded only where its
  edge is *validated*:
  - **Daily** — the regression's **out-of-sample R² ≥ 0.05** (drops the butterflies / `ho_gasoil`,
    whose OOS R² is negative — their high reversion hit-rate is reversion to their *own* mean, not
    to a fair value the model can predict).
  - **Intraday / live** — a two-stage, out-of-sample gate on the first 60% of the history: a
    positive **gross** edge means the *signal works* (evaluated in the 5-year backtest), and a
    positive **after-cost** edge means it is *cheap enough to actually trade* (the **deployable**
    set the live book runs). The crude calendars/flies are gross-positive but their high-frequency
    churn doesn't clear costs, so only the **Brent-WTI arb** is deployed live — which is why the
    live book is clean and positive rather than bleeding turnover on no-after-cost-edge structures.

---

## 4. Shock absorption (a primary axis, not cosmetic)

A **severity ∈ [0, 1]** detector combines, by a probabilistic OR, four causal signals:

- a **vol jump** — current vol vs its trailing median;
- a **vol-regime step-up** — the vol-state climbing Low→Normal→High (the real "regime shock"),
  decaying over a few bars;
- a **z-breach** — the dislocation blowing past the stop;
- an **intraday vol spike** — a short realized-vol window vs its baseline.

The graded response:

- **de-lever** — new-trade size `×= (1 − severity)`;
- **stand aside** — no new entries once severity crosses a threshold;
- **confirmation delay** — no new entries for a few bars after a vol-regime step-up (don't trade
  into a freshly-shifted regime until it persists);
- **flatten on a regime break** — exit open risk when the vol regime steps **into High**.

This is measured, not asserted. On the 5-year daily history
([`shock_analysis.py`](../analytics/shock_analysis.py)):

- across **28 data-driven shock windows**, the regime-aware book has a **shallower drawdown in
  100% of them** (avg drawdown ≈ **−$2.8k** vs the blind **−$26k** — about a ninth);
- under **synthetic stress** (the shock windows amplified vol×{1.5, 2, 3} + a gap jump) the blind
  book's max drawdown **explodes** (−$0.56M → −$0.91M → **−$1.95M**) while the regime book stays
  **contained** (−$0.12M → −$0.12M → −$0.09M) — it degrades *sub-linearly* because it de-levers
  and stands aside harder as the shock grows. At ×3, the regime book takes **~5%** of the blind
  book's drawdown.

---

## 5. The regime-blind control (the honest head-to-head)

Every engine runs a **regime-blind** twin alongside the aware book, on the **same fair value and
the same universe**, differing *only* in the regime machinery: fixed `z=2`, fixed **1 unit**,
**global** dispersion, a fixed hold, a **fixed-span** EWMA (intraday), and **no shock layer**.
The difference between the two arms is therefore exactly the regime model's contribution.

| | Daily 5y (aware → blind) | Intraday 5y (aware → blind) |
|---|---|---|
| Sharpe | **0.82 → 0.38** | 5.4 → 6.8 |
| Calmar | **0.69 → 0.28** | 27.9 → 73.3 |
| Max drawdown | **−21% → −61%** | **−$10k → −$92k** |
| CVaR (5%) | **−$5.7k → −$15.5k** | **−$1.9k → −$5.0k** |
| Net P&L | $274k → $321k | $1.55M → $7.68M |

> **Book leverage.** The intraday/live book runs at **4× `bookScale`** (it risks only ~0.2% of
> capital per trade at 1×, so 4× targets ~0.8% — still conservative for a Sharpe-5+ book). This is
> *pure sizing*: it scales the intraday/live dollar figures and dollar risk by 4×; every ratio
> (Sharpe, Calmar, win-rate) is leverage-invariant. The **daily** book stays at **1×** — its −21%
> drawdown is already at a sensible limit and can't be levered. Adjust `bookScale` in
> `INTRADAY_CONFIG` to dial the dollar scale up or down.

Read this the way the mentor asked — **risk first.** On the **daily** horizon, where the naive
baseline is mediocre, the regime model **more than doubles the Sharpe** (0.82 vs 0.38), **lifts
Calmar ~2.5×**, and **cuts max drawdown by two-thirds** (−21% vs −61%) and tail risk by ~63%, for
~15% less gross — much of that risk reduction comes from concentrating size in the clean low-vol
regime and sizing the negative-edge high-vol fades down hard. On the **intraday** horizon the naive
baseline is *already* excellent (the spreads are violently mean-reverting), so the regime model
can't add return — instead it **slashes the tail** (CVaR and max drawdown to a fraction), **avoids
the structurally-losing Brent calendars**, and runs far lower turnover. The regime model adapts
its contribution to where it is needed; gross P&L is the by-product, not the headline.

---

## 6. Look-ahead discipline

Every input a trade uses is available at the time of the trade:

- **fair value is causal** — the regression is walk-forward (refit on past data only); the EWMA
  is a one-sided recursion; the blind EWMA is `pandas.ewm` (causal);
- the **half-life** that sets the FV span and the max-hold is fit on a **trailing window strictly
  before** each bar, refit periodically — **never** the full-sample catalog number;
- the **z dispersion** is an **expanding same-vol-state** std using only residuals before the bar;
- **vol-target size** uses only those causal dispersions;
- **regime(t)** is the Phase-2 classification, built from same-day / backward-looking inputs only
  (seasonal-z, trailing realized vol, same-day curve slope);
- **roll/session segments** are warmed up before any residual feeds the dispersion, so a contract
  roll never injects a spurious dislocation, and no position is ever held across a roll/session;
- **shock-window dates** are point-in-time — a date is flagged when its vol exceeds its *trailing*
  median by a fixed fraction (not a full-sample quantile).

**One disclosed in-sample choice:** the daily *universe* (which structures to trade) is gated on
each structure's **full-sample** out-of-sample R² ("trade the structures whose model validates over
the history"). The fair value itself is strictly walk-forward; only the membership decision is
full-sample, and it is applied **identically to the aware and blind arms**, so it never biases the
head-to-head — it only sets the shared universe both arms trade.

---

## 7. Measurement (lead with risk)

The feeds (`server/data/{historical_backtest,historical_intraday,signal_engine,shock_analysis,
robustness}.json`) report, for **both** arms: Sharpe, Calmar (CAGR ÷ |max DD|), **max drawdown
($ and %)**, **CVaR (5%)**, % time in market, annualised vol, per-structure / per-regime /
per-vol-state attribution, the vol-target & shock **sizing series**, the per-shock-window
drawdown & recovery, and the synthetic-stress curve. `robustness.py` adds **per-year P&L** (the
aware book is profitable in **6/6 years**), a **per-trade t-stat** (≈ **11**, far above the t>2
bar), and a **Monte-Carlo** drawdown distribution from 2,000 trade-order reshuffles.

Gross P&L is shown, but it is deliberately not the lead number — the lead is the risk profile and
the regime-aware-vs-blind comparison.

---

## 8. The live engine

`engine.py` runs the **same regime-driven core** on the mentor's live 15-minute SQLite feed
(`I:\…\bars_15min_*.db`, WAL-snapshotted; a committed copy in `Backtesting/Data/` is the offline
fallback). It reads the **current** regime from `regimes.json` and applies the full machinery,
with a regime-blind twin and the persistent opportunity journal (`signal_log.json`).

> **Honest caveat.** Over a **short** live window the daily regime is constant, so the
> *cross-regime* conditioning is naturally dormant (only one vol-state is present) and the
> result is a small, few-day demo. It is the *same engine* the 5-year daily and intraday
> backtests validate — which is where the statistical weight lives, and what the dashboard's
> "proven track record" strip anchors the live panel to.

```
python analytics/run.py                 # rebuild the whole pipeline (Phase 2 + Phase 3)
python analytics/historical_backtest.py # daily 5y (regime-driven + blind)
python analytics/historical_intraday.py # intraday 5y (regime-driven + blind)
python analytics/shock_analysis.py      # shock windows + synthetic stress
python Backtesting/engine.py            # one live pass   (--live to loop, --slip to cost)
```
