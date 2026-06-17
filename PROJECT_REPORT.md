# The Voltaire Energy Terminal
### A complete, plain-English guide to what this project is, why it exists, and exactly how it works

*Written so that someone who has never heard the words "futures," "spread," or "backwardation" can finish this document and understand the entire project. The focus is the **financial markets** — what the numbers mean and why a trader cares — not the software.*

---

## How to read this document

This report is built in layers. We start with the absolute basics of the oil market — assuming you know nothing — and only once those are solid do we explain what the project actually does with them. If you already know what a "calendar spread" is, you can skim Part II; if you don't, Part II is where everything later will start to make sense.

- **Part I** — Why oil is traded at all, and who trades it.
- **Part II** — The building blocks: futures, the forward curve, spreads, volatility, inventories. *(The vocabulary. Read this slowly.)*
- **Part III** — What the project is, in one picture.
- **Part IV** — Phase 1: the live market dashboard.
- **Part V** — Phase 2: reading the market's "mood" and finding mispriced trades.
- **Part VI** — Phase 3: testing the trading idea on real data (the backtest).
- **Part VII** — How to read the results honestly.
- **Glossary** — Every term, defined in one line.

---

# Part I — The oil market, from zero

## What is being traded?

Crude oil is the raw material that gets refined into the fuels the world runs on: petrol (gasoline) for cars, diesel for trucks, jet fuel for planes, heating oil for homes. Because almost every economy depends on it, the price of oil is one of the most-watched numbers in finance.

But there is no single "price of oil." Oil comes in different grades from different places, and — crucially — it is bought and sold not just for *today*, but for delivery *months and years into the future*. Understanding the project requires understanding that second point deeply, so we will spend time on it.

## The two benchmark oils: Brent and WTI

When people say "the oil price," they almost always mean one of two **benchmark** grades:

- **Brent** — oil from the North Sea (off the coast of the UK/Norway). It is the benchmark for most of the world (Europe, Africa, the Middle East). It trades on an exchange called **ICE**. In our data it carries the code **`CO`**.
- **WTI** (West Texas Intermediate) — oil produced in the United States. It is the benchmark for the Americas. It trades on an exchange called the **CME/NYMEX**. In our data it carries the code **`CL`**.

The two are similar but not identical, and the *gap* between their prices (the **Brent–WTI spread**) is itself one of the most-traded relationships in the market. We will return to this.

## Who trades oil, and why?

Three broad groups:

1. **Hedgers** — airlines, refiners, oil producers. They trade to *reduce* risk. An airline that knows it must buy jet fuel next year can lock in a price today, so a price spike doesn't bankrupt it.
2. **Speculators** — hedge funds, trading desks, individuals. They trade to *make money* from price moves. They take on the risk the hedgers want to shed.
3. **Physical players** — companies that actually move barrels of oil around the world.

This project is written from the point of view of a **speculator / trading desk**: it is a tool to find and test profitable trades. It does not move real barrels.

---

# Part II — The building blocks

This is the most important section. Every later part builds on it.

## 1. Futures contracts

You cannot easily buy a tanker of oil and store it in your garage. So the market trades **futures contracts** instead.

A **futures contract** is a standardized, legally binding agreement to buy or sell a fixed amount of oil at a fixed price, for delivery on a specific future date. One standard oil contract covers **1,000 barrels**.

The key idea: a futures contract has a **price today** even though delivery is in the future. That price moves up and down every second as people buy and sell, exactly like a stock. Most speculators never take delivery — they buy a contract, and sell it later at a (hopefully) better price, pocketing the difference. They are trading the *price*, not the physical oil.

> **Why this matters for the project:** everything the project analyzes is the *price of futures contracts*, captured as it moves through the day.

## 2. Contract months ("tenors")

Here is the part that surprises newcomers. For any one oil (say WTI), there isn't one futures contract — there is a whole **ladder** of them, one for each future delivery month, stretching out years.

Each contract is labelled by its delivery month using a letter code plus a year:

| Code | Month | | Code | Month |
|---|---|---|---|---|
| F | January | | N | **July** |
| G | February | | Q | **August** |
| H | March | | U | **September** |
| J | April | | V | October |
| K | May | | X | November |
| M | June | | Z | December |

So `CL_N26` means "WTI, July 2026 delivery." `CO_Q26` means "Brent, August 2026 delivery."

The contracts are ranked by how soon they deliver:

- **M1 ("the front month" / "prompt")** — the nearest contract to expiry. The most actively traded.
- **M2** — the next one out.
- **M3** — the one after that. And so on.

In June 2026, for WTI, M1 = July (`N26`), M2 = August (`Q26`), M3 = September (`U26`).

## 3. The forward curve

If you line up the prices of all those contracts — M1, M2, M3, … out into the future — and plot them, you get the **forward curve** (also called the *term structure*). It answers: "what does the market think oil will cost at each future date?"

The *shape* of this curve is enormously informative, and it comes in two flavours:

- **Backwardation** — near-term contracts are **more expensive** than far-term ones; the curve slopes **down**. This usually signals that oil is **scarce right now** — buyers are paying a premium to get barrels immediately. Backwardation is generally a "tight market" / bullish sign.

- **Contango** — near-term contracts are **cheaper** than far-term ones; the curve slopes **up**. This usually signals **oversupply** — there's plenty of oil now, so nobody pays extra for immediate delivery; in fact you'd rather buy later. Contango is generally a "loose market" / bearish sign.

> **Plain analogy:** imagine fresh strawberries. In peak season they're cheap now and you'd pay more for "guaranteed strawberries in winter" (contango). During a shortage, you'll pay a premium to get them *today* rather than wait (backwardation). Oil's curve tells the same story about scarcity.

## 4. Spreads — the heart of this project

A speculator can simply bet "oil will go up" by buying a contract. But that is a blunt, risky bet — it depends on the entire world oil price, which is driven by wars, economies, OPEC decisions, everything.

A more refined approach is to trade **spreads**: the *difference in price between two related contracts*. When you trade a spread you **buy one contract and simultaneously sell another**. You no longer care whether oil goes up or down overall — you only care about whether the *gap between the two* widens or narrows. This strips out the big, unpredictable market-wide moves and isolates a smaller, more stable relationship.

This project trades several kinds of spreads. Here are the ones it uses:

### (a) Calendar spreads (M1–M2, M2–M3)

A **calendar spread** is the price difference between two contract months of the *same* oil. For example **WTI M1–M2** = (price of July WTI) − (price of August WTI).

- If you think near-term oil will get *tighter* (more backwardated), you **buy the spread** (buy the near month, sell the far month).
- The calendar spread is, in effect, a pure bet on the *shape of the forward curve* — on scarcity vs glut — without betting on the overall oil price at all.

### (b) Butterflies ("flies")

A **butterfly** combines two calendar spreads to bet on the *curvature* of the forward curve — whether the middle of the curve is out of line with its neighbours. A WTI fly is built as:

> **+1 × M1  −2 × M2  +1 × M3**

(buy one July, sell two August, buy one September). If August is priced strangely relative to July and September, the fly captures it. It's an even more surgical, market-neutral trade than a calendar spread.

### (c) The Brent–WTI spread

This is the price difference between the two benchmark oils: **Brent − WTI**. It reflects regional supply/demand differences (US vs the rest of the world), shipping costs, and pipeline bottlenecks. It is one of the most liquid and closely watched spreads in all of commodities.

### (d) Crack spreads (background)

A **crack spread** is the difference between crude oil and the refined products made from it (petrol, diesel/heating oil). It approximates a refiner's profit margin — "buy crude, sell the fuel." The famous **3:2:1 crack** models a refinery turning 3 barrels of crude into 2 of petrol and 1 of diesel. *The project's broader framework analyzes cracks, but the live backtest data only contains crude, so the backtest itself trades crude spreads only — more on this later.*

## 5. Volatility

**Volatility** measures how violently a price swings around. High volatility = big, fast moves; low volatility = calm, gentle drift. It is usually expressed as an annualized percentage (e.g. "52% volatility"). Volatility matters because the *same* trade is far riskier in a stormy market than a calm one, and because some strategies only work in certain volatility conditions.

## 6. Inventories (stockpiles)

Governments and agencies report how much oil is sitting in storage tanks. In the US, the **EIA** (Energy Information Administration) publishes this weekly. Inventories are the single clearest read on supply and demand:

- **Stocks falling / below normal** → oil is being consumed faster than produced → **tight** market → supportive of prices.
- **Stocks rising / above normal** → a glut is building → **loose** market → bearish.

Analysts compare current stocks to the **5-year seasonal average** (because oil demand is seasonal — more driving in summer, more heating in winter), and express the gap as a number of **standard deviations** from normal (explained next).

## 7. The z-score and "mean reversion" — the two ideas the strategy rests on

These two concepts are the engine of the whole trading strategy, so they get extra care.

### The z-score (how unusual is this number?)

Suppose a spread normally hovers around **1.50**, and on a typical day wiggles by about **0.10** up or down. One day it jumps to **1.80**. Is that a big deal?

A **z-score** answers exactly that. It measures *how far a value is from its own average, counted in "typical wiggles."* The "typical wiggle" is the **standard deviation**.

> z = (current value − average value) ÷ typical wiggle

In our example: (1.80 − 1.50) ÷ 0.10 = **+3.0**. The spread is 3 standard deviations above normal — a genuinely rare, stretched reading. A z-score near **0** means "totally normal." A z-score of **+2 or −2** means "unusually high / low." **±3** is extreme.

This lets us compare wildly different spreads on one common ruler: *"how stretched is this, relative to its own normal behaviour?"*

### Mean reversion (the rubber-band idea)

**Mean reversion** is the observation that many relationships, after being stretched unusually far from their average, tend to snap *back* toward that average — like a rubber band. A spread that is +3 standard deviations "rich" (too high) often falls back toward normal; one that is −3 "cheap" (too low) often rises back.

The strategy in this project is a **mean-reversion** strategy. In one sentence:

> **When a spread becomes unusually stretched (a big z-score), bet that it will snap back toward normal.**

That's the whole idea. Everything in Phase 2 and Phase 3 is about doing this *carefully* — measuring "stretched" properly, only acting when the odds are good, and proving the idea actually works.

---

# Part III — What the project is

The **Voltaire Energy Terminal** is a professional-style oil-trading dashboard. It was built in three phases, each adding a layer:

1. **Phase 1 — The live market dashboard.** Gather every relevant piece of live data (prices, inventories, weather, news, positioning) into one screen, so a trader can see the state of the market at a glance.

2. **Phase 2 — Market analysis & signal generation.** Go beyond just *showing* data: automatically read the market's current "mood" (its **regime**), work out what each spread *should* be worth (its **fair value**), and flag the spreads that look mispriced — ranked, scored opportunities.

3. **Phase 3 — The backtest.** Take the trading idea from Phase 2 and *test it on real market data*: simulate every trade it would have made, record the profit or loss of each, and judge whether the idea actually works.

The rest of this document explains each phase in financial terms.

---

# Part IV — Phase 1: the live market dashboard

Phase 1 answers a simple question for the trader: **"What is happening in the oil market right now?"** It pulls together live, free, public data sources, each of which tells part of the story:

- **Prices & the forward curve** (from Yahoo Finance) — live futures prices for Brent, WTI and the refined products, and the shape of the forward curve (backwardation vs contango).
- **Inventories & fundamentals** (from the US EIA) — official weekly stockpile data: crude, petrol, diesel. The supply/demand truth.
- **Weather** (from Open-Meteo) — temperature forecasts in key demand regions; cold snaps drive heating-oil demand, heatwaves drive power/cooling demand.
- **Hurricanes/storms** (from the US NOAA) — storms in the Gulf of Mexico can shut down a large chunk of US oil production and refining, moving prices sharply.
- **Positioning** (from the US CFTC) — the weekly "Commitments of Traders" report, showing whether big speculative funds are heavily betting up or down. Extreme positioning often precedes reversals.
- **News & sentiment** (from a live newswire + an AI language model called FinBERT) — headlines are automatically scored as positive, negative or neutral for the oil market, giving a real-time read on the mood.

Individually, each is a data feed. Together, they are a **situational-awareness cockpit**: at a glance, is the market tight or loose, calm or stormy, bullishly or bearishly positioned?

This phase doesn't make trading decisions. It sets the stage for the phases that do.

---

# Part V — Phase 2: reading the market's mood and finding mispriced trades

Phase 2 is where the project starts *thinking*. It has three jobs: classify the **regime**, compute each spread's **fair value**, and produce **ranked signals**.

## 1. Market regimes — the market's "mood"

A core insight of professional trading is that **the same trade behaves differently in different market environments.** Fading a stretched spread might be brilliant in a calm, well-supplied market and disastrous in a panicky, scarce one. So before anything else, the system classifies the *current environment* — its **regime**.

It does this by reading several independent dimensions of the market and labelling each:

- **Inventory** — are stockpiles Tight, Balanced, or Oversupplied? (from EIA data)
- **Term structure** — is the forward curve in Backwardation or Contango? (the scarcity signal)
- **Volatility** — is the market High, Normal, or Low vol?
- **Trend** — is oil trending Up, Down, or Range-bound?
- **Season** — are we in the Driving season (summer), Heating season (winter), or a shoulder period?

Combining these gives a compact label for the market's mood. In the data used for this project the live regime was, for example:

> **"Balanced · High Vol"** — inventories roughly at seasonal norms, but the market swinging violently (52% annualized volatility), with the forward curve backwardated (a tight, scarce signal) and prices trending up.

Why bother? Because the system then measures every spread's behaviour *within each regime separately*. "What is normal for the WTI calendar spread **when the market is Balanced and High-Vol**" is a much sharper question than "what is normal in general."

## 2. Fair value — what should this spread be worth?

For every spread, Phase 2 estimates a **fair value**: the price the spread *ought* to trade at, given current conditions. It does this two complementary ways:

1. **The regime average.** Within the current regime, what has this spread averaged historically? If WTI M1–M2 normally sits around 4.6 in a "Balanced · High Vol" regime, that's a baseline fair value.

2. **A statistical model (regression).** A more sophisticated estimate that relates the spread to underlying *drivers* — things like the US dollar's strength (DXY), the stock market's fear gauge (VIX), recent inventory changes, and price momentum. The model learns, from years of history, how the spread typically responds to these drivers, and outputs the value the spread *should* have given today's driver readings.

The **difference** between where a spread actually is and its fair value is the **dislocation** — the potential trade. A spread far *above* fair value is "**rich**" (a candidate to sell); far *below* is "**cheap**" (a candidate to buy).

The system expresses this dislocation as a **z-score** (Part II.7), so all spreads are measured on the same "how stretched is this?" ruler.

## 3. Ranked signals — the shortlist of opportunities

Phase 2 then produces a ranked list of **opportunities**, each carrying:

- **the instrument** (which spread) and **direction** (buy the cheap one / sell the rich one);
- **the dislocation** (the z-score — how stretched);
- **a written rationale** in plain English (e.g. *"Brent–WTI averages 6.26 in this regime; it is now 7.01, +0.2σ rich… backtest: such signals reverted 83% of the time"*);
- **a confidence score**;
- and — critically — **a historical hit-rate from a validation backtest.**

## 4. The validation backtest — does this even work historically?

A trading idea is worthless unless it has actually worked. So Phase 2 includes a **historical validation**: it looks back over *years* of daily data and asks, for each spread, *"In the past, when this spread was stretched to 1.5 standard deviations, how often did it actually revert?"*

The answer — the **hit-rate** — is the foundation of trust in the strategy. For the spreads in this project, the historical hit-rates were strong:

| Spread | Reverted (hit-rate) | vs random baseline | Edge |
|---|---|---|---|
| Brent–WTI | **83%** | 49% | +34% |
| WTI butterfly | **82%** | 49% | +32% |
| WTI M1–M2 | **75%** | 50% | +25% |
| Brent M1–M2 | **72%** | 48% | +24% |

A "hit-rate" of 83% means: historically, when this spread was this stretched, it snapped back toward normal 83 times out of 100. The "baseline" (~49%) is what you'd expect from a coin-flip. The **edge** — the gap between them — is the evidence that the strategy is capturing something real, not luck.

This validation is *daily* data over *years*. Phase 3 is where we take this validated idea and run it on fresh, fast, intraday data.

---

# Part VI — Phase 3: the backtest (testing the idea on real data)

Phase 2 proved the idea works on *years of daily* data. Phase 3 asks a tougher, more practical question:

> **"If I had actually run this strategy on real, minute-by-minute market data, trade by trade, exactly what would have happened?"**

This is a **backtest**: a careful simulation of the strategy on historical data, recording every single trade and its profit or loss. It is the closest thing to a dress rehearsal before risking real money.

## 1. The data being tested

The backtest runs on a database of **15-minute price bars** for crude futures. A "15-minute bar" simply summarizes all the trading in a 15-minute window (its open, high, low and closing price). There are two sources, and the engine automatically uses whichever is **fresher**: a snapshot committed to the project's `Backtesting/Data` folder (the offline fallback, ~156 bars), and the **mentor's live company feed**, which streams new bars as the market trades. The results in this report were produced on the **live feed**, which by 17 June held **258 bars** spanning **12 June → 17 June 2026** — a Friday session, the weekend gap, and into the following week of active trading.

Because this data contains only crude (WTI + Brent), the backtest trades the crude spreads — calendars, butterflies, and Brent–WTI — and not the refined-product cracks.

## 2. The strategy being tested (restated precisely)

The exact Phase-2 strategy — **regime-conditioned relative-value mean-reversion** — applied to this fast data. The engine was **refined in three ways** over its first version to chase better, more *honest* profit; each refinement is explained in plain English here and dissected in depth in the companion document [`Backtesting/STRATEGY.md`](Backtesting/STRATEGY.md).

**Step 1 — Estimate a robust fair value.** For each spread, continuously estimate its **fair value** from its recent prices. Rather than a plain rolling *average* (which is dragged around by the very spike we want to fade), the engine uses a **robust centre — the rolling median, with its spread measured by the MAD** (median absolute deviation). The median ignores the one-off dislocation bar, so the "normal" we compare against isn't contaminated by the abnormal move itself. *(See the honest note below on why fair value is estimated from the live data rather than reusing Phase 2's older daily levels.)*

**Step 2 — Measure the z-score.** How stretched is the spread right now, in standard-deviation units, versus that robust centre.

**Step 3 — Enter only on a *corroborated*, *favorable* dislocation.** Enter when **all** of these hold:
  - the spread is dislocated **≥ 1.5 standard deviations** (the Phase-2 threshold) — but **not more than ~2.1**, because a spread stretched right up against our stop-loss has great reward on paper but poor odds; **and**
  - the **daily fundamentals model agrees on the direction** — i.e. Phase 2's regression fair value (built from inventories, the dollar, volatility, momentum, seasonality) *also* says the spread is rich (to sell) or cheap (to buy). This **reconnects the two fair-value engines**: the fast intraday read and the slow fundamental read must point the same way; **and**
  - the **reward-to-risk is favorable** — the room back to fair value must be at least 1.5× the room to the stop-loss (more on this below).
  - Then **fade** it: sell if rich, buy if cheap (betting on reversion).

**Step 3b — Size the trade by the 1% rule.** Rather than trading a fixed amount, the engine sizes each position so that **if the stop-loss is hit, the loss is at most 1% of capital** (about $2,500 on the $250,000 account). The size is simply *risk budget ÷ distance to the stop*: calmer, tighter setups get a bigger position, riskier ones a smaller position, so **every trade puts the same small slice of the account at risk**. This is the standard professional discipline that stops any single trade from doing real damage.

**Step 4 — Exit with better geometry.** The first version took a tiny profit and risked a large loss; the refined exits fix that asymmetry. Exit when any of these happen:
  - it **reverts through to fair** (z back within ±0.1, the *whole* reversion, not just the first sliver) → **take profit**;
  - it stretches against us to **2.5 standard deviations** (a *tighter* stop than the old 3.0, so we risk less than we aim to make) → **stop loss**;
  - it simply **fails to revert in time** — specifically, after roughly **three "half-lives"** of the spread's own measured mean-reversion speed (an *Ornstein-Uhlenbeck* estimate of how fast it typically snaps back) → **time stop**. This cuts the slow bleeders that would otherwise drift all the way to the stop.
  - the session ends / the weekend gap arrives → **flatten** (never hold blindly through a multi-day gap).

**Step 5 — Make it cost-aware (optional NET mode).** By default the backtest is still **gross** (zero cost, per the brief — it isolates the pure signal). But it can now be run **net of realistic trading costs** with a single switch (`--slip`), and in that mode it **only takes a trade whose expected reversion is worth at least twice its round-trip cost** — so it stops paying to harvest moves smaller than the spread it has to cross. This is what finally answers *"is this actually profitable to trade?"* rather than just *"does the prediction work?"*

## 3. The trade log — the main output

The centrepiece of Phase 3 is the **trade log**: a complete record of *every single trade* the strategy took. For each trade it records, in plain detail:

- **which spread** and **direction** (buy/sell);
- **entry time and price**, and the **z-score** at entry (how stretched it was);
- **exit time and price**, and **why** it exited (took profit / stopped out / **timed out** / session end);
- **how long it was held** (in bars and minutes), and the spread's measured **half-life** (its reversion speed);
- **the profit or loss in dollars** (the "PnL"), and in net mode the **cost** charged and the **net PnL** after it;
- **MAE / MFE** — the worst paper loss and best paper profit *during* the trade (how much heat it took before resolving);
- **the fundamentals view** (the daily model's z and whether it **agreed** with the trade);
- **the regime** it was traded in and a **confidence score** (lifted when fundamentals agree, cut when they don't).

This log is produced both as a spreadsheet (`trades.csv`, openable in Excel) and as a human-readable document (`trades_log.md`) where each trade is written out in words.

### What the dollar figures mean

Each oil contract is **1,000 barrels**, so a **$1.00 per barrel** move in a spread is worth **$1,000 per contract**. The simulation starts with a notional **$250,000** of capital and sizes each trade by the **1% rule** described above (risking ~$2,500 per trade). By default the backtest runs on a **gross basis with slippage set to zero** — measuring the *pure signal*, before real-world trading frictions. This was the brief's instruction, and it isolates the question *"does the prediction work?"*. The refined engine can **also** run **net of realistic costs**, which answers the separate, harder question *"can you actually execute it for a profit?"* — and the contrast between the two is the most important result in this report.

> **One honest caveat on the 1% rule.** It caps the risk of *each trade individually*. But the seven spreads are close cousins (all crude oil) and often move together, so when several are open at once their risks add up — the account can swing by more than 1% at a time. Capping the *combined* risk of all open positions is the natural next step.

## 4. The results

Running the refined strategy on the **live company feed (~279 fifteen-minute bars, 12–17 June 2026)**, now with the **1% rule sizing** and **favorable-R:R** filter switched on. Because the 1% rule scales position size to risk, dollar results are best read as a **percentage of the $250,000 account**. *(Exact figures drift as more live bars accumulate; the **pattern** is the point.)*

| Mode | Trades | Gross | Net | Win | Profit factor | Avg R:R | Risk/trade | Max drawdown |
|---|---|---|---|---|---|---|---|---|
| **Gross** (pure signal) | 114 | **+$297k (+119%)** | — | 73% | 2.39 | 2.6 | ~1% | −$58k (−23%) |
| **Net + fundamentals gate** | ~10–30 | varies | net-positive | ~80% | >1 (net) | ~3 | ~1% | small |

How to read this:

- **The 1% rule did its job.** Every trade risked ≈ **$2,400 (about 1% of capital)** at its stop, regardless of which spread or how jumpy it was. That single discipline is what turns the old "tiny one-unit" results into **meaningful, controlled-risk size** — the same edge (profit factor ~2.4), just sized to matter.
- **Favorable R:R, honestly applied.** The average trade now offers about **2.6× more reward than risk**, taken from the *sweet-spot* band — not from spreads stretched right against the stop, which look great on paper but lose too often (we deliberately exclude those).
- **The cost story still holds** (from the earlier finding): once realistic costs are charged, trading everything is a net loser; only the **fundamentals-corroborated** trades stay net-positive. Filtering, not frequency, is where the money is.

But there is a blunt caveat that matters more now that size is real: the **−23% drawdown**. See Part VII.

The honest headline is a **method**, not a single profit number: the edge is genuine, sized to a controlled 1%-per-trade risk, favorable in reward-to-risk, fragile to costs, and — as the drawdown shows — still exposed at the *portfolio* level. The next part reads all of this critically.

---

# Part VII — How to read the results honestly

A good analyst is their own harshest critic. Here is the honest interpretation — exactly what you should tell a mentor or risk manager.

## 1. Win rate, profit, and what the refinements deliberately traded away

The first version of this engine reported an **83% win rate** — which sounds dazzling until you see *how* it was earned: it took profit at a **near** target (a sliver of the reversion) while only stopping out at a **far** level. That geometry *manufactures* a high win rate — lots of tiny wins, a few larger losses — and in that version the average win was actually *smaller* than the average loss. A high win rate from a near-target/far-stop design is partly a **mechanical artifact, not skill.**

The refined exits **deliberately give up some of that win rate** (down to ~64% gross) in exchange for a healthier shape: the new target holds for the *whole* reversion, the stop is *tighter* than the target distance, and the time stop cuts losers early. So each win is **bigger**, each loss is **smaller and quicker**, and the genuine edge shows up where it should — in the **profit factor** and **expectancy**, not the headline win rate. This is the correct trade-off to make: win rate is vanity, expectancy is sanity.

The dollar totals are still modest for two honest reasons that have nothing to do with whether the signal works: the **position size is tiny** (one contract per spread) and **intraday spread moves are small** (a few cents). The strategy is barely *sized*, not barely *working* — and edge-weighted position sizing is the obvious next lever (deliberately left out here to keep the test clean).

## 2. The cost test — the caveat the first version hid, now answered head-on

The single most important number in this report is the one the original gross-only backtest could not show: **net of realistic trading costs, the unfiltered strategy loses money.** Trading 193 times to harvest few-cent reversions, you pay the bid–ask spread on every entry and exit, and those costs are larger than the moves you capture. A backtest that only ever reports the *gross* figure is, in effect, flattering itself.

This is not a reason to abandon the strategy — it is a reason to **trade it selectively**. When the engine is forced to clear costs *and* to act only when the daily fundamentals model agrees, it self-selects down to ~28 trades that remain **net-positive with a tiny drawdown**. The lesson is the honest one a desk would draw: *the signal is real but cost-fragile; profitability comes from discipline (fewer, corroborated, larger trades), not from trading more.* Being able to **measure** this — to put a net number next to the gross one — is itself the upgrade.

## 3. Position sizing did its job — but watch the *portfolio* risk

The 1% rule worked exactly as designed at the **per-trade** level: each trade risked about 1% of capital, no matter the spread. That is the right way to size, and it's what lets the strategy run at a size that actually produces meaningful dollars instead of pocket change.

But notice the **−23% drawdown**. How can the account fall 23% if no single trade risks more than 1%? Because the seven spreads are **close cousins** — they're all built from the same crude-oil curve, so they tend to get stretched, and snap back, *together*. When five or six of them are in losing trades at the same moment, their individual 1% risks **stack** into a much larger combined loss. The 1% rule controls each trade in isolation; it does **not** control how correlated trades pile up.

This is the honest next problem to solve: a **portfolio-level risk cap** — limiting the *combined* risk of everything open at once, or sizing down when positions are correlated. It's the natural follow-on to the two controls added here, and it's the difference between "each bet is safe" and "the whole book is safe."

## 4. The regime caveat (an important subtlety)

Phase 2's regimes are based on *daily, fundamental* data (inventories, the dollar, volatility) that change over **weeks**. The backtest window is only **3 days long**, so within it the regime **never changes** — it is "Balanced · High Vol" the entire time.

This means that, over this short window, the regime *conditioning* part of the strategy does no real work — there is nothing to switch between. What the backtest genuinely tests is the **mean-reversion core** of the strategy, with the regime attached as honest context and the validated historical hit-rates feeding the confidence score. This is an inherent property of running a *daily* framework on a *3-day* sample — not a flaw to be hidden, but a limitation to be stated.

## 5. The fair-value caveat

The backtest estimates each spread's fair value from a **robust rolling centre (median/MAD) of the recent data**, rather than reusing Phase 2's stored daily fair values. Why estimate it live? Because Phase 2's stored levels are from an earlier date and the contracts have since re-priced — for example, the live WTI M1–M2 spread sits around **1.3**, while Phase 2's older "fair" level for it was around **4.6**. Forcing the old number onto today's market would make every spread look artificially "cheap" — pure noise, not signal. The *level* doesn't transfer; what the engine borrows from Phase 2 instead is the **direction** of the fundamental view (rich vs cheap), which does transfer and is used as the agreement gate. And the centre is a **median, not a mean**, precisely so the dislocation we're trading doesn't pollute the "normal" we measure it against.

## 6. The honest headline caveats, in one place

1. **Small sample.** A few hundred bars over a handful of sessions → a modest number of trades. This is a *working engine and a methodology*, not a statistically final result. Feeding it more days of data is the path to confidence — and anything tuned on this little data risks being overfit, so the structural changes (better exits, cost-awareness) should be trusted more than any single fitted number.
2. **Costs are now tested, not ignored.** The default run is still gross (per the brief), but the engine can charge realistic slippage — and when it does, the headline flips negative unless trades are filtered. The illustrative cost used (1¢/leg) should be replaced with the desk's true spread.
3. **Crude-only.** The live data is WTI + Brent, so the product cracks aren't backtested here.
4. **In-window only.** Roll/expiry of contracts within the window is not modelled (the window is short).
5. **Per-trade risk, not portfolio risk.** The 1% rule caps each trade; it does not yet cap the *combined* risk of correlated positions, which is why the drawdown can exceed 1% (§3). A portfolio-level cap is the next control.

Stating these plainly is not weakness — it is exactly what separates a credible analysis from a misleading one.

---

# Part VIII — How the three phases fit together

The project is a single, coherent pipeline that mirrors how a real trading desk thinks:

1. **See the market** (Phase 1) — gather every live signal: prices, the curve, inventories, weather, storms, positioning, news.
2. **Form a view** (Phase 2) — read the regime, compute fair values, and rank the mispriced spreads, each scored by a confidence grounded in years of validation.
3. **Prove the view** (Phase 3) — backtest the strategy trade-by-trade on real data, producing a complete, honest trade log with full profit-and-loss accounting.

Each phase feeds the next. The regime and the validated hit-rates from Phase 2 flow directly into the confidence score on every trade in Phase 3. The whole thing is designed to move from *information* → *insight* → *evidence*.

---

# Glossary — every term in one line

- **Barrel** — the standard unit of oil; one futures contract = 1,000 barrels.
- **Backwardation** — forward curve slopes down (near oil dearer than far); signals scarcity/tightness.
- **Benchmark** — a reference grade of oil; the two main ones are Brent and WTI.
- **Brent** — the North Sea / global benchmark oil (code `CO`, ICE exchange).
- **Brent–WTI spread** — the price gap between the two benchmark oils.
- **Butterfly / fly** — a 3-leg spread (+1 M1, −2 M2, +1 M3) betting on the curvature of the forward curve.
- **Calendar spread** — the price gap between two contract months of the same oil (e.g. M1–M2).
- **Contango** — forward curve slopes up (near oil cheaper than far); signals oversupply/glut.
- **Contract month / tenor** — the delivery month of a futures contract, coded by a letter + year.
- **Crack spread** — the gap between crude and the refined fuels made from it; a refiner's margin proxy.
- **Drawdown** — the drop from a peak in account value to a later trough; a measure of pain/risk.
- **EIA** — US Energy Information Administration; publishes official weekly oil inventory data.
- **Expectancy** — the average profit per trade across all trades.
- **Fair value** — what a spread *should* be worth, given conditions; the reference for "rich/cheap."
- **Fade** — to bet *against* a recent move (sell something that just rose, buy something that just fell).
- **Forward curve / term structure** — the line of futures prices across all delivery months.
- **Front month (M1) / prompt** — the nearest-to-expiry, most-traded contract.
- **Futures contract** — a standardized agreement to buy/sell oil at a set price for future delivery.
- **Gross basis** — results before trading costs (slippage, commission).
- **Hedger** — a market participant trading to reduce risk (airlines, refiners, producers).
- **Half-life** — how long a stretched spread typically takes to revert halfway back to fair; the engine's "is it reverting fast enough?" clock, behind the time stop.
- **Hit-rate** — the % of times a stretched spread historically reverted; the core measure of edge.
- **MAD (median absolute deviation)** — a robust measure of "typical wiggle" that, unlike standard deviation, isn't inflated by a single extreme bar; the scale behind the robust z-score.
- **Net basis** — results *after* trading costs (slippage); the honest "tradeable profit" figure, vs the gross "pure signal."
- **Ornstein-Uhlenbeck (OU)** — the standard mathematical model of a mean-reverting series; used here only to estimate each spread's reversion half-life.
- **Inventories / stocks** — oil sitting in storage; the clearest read on supply vs demand.
- **Leg** — one of the individual contracts inside a spread trade.
- **Liquidity** — how easily a contract can be traded without moving its price.
- **MAE / MFE** — Maximum Adverse / Favourable Excursion: the worst/best paper PnL during a trade.
- **Mean reversion** — the tendency of a stretched value to snap back toward its average.
- **PnL** — Profit and Loss; the money made or lost.
- **Profit factor** — total dollars won ÷ total dollars lost; above 1 is profitable.
- **Regime** — the market's current "mood," labelled across inventory, structure, volatility, trend, season.
- **Regression** — a statistical model relating a spread to its underlying drivers, to estimate fair value.
- **Rich / cheap** — a spread trading above (rich) or below (cheap) its fair value.
- **Slippage** — the small cost of trading (the gap between expected and actual fill price); zero in gross mode, configurable for the net test.
- **Speculator** — a participant trading to profit from price moves, not to hedge.
- **Spread** — the price difference between two related contracts, traded as one position.
- **Standard deviation** — the "typical wiggle" of a value; the unit behind the z-score.
- **Stop loss** — a pre-set exit that caps the loss on a losing trade.
- **Volatility** — how violently a price swings; usually an annualized %.
- **WTI** — the US benchmark oil (code `CL`, CME/NYMEX exchange).
- **z-score** — how far a value is from its average, measured in standard deviations; the "how stretched?" ruler.

---

*End of report. This document covers the project end-to-end: the financial foundations, the live dashboard (Phase 1), the regime analysis and signal generation (Phase 2), and the trade-by-trade backtest with its honest interpretation (Phase 3).*
