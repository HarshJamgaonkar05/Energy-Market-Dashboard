# The Voltaire Energy Terminal

### A complete, plain-English guide to what this project is, why it exists, and exactly how it works

Written so that someone who has never heard the words "futures," "spread," or "backwardation"
can finish this document and understand the entire project. The focus is the **financial
markets** — what the numbers mean and why a trader cares — not the software.

**How to read this document.** It is built in layers. We start with the absolute basics of the
oil market — assuming you know *nothing* — and only once those are solid do we explain what the
project actually does with them. If you already know what a "calendar spread" is, skim Part II;
if you don't, Part II is where everything later starts to make sense. Take Part II slowly.

- **Part I** — Why oil is traded at all, and who trades it.
- **Part II** — The building blocks: futures, the forward curve, spreads, volatility,
  inventories, mean reversion. (The vocabulary. Read this slowly.)
- **Part III** — What the project is, in one picture.
- **Part IV** — Phase 1: the live market dashboard.
- **Part V** — Phase 2: reading the market's "regime" and finding mispriced spreads.
- **Part VI** — Phase 3: the regime-driven trading strategy and how we tested it.
- **Part VII** — How to read the results honestly.
- **Glossary** — every term, in one line.

---

## Part I — The oil market, from zero

Crude oil is the raw material that gets refined into the fuels the world runs on: petrol
(gasoline) for cars, diesel for trucks, jet fuel for planes, heating oil for homes. Because
almost every economy depends on it, the price of oil is one of the most-watched numbers in
finance.

**But there is no single "price of oil."** Two things complicate it, and the whole project
lives in that complication:

1. **Oil comes in different grades from different places.** When people say "the oil price"
   they almost always mean one of two benchmark grades:
   - **Brent** — oil from the North Sea (off the UK/Norway). The benchmark for most of the world
     (Europe, Africa, the Middle East). It trades on an exchange called **ICE**. In our data it
     carries the code `CO` (and `LCO` in the historical files).
   - **WTI (West Texas Intermediate)** — oil produced in the United States. The benchmark for
     the Americas. It trades on the **CME/NYMEX**. In our data it carries the code `CL`.

   The two are similar but not identical, and the gap between their prices — the **Brent-WTI
   spread** — is itself one of the most-traded relationships in the market.

2. **Oil isn't bought only for today.** It is bought and sold for delivery *months and years
   into the future*. There is a price for oil delivered next month, a (usually different) price
   for the month after, and so on. Understanding this second point deeply is the key to
   everything, so Part II spends real time on it.

**Who trades it, and why?** Two broad groups. **Hedgers** — airlines, refiners, producers — use
the market to *lock in* prices and reduce risk (an airline buying future jet fuel so a price
spike won't bankrupt it). **Speculators** — funds, trading desks — take the other side, trying
to profit from price moves. This project is a speculator's tool, but a careful, risk-first one.

---

## Part II — The building blocks (read this slowly)

### II.1 Futures contracts

A **futures contract** is an agreement to buy or sell a set amount of oil at a price agreed
*today*, for delivery in a specific *future month*. So there isn't one oil price — there's a
price for "WTI delivered in July," another for "WTI delivered in August," and so on, stretching
out for years. Each is its own contract that trades independently.

One contract is **1,000 barrels**. So if a price moves by $1.00 per barrel, that contract's
value moves by $1,000. Keep that number in mind — every dollar figure later is built on it.

Contracts are named by their delivery month using letter codes (e.g. `CL_N26` = WTI, July 2026;
`CO_Q26` = Brent, August 2026). The **nearest** contract to deliver is "M1," the next is "M2,"
then "M3," and so on. As time passes, M1 expires and M2 becomes the new M1 — this is called the
**roll**, and we'll see it matters for the intraday data.

### II.2 The forward curve

Line up those monthly prices in order — July, August, September, … — and you get the **forward
curve**: a picture of what the market thinks oil is worth at each future date. The *shape* of
that curve tells a story:

- **Backwardation** — near months are *more expensive* than far months (the curve slopes down).
  This usually signals **tightness**: buyers want oil *now* and will pay up for it.
- **Contango** — near months are *cheaper* than far months (the curve slopes up). This usually
  signals **glut**: there's plenty of oil around, and storing it for later costs money.

Intuition: if you're desperate for oil today, you'll pay a premium for immediate delivery
(backwardation). If oil is piling up in tanks, nobody pays extra for "now," and the far months
(which include storage costs) trade higher (contango). Our sample period (2021–2026) was mostly
backwardated — a useful fact later.

### II.3 Spreads — the single most important idea

Here is the heart of the whole project. Instead of betting on whether oil goes **up or down**
(which is notoriously hard), we trade the **gap between two related prices** — a **spread**.

A simple example: the price of WTI for July delivery **minus** the price for August delivery.
That difference might be $0.74. We **buy one month and sell the other at the same time.** Because
we're long one and short the other, the big up-and-down swings in the overall oil price
**cancel out**. What's left is a small, steady, well-behaved relationship — far easier to
predict than "will oil go up?"

We use three *shapes* of spread, all built from WTI and Brent only:

- **Calendar spread** — the same oil, two different months (e.g. July vs August WTI). Written
  M1-M2 (nearest minus 2nd-nearest) or M2-M3. A pure bet on whether near-term oil is getting
  tighter or looser than later oil.
- **Butterfly ("fly")** — a three-month combination: buy one early month, sell two of the
  middle month, buy one late month (e.g. +M1 −2×M2 +M3). It checks whether the *middle* month
  is out of line with its neighbours. The most surgical, market-neutral of the three.
- **Brent-WTI** — the gap between the two *kinds* of oil itself, driven by shipping costs and
  regional supply differences.

In every case we own **no outright oil** — only the *gap*. That's why this is called
**relative-value** trading.

### II.4 Volatility — calm seas vs storms

**Volatility** is how violently prices jump around. A calm market barely moves; a stormy one
lurches. This matters enormously for our strategy, because *the same $0.10 move means different
things in different weather*: it's a big, meaningful stretch in a calm market, and routine noise
in a stormy one. A strategy that ignores volatility will mistake noise for signal exactly when
it's most dangerous. Reading the volatility "weather" is a core part of this project's edge.

### II.5 Inventories — how much oil is in the tank

Governments and agencies track how much crude is sitting in storage. In the US, the **EIA**
(Energy Information Administration) publishes inventory levels **weekly**. What matters isn't the
raw number but how it compares to the **seasonal norm** (oil stocks naturally rise and fall with
the seasons). Stocks far *below* the seasonal norm = tightness (bullish for near-term prices);
far *above* = glut. Inventories are one of the main fundamental forces that move spreads, and
Phase 2 feeds them into its fair-value model.

### II.6 Mean reversion — the rubber band

The last idea, and the engine of the whole strategy. Picture a spread as a **rubber band** at
rest at a comfortable length. Now and then a burst of buying or selling **stretches** it — too
wide or too narrow. History shows it usually **snaps back** toward normal. That tendency to
return is called **mean reversion**.

So the entire trading idea, in one sentence: **when a spread is unusually stretched, bet that it
returns to normal.** Everything else — and there is a lot of "everything else" — is about doing
that *carefully*: measuring "stretched" honestly, sizing the bet sensibly, and getting out of
the way when the market turns dangerous.

---

## Part III — The project in one picture

The Voltaire Terminal is built in three phases that stack on top of each other:

1. **Phase 1 — the dashboard.** A live web terminal that pulls free/open market data (prices,
   the forward curve, inventories, weather, news) and shows the state of the oil market in real
   time.
2. **Phase 2 — the regime model.** An offline analytics layer that reads the market's *state*
   (its "regime") each day, builds a statistical fair-value model for each spread, and ranks
   which spreads look mispriced right now.
3. **Phase 3 — the strategy.** A relative-value mean-reversion trading strategy that is
   **driven by the Phase-2 regime model**, tested three ways (daily over five years, intraday
   over five years, and live on the company feed).

The thread that ties Phases 2 and 3 together — and the heart of the redesign — is that the
regime model doesn't just *describe* the market; it **drives the trading.**

---

## Part IV — Phase 1: the live dashboard

A React + Node web app that aggregates free data sources — Yahoo Finance for prices, the EIA for
fundamentals, Open-Meteo for weather, Financial Juice for news — into a set of panels: live
prices and biggest movers, the forward curves, crack spreads (the gap between refined products
and crude), inventories, a one-line market "narrative," and — wired in by Phases 2 and 3 — the
regime view, the live signal engine, and the backtest reports.

The design keeps the backend **thin**: all the heavy statistics are precomputed *offline*
(Phases 2 and 3) into static JSON files, which the server simply reads and serves. The live app
never runs Python in the request path, so it stays fast and the analytics can be as heavy as
they need to be.

---

## Part V — Phase 2: reading the regime, finding mispriced spreads

Phase 2 turns the raw data into three things the strategy uses. (It runs as an offline Python
batch that writes JSON into `server/data/`.)

**1. The regime — the market's "mood."** Every trading day is classified by its *state*. Five
dimensions are recorded — inventory, term structure (the curve shape), volatility, price trend,
and season — but the headline segmentation is **Inventory × Volatility**, the two dimensions
that actually *vary* across 2021–2026 (the curve was backwardated ~95% of the time, so it's kept
as context rather than a splitting axis). That gives nine regimes (e.g. "Balanced · High Vol").
For each regime we measure how every spread behaves there — its average level, how much it
wiggles, and how fast it snaps back (its **half-life**) — plus how regimes transition into one
another. This is the "weather report" the strategy reads before every trade.

**2. The fair-value model — a spread's "normal," from real-world causes.** For each spread we
fit a **regression**: a statistical formula that predicts the spread from fundamentals —
inventory levels, the US dollar, the market's "fear gauge," recent momentum, the season.
Crucially, the displayed fair value is produced **walk-forward / out-of-sample**: each day's
prediction is made using *only data from before that day*, so the model is never secretly graded
on data it already saw. (This honesty is non-negotiable — a model tested on its own answers
always looks brilliant and means nothing.) This setup also tells us *which* spreads the model
can genuinely price — strong out-of-sample accuracy for the product cracks, but *negative* for
some butterflies, which the strategy then refuses to trade.

**3. The signals — what looks mispriced now.** Combining the regime view and the fair-value
model, Phase 2 ranks which spreads are dislocated *right now*, each with a plain-English
rationale, a confidence score, and the spread's historical snap-back rate.

---

## Part VI — Phase 3: the regime-driven strategy

Phase 3 takes the simple, robust idea from Part II.6 — *fade a stretched spread, bet it reverts*
— and makes the Phase-2 regime model drive every part of it. (The blow-by-blow lives in
`docs/STRATEGY.md` and `docs/FINAL_BACKTESTING_REPORT.md`; here is the essence, still from zero.)

### VI.1 Fair value, two timeframes

To know if a spread is stretched, we need its **fair value** ("normal" level). The first version
of the strategy made — and then had to undo — one key mistake, and understanding it is the
cleanest way in.

**The v1 mistake:** "Phase 2's fair-value model needs fundamentals (inventories, the dollar…),
but the *intraday* feed has only prices, and the model barely moves minute-to-minute — so we
*can't* use the regime model intraday. We'll just use a plain rolling average of the spread."

That confused **two different things** Phase 2 delivers: a **fundamentals regression** (a daily
price model) and a **regime model** (the market's state + each spread's measured reversion
speed). The regression genuinely can't run intraday — but the **regime model can**, and its
measured reversion speed is *exactly* what an intraday mean-reversion book needs. So:

| Timeframe | Fair value |
|---|---|
| **Daily** | the Phase-2 fundamentals regression, walk-forward (out-of-sample) |
| **Intraday & live** | a **regime-parameterized moving average** — its memory length is set by the regime's *measured* reversion speed, not a fixed window |

### VI.2 Measuring "stretched" — the z-score, regime-aware

We turn "how far from normal" into one number: the **z-score**, read as *"how many normal
wiggles away from normal are we?"* A "wiggle" is the spread's typical jiggle. The twist: we
measure that wiggle **within the current volatility state** (Part II.4). So a "+2" in calm
markets and a "+2" in stormy markets mean the same thing — the regime puts every reading on the
right ruler. Around 0 = normal; **+2 or more = rich** (too wide); **−2 or less = cheap** (too
narrow).

### VI.3 The regime sets the rules

Per volatility state, the engine looks up its whole playbook: **how stretched** a spread must be
before we fade it (deeper in stormy markets — 1.5σ in calm, 2.0σ normal, 2.5σ in high vol),
**when to take profit** (we ride the snap-back *through* normal to a small overshoot, because
stretched spreads usually overshoot before settling), **when to cut** (a stop), **how long to
hold** (a multiple of the regime's half-life), and **how big to bet.**

### VI.4 Sizing — constant risk, not constant size

Rather than one fixed unit per trade, the strategy uses **vol-target sizing**: it sets the
position so each trade risks roughly the *same number of dollars*. A stormy regime is
automatically sized **down** (its moves are bigger, so fewer contracts give the same dollar
risk), so the book never levers a calm regime into a blow-up. On the daily book it goes further
and concentrates size where the fundamental edge is cleanest (low vol), which lifts the daily
Sharpe and halves the drawdown.

### VI.5 Shock absorption — the safety system

This is a primary point of the redesign: *how does the book behave when the market shocks?* A
**severity** score (0 to 1) is built each bar from volatility jumps, regime step-ups, and
stop-breaches. The more severe, the more the book pulls back: it **de-levers** (bets smaller),
**stands aside** (stops taking new trades), waits for **confirmation** after a regime change,
and **flattens** open risk when volatility jumps into a high state. The naive baseline does none
of this — which is exactly why it bleeds in shocks and the regime book doesn't.

### VI.6 The honest control — regime-aware vs regime-blind

Every test runs a **regime-blind twin** alongside the real strategy: the *same* fair value and
the *same* spreads, but with the regime layer switched off (fixed threshold, one fixed unit, one
global ruler, no shock layer). The difference between the two is *exactly* what the regime model
contributes — and we read it **risk-first**, not by the biggest dollar number.

### VI.7 The three backtests

- **Intraday, 5.4 years of 15-minute data (the statistical backbone):** net ≈ **$1.55M**,
  **Sharpe 5.44**, worst drawdown ≈ 1.6% of capital, profitable in **all six years**,
  t-statistic ≈ **12** (the edge is real, not luck).
- **Daily, 5.4 years (the regime model's clearest win):** **Sharpe 0.82** vs a blind 0.38, worst
  drawdown **−21%** vs the blind's −61% — roughly double the risk-adjusted return at a third of
  the pain, for ~15% less gross profit.
- **Live (the company feed, a few days):** a small, honest **+$520** that *beats* its blind twin
  (−$880); a freshness check, not a verdict.

**Shock results.** Across 28 data-driven shock windows the regime book has a *shallower*
drawdown in **100%** of them; under a ×3 synthetic stress the blind book's worst drawdown blows
out to **−$1.95M** while the regime book stays near **−$0.09M**. That is the safety system
working.

---

## Part VII — How to read the results honestly

- **Lead with risk, not gross P&L.** The headline isn't the biggest dollar number — it's the
  Sharpe (return per unit of risk), the drawdown (worst peak-to-valley fall), the tail risk, and
  how the book behaves through shocks. A regime-*blind* book can post a bigger gross number while
  carrying far more risk — which is the whole reason we show the two side by side.
- **Gross says "does the signal work"; net says "is it worth trading."** After realistic costs,
  only some structures keep their edge — which is why the live book deploys only the one with a
  genuine after-cost edge (Brent-WTI) and merely *evaluates* the rest.
- **The live window is thin** — a few days is a freshness check, not a verdict. The two 5-year
  backtests carry the statistical weight.
- **Everything is look-ahead-free** in the signal path — the fair value, the wiggle, the
  reversion speed, and the shock dates are all computed using only past data (independently
  audited).
- **The dollar scale is a sizing choice.** The intraday/live book runs at a conservative 4×
  leverage; that scales the dollars and the dollar risk equally and leaves every ratio (Sharpe,
  Calmar, win-rate) untouched.

---

## Glossary

- **Crude / WTI / Brent** — oil; the US (`CL`) and global (`CO`) benchmark grades.
- **Futures contract** — an agreement to buy/sell oil at a set price for a future delivery
  month; one contract = 1,000 barrels.
- **Forward curve** — the prices for each future delivery month, plotted in order.
- **Backwardation / contango** — near months pricier (tight) / cheaper (glut) than far months.
- **Spread** — the gap between two related prices, traded as one bet (we own only the gap).
- **Calendar / butterfly / Brent-WTI** — the three spread shapes we trade.
- **Roll** — when the nearest contract expires and the next becomes the new nearest.
- **Volatility** — how violently prices move (the market's "weather").
- **Inventories** — oil in storage vs the seasonal norm; a key fundamental force.
- **Regime** — the market's state, here Inventory × Volatility.
- **Fair value** — a spread's "normal" level (daily: a fundamentals model; intraday: a
  regime-adaptive moving average).
- **z-score / stretch** — how unusual the current level is, in same-regime wiggles.
- **Rich / cheap** — a spread unusually wide (rich) or narrow (cheap) vs normal.
- **Mean reversion** — the tendency of a stretched spread to snap back to normal (the rubber band).
- **Fade** — to bet against a move (sell what jumped up, buy what dropped).
- **Vol-target sizing** — betting so each trade risks ~constant dollars.
- **Shock absorption** — automatically pulling risk in when the market gets stressed.
- **Regime-blind control** — the same strategy with the regime layer off; the comparison baseline.
- **Sharpe** — return per unit of volatility (higher = better risk-adjusted return).
- **Calmar** — return per unit of drawdown.
- **Drawdown** — the worst drop from a high point to a later low; the "pain" measure.
- **CVaR (5%)** — the average loss on the worst 5% of days (tail risk).
- **Gross vs net** — results before vs after trading costs.
- **Walk-forward / out-of-sample** — tested only on data the model hadn't seen; the honest way.
