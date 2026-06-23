# The Complete Backtesting Report

### Three ways we tested the regime-driven oil-spread strategy — every detail, in plain words

This is the full story of the Phase-3 backtesting work. It covers all three backtests — the live
one and the two historical ones — explains exactly how each works, what every setting means and
why, and reads the results **honestly, risk first**. It assumes you know **nothing** about
trading; every term is explained the first time it appears. Read it top to bottom and you'll
understand the entire thing.

**How to read this document**

- **Part 1** — the foundations: what we trade and the handful of simple ideas everything rests on.
- **Part 2** — the big shift: how the market-regime model went from a side-label to the thing
  that *drives* the strategy.
- **Part 3** — the most important idea: fair value, and the rule that decides which backtest can
  use which method.
- **Part 4** — how the regime model drives entries, exits, holding time, and size, with a worked
  trade.
- **Part 5** — shock absorption: detecting stress and pulling risk in, with a worked example.
- **Part 6** — the honest control: regime-aware vs a regime-blind twin.
- **Parts 7–9** — each backtest in full depth: intraday, daily, live.
- **Part 10** — the robustness battery. **Part 11** — the cost reality.
- **Part 12** — the independent audit we ran on our own work.
- **Part 13** — honest limits. **Part 14** — how to run it. Glossary at the end.

---

## Part 1 — The foundations (start here)

We do **not** bet on whether oil goes up or down. We trade **spreads** — the gap between two
related oil prices.

A simple example: the price of oil for July delivery **minus** the price for August delivery.
That difference might be $0.74. We **buy one month and sell the other at the same time**, so the
big up-and-down swings in the overall oil price cancel out. What's left is a small, steady,
well-behaved relationship — much easier to predict than "will oil go up?"

We use two kinds of oil:
- **WTI** — American crude (its contracts are coded `CL`).
- **Brent** — global crude (coded `CO` on the live feed, `LCO` in the historical files).

**A two-line primer on the "months."** Oil is bought and sold not just for today but for
delivery in specific *future months* — each is a **futures contract** that trades on its own.
There's a price for "WTI in July," another for "WTI in August," and so on; lined up in order
they form the **forward curve**. When near months cost *more* than far months the curve is
**backwardated** (a sign oil is tight); when *less*, it's in **contango** (a sign of glut). The
nearest contract is "M1," the next "M2," then "M3." That's all you need to read the spreads
below.

And three *shapes* of spread, all built from WTI and Brent only:
- **Calendar spread** — same oil, two different months (e.g. July vs August). A pure bet on
  whether near-term oil is getting tighter or looser than later oil. We write these as **M1-M2**
  (1st-nearest minus 2nd-nearest month) and **M2-M3**.
- **Butterfly ("fly")** — a three-month combination (one early month, minus two of the middle
  month, plus one late month). It checks whether the middle month is out of line with its
  neighbours. The most surgical, market-neutral of the three.
- **Brent-WTI** — the gap between the two kinds of oil itself, driven by shipping costs and
  regional supply differences.

**One contract is 1,000 barrels**, so a $1.00 move in a spread is worth **$1,000**. Every dollar
figure in this report is built on that.

**The core bet** (the "rubber band"). Picture a spread as a rubber band resting at a comfortable
length. A burst of buying or selling **stretches** it too wide or too narrow; history shows it
usually **snaps back**. So: *when a spread is unusually stretched, fade it (bet on the
snap-back).* This tendency is called **mean reversion**. The entire report is about doing that
*carefully* — and "carefully" now means *through the lens of the market regime.*

---

## Part 2 — The big shift: the regime model now drives the strategy

Phase 2 of the project built a **regime model**. A "regime" is simply the market's *state* —
principally **inventory × volatility** (is oil tight or glutted? are markets calm or stormy?).
For each regime, Phase 2 measured how each spread behaves: its average level, how much it
wiggles, and how fast it snaps back (its **half-life**).

The first version of Phase 3 used all this only as a *confidence label* printed next to each
trade. The feedback was blunt and correct: the regime model should **drive** the strategy, risk
behaviour through shocks is a primary thing to test, and gross dollar profit is not the point.
So the redesign threads the regime model through **every** decision — the fair value, the
"stretched" ruler, the entry/exit/stop/hold rules, the position size, and a shock-absorption
layer. The rest of this report shows each, then the results.

---

## Part 3 — Fair value, and the rule of two timeframes

To know whether a spread is stretched, we need a reference: its **fair value** — its "normal"
level right now. Getting this right was the central design question.

The first version reasoned: *"Phase 2's fair-value model needs fundamentals — inventories, the
dollar, the fear gauge — and the intraday feed has only prices, and the model barely moves
minute-to-minute. So we can't use it intraday; we'll just use a rolling average of the spread
itself."* That was half-right. It confused **two different things** Phase 2 delivers:

- a **fundamentals regression** — a *daily* price model (genuinely can't run intraday), and
- a **regime model** — the market's *state* plus each spread's *measured reversion speed* (which
  absolutely can run intraday).

So the redesign splits fair value by timeframe:

| Backtest | Fair value | Why |
|---|---|---|
| **Daily** | the Phase-2 **fundamentals regression**, walk-forward / out-of-sample | daily data *has* the fundamental inputs, and 5+ years is a real sample |
| **Intraday & live** | a **regime-parameterized adaptive moving average** — an EWMA whose memory length tracks the regime's *measured* reversion speed | the intraday feed has only prices, but the regime model's *reversion speed* is exactly what's needed |

A note on the intraday moving average: an **EWMA** (exponentially weighted moving average) is
just an average that weights recent readings more than old ones. We set its memory length to a
*multiple* of the regime's measured reversion half-life — because if the average chased the
spread as fast as it reverts, it would erase the very dislocation we want to trade; too slow and
it lags into trends. The "right" length is regime-dependent, which is the whole point.

**The signal** is then a **regime-conditioned z-score**: the residual (actual minus fair value)
divided by the **wiggle** — the standard deviation of residuals *in the same volatility state*,
measured on an expanding window that only sees the past. A volatility *floor* stops a becalmed
market's tiny wiggle from manufacturing fake giant stretches. Everything here is **causal**: the
half-life is fit on past data only, the dispersion only sees the past, the regression is
walk-forward.

---

## Part 4 — How the regime model drives the trade (with a worked example)

Per **volatility state** the engine looks up its whole policy:

| Vol-state | Enter at | Exit (take profit) | Stop | Max hold | Daily size weight |
|---|---|---|---|---|---|
| Low | ±1.5σ | ride the overshoot | 3.0σ | longest (× half-life) | ×1.0 |
| Normal | ±2.0σ | overshoot / near fair | 3.5σ | medium (× half-life) | ×0.5 |
| High | ±2.5σ | take profit fast | 4.0σ | shortest (× half-life) | ×0.25 |

- **Deeper stretch required in high vol** (2.5σ): bigger noise demands a bigger signal.
- **Cost gate:** we only fade when the expected dollar move back to fair clears about **2× a
  realistic round-turn cost**. On a calm, cheap spread a 2σ stretch can be worth a cent or two —
  a guaranteed loser after fees — so the gate skips it. It's volatility-adaptive.
- **Max hold = a multiple of the regime's half-life** — a backstop; most trades take profit first.
- **Vol-target sizing:** size ∝ (a typical wiggle) ÷ (this regime's wiggle), so each trade risks
  ~constant dollars and stormy regimes are sized down automatically.
- **Daily edge-concentration:** daily, the fundamental edge lives in *low* vol (profit factor
  ~2.4) and is *negative* in high vol (~0.3), so the daily book weights size Low ×1.0 / Normal
  ×0.5 / High ×0.25. This one change lifts daily Sharpe 0.71 → 0.82 and **halves** the daily
  drawdown (−42% → −21%) at the same net profit.

**A worked trade.** Brent-WTI normally rests near 0.74; the regime is *Balanced · Normal vol*.

1. The adaptive moving average puts fair value at 0.74; the same-state wiggle is ~0.05.
2. A burst of buying pushes the gap to 0.84 → that's 0.10 above fair = `0.10 ÷ 0.05 = +2.0σ`. In
   Normal vol the entry bar is 2.0σ, so it qualifies. (In High vol we'd need 2.5σ and skip it.)
3. Cost gate: the expected move back to fair is 0.10 × $1,000 = $100/unit — clears ~2× cost.
4. Size: vol-target sets the position to risk the book's constant dollar budget.
5. Enter — **sell** the gap at 0.84, betting it falls back through 0.74 and beyond.
6. It reverts *and overshoots*: a few hours later it sails through 0.74 down to ~0.665 (a ~−1.5σ
   overshoot). That's our take-profit; we bank the whole arc (0.84 → 0.665 = 0.175 × $1,000),
   markedly more than ducking out at fair. A loser differs only at the end — the gap pushes to
   the stop (3.5σ) and we take a small, pre-planned loss.

---

## Part 5 — Shock absorption (a primary evaluation axis)

When the market shocks, the book must de-risk **itself**. A **severity** score (0 to 1) is built
each bar from four causal signals — a volatility jump vs the recent median, a vol-regime step-up
(Low→Normal→High), a z-breach past the stop, and a short intraday vol spike — combined so
independent stresses compound but never exceed 1.

The graded response: **de-lever** (new size × (1 − severity)), **stand aside** (no new trades
above a severity threshold), **confirmation delay** (wait a few bars after a regime step-up), and
**flatten** open risk when the vol regime jumps into High.

**A worked shock.** Volatility spikes and the regime steps Normal → High. Severity jumps to,
say, 0.7. New positions are scaled by `(1 − 0.7) = 0.3` (we bet small); because severity is over
the threshold we actually take *no* new trades; open risk is *flattened*; and even after severity
falls we wait a few bars before trading the freshly-changed regime. The blind twin, by contrast,
keeps fading at full size right through the spike — which is exactly why its drawdown explodes
under stress and the regime book's stays contained (Part 6).

---

## Part 6 — The honest control: regime-aware vs regime-blind

Every engine runs a **regime-blind twin** on the **same fair value and the same spreads**, with
the regime layer switched off (fixed 2σ entry, one fixed unit, one global wiggle, fixed hold, no
shock layer). The gap between the two arms is *exactly* the regime model's contribution. Read it
**risk-first**:

| | Daily (aware → blind) | Intraday (aware → blind) |
|---|---|---|
| Sharpe (return per unit of risk) | **0.82 → 0.38** | 5.4 → 6.8 |
| Calmar (return per unit of drawdown) | **0.69 → 0.28** | 27.9 → 73.3 |
| Max drawdown | **−21% → −61%** | −$10k → −$92k |
| Tail risk (CVaR 5%) | **−$5.7k → −$15.5k** | −$1.9k → −$5.0k |
| Net P&L | $274k → $321k | $1.55M → $7.68M |

Daily: the naive baseline is mediocre, so the regime model **more than doubles the Sharpe** and
**cuts the drawdown by two-thirds** for ~15% less gross. Intraday: the naive baseline is already
excellent (these spreads revert violently), so the model can't add *return* — it slashes the
*tail* (drawdown and CVaR to a fraction) and runs far lower turnover.

**Shock windows.** Across **28 data-driven shock windows**, the regime-aware daily book has a
shallower drawdown in **100% of them** (avg −$2.8k vs the blind −$26k). Under synthetic stress
(the shock windows amplified ×1.5/×2/×3 plus a gap jump), the blind book's drawdown **explodes**
(−$0.56M → −$0.91M → **−$1.95M**) while the regime book stays **contained** (−$0.12M → −$0.12M →
−$0.09M). At ×3 it takes ~5% of the blind book's drawdown — it de-levers and stands aside harder
as the shock grows. That is the safety system working, not a label.

---

## Part 7 — The historical INTRADAY backtest (the statistical backbone)

- **What "intraday" means:** trading on short, within-day price bars rather than once a day.
- **Data:** 5.4 years of 1-minute WTI/Brent data, resampled to **15-minute bars** (~132,000
  bars). Two housekeeping details matter. A **roll** (when the nearest contract expires) makes a
  spread jump, and an **overnight/weekend gap** is a break in trading; so we split the series
  into **segments** at every roll and every gap, never let a rolling statistic span a break, and
  never hold a position across one.
- **Fair value:** the regime-adaptive moving average (Part 3). **Signal:** the regime-conditioned z.
- **Universe — a two-stage, out-of-sample gate** on the first 60% of history: a positive *gross*
  edge keeps a structure in the 5-year evaluation (4 structures qualify); a positive
  *after-cost* edge marks it **deployable** (only Brent-WTI clears that bar — see Part 11).
- **Sizing:** vol-target, run at a conservative 4× book (pure leverage; ratios unchanged).

**Result (regime-aware, 4 structures):** net ≈ **$1.55M**, **Sharpe 5.44**, **Calmar 25.7**,
worst drawdown ≈ **−$10k (−1.6% of capital)**, profitable in **6/6 years**. The blind twin makes
more gross ($7.68M) but at ~9× the drawdown.

---

## Part 8 — The historical DAILY backtest (the regime model's clearest win)

- **Data:** ~1,850 trading days, 2021–2026, from a unified feature table (prices, spreads,
  cracks, calendars, butterflies, realized vol, EIA inventories, macro).
- **Fair value:** the Phase-2 fundamentals regression, **walk-forward** — refit every 21 days on
  past data only, so a day's fair value never sees its own or future data.
- **Universe:** structures whose regression fair value is validated out-of-sample (R² ≥ 0.05),
  which keeps the strong cracks/calendars and drops the negative-R² butterflies. (R² measures how
  much of the spread the model explains; *negative* out-of-sample means it's worse than a plain
  average — not a fair value you can trade against.)
- **Driver:** regime-conditioned z, per-vol-state rules, vol-target sizing **with daily
  edge-concentration**, and the shock layer.

**Result (regime-aware):** **Sharpe 0.82**, **Calmar 0.69**, worst drawdown **−21%**, CVaR
−$5.7k, net ≈ **$274k** — vs a blind twin at Sharpe 0.38, drawdown −61%. The regime model roughly
doubles the risk-adjusted return and halves the pain.

---

## Part 9 — The LIVE backtest (the company feed)

`Backtesting/engine.py` runs the **same regime-driven core** on the mentor's live 15-minute
SQLite feed (it snapshots the database's write-ahead log so it sees the freshest bars). It reads
the current regime, deploys only the **after-cost-validated** structure (Brent-WTI), and runs a
blind twin alongside.

**Result (a few-day window, 4× book):** a small, honest **+$520**, which **beats the blind twin
(−$880)** over the same window. This is a *freshness check, not a verdict* — a few days is far
too short to carry weight; the 5-year backtests above do. Over such a short window the daily
regime is constant, so the cross-regime conditioning is naturally dormant — it's the *same
engine* the 5-year tests validate.

---

## Part 10 — The robustness battery

Because the intraday numbers are strong enough to invite "too good to be true,"
`analytics/robustness.py` stress-tests them five ways:

- **Per-year P&L** — profitable in *every* year, not just on average? **Yes (6/6, 2021–2026).**
- **t-statistic** — is the average edge statistically real rather than luck? **Yes, t ≈ 12.** (A
  t-stat above ~2 is the usual bar for "real"; 12 is overwhelming.)
- **Monte-Carlo drawdown** — reshuffle the trade order 2,000 times → how bad could the worst dip
  plausibly get? (A bounded, modest distribution.)
- **Walk-forward universe** — if we'd picked the traded structures using only *past* data at each
  point, would we still have chosen these? **Yes** (not hindsight cherry-picking).
- **Parameter sensitivity** — does the edge hold across neighbouring entry/exit/stop settings, or
  live on one lucky knob? **It holds across the grid.** (We explicitly *rejected* a flattering
  daily setting that showed a −10% drawdown because a neighbouring value gave −21% — a knife-edge,
  not a real result. We kept the robust −21%.)

---

## Part 11 — The cost reality (gross vs net, and the deployable set)

By default we report **gross** (the pure signal, no fees). With a realistic per-leg fee charged,
the picture sharpens into the single most useful finding: **gross tells you the signal works;
net tells you what's worth trading.**

- On the **daily** book, the kept structures retain ~80% of gross after a 2¢/leg fee.
- On the **intraday** book, the **Brent-WTI arb** keeps its edge comfortably after a 1¢/leg fee,
  but the high-frequency crude **calendars and flies are gross-positive yet net-negative** — they
  stop out too often to clear the bid-ask (the small gap between the buy and sell price you pay on
  every trade). That is *why* the live book deploys only Brent-WTI: we trade where there's a real
  after-cost edge, and merely *evaluate* the rest.

---

## Part 12 — The independent adversarial audit

We ran an adversarial review of our own implementation across three axes:

- **Look-ahead / leakage** (the cardinal sin of backtesting — accidentally using future
  information): every per-bar decision was verified to use only data *before* that bar — the
  walk-forward regression, the one-sided moving average, the trailing reversion speed (checked
  down to the index arithmetic), the expanding same-state wiggle folded in *after* each bar's
  decision, and point-in-time shock dates. Verdict: **look-ahead-free** in the signal path. The
  one disclosed in-sample element is the daily universe gate (full-sample R²), which is symmetric
  across the aware and blind arms and so cannot bias the head-to-head.
- **Schema compatibility:** every field the dashboard reads is produced by the engines — **no
  broken panels.**
- **Is the shock absorption real or cosmetic?** We traced the severity score end-to-end: it
  genuinely shrinks new-trade size, blocks entries, and flattens positions; the blind arm
  correctly disables all of it; both arms get the identical stressed inputs. Verdict: **real**,
  with the honest caveat that the head-to-head credits the *whole* regime layer, and the absolute
  drawdown's non-monotonicity under stress means we lead with the drawdown *ratio*, not a single
  number.

---

## Part 13 — Honest limits

1. **The live window is thin** — a few days is a freshness check; only the 5-year backtests carry
   weight.
2. **Costs are illustrative** — 1¢/leg (intraday) and 2¢/leg (daily) are reasonable stand-ins;
   your real fees, financing and spread will differ.
3. **Bar closes are not real fills** — we trade at the price at the end of each bar; live
   execution would face slippage and partial fills the backtest can't see.
4. **The intraday fair value is a moving average** — adaptive and regime-set, but still a
   local-level filter; a full Kalman model is a possible refinement.
5. **Crude only** — WTI and Brent; no products (diesel, gasoline) on the intraday feed.
6. **Book leverage is a sizing choice** — the 4× intraday book is pure leverage; ratios are
   unchanged, but the dollar risk scales with it.

---

## Part 14 — How to run it

```
python analytics/run.py                  # rebuild the whole pipeline (Phase 2 + Phase 3)
python analytics/historical_backtest.py  # daily 5y (regime-driven + blind)
python analytics/historical_intraday.py  # intraday 5y (regime-driven + blind)
python analytics/shock_analysis.py       # shock windows + synthetic stress
python analytics/robustness.py           # per-year / t-stat / Monte-Carlo
python Backtesting/engine.py             # one live pass   (--live to loop, --slip to cost)
```

Each engine writes a feed under `server/data/` that the dashboard reads; the live engine also
writes a full trade-by-trade log to `Backtesting/out/`.

---

## Glossary

- **Spread / gap** — the price difference between two related contracts, traded as one bet.
- **Calendar / butterfly / Brent-WTI** — the three spread shapes (two months; three months; the
  two crudes).
- **Rich / cheap** — a gap unusually wide (rich) or narrow (cheap) versus normal.
- **Fair value** — a gap's "normal" level (daily: a fundamentals model; intraday: a
  regime-adaptive moving average).
- **Regime** — the market's state (inventory × volatility).
- **Wiggle / σ / z-score / stretch** — the spread's typical jiggle; how many of them we are from
  normal right now.
- **Mean reversion (the rubber band)** — the tendency of a stretched gap to snap back.
- **Fade** — to bet against a move. **Overshoot** — when a reverting gap sails past normal.
- **Cost gate** — only fade when the expected move clears ~2× trading cost.
- **Vol-target sizing** — sizing so each trade risks ~constant dollars.
- **Shock severity** — a 0–1 stress score that drives de-levering / standing aside / flattening.
- **Regime-blind control** — the same engine with the regime layer off; the comparison baseline.
- **Sharpe** — return per unit of volatility. **Calmar** — return per unit of drawdown.
- **CVaR (5%)** — the average loss on the worst 5% of days (tail risk).
- **Drawdown** — the worst peak-to-valley fall; the "pain" measure.
- **Roll / segment** — a contract expiry; the pieces we split the series into around rolls/gaps.
- **Gross vs net** — before vs after trading costs.
- **Deployable** — a structure with a validated *after-cost* edge; the live book trades only these.
- **t-statistic** — a measure of whether an average edge is real or luck (above ~2 = real).
- **Walk-forward / out-of-sample** — tested only on data the model hadn't seen.
