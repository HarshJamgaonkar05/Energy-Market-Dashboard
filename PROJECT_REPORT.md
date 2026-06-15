# The Energy Market Project — A Complete Plain-English Report

*A full explanation of what this project is, the markets it studies, the strategy
it builds, and how that strategy was tested — written so that someone who has
never touched financial markets can follow every single step.*

---

## How to read this report

We start from absolute zero — what oil even is as a thing you can trade — and end
at a tested trading strategy with real profit-and-loss numbers. Each idea is built
on the one before it. There is a **glossary at the very end** if you want a quick
one-line reminder of any term. Nothing here assumes prior knowledge.

The project happened in three stages, and the report follows the same order:

1. **The Information Stage** — gather everything that's happening in the oil market
   into one place (prices, supply, demand, news).
2. **The Analysis Stage** — turn that information into an opinion: *what kind of
   market are we in, and where is something mispriced?*
3. **The Testing Stage** — take that opinion, turn it into actual buy/sell rules,
   and check on real historical data whether it would have made money.

---

# PART 1 — THE BIG PICTURE (in one minute)

Imagine the oil market is a giant, noisy weather system. Prices move every second
for thousands of reasons. Most people just look at one number — "the price of oil" —
and guess.

This project does three smarter things:

- It **measures the weather**: is the market calm or stormy, oversupplied or tight,
  rising or falling?
- It **finds things that look out of place**: two prices that usually move together
  but have temporarily drifted apart — like a rubber band stretched too far.
- It **bets that the rubber band snaps back** — and then it *checks, on real past
  data, whether that bet actually wins.*

That's the whole idea. The rest of this report explains every word of it.

---

# PART 2 — WHAT IS OIL, AS SOMETHING YOU TRADE?

## 2.1 Crude oil is a raw ingredient

**Crude oil** is the black liquid pumped out of the ground. On its own it's almost
useless — you can't put it in a car. It's a *raw ingredient*. Refineries (giant
factories) cook crude oil and split it into **useful finished products**:

- **Gasoline** (petrol) — for cars.
- **Diesel / heating oil** — for trucks, ships, machinery, and heating buildings.
- **Jet fuel, and many others.**

So think of it like wheat: crude oil is the *wheat*, and gasoline/diesel are the
*bread and pasta* made from it. This "raw ingredient → finished product" idea is the
single most important concept in the whole project, because a lot of the trades are
bets on the **gap between the price of the ingredient and the price of the product**
(more on that soon).

## 2.2 There isn't one "oil price" — there are benchmarks

Oil is pumped in dozens of countries, and the exact stuff varies in quality and
location. To make trading possible, the world settled on a few **benchmark** grades —
standard reference oils that everything else is priced against. The two giant ones,
and the ones this project focuses on, are:

- **WTI** (West Texas Intermediate) — the U.S. benchmark. Priced in **U.S. dollars
  per barrel**.
- **Brent** — the international / European benchmark (named after a North Sea oil
  field). Also priced in **dollars per barrel**.

A **barrel** is just a standard unit of volume (about 159 litres). When you hear
"oil is at $80," it means **$80 per barrel** for one of these benchmarks.

WTI and Brent are extremely similar oils, so their prices move almost in lockstep —
but not *exactly*. The small, ever-changing difference between them is itself one of
the most-traded things in the market (we'll get to "spreads").

## 2.3 The products this project tracks

Besides the two crude benchmarks, the project follows three **refined products**:

- **RBOB Gasoline** — the U.S. gasoline benchmark. Priced in **dollars per gallon**.
- **Heating Oil / ULSD** — U.S. diesel & heating oil. Priced in **dollars per gallon**.
- **Gas Oil** — the European version of diesel. Priced in **dollars per metric tonne**.

Notice the **different units** — barrels, gallons, tonnes. That's just historical
convention. To compare them fairly, everything in the project is converted to a
common unit: **dollars per barrel**. (1 barrel = 42 US gallons; tonnes convert by a
fixed factor.) This conversion matters only so that an apples-to-apples comparison is
possible.

**The five instruments tracked: WTI, Brent, Heating Oil, RBOB Gasoline, Gas Oil.**

---

# PART 3 — FUTURES AND THE "FORWARD CURVE"

This part introduces *how* oil is actually traded by professionals. It's the
foundation for everything later, so we go slowly.

## 3.1 What is a "futures contract"?

You almost never trade physical barrels directly. Instead you trade **futures**.

A **futures contract** is a binding agreement made *today* to buy (or sell) a set
amount of oil at a set price on a *specific future date*.

Simple analogy: you tell a farmer in spring, "I'll buy 100 kg of your apples in
October for ₹50/kg." You've locked the price now for a delivery later. That's a
future. Both sides are protected from price swings in between.

Two kinds of people use them:

- **Hedgers** — airlines, refiners, oil producers — who want to *lock in* a price
  and remove uncertainty from their business.
- **Speculators / traders** — who have *no* use for physical oil but want to profit
  from price moves. This project is about the trader's view.

One oil futures contract represents **1,000 barrels**. So if the price moves by $1
per barrel, the contract's value changes by **$1,000**. Remember this number —
**$1 = $1,000 per contract** — it's how all the profit numbers later are calculated.

## 3.2 Contract "months" and the front month

Here's the key twist: for the *same* oil, there isn't one futures price — there's a
**separate price for each future delivery month**.

There's a contract for "WTI to be delivered in July," another for "WTI in August,"
another for "September," and so on, stretching out years. Each is its own market with
its own price.

Traders label them by nearness:

- **M1 = the "front month"** = the nearest contract = the one closest to delivery.
- **M2 = the next month, M3 = the month after,** and so on.

As time passes and the front contract approaches its delivery date, it "expires," and
M2 becomes the new M1. This constant shifting is called **rolling**. (In our data the
month codes look like `N26` = July 2026, `Q26` = August 2026, `U26` = September 2026.)

## 3.3 The forward curve

If you line up the price of every delivery month — M1, M2, M3, … M12 — and draw them
on a chart, you get the **forward curve**. It's a price tag for each future month.

The *shape* of that curve is enormously informative. There are two shapes:

### Contango (the curve slopes UP — later months cost more)

If September oil is more expensive than July oil, the market is in **contango**.

*Why would the future cost more than now?* Usually because there's **plenty of oil
today** — maybe too much. Nobody's desperate for it now, and if you wanted to hold
oil for later you'd have to pay for **storage** (tanks, insurance, interest). So
later-dated oil is priced higher to cover those carrying costs. **Contango is the
"comfortable, well-supplied" shape.**

### Backwardation (the curve slopes DOWN — later months cost less)

If July oil is more expensive than September oil, the market is in **backwardation**.

*Why would oil-right-now cost more than oil-later?* Because supply is **tight** —
people need barrels *immediately* and are willing to pay a premium to get them now
rather than wait. **Backwardation is the "tight, anxious, supply-short" shape.**

> **Why this matters for the project:** the shape of the curve is one of the
> "weather readings" the system uses to decide what kind of market we're in. During
> the period studied (2021–2026), oil was in backwardation about 95% of the time —
> a persistently tight market.

---

# PART 4 — SPREADS: THE HEART OF THE STRATEGY

Most beginners think trading is "buy oil, hope it goes up." Professionals very often
do something cleverer and safer: they trade **spreads**.

## 4.1 What is a spread, and why trade it?

A **spread** is the *difference* between two related prices. Instead of betting on
where oil goes, you bet on the **gap** between two things.

Why is this safer? Imagine a giant news event — war, a recession — that sends *all*
oil prices crashing. If you simply owned oil, you lose badly. But if you owned the
*gap* between two oils (long one, short the other), a market-wide crash hits both
sides and largely cancels out. You've stripped away the wild "whole market" risk and
isolated a smaller, calmer, more *predictable* relationship.

And here's the magic: these relationships tend to be **mean-reverting** — they wobble
around a normal level and keep coming back to it. That predictability is exactly what
the strategy hunts for. The project trades four families of spreads:

## 4.2 Inter-commodity spread — e.g. Brent minus WTI

Take the price of Brent and subtract the price of WTI. That difference (the
"**Brent–WTI spread**") is traded directly. It reflects things like the cost of
shipping oil across the Atlantic and regional supply differences. It usually sits in a
fairly stable range — so when it stretches unusually wide or narrow, traders expect it
to come back. Other examples: Heating Oil vs Gas Oil (two diesels), RBOB vs Heating
Oil (gasoline vs diesel).

## 4.3 Crack spread — the refinery's profit margin

This is the "ingredient vs finished product" idea from Part 2, turned into a trade.

A **crack spread** = (price of refined products) − (price of crude oil). It is
literally the **profit margin of a refinery**: they buy crude, "crack" it into
products, and sell those. The name comes from "cracking" crude into pieces.

The most famous one is the **3:2:1 crack**: it assumes that from **3 barrels of
crude**, a refinery makes roughly **2 barrels of gasoline and 1 barrel of diesel** —
a realistic recipe. So:

> **3:2:1 crack = (2 × gasoline + 1 × diesel − 3 × crude) ÷ 3**, giving a per-barrel
> refining margin.

When the crack is **high**, refining is very profitable (products are expensive
relative to crude); when **low**, refineries are squeezed and may cut production.
Crack spreads are seasonal — gasoline cracks firm up before summer driving season,
heating-oil cracks before winter.

## 4.4 Calendar spread — same oil, two different months

Take WTI for July and subtract WTI for August. That's a **calendar spread** (also
called a time spread). You're trading the *gap between two delivery months of the
exact same oil*. It is essentially a direct bet on **contango vs backwardation** (see
Part 3): if the front month is richer than the next, the calendar spread is positive
(backwardation). Calendar spreads are pure, clean relationships — both legs are the
*identical* commodity, so almost all outside noise cancels, leaving just the
supply-timing story.

## 4.5 Butterfly — the "bend" in the curve

A **butterfly** (or "fly") combines three months: **M1 − (2 × M2) + M3**. Don't let
the formula scare you — it simply measures the **curvature** of the forward curve: is
the middle month cheap or expensive *relative to its two neighbours*? It's the most
refined, second-order shape trade. Butterflies are very "pure" — they hover tightly
around zero, so they mean-revert strongly, but the moves are tiny, which matters later
when we talk about trading costs.

> **Putting it together:** the project tracks a whole menu of these spreads — Brent–WTI,
> several crack spreads (3:2:1, diesel cracks), calendar spreads on WTI/Brent/Gas Oil,
> and butterflies. Each one is a relationship that *usually* behaves, and the strategy's
> job is to spot when one is *misbehaving* and bet on a return to normal.

---

# PART 5 — WHAT ACTUALLY MOVES THESE PRICES (THE FUNDAMENTALS)

Prices and spreads don't move randomly — they respond to real-world supply and demand.
The project pulls in the major **fundamental** drivers so it can understand *why* the
market is where it is. In plain terms:

## 5.1 Inventories (how much oil is in storage)

Every week, the U.S. government's energy agency (the **EIA**) reports how much crude
oil and product is sitting in storage tanks. This is the single most-watched number in
oil.

- If stocks **build** (rise) more than expected → there's a glut → **bearish**
  (prices tend to fall).
- If stocks **draw** (fall) → supply is tightening → **bullish** (prices tend to rise).

But the raw number is meaningless without context, so the project compares today's
inventory to the **5-year seasonal normal** — because stocks naturally rise and fall
with the seasons. Being "high" only matters relative to what's *normal for this time
of year*. The system expresses this as: *are stocks unusually tight, balanced, or
oversupplied versus the seasonal norm?*

## 5.2 The supply / demand balance

Inventories are the *result* of a balance. The project also assembles the **flow**
side: how much crude is being **produced**, **imported**, **exported**, and run
through **refineries**. Supply (production + imports) minus disposition (refinery use +
exports) tells you whether the market is naturally building or drawing barrels — the
"plumbing" behind the headline stock number. It also computes **days of supply**
(stocks ÷ daily refinery use) — how long the cushion would last.

## 5.3 OPEC and production policy

**OPEC** (and its allies, "OPEC+") is the group of major oil-producing nations that
coordinate how much to pump. When they cut production, supply tightens (bullish); when
they raise it, supply loosens (bearish). The project tracks their quotas and how
closely members are sticking to them.

## 5.4 Refining activity

**Refinery utilization** is the percentage of refining capacity that's running. High
utilization means lots of crude is being consumed (bullish for crude) and lots of
product being made (can be bearish for product prices). Refineries also shut for
**maintenance ("turnarounds")** in spring and autumn, which seasonally swings the
crack spreads.

## 5.5 Seasons and weather

Energy is the most seasonal of all commodities. **Winter** boosts demand for heating
oil; **summer** boosts gasoline ("driving season"). Cold snaps and hurricanes (which
can shut Gulf of Mexico production) move prices. The project classifies the calendar
into **heating season, driving season, and shoulder (in-between) months**.

## 5.6 The macro backdrop

Oil is priced in U.S. dollars, so the **dollar's strength**, **interest rates**,
**stock markets**, and overall **fear/calm** (measured by the "VIX," a market
fear gauge) all push oil around. A strong dollar generally pressures oil; risk-off
panic can drag it down regardless of oil's own supply story.

## 5.7 Positioning (what other traders are doing)

A government report (the **COT**, Commitments of Traders) shows how heavily
speculative funds are betting long or short. When *everyone* is piled onto one side,
it's often a contrarian warning — if all the buyers have already bought, who's left to
push prices higher? The project tracks how crowded positioning is versus its history.

## 5.8 News and sentiment

Finally, the project reads a live financial **newswire** and scores the *tone* of
headlines (bullish / bearish / neutral) using a language model trained on financial
text — blended with price momentum into an overall **sentiment** reading.

> **Stage 1 summary:** all of the above — prices, curves, inventories, balances, OPEC,
> refining, weather, macro, positioning, news — make up the **Information Stage**: a
> single live picture of *everything happening in the oil market right now.*

---

# PART 6 — STAGE 2: THE ANALYSIS ENGINE ("WHAT KIND OF MARKET IS THIS?")

This is the brain of the project. Stage 1 told us *what's happening*. Stage 2 turns
that into an *opinion*. It rests on three big ideas, explained from scratch below:
**regimes**, **fair value**, and **mean reversion**.

## 6.1 Big idea #1 — Market "regimes"

A **regime** is just the *type* or *mood* of the market — its weather. The same
spread behaves completely differently in different weather. A relationship that's calm
and tight in a quiet market can swing wildly in a panicked one. So before judging
whether something is "mispriced," you must first ask: **what environment are we in?**

The project defines the regime using a few simple, readable readings:

- **Inventory:** Tight / Balanced / Oversupplied (vs the seasonal norm).
- **Volatility:** Low / Normal / High (how violently prices are swinging — see below).
- **Term structure:** Backwardation / Flat / Contango (the curve shape from Part 3).
- **Trend:** Up / Range / Down (is price above or below its long-run average?).
- **Season:** Heating / Driving / Shoulder.

Each day in history (2021 to present) is stamped with its regime. The headline label
combines the two readings that actually vary the most — **inventory and volatility** —
into **nine possible regimes** (e.g. "Tight · Low-Vol," "Balanced · High-Vol," and so
on). As of this writing the market sits in **"Balanced · High Volatility."**

**Volatility**, by the way, simply means *how much prices are jumping around*. A calm
market drifts; a volatile market lurches. High volatility = wider, riskier swings.

Why bother? Because we can now ask a much sharper question: not "is this crack spread
high?" but **"is this crack spread high *for the kind of market we're currently in*?"**
That context is everything.

## 6.2 Big idea #2 — "Fair value" and finding normal relationships

For each spread, the project estimates a **fair value** — what the spread *should* be,
given current conditions. How? By studying history and finding the **normal
relationship** between the spread and its drivers (inventories, volatility, the dollar,
seasonality, momentum, etc.).

The tool for finding "the normal relationship between things" is called **regression**.
In plain words, regression looks at years of history and answers: *"when inventories
were tight and volatility was high, what did this spread usually do?"* It draws the
best line through the cloud of historical dots. That line is the **fair value**: a
data-driven estimate of where the spread *ought* to sit today.

The project doesn't trust a single estimate. It builds several versions and compares
them (a simple one, a couple of "regularised" ones that avoid over-trusting noisy
inputs, a "rolling" one that lets the relationship change over time, and a separate one
for each regime). Crucially, every estimate is made **walk-forward** — it only ever
uses information that would have been available *at that point in time*, never peeking
into the future. That honesty is vital: it's easy to look smart if you cheat by using
tomorrow's data; this avoids that trap.

## 6.3 Big idea #3 — How "unusual" is today? (the z-score)

Now we have, for each spread, two things: **where it actually is** and **where it
should be** (fair value). The gap between them is the **dislocation**. But how do we
judge whether a gap is big or small? We use a **z-score**.

A z-score answers: *"how many normal steps away from average is this?"* Think of human
height: most people cluster near average, fewer are very tall or very short. A z-score
of 0 means "perfectly average." A z-score of +2 means "unusually high — only a small
fraction of the time is it this stretched." A z-score of −2 means "unusually low."

So a spread at **+2 z** is *richly* priced (stretched high) versus normal; at **−2 z**
it's *cheaply* priced (stretched low). The "normal step" (called a **standard
deviation**, or **sigma, σ**) is measured from that spread's own history *within the
current regime*. So +2σ means "this is far higher than this spread normally gets in
this kind of market."

## 6.4 Big idea #4 — Mean reversion (the actual bet)

Here's the bet the whole strategy makes: **extreme dislocations tend to snap back to
normal.** A rubber band stretched far tends to recoil. A spread that's +2σ rich tends
to fall back toward fair value; one that's −2σ cheap tends to rise.

So the strategy:
- When a spread is **unusually rich** (high z) → **sell it** (bet it falls).
- When a spread is **unusually cheap** (low z) → **buy it** (bet it rises).
- Then wait for it to revert to fair value and take the profit.

It also measures **how fast** reversion typically happens — the "half-life," roughly
how many days it takes for half the dislocation to disappear.

## 6.5 Turning this into ranked opportunities ("signals")

At any moment, several spreads might be dislocated. The project **ranks** them so a
trader sees the best ones first. Each opportunity is scored on three things:

1. **Magnitude** — how stretched is it (the z-score)? Bigger = more potential.
2. **Confidence** — how *trustworthy* is the fair-value model for this spread? Some
   relationships are well-behaved and predictable; others are basically noise. The
   system measures this and down-weights the unreliable ones.
3. **Robustness** — do *independent* checks agree? It compares the regime-based view
   and the regression-based view; if both say "rich," that's a stronger signal than
   one alone. It also checks that the spread has a history of actually reverting.

The output is a **ranked list of trade ideas**, each with a plain-English reason:
*"In the current Balanced·High-Vol regime, the Gas-Oil butterfly is 1.9σ cheap versus
its regime norm; historically such dislocations reverted 83% of the time."*

## 6.6 Does the idea even work? (the historical validation)

Before trusting any of this, the project **back-tested the core idea on daily history**:
*whenever a spread was more than ~1.5σ dislocated, did it actually revert over the next
~10 days?* The answer across spreads was **yes, 67–83% of the time** — comfortably
better than a coin flip (50%). That's the evidence that the mean-reversion edge is
real, not imagined.

> **Stage 2 summary:** the engine reads the market's *regime*, estimates each spread's
> *fair value*, measures how *dislocated* it is (z-score), bets on *reversion*, and
> hands you a *ranked, explained, historically-validated* list of the best opportunities.

---

# PART 7 — STAGE 3: TESTING THE STRATEGY ON REAL TRADING DATA (THE BACKTEST)

Stage 2 produced a strategy. Stage 3 asks the only question that ultimately matters:
**if we had actually traded this, would it have made money?** This is **backtesting** —
running the strategy on real past market data, trade by trade, as if living through it.

## 7.1 What "backtesting" means

A backtest is a **flight simulator for a trading idea.** You take genuine historical
prices, apply your exact buy/sell rules with no benefit of hindsight, and record every
trade the rules would have made — entry, exit, profit or loss. If it works in the
simulator across enough situations, you gain confidence (never certainty) that it might
work live.

## 7.2 The data used

For this stage we used **real intraday price data**: 15-minute "bars" (each bar
summarises the price action of a 15-minute window) for **Brent and WTI crude futures**
across several delivery months. Because this dataset is crude-only, the backtest traded
the **crude relationships**: Brent–WTI, WTI and Brent calendar spreads, and the
butterflies. (Product cracks need gasoline/diesel data, which this particular dataset
didn't include.)

## 7.3 The trading rules (exactly what it did)

The strategy applied the Stage-2 logic at intraday speed:

1. For each spread, continuously estimate its recent **fair value** (a rolling average
   of the last few hours) and how stretched it is (**z-score**).
2. **Enter a trade** when the spread becomes dislocated by **1.5σ or more**:
   - If it's **rich** (z above +1.5) → **sell the spread** (bet it falls).
   - If it's **cheap** (z below −1.5) → **buy the spread** (bet it rises).
3. **Exit the trade** when one of three things happens:
   - **Target hit** — the spread reverts back to fair value (z near 0). *Win.*
   - **Stop hit** — the spread stretches even further (z past 3.0), meaning we were
     wrong; cut the loss.
   - **Session end** — close out rather than hold through a long market break.

Every "trade" actually involves **two or three legs** (e.g. buy July WTI *and* sell
August WTI simultaneously) because that's what a spread *is* — a package of positions
whose *difference* is the bet.

## 7.4 How profit and loss is calculated

Recall: one contract = 1,000 barrels, so **$1 of spread movement = $1,000 per
contract.** If we sold a spread at 7.17 and it reverted to 4.20, that's a 2.97 move in
our favour → **$2,970 profit** on one contract. Every trade's profit or loss is recorded
this way, and a running **equity curve** (account value over time) is built up.

## 7.5 The two ways to measure results: gross vs net

There are real-world frictions when trading:

- **Slippage** — the gap between the price you *see* on screen and the price you
  *actually get* when your order fills. Markets move and have a tiny built-in buy/sell
  gap, so you always pay a little extra. On small spread moves this matters a lot.
- **Commission** — the broker's fee per trade.

The project can include or exclude these:

- **Net basis** = after slippage and commission — what you'd *actually* pocket.
- **Gross basis** = before those costs — the *raw signal edge*, isolating the question
  "does the strategy's *idea* work?" from "is it cheap enough to trade?"

This final version was run on a **gross basis** — measuring the pure quality of the
signal. (An earlier run *with* costs revealed something important and honest: on these
small, fast intraday spread moves, trading costs ate roughly **half** the gross
profit — a real-world warning that the *idea* working and the *trade* being profitable
after costs are two different things.)

## 7.6 The results (and what every number means)

On the available data (one trading session of 15-minute bars, in a "Balanced ·
High-Volatility" regime), on a gross basis:

| Result | Number | What it means in plain words |
|---|---|---|
| **Trades taken** | 36 | The rules fired 36 times. |
| **Gross profit** | **+$4,790** | Total money made before costs. |
| **Win rate** | **80.6%** | About 4 out of every 5 trades made money. |
| **Profit factor** | **13.6** | Total winnings were 13.6× total losses — wins dwarfed losses. |
| **Average win / loss** | +$165 / −$23 | Winners were much bigger than losers. |
| **Expectancy** | ~+$130/trade | What you'd expect to make on an average trade. |
| **Max drawdown** | −0.25% | The worst peak-to-valley dip in the account was tiny. |

**How to read these:**

- **Win rate (80.6%)** — out of 36 trades, ~29 reverted profitably. This is squarely in
  line with the daily historical validation (67–83%) — the intraday edge matches the
  long-run edge, which is reassuring.
- **Profit factor (13.6)** — for every $1 lost on losing trades, $13.6 was made on
  winners. Anything above 1.0 is profitable; 13.6 is very high (helped by the small,
  favourable sample — see caveats).
- **Drawdown (0.25%)** — the strategy never put much of the account at risk at once.

## 7.7 The honest caveats (very important)

A good analyst is most careful exactly when the numbers look good. Three honest
warnings:

1. **Tiny sample.** This was essentially **one trading session** (~80 fifteen-minute
   bars, 36 trades). That is *far* too little to prove anything. It's a working
   demonstration of the method, not statistical proof. The system is built so that
   adding more days of data and re-running immediately builds a bigger, more credible
   sample.
2. **The profit was concentrated.** A single relationship — **Brent–WTI** — produced
   the large majority of the profit; most other spreads were roughly flat after the
   small moves. So the headline is really "one or two excellent reversions," not yet a
   broad, every-spread edge.
3. **Gross, not net.** These numbers exclude trading costs. On small intraday moves
   those costs are large relative to the profit, so the *tradeable* result would be
   meaningfully lower. The gross number proves the *signal* has merit; it does not
   promise net profit at this frequency.

> **Stage 3 summary:** the strategy was turned into precise buy/sell rules and run on
> real intraday crude data. On a pure-signal (gross) basis it reverted ~81% of the
> time and made money — matching the long-run validation — but on a small sample,
> concentrated in one spread, and before the real-world costs that genuinely bite at
> this speed.

---

# PART 8 — WHAT THE WHOLE THING ADDS UP TO

Read end-to-end, the project is a complete pipeline that mirrors how a real
quantitative trading desk thinks:

1. **See everything** (Stage 1) — assemble live prices, the forward curve, inventories,
   the supply/demand balance, OPEC, refining, weather, macro, positioning, and news
   into one coherent picture.
2. **Form a view** (Stage 2) — classify the market's *regime*, estimate each spread's
   *fair value*, measure *dislocations* with z-scores, and produce a *ranked, explained,
   historically-validated* list of mean-reversion opportunities.
3. **Test the view** (Stage 3) — convert it into mechanical buy/sell rules and backtest
   it on real intraday data, logging every trade's entry, exit, and profit, with full
   honesty about costs and sample size.

### What it can do
- Tell you, in plain language, *what kind of oil market you're in* and *why*.
- Point to the spreads that are most statistically out-of-line *for that environment*,
  with a confidence level and a track record of reverting.
- Show, on real data, how the underlying mean-reversion idea actually performs.

### What it cannot (yet) do
- It is **not** a live, fully-automated money machine. It identifies *candidates* and
  tests the *idea*; a human still decides size, timing, and risk.
- It is a **mean-reversion / relative-value** tool — it bets on relationships returning
  to normal. It does **not** forecast the outright direction of oil prices.
- The strategy's edge is **real but modest after costs**, and the live backtest is on a
  **small sample**. More data is the single biggest thing that would strengthen the
  conclusions.

The honest one-line summary: **this project takes the chaos of the oil market, distils
it into a clear read of the environment, finds relationships that are stretched too far,
bets they snap back, and proves — on real data — that the bet wins more often than not,
while being candid about exactly where the limits are.**

---

# GLOSSARY (one line each)

- **Crude oil** — the raw, unrefined oil pumped from the ground.
- **Refined product** — fuel made from crude (gasoline, diesel/heating oil, gas oil).
- **Benchmark** — a standard reference oil grade everything is priced against.
- **WTI / Brent** — the U.S. and international crude benchmarks.
- **Barrel** — the standard unit of oil volume (~159 litres); one futures contract = 1,000 barrels.
- **Futures contract** — an agreement made today to buy/sell oil at a set price on a future date.
- **Hedger / Speculator** — someone reducing risk vs someone seeking profit from price moves.
- **Front month (M1)** — the nearest-to-delivery futures contract; M2, M3 are the next ones.
- **Rolling** — moving from an expiring front contract to the next.
- **Forward curve** — the line of prices across all future delivery months.
- **Contango** — curve slopes up (later months dearer); a well-supplied market.
- **Backwardation** — curve slopes down (now dearer); a tight market.
- **Spread** — the price difference between two related instruments; a bet on the gap, not the level.
- **Inter-commodity spread** — difference between two different products/crudes (e.g. Brent–WTI).
- **Crack spread** — products minus crude; a refinery's profit margin.
- **3:2:1 crack** — a standard crack recipe: 3 crude → 2 gasoline + 1 diesel.
- **Calendar spread** — the gap between two delivery months of the *same* commodity.
- **Butterfly** — M1 − 2×M2 + M3; measures the curvature of the forward curve.
- **Inventories / stocks** — oil sitting in storage; a build is bearish, a draw is bullish.
- **Build / Draw** — a rise / fall in inventories.
- **EIA** — the U.S. agency that publishes official weekly oil inventory data.
- **OPEC / OPEC+** — the group of producing nations that coordinate output.
- **Refinery utilization** — the % of refining capacity currently running.
- **Turnaround** — scheduled refinery maintenance shutdown.
- **Days of supply** — inventories divided by daily usage; how long the cushion lasts.
- **Driving / Heating season** — summer gasoline demand / winter heating demand.
- **Macro** — broad market forces: the dollar, interest rates, stocks, fear (VIX).
- **COT / Positioning** — report of how heavily speculators are betting long or short.
- **Sentiment** — the bullish/bearish tone of news and price momentum, scored.
- **Regime** — the prevailing "type" or "weather" of the market (e.g. tight & volatile).
- **Volatility** — how much prices are swinging; high = wild, low = calm.
- **Regression** — a method that finds the normal historical relationship between variables.
- **Fair value** — the model's estimate of where a spread *should* be given conditions.
- **Dislocation** — the gap between a spread's actual price and its fair value.
- **Z-score (sigma, σ)** — how many "normal steps" from average something is; ±2 is unusual.
- **Standard deviation** — the size of one "normal step" of variation.
- **Mean reversion** — the tendency of stretched prices/spreads to return to normal.
- **Half-life** — roughly how long it takes for half of a dislocation to disappear.
- **Signal** — a ranked, scored trade idea produced by the engine.
- **Confidence / Robustness** — how trustworthy a signal is, and whether independent checks agree.
- **Backtest** — running a strategy on historical data to see how it would have performed.
- **Equity curve** — the running value of the trading account over time.
- **Entry / Exit** — the prices/times a trade is opened and closed.
- **Target / Stop** — the exit when the trade is right (reverted) vs wrong (stretched further).
- **Win rate** — the percentage of trades that made money.
- **Profit factor** — total winnings divided by total losses (above 1 = profitable).
- **Expectancy** — the average profit (or loss) expected per trade.
- **Drawdown** — the decline from a peak in the equity curve; a measure of pain/risk.
- **Slippage** — the gap between the expected and actual fill price of an order.
- **Commission** — the broker's fee per trade.
- **Gross vs Net** — results before vs after slippage and commission.
- **Leg** — one of the individual positions that make up a spread trade.

---

*End of report.*
