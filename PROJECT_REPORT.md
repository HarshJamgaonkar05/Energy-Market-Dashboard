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

The backtest runs on a database of **15-minute price bars** for crude futures. A "15-minute bar" simply summarizes all the trading in a 15-minute window (its open, high, low and closing price). There are two sources, and the engine automatically uses whichever is **fresher**: a snapshot committed to the project's `Backtesting/Data` folder (the offline fallback, ~156 bars), and the **mentor's live company feed**, which streams new bars as the market trades. The results in this report were produced on the **live feed**, which by 18 June held **~350 bars** spanning **12 June → 18 June 2026** — a Friday session, the weekend gap, and into the following week of active trading.

Because this data contains only crude (WTI + Brent), the backtest trades the crude spreads — calendars, butterflies, and Brent–WTI — and not the refined-product cracks.

## 2. The strategy being tested (restated precisely)

The Phase-2 idea — **relative-value mean-reversion** — applied to this fast data, as a single clean engine. It is deliberately simple; the plain-English deep dive is in the companion document [`Backtesting/STRATEGY.md`](Backtesting/STRATEGY.md).

**First, the key question: can we reuse Phase 2's fair-value model?** Phase 2 built a clever statistical fair value for each spread from *fundamentals* (inventories, the dollar, volatility, the season). The natural instinct is to reuse it here — but we looked carefully, and **it cannot be used intraday**, for three concrete reasons:
  - **Its ingredients aren't in this data.** The intraday feed contains *only oil prices* — none of the fundamental inputs the model needs — so it literally cannot be computed.
  - **Its number is out of date.** Phase 2's fair value for WTI Jul–Aug is ~**2.18**; that gap actually trades at ~**0.74** now. Forcing the old number on would flag a permanent false "cheap."
  - **It barely moves intraday.** Fundamentals update daily/weekly, so over a few days the model is a flat line — it can't explain the minute-by-minute moves we're trading.

So fair value is estimated **from each spread's own recent history**, and Phase 2 is kept as *context* (its proven hit-rates feed the confidence score), not as the price reference. With that settled, the strategy is four simple steps:

**Step 1 — Estimate fair value.** For each spread, take the **average of its last 24 readings (~6 hours)**. That rolling average is "normal." As new readings arrive it rolls forward, keeping up with a slowly drifting spread.

**Step 2 — Measure the z-score.** How far the spread is from that average right now, counted in *standard deviations* (its typical wiggle). A z-score of +2 means "two normal wiggles too high."

**Step 3 — Enter on a clear dislocation.** When the spread is stretched to **2 standard deviations or more**, **fade** it: sell if it's rich (stretched wide), buy if it's cheap (stretched narrow). That single, strict condition is the whole entry — no extra filters.

**Step 4 — Exit, on the first of four triggers.**
  - it **reverts through to fair** (z back within ±0.25) → **take profit** (the whole snap-back, not a sliver);
  - it stretches further against us to **3.5 standard deviations** → **stop loss**;
  - it **hasn't resolved within ~12 hours** → **time stop** (cut the dead trades);
  - the session/weekend gap arrives → **flatten** (never hold blindly through a multi-day gap).

**Sizing — fixed one unit per trade.** Every trade is the same small size, so the result is the **raw per-unit signal**, not a leveraged book. (An earlier version added clever 1%-of-capital sizing; it multiplied every position ~100× and turned the figures into scary six-figure numbers that obscured whether the *signal* was any good, so it was stripped back out. Sizing is a separate decision layered on *after* you trust the signal — see Part VII.)

## 3. The trade log — the main output

The centrepiece of Phase 3 is the **trade log**: a complete record of *every single trade* the strategy took. For each trade it records, in plain detail:

- **which spread** and **direction** (buy/sell);
- **entry time and price**, and the **z-score** at entry (how stretched it was);
- **exit time and price**, and **why** it exited (took profit / stopped out / **timed out** / session end);
- **how long it was held** (in bars and minutes);
- **the profit or loss in dollars** (the "PnL"), and in net mode the **cost** charged and the **net PnL** after it;
- **MAE / MFE** — the worst paper loss and best paper profit *during* the trade (how much heat it took before resolving);
- **the regime** it was traded in and a **confidence score** (grounded in Phase 2's validated hit-rate for that spread).

This log is produced both as a spreadsheet (`trades.csv`, openable in Excel) and as a human-readable document (`trades_log.md`) where each trade is written out in words.

### What the dollar figures mean

Each oil contract is **1,000 barrels**, so a **$1.00 per barrel** move in a spread is worth **$1,000 per contract**. Every trade is a **fixed one unit**, so the dollar figures are the *raw per-unit signal* — small, honest, and directly comparable across trades. (The $250,000 starting capital is only a baseline for the running-total chart.) By default the backtest runs on a **gross basis with slippage set to zero** — measuring the *pure signal*, before real-world trading frictions; that was the brief's instruction, and it isolates the question *"does the prediction work?"*. Running it **net of realistic costs** (`--slip`) answers the separate, harder question *"can you actually execute it for a profit?"*.

## 4. The results

On the **live company feed (~350 fifteen-minute bars, 12–18 June 2026)**, fixed one unit per trade. *(Exact figures drift as more live bars accumulate; the shape is the point.)*

| Metric | Result | What it means |
|---|---|---|
| **Trades** | 76 | the strategy found 76 stretched-spread opportunities |
| **Gross profit** | **+$4,270** | total per-unit dollars made (before costs) |
| **Win rate** | **78%** | 78% of trades were profitable |
| **Profit factor** | **3.03** | for every $1 lost, $3.03 was won |
| **Expectancy** | **+$56 / trade** | the average trade made $56 |
| **Max drawdown** | **−$1,450** | the worst peak-to-trough dip along the way |
| **Net (after a 1¢/leg fee)** | **~break-even (+$150)** | costs eat the small intraday edge |

How to read this:

- **The signal works.** A profit factor of 3.0 and a 78% win rate over 76 trades is a genuine, healthy mean-reversion edge — the gaps really do snap back more often than not.
- **The numbers are small and honest.** One contract per trade and few-cent intraday moves mean modest dollars. That's the *raw signal*, not a sized portfolio — exactly what a clean test should report.
- **Costs are the deciding factor.** Charge a realistic fee and the edge thins to roughly break-even. This is the honest truth about a high-frequency, small-move strategy, and it's the headline of the next part.

Per spread, most were profitable (the butterflies and Brent–WTI strongest); one — Brent Sep–Oct — actually **lost** money, shown plainly rather than hidden. The honest headline is a **method**: the edge is real but small, and whether it's *tradeable* comes down to costs.

---

# Part VII — How to read the results honestly

A good analyst is their own harshest critic. Here is the honest interpretation — exactly what you should tell a mentor or risk manager.

## 1. A high win rate *and* a high profit factor — why that's a good sign

The strategy wins **78%** of the time, and — unlike a "win-often-lose-big" trick — it *also* has a strong **profit factor of 3.0**. Those two together are the healthy combination: it wins often **and** the wins outweigh the losses (it won $3 for every $1 lost). The reason is the exit design — we hold for the **whole** snap-back (a 1.75-wiggle reward) but cut losers at a slightly **closer** stop (a 1.5-wiggle risk), so winners are a touch bigger than losers on top of being more frequent. Win rate alone can be faked; win rate *plus* profit factor cannot. The honest scoreboard is the profit factor and the expectancy, and both are clearly positive.

The dollar totals are **small on purpose**: one contract per trade and few-cent intraday moves. That is the *raw signal*, not a sized book — exactly what a clean test should show.

## 2. The cost test — the number that actually decides it

The most important honest point: **gross, the signal works; net of realistic fees, it thins to roughly break-even.** This is a high-frequency, small-move strategy — you pay the bid–ask spread on every entry and exit, and those costs are about the size of the moves you're capturing. A backtest that only ever shows the *gross* figure is quietly flattering itself.

This isn't a reason to bin the strategy — it's the honest brief a desk would write: *the prediction is real, but the edge per trade is small, so execution cost is the deciding factor.* The path to a tradeable version is **fewer, higher-conviction trades** (bigger expected moves that clear the cost), not more trades. Being able to put a **net** number next to the gross one is what makes the analysis credible.

## 3. Why we size at one fixed unit (and the experiment we removed)

This backtest sizes every trade at **one unit**, on purpose, so the result is the *raw signal*. An earlier iteration tried a textbook **1%-of-capital sizing rule** — size each trade so a stop-out loses 1% of $250,000. It technically worked, but it multiplied every position by ~100×, turning the results into **six-figure swings** (+$300k gross, −$58k drawdown) that looked dramatic but said nothing new about the *signal* — they just scaled it up *and* scaled the risk up with it. Worse, because the seven spreads are close cousins (all crude), their risks stacked into a portfolio drawdown far bigger than any single trade's 1%.

The lesson, kept here as the honest takeaway: **sizing is a separate decision you layer on *after* you trust the signal — and it needs portfolio-level risk limits, not just per-trade ones.** Mixing it into the signal test only obscured whether the underlying edge was real. So we test the edge cleanly at one unit; sizing is future work.

## 4. The regime caveat (an important subtlety)

Phase 2's regimes are based on *daily, fundamental* data (inventories, the dollar, volatility) that change over **weeks**. The backtest window is only **a few days long**, so within it the regime **barely changes** — it is "Balanced · High Vol" essentially throughout.

So over this short window the regime *conditioning* does little real work — there's nothing to switch between. What the backtest genuinely tests is the **mean-reversion core**, with the regime attached as honest context and Phase 2's validated hit-rates feeding the confidence score. That's an inherent property of running a *daily* framework on a *few-day* sample — a limitation to state, not a flaw to hide.

## 5. The fair-value caveat

The backtest estimates each spread's fair value as a **rolling average of its own recent prices**, *not* by reusing Phase 2's fundamental model — because that model **can't be used here** (its inputs aren't in the intraday feed, its stored level is stale, and it's flat over a few days; see Part VI). This is the right tool for the timeframe, but it has an honest weakness of its own: a plain average can be **tugged by a single sharp spike**, slightly distorting "normal" on the very bar we're reacting to. A more robust centre (a median, say) is a sensible refinement; we kept the simple average for clarity.

## 6. The honest headline caveats, in one place

1. **Small sample.** ~350 bars over a handful of sessions → a modest number of trades. This is a *working engine and a methodology*, not a statistically final result. More days of data is the path to confidence.
2. **Costs decide it.** Gross isolates the signal (and it's positive); net of a realistic fee it's roughly break-even. Real profitability needs lower costs or pickier, higher-conviction trades. The illustrative 1¢/leg should be replaced with the desk's true spread.
3. **Crude-only.** The live data is WTI + Brent, so the product cracks aren't backtested here.
4. **In-window only.** Roll/expiry of contracts within the window is not modelled (the window is short).
5. **One-unit sizing.** This reports the raw per-unit signal, not a sized/leveraged portfolio. Position sizing and portfolio risk limits are a separate layer on top (§3).

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
- **Hit-rate** — the % of times a stretched spread historically reverted; the core measure of edge.
- **Net basis** — results *after* trading costs (slippage); the honest "tradeable profit" figure, vs the gross "pure signal."
- **Time stop** — closing a trade that hasn't resolved within a set time (~12h here), to avoid dead positions.
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
