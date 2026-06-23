# The Trading Strategy — explained simply, in depth

### What the strategy does and why, in plain words and worked examples

This is the full guide to the trading idea behind the three Phase-3 engines
(`analytics/historical_backtest.py`, `analytics/historical_intraday.py`, and the live
`Backtesting/engine.py`). It goes step by step with real numbers but keeps the language
simple. If you can picture a stretched rubber band snapping back, you can follow all of it.

**The whole journey in one line:** work out what a price gap *should* be → measure how
stretched it is *for the market regime we're in* → size the bet to the risk → fade it →
ride the snap-back through fair to an overshoot → and, when the market shocks, automatically
pull risk in.

The one thing that changed from the first version, and that everything below now rests on:
**the market-regime model is no longer a label on the side — it drives every decision.**

---

## 0. The absolute basics (assume you know nothing)

Skip this if you already trade; read it slowly if you don't. Five ideas and you're ready.

- **Oil isn't one price.** There are two benchmark crudes — **WTI** (American, code `CL`) and
  **Brent** (global, code `CO`/`LCO`) — and each is bought and sold not just for today but for
  delivery in specific *future months*. So there's a price for "WTI in July," another for "WTI
  in August," and so on. Each is a **futures contract**; one contract is **1,000 barrels**, so a
  $1.00 move is worth **$1,000**.
- **The forward curve** is those monthly prices in order. When near months cost *more* than far
  months it's **backwardation** (a sign oil is tight); when *less*, **contango** (a sign of
  glut).
- **A spread is the gap between two related prices** — and it's what we trade. Example: WTI July
  minus WTI August, maybe $0.74. We **buy one leg and sell the other at the same time**, so the
  big swings in the oil price cancel out and only the *gap* is left — far easier to predict than
  "will oil go up?" We own no outright oil, only the relationship. This is **relative-value**
  trading.
- **Three shapes of spread:** a **calendar** (same oil, two months — e.g. M1-M2 = nearest minus
  2nd-nearest), a **butterfly** (a three-month combination that isolates the middle month), and
  **Brent-WTI** (the gap between the two crudes).
- **Mean reversion is the engine.** Picture a spread as a **rubber band** resting at a
  comfortable length. A burst of buying/selling **stretches** it; it usually **snaps back**.
  *When a spread is unusually stretched, we bet it returns to normal.* That's the whole idea —
  everything else is doing it carefully.

---

## 1. The big idea (in one minute)

We trade **spreads** — the gap between two related oil prices (e.g. WTI for July delivery
minus WTI for August). We buy one leg and sell the other at the same time, so the big
up-and-down swings in the oil price cancel out. What's left is a small, well-behaved gap
that tends to **revert to normal** after it gets stretched. When the gap is unusually
stretched, we bet it returns to normal. That's the core.

Everything else is about doing that *carefully*, and "carefully" is where the **regime
model** comes in. The market is not always the same: sometimes it's calm, sometimes it's
violently volatile; sometimes inventories are tight, sometimes glutted. A stretch that means
"easy money" in a calm market can mean "stand well back" in a stormy one. The strategy reads
the regime first, then decides how far to let a gap stretch before trading it, how big to
bet, how long to hold, and when to get out of the way entirely.

We screen the WTI/Brent crude spreads in three shapes — **calendars** (same oil, two
months), **butterflies** (a three-month combination that isolates the middle month), and
**Brent-WTI** (the gap between the two crudes) — and trade only the ones with a *validated*
edge (see §8).

---

## 2. What is "fair value"? — and the key reversal from v1

To know whether a gap is stretched we need a reference: its **fair value** ("normal"
level). The first version of this strategy made a decision it then had to walk back, and
understanding that reversal is the cleanest way to understand the redesign.

**The old reasoning (v1):** "Phase 2 built a fundamentals model that prices each spread from
inventories, the dollar, the fear gauge and the season. But its *inputs* aren't in the
intraday feed, its level is stale, and it barely moves minute-to-minute — so we *can't* use
the regime model intraday. We'll just use a rolling average of the gap's own recent history."

**Why that was half-right and half-wrong.** It conflated **two different things** that Phase 2
delivers:

- a **fundamentals regression** (a daily price model), and
- a **regime model** (the market's *state* — inventory × volatility — plus each spread's
  measured reversion speed, its dispersion, and how regimes transition).

The regression genuinely *can't* run intraday. **The regime model can** — its state is a
daily label that applies to every intraday bar, and its measured reversion speed and
dispersion are *exactly* what an intraday mean-reversion book needs. So the redesign uses:

| Engine | Fair value |
|---|---|
| **Daily** | the Phase-2 **fundamentals regression**, walk-forward / out-of-sample |
| **Intraday & live** | a **regime-parameterized adaptive filter** — an EWMA whose memory length is set by the regime's *measured* reversion half-life (not a fixed window) |

In **both** cases the regime model then drives the thresholds, the holding time, the
**position size**, and the **shock response**. The regime model is no longer a confidence
label — it *is* the strategy.

---

## 3. Step one — work out "normal" the regime-aware way

**Daily.** Fair value is the Phase-2 fundamentals regression, refit walk-forward (it only
ever learns from the past), so a day's fair value never peeks at its own or future data.

**Intraday/live.** Fair value is an **adaptive EWMA** — a rolling average that weights recent
readings more, *and whose memory length is tied to how fast this spread actually reverts in
the current regime.* A fast-reverting regime gets a more responsive anchor; a slow one gets a
smoother anchor. Crucially the span is a *multiple* of the measured reversion half-life: if
the anchor moved as fast as the spread reverts, it would chase the gap and erase the very
dislocation we want to trade; too slow and it lags into session trends. We keep it in a tight,
validated band around the well-behaved level the blind baseline (§9) uses.

The reversion half-life itself is **measured, trailing** — estimated only from data before
each bar and refreshed periodically, never from the full sample.

---

## 4. Step two — measure "stretched", conditioned on the regime

We turn "how far from normal" into one number — the **z-score**, read as "how many normal
wiggles away from normal are we?" The twist versus v1: the "wiggle" (the dispersion we divide
by) is measured **within the same volatility state**, using an *expanding* window that only
sees the past.

Why this matters: a $0.10 stretch is a big deal in a calm regime and routine noise in a
stormy one. By measuring the wiggle per vol-state, a "+2" in calm markets and a "+2" in
stormy markets are genuinely comparable — the regime puts every reading on the right ruler.
A volatility *floor* stops a becalmed regime's tiny wiggle from manufacturing giant z-scores
out of cents.

- around 0 = sitting at normal
- **+2 or more** = unusually **rich** (gap too wide)
- **−2 or less** = unusually **cheap** (gap too narrow)

---

## 5. Step three — the regime sets the rules (entry, exit, hold)

This is the heart of "the regime drives the strategy." Per **vol-state** the engine looks up
its entire policy:

| Vol-state | Enter at | Exit (take profit) | Stop | Max hold | Daily size weight |
|---|---|---|---|---|---|
| **Low** | ±1.5σ | ride the overshoot | 3.0σ | longest (× half-life) | ×1.0 |
| **Normal** | ±2.0σ | overshoot / near fair | 3.5σ | medium (× half-life) | ×0.5 |
| **High** | ±2.5σ | take profit fast | 4.0σ | shortest (× half-life) | ×0.25 |

- **Higher bar in high vol.** In a stormy regime we demand a *deeper* stretch (2.5σ) before
  fading — the noise is bigger, so the signal must be too.
- **Max hold = a multiple of the regime's half-life.** Fast-reverting regimes get a short
  leash; slow ones a longer one. The hold is a backstop — most trades exit on the take-profit
  first.
- **A cost gate.** We only fade when the expected dollar move back to fair clears ~2× a
  realistic round-turn cost. A 2σ stretch on a calm, cheap gap can be worth a cent or two —
  a guaranteed loser after fees — so the gate skips it. It's volatility-adaptive: it waves
  through the worthwhile stretches and filters the cheap churn.

**The exit (take profit).** Stretched gaps usually **overshoot** — they sail through fair and
out the other side before settling — so we don't bail at fair; we ride the reversion through
to a modest overshoot and bank the whole arc. We also exit on a stop (it stretched further
against us), a time stop (it's gone nowhere), or a session/roll break (we never hold across a
close).

---

## 6. Step four — vol-target sizing (constant risk, not constant size)

v1 bet one fixed unit per trade. The redesign sizes each trade so it risks **roughly the same
number of dollars**, regardless of structure or regime:

> size ∝ (a typical dispersion) ÷ (this regime's dispersion)

So a high-volatility regime is **automatically sized down** (its moves are bigger, so fewer
units give the same dollar risk) and the book never levers a calm regime into a blow-up. The
size series is shipped to the dashboard so you can literally watch the book breathe with the
regime.

**Daily edge-concentration.** On the *daily* horizon the fundamental fair value is cleanest in
**low vol** (it makes most of its money there, with a high profit factor), marginal in normal
vol, and actually *negative* in high vol. So the daily book additionally weights size by edge
quality — Low ×1.0, Normal ×0.5, High ×0.25. Cutting the low-quality high-vol bets lifts the
daily Sharpe from **0.71 to 0.82** and **halves the max drawdown (−42% → −21%)** for the same
net P&L. (The intraday book keeps full per-state size — there the normal/high regimes *do*
carry edge.)

---

## 7. Step five — shock absorption (the safety system)

This is new in the redesign and is a primary point of the whole exercise: **how does the book
behave when the market shocks?** A **severity** score from 0 to 1 is built each bar from four
causal signals:

- a **vol jump** — current volatility vs its recent median;
- a **vol-regime step-up** — the state climbing Low → Normal → High (the real "regime shock");
- a **z-breach** — the dislocation blowing past the stop;
- an **intraday vol spike** — a short burst of volatility vs the baseline.

The graded response (the more severe, the more we pull back):

1. **De-lever** — new positions are scaled by `(1 − severity)`;
2. **Stand aside** — once severity crosses a threshold, take *no* new trades;
3. **Confirmation delay** — after the regime steps up, wait a few bars before trading into it;
4. **Flatten on a regime break** — when the vol regime jumps into High, cut open risk.

This is measured, not asserted — see §9 and the backtesting report's shock section.

---

## 7b. Two worked examples

**A full regime-driven trade, start to finish.** Suppose Brent-WTI normally rests near 0.74,
and the current regime is *Balanced · Normal-vol*.

1. **Measure normal.** The adaptive EWMA (memory set by the regime's measured half-life) puts
   fair value at 0.74. The same-vol-state wiggle is about 0.05.
2. **A stretch appears.** A burst of buying pushes the gap to 0.84 — that's 0.10 above fair, or
   `0.10 ÷ 0.05 = +2.0σ`. In *Normal* vol the entry bar is 2.0σ, so it qualifies. (In *High*
   vol we'd have required 2.5σ and skipped this.)
3. **Cost gate.** The expected move back to fair is 0.10 × $1,000 = $100 per unit — comfortably
   more than ~2× a realistic round-turn cost — so the trade clears.
4. **Size it.** Vol-target sizing sets the position so it risks the book's constant dollar
   budget; in Normal vol that's near the baseline unit (high vol would have sized it down).
5. **Enter** — *sell* the gap at 0.84, betting it falls back through 0.74 and beyond.
6. **It reverts and overshoots.** A few hours later the gap doesn't just touch 0.74 — it sails
   through to ~0.665 (a ~−1.5σ overshoot). That's the take-profit; we close and bank the whole
   arc (0.84 → 0.665 = 0.175 × $1,000 per unit), markedly more than ducking out at fair.

A losing trade differs only at the end: the gap pushes *up* to the stop (3.5σ in Normal) and we
take a small, pre-planned loss — or it stalls and the time stop closes it near break-even.

**A shock window, start to finish.** Now suppose volatility suddenly spikes and the regime
steps from Normal to **High** vol:

1. The **severity** score jumps (vol jump + regime step-up both fire), say to 0.7.
2. **De-lever:** any new position is scaled by `(1 − 0.7) = 0.3` — we bet small.
3. **Stand aside:** because severity is over the threshold, we actually take *no* new trades
   until it subsides.
4. **Flatten:** because the vol regime stepped into High, open risk is cut.
5. **Confirmation delay:** even once severity falls, we wait a few bars before trading into the
   freshly-changed regime.

The blind twin, by contrast, keeps fading at full size right through the spike — which is
exactly why its drawdown explodes under stress while the regime book's stays contained (§9).

---

## 8. Which structures we actually trade (the whitelist)

A structure is traded only where its edge is *validated* — data-driven, no hand-set flags:

- **Daily:** trade a structure only where the regression's out-of-sample R² ≥ 0.05 (so the
  fair value genuinely beats a naive mean). This drops the butterflies and a couple of
  calendars whose model has *negative* out-of-sample R².
- **Intraday/live:** a two-stage, out-of-sample gate on the first 60% of history. A positive
  **gross** edge means *the signal works* (kept in the 5-year backtest). A positive
  **after-cost** edge means it's *cheap enough to actually trade* (the **deployable** set the
  live book runs). The crude calendars/flies are gross-positive but their high-frequency churn
  doesn't clear costs — so the **live book deploys only the Brent-WTI arb**, the one structure
  with a robust after-cost edge.

That distinction (gross = "does the signal work", net = "is it worth trading") is why the live
panel is clean and positive rather than bleeding turnover on no-edge structures.

---

## 9. The honest control — regime-aware vs regime-blind

Every engine runs a **regime-blind twin** alongside the real book, on the **same fair value
and the same universe**, with the regime layer switched *off*: fixed 2σ entry, fixed one unit,
a single global dispersion, a fixed hold, no shock layer. The difference between the two arms
is therefore *exactly* what the regime model contributes. We read the result **risk-first**,
as the brief demands — gross P&L is the by-product, not the headline.

| | Daily (aware → blind) | Intraday (aware → blind) |
|---|---|---|
| Sharpe | **0.82 → 0.38** | 5.4 → 6.8 |
| Calmar | **0.69 → 0.28** | 27.9 → 73.3 |
| Max drawdown | **−21% → −61%** | −$10k → −$92k |
| Tail risk (CVaR 5%) | **−$5.7k → −$15.5k** | −$1.9k → −$5.0k |

On the **daily** horizon the naive baseline is mediocre, so the regime model *more than
doubles the Sharpe* and *cuts the drawdown by two-thirds*. On the **intraday** horizon the
naive baseline is already excellent (these spreads revert violently), so the regime model
can't add return — instead it slashes the tail (CVaR and max drawdown to a fraction) and
avoids the structurally-losing structures. The model adapts its contribution to where it's
needed.

**Shock windows.** Across 28 data-driven shock windows over five years, the regime-aware book
has a *shallower* drawdown in **100% of them** (average −$2.8k vs the blind −$26k). Under a
synthetic stress test (the shock windows amplified ×1.5/×2/×3 plus a gap jump) the blind
book's drawdown explodes (−$0.56M → −$0.91M → **−$1.95M**) while the regime book stays
contained (−$0.12M → −$0.12M → **−$0.09M**) — it de-levers and stands aside harder as the
shock grows. At ×3 it takes about **5%** of the blind book's drawdown. That is the safety
system working, not a label.

---

## 10. Position sizing & the dollar scale

The headline metrics above are **leverage-invariant** (Sharpe, Calmar, win-rate don't depend
on how big you bet). The dollar figures do. The intraday/live book runs at a **4× `bookScale`**
— it risks only ~0.2% of capital per trade at 1×, so 4× targets ~0.8%, still conservative for
a Sharpe-5+ book, and the drawdown stays ~1–2% of capital. That is *pure sizing*: it scales
the dollars and the dollar risk equally and leaves every ratio untouched. The **daily** book
stays at 1× — its −21% drawdown is already at a sensible limit. `bookScale` is a single number
in the config; dial it up or down for a bigger or smaller dollar book.

---

## 11. The results

**Intraday, 5.4 years of 15-minute data (the statistical backbone).** Four validated
structures, regime-driven, 4× book: **net ≈ $1.55M**, **Sharpe 5.44**, max drawdown ≈ **−1.6%**
of capital, profitable in **6/6 years**, t-statistic ≈ **12** (the edge is real, not luck).
The blind twin makes more gross but at far higher tail risk.

**Daily, 5.4 years (the regime model's clearest win).** **Sharpe 0.82** (vs blind 0.38),
**Calmar 0.69**, max drawdown **−21%** (vs blind −61%), net ≈ **$274k** — for ~15% less gross
than the riskier blind book.

**Live (the mentor's company feed, a few days).** Deploys only the Brent-WTI arb; a small,
honest **+$520** at 4×, and it **beats the blind twin** (−$880) over the same window. This is
a freshness check, not a verdict — the few-day window is too short to carry weight; the 5-year
backtests do.

---

## 12. Look-ahead discipline (why the numbers are trustworthy)

Every input a trade uses is available at the time of the trade:

- the daily fair value is walk-forward (refit on past data only); the intraday EWMA is
  one-sided; the blind EWMA is causal;
- the reversion half-life is fit on a *trailing* window strictly before each bar;
- the z dispersion is an *expanding same-vol-state* std using only prior residuals;
- the regime label uses same-day / backward-looking inputs only;
- shock-window dates are point-in-time (a vol jump vs its *trailing* median);
- roll/session segments are warmed up before any residual feeds the statistics, and no
  position is held across a roll or session break.

One disclosed in-sample choice: the daily *universe* (which structures to include) is chosen on
the full-sample out-of-sample R² — but it's applied identically to the aware and blind arms, so
it never biases the head-to-head.

---

## 13. How to run it

```
python analytics/run.py                  # rebuild the whole pipeline (Phase 2 + Phase 3)
python analytics/historical_backtest.py  # daily 5y (regime-driven + blind control)
python analytics/historical_intraday.py  # intraday 5y (regime-driven + blind control)
python analytics/shock_analysis.py       # shock windows + synthetic stress
python Backtesting/engine.py             # one live pass  (--live to loop, --slip to cost)
```

The engine's exact mechanics are in `Backtesting/IDEATION.md`; the whole-project overview is in
`docs/PROJECT_REPORT.md`; the deep backtesting write-up is in `docs/FINAL_BACKTESTING_REPORT.md`.

---

## 14. Mini-glossary

- **Spread / gap** — the price difference between two related contracts, traded as one bet.
- **Rich / cheap** — a gap unusually wide (rich) or narrow (cheap) versus normal.
- **Fair value** — the gap's "normal" level (daily: a fundamentals model; intraday: a
  regime-adaptive moving average).
- **Regime** — the market's state: inventory × volatility (Low / Normal / High vol).
- **z-score / stretch** — how many same-regime wiggles from normal we are right now.
- **Vol-target sizing** — betting size set so each trade risks ~constant dollars.
- **Shock severity** — a 0–1 score of how stressed the market is; drives de-levering.
- **Regime-blind control** — the same engine with the regime layer off; the comparison baseline.
- **Sharpe / Calmar** — risk-adjusted return measures (return per unit of volatility / per unit
  of drawdown).
- **Drawdown** — the worst peak-to-valley fall in the running total; the "pain" measure.
- **Gross vs net** — results before vs after trading costs.
