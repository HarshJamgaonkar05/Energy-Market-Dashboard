# VOLTAIRE Terminal — Presentation Script

> A spoken walkthrough of the dashboard, written for an audience that knows **nothing**
> about energy markets. Read it top to bottom; every term is explained the first time it
> appears. Stage directions are in *(italics)*. The numbers quoted match what's on screen.

---

## 0. The one-sentence pitch

> "What you're looking at is a **trading terminal for the energy markets** — a single screen
> that pulls together the price of oil and fuel, plus every major force that pushes those
> prices up or down, so a trader can make a decision in seconds instead of opening twenty
> different websites."

Think of it as a **cockpit dashboard for someone who buys and sells oil for a living**.
A pilot doesn't read twenty separate gauges in twenty separate rooms — they get altitude,
speed, fuel, and weather on one panel. This does the same thing for the oil market.

It's modelled on the tools the professionals actually use — **Bloomberg Terminal, Refinitiv,
Kpler, Vortexa, TradingView** — hence the dark screen, dense numbers, and the green-up /
red-down colour code you'll see everywhere.

---

## 1. The mental model you need before anything else

*(Pause here. This single idea makes the whole dashboard make sense.)*

The oil business is a **factory pipeline**:

```
   CRUDE OIL  ──►  REFINERY  ──►  REFINED PRODUCTS
  (raw input)                    (the stuff people actually burn)
```

1. **Crude oil** comes out of the ground. It's the raw material. You can't put it in your car.
2. A **refinery** cooks it and splits it into useful fuels.
3. Those fuels — **gasoline, diesel/heating oil, jet fuel** — are the **products** people buy.

This dashboard tracks **both ends of that pipeline**, because a trader makes money on the
*gap* between them. Hold that thought — it comes back when we hit "crack spreads."

### The five things this terminal watches

> "Everything on this screen revolves around just five tradable instruments — two raw
> crudes and three finished fuels."

| Symbol | What it is | Price shown | Plain English |
|--------|-----------|-------------|---------------|
| **BRENT** | Brent Crude | **$82.47 / barrel** | The *global* benchmark crude oil (from the North Sea). When the news says "oil hit $80," they usually mean Brent. |
| **WTI** | West Texas Intermediate | **$78.92 / barrel** | The *US* benchmark crude. Priced in Cushing, Oklahoma. |
| **HO** | Heating Oil / ULSD | **$2.512 / gallon** | A *distillate* — basically diesel and home heating fuel. |
| **RBOB** | RBOB Gasoline | **$2.342 / gallon** | The wholesale gasoline (petrol) you eventually pump into a car. |
| **GASOIL** | ICE Gas Oil | **$742.50 / tonne** | Europe's diesel benchmark — the European cousin of heating oil. |

Two crudes (the raw input), three products (the output). That's the whole universe.

> **Watch the units — this trips people up.** Crude is priced in **dollars per barrel**.
> Gasoline and heating oil are in **dollars per gallon**. European gas oil is in **dollars
> per metric tonne**. Behind the scenes the terminal converts everything to *dollars per
> barrel* (1 barrel = 42 gallons; 1 tonne of gas oil ≈ 7.45 barrels) so the five can be
> compared apples-to-apples.

### How to read the colours (say this once, it applies everywhere)

- **Green / a `+` number = price went UP.**
- **Red / a `−` number = price went DOWN.**
- The market also has slang for direction: **"bullish" = expecting prices to rise**,
  **"bearish" = expecting prices to fall.** You'll hear me use those.

*(Point at the top strip of five tiles.)* These five tiles are the heartbeat. Right now
gasoline (RBOB) and European gas oil are up strongly (+2.9%, +3.2%), heating oil is the lone
loser (−1.2%). The little zig-zag line on each tile is a **sparkline** — a mini 30-point price
history so you can see the trend at a glance without needing a full chart.

---

## 2. The furniture that's always on screen

Before we go page by page, two things never leave:

- **The scrolling ticker** *(top, constantly moving):* the live price and % change of all five
  instruments **plus** the headline spreads (BRENT-WTI, the 3:2:1 crack, etc.). It's the
  "stock ticker" you've seen scroll across the bottom of news channels.
- **The left sidebar** is the navigation. Five sections:
  **Dashboard, Analytics, Market Drivers, Inventories, News.** The little green "Live · 12ms"
  light at the bottom is mimicking a real data feed's connection status. We'll take the five
  pages in order.

---

## 3. Page 1 — DASHBOARD (the overview / "everything at a glance")

> "This is the home screen — the trader's morning coffee view. One look tells them where
> prices are, what's moving, and what they need to worry about today."

Walk through the blocks:

- **The five price tiles** (top) — covered above. The market's pulse.

- **Price chart (large, left):** all five instruments plotted together over ~90 days, each
  one **rebased to 100 at the start.** *Why rebase to 100?* Because the raw prices are on wildly
  different scales ($82 crude vs $2.50 gasoline vs $742 gas oil) — you couldn't see them on one
  axis. Rebasing to 100 turns every line into "**percentage moved since day one**," so you can
  compare *who outperformed whom* on a single chart.

- **Forward Curve (small chart):** the price of oil for delivery this month, next month, the
  month after… out to a year. *(Full explanation on the Analytics page — for now just say it
  shows "the market's expectation of future prices.")*

- **Correlation heatmap:** a grid showing how tightly the five move together. Bright = they
  move in lockstep, dim = they drift apart. *(Detail on Analytics.)*

- **Market Movers:** today's biggest winners and losers, ranked, with **volume** (how many
  contracts traded — a proxy for how much attention/conviction is behind the move). Gas oil
  +3.2% on 184K lots is leading; the Brent-WTI spread is up 11.6%.

- **News feed (right rail):** the latest market-moving headlines. *(Detail on the News page.)*

- **Sentiment panel:** a "mood ring" for each product group — a **composite index from 0–100**
  where 50 is neutral. Above 50 leans bullish (green), below leans bearish (red). Right now:
  **Gasoline 71 (very bullish), Crude 64, Distillates 58, Gas Oil 46 (neutral).** It's a quick
  read on which way the crowd is leaning.

- **Economic Calendar:** scheduled data releases coming today with their times. *(Detail on
  Market Drivers.)*

- **Fundamentals strip (bottom):** snapshot tiles for **Inventories, Shipping, and Weather** —
  the three big "supply & demand" forces, each with its own full section later.

> "So the dashboard answers four questions in one screen: *Where are prices? What's moving?
> What's the mood? What's coming up today?*"

---

## 4. Page 2 — ANALYTICS (where traders actually look for an edge)

This page is three professional tools stacked. This is the most "finance-heavy" page, so go slow.

### 4a. Crack Spreads — "the refinery's profit margin"

> "Remember the factory pipeline: crude in, products out. The **crack spread** is the
> **profit a refinery makes** from that conversion. It's literally the gap between what the
> finished fuels sell for and what the raw crude cost."

The name comes from "**cracking**" crude into products in the refinery.

- A simple crack = one product minus one crude (e.g. *RBOB gasoline price − WTI crude price*).
- The headline one is the **3:2:1 crack**, and the recipe is the whole point:

  > "Take **3 barrels of crude oil**, refine them, and you roughly get **2 barrels of
  > gasoline + 1 barrel of heating oil**. The 3:2:1 crack is the dollar profit on that
  > 3-barrel batch. Right now it's about **$21.82 a barrel.**"

**Why a trader cares:** the crack is the refinery's incentive. A **wide/rising crack** means
refining is very profitable → refineries run harder → they buy *more crude* and make *more
product*. A **narrow crack** means refineries may cut runs. So the crack is both a profit
signal and a demand signal.

*(On screen:)* pick any crack on the left list, and the chart shows its 60-day history with the
**60-day low / average / high** underneath — so you can instantly see if today's margin is
cheap or expensive versus its own recent range.

### 4b. Futures Spreads — the forward curve, and "contango vs backwardation"

> "Oil mostly trades as **futures** — contracts to deliver oil on a set future date. There's a
> price for delivery next month (M1), the month after (M2), all the way out. String those
> prices together and you get the **forward curve** — the market's published opinion of the
> future."

The single most important thing the curve tells you is its **shape**, and there are two words:

- **Backwardation** *(curve slopes DOWN — near-term costs more than later):*
  > "This means the market wants oil **right now** and is paying a premium for it — a sign of
  > **tight supply**. Traders read backwardation as **bullish.**"

- **Contango** *(curve slopes UP — later months cost more):*
  > "This means there's **plenty of oil today**, so today's price is cheap relative to the
  > future. Often a sign of **oversupply.** In extreme cases traders buy cheap oil now, store
  > it, and sell the expensive future contract."

*(On screen:)* the page labels the current structure for you, e.g. *"Brent: Backwardation."*

Two more tables on this page:

- **Calendar spreads** (M1–M2, M1–M6, M1–M12): the *difference* between two delivery months on
  the **same** commodity. It's just a precise, tradable way to measure how steep that
  contango/backwardation slope is.
- **Inter-commodity spreads**: the gap between *two different* instruments — e.g.
  **Brent − WTI** (the "crude arb," about **$3.55**), or gasoline vs heating oil. These are how
  traders bet on *relationships* rather than outright price direction.

> "The takeaway: you don't have to bet 'oil goes up.' You can bet that *this* oil beats *that*
> oil, or that *now* beats *later*. Spreads are how the pros express a precise view with less risk."

### 4c. Correlation Matrix — "what moves together"

> "This grid shows, for every pair of our five instruments, **how tightly they move together**
> over the last 30 days. The scale runs 0 to 1: **1.0 = they move in perfect lockstep,**
> lower = they go their own way."

Why it matters: if you're trying to *hedge* (offset risk) or build a spread trade, you need to
know what's a good substitute for what. The read-out on this page summarises it:

- **The two crudes (Brent & WTI) are ~0.97** — nearly identical twins.
- **Heating Oil & Gas Oil are ~0.95** — both are diesel-type distillates, so they track tightly.
- **RBOB gasoline is the loosest** — it's a lighter, *seasonal* product (driving-season demand),
  so it does its own thing.

---

## 5. Page 3 — MARKET DRIVERS (the *why* behind the prices)

> "The first two pages told us **what** prices are doing. This page is **why.** These are the
> real-world fundamentals that push oil around. Four sections."

### 5a. Macro & Rates — "the weather system the whole market sits in"

Four tiles: **DXY (US Dollar Index, 104.21), S&P 500 (5,284), VIX (14.32), and the 10-Year
Treasury yield (4.22%).** None of these are oil — they're the broader economy. Why are they here?

- **The Dollar (DXY):** oil is priced in dollars worldwide. A **stronger dollar usually pushes
  oil prices down** (oil gets more expensive for everyone outside the US), and vice-versa.
- **S&P 500 (stocks):** a proxy for economic health and risk appetite. Booming economy → more
  energy demand.
- **VIX ("the fear gauge"):** measures expected stock-market volatility. High VIX = investors
  are scared, which tends to drag risky assets (including oil) down.
- **10-Year yield:** the cost of money / the macro backdrop. Rising yields can signal a cooling
  economy and a firmer dollar — generally a headwind for oil.

> "So this section is the macro mood music. Oil doesn't trade in a vacuum; if the dollar
> spikes and stocks crater, even bullish oil news can get drowned out."

### 5b. Oil Supply Drivers — "how much oil is being made"

This is the supply side of supply-and-demand. Four pieces:

- **OPEC+ Quota Compliance** *(the table).* **OPEC+** is the cartel of big oil-producing
  nations (Saudi Arabia, Russia, Iraq, UAE…) that agree to **production quotas** — caps on how
  much each pumps — to manage the global price.
  > "Compliance asks: *is each member actually sticking to its limit?* **Over 100% (green) means
  > they're producing at or below their cap — disciplined, which supports prices. Under 100%
  > (red) means they're cheating — pumping too much — which is bearish.**"

  *(On screen:)* Saudi Arabia is compliant; **Russia, Iraq, and Kazakhstan are over-producing**
  (red) — exactly the kind of "cartel discipline is slipping" story that pressures prices.

- **US Oil Rigs (Baker Hughes): 497.** The number of active drilling rigs in the US. It's a
  **leading indicator of future supply** — more rigs today means more US shale oil in a few
  months.

- **US Crude Stocks: 429.1 MMbbl** (million barrels) — how much crude is sitting in US storage.

- **OPEC+ Spare Capacity: 4.21 mb/d** (million barrels per day) — the "shock absorber." It's how
  much *extra* oil OPEC could pump quickly if there were a supply crisis. **Low spare capacity =
  fragile market = prices jumpy.**

- **Weekly Builds & Draws chart:** every week the US reports how its crude inventory changed.
  > "A **'draw' (inventory fell, shown green) is bullish** — it means demand outran supply.
  > A **'build' (inventory rose, shown red) is bearish.** The bars are the official EIA figure;
  > the dashed line is the earlier industry (API) estimate. Latest week drew **4.2 million
  > barrels** — a bullish print."

### 5c. Freight & Shipping — "the cost to physically move the oil"

> "Oil is useless in the ground in Saudi Arabia if you need it in China. Someone has to ship
> it — and shipping costs feed straight into delivered prices."

- **Tanker rate tiles (VLCC, Suezmax, Aframax)**: those are the three sizes of oil tanker,
  biggest to smaller. The rate is the **hire cost in dollars per day** — e.g. a **VLCC** (Very
  Large Crude Carrier, ~2 million barrels) on the Arab Gulf→China route runs **$38,420/day.**
  Codes like *TD3C* are the standard industry route names. **BDI (Baltic Dry, 1,842)** is the
  broad benchmark for dry-bulk shipping — a general global-trade health gauge.
- **Port congestion (Singapore, Rotterdam, Fujairah, Houston, Suez, Shanghai):** how backed-up
  the key oil ports are — vessel counts and delay in days. **Suez at 92% / 5.8-day delay** is a
  bottleneck; congestion = oil stuck at sea = effectively tighter supply.
- **Route spreads ($/bbl):** the freight cost difference between routes — relevant to whether
  it's profitable to ship oil from A to B (the "arbitrage").

### 5d. Weather & Demand — "how much fuel people need to burn"

> "Weather is demand. Cold winters burn heating oil; hot summers burn fuel for air-con power.
> So traders watch the forecast like farmers do."

- **HDD — Heating Degree Days (US 142, EU 124):** a number that measures **how cold it is
  versus normal.** Higher HDD = colder = **more heating fuel demand = bullish for distillates
  and gas.**
- **CDD — Cooling Degree Days (Asia 38):** the mirror image — measures heat, i.e. air-conditioning
  (power) demand.
- **ENSO / El Niño Index (1.42):** a climate pattern that shifts global temperatures a season
  ahead — traders use it to anticipate demand.
- **Temperature forecast vs normal chart** and a **Storm Tracker** (Polar Vortex, hurricanes):
  storms both spike demand *and* can knock out Gulf Coast production and refineries — a
  double-edged supply/demand shock.

---

## 6. Page 4 — INVENTORIES ("how full are the storage tanks?")

> "Inventory is the market's fuel gauge. **Low and falling stocks = tight market = bullish.
> High and rising = glut = bearish.** Simple as that."

- **Top tiles:**
  - **US Crude Total: 429.1 MMbbl** — the headline storage number.
  - **Cushing, OK: 24.6 MMbbl** — *the* delivery point for WTI futures. When Cushing drains,
    WTI gets jumpy, so traders watch this one specific tank farm closely.
  - **SPR — Strategic Petroleum Reserve: 369.8 MMbbl** — the US government's emergency oil
    stash, released only in a crisis.
  - **Gasoline: 247.2 MMbbl** — finished-product storage.

- **52-week stocks vs 5-year average chart:** the gold line is current inventory; the shaded
  band is the **5-year normal.** *Sitting below the band = tighter than usual = supportive of
  prices.* This "vs the 5-year average" comparison is exactly how the EIA and traders frame it.

- **Refinery Utilization: 91.2%:** how hard US refineries are running as a % of capacity. High
  utilization = they're processing lots of crude (drawing it down) and pumping out product.

- **PADD breakdown:** the US is split into five petroleum districts called **PADDs** —
  **PADD 1 = East Coast, 2 = Midwest, 3 = Gulf Coast (by far the biggest refining hub),
  4 = Rockies, 5 = West Coast.** Lets you see *where* the build/draw is happening.

- **Global Crude Storage:** storage fullness around the world — **OECD** (developed economies),
  **China's reserve, ARA** (the Amsterdam–Rotterdam–Antwerp hub, Europe's storage heart),
  and **"Floating"** (oil sitting in tankers at sea — a sign of glut when it rises).

---

## 7. Page 5 — NEWS ("the headlines that move the tape")

> "Prices react to news in seconds. This is the trader's filtered wire — only energy-relevant
> headlines, time-stamped, colour-coded by how big a deal each one is."

- Each item shows a **time, a source** (Reuters, Bloomberg, Platts, Argus, the EIA, etc. — these
  are the real news/data agencies of the oil world), a **severity** (high/medium/low), and a
  **tag** so you can filter: **OPEC, GEOPOLITICS, FREIGHT, STOCKS, PRODUCTS, MACRO.**
- Notice how the headlines **connect to every other page**: *"OPEC+ signals production cut"*
  (the Supply Drivers page), *"Strait of Hormuz tensions"* and *"Red Sea transit drops 38%"*
  (Freight), *"crude inventories drew 4.2 MMbbl"* (Inventories), *"Fed minutes… dollar
  strengthens"* (Macro). The news is the *narrative* tying all the numbers together.
- The **Economic Calendar** (also shown on Market Drivers) lists **scheduled** releases — the
  big pre-known events like **US Crude Stocks, EIA Distillate data, and FOMC minutes** — with a
  **forecast vs the previous reading**, so traders know *exactly when* the market might lurch and
  can be positioned for it.

---

## 8. The closing line

> "So that's VOLTAIRE Terminal. Five instruments at the core — two crudes, three fuels. Then
> four lenses on top of them: **Analytics** (the profit margins and spreads traders trade),
> **Market Drivers** (the macro, supply, shipping, and weather that move prices), **Inventories**
> (the supply gauge), and **News** (the story behind the moves). Put together, it takes someone
> from *'I have no idea what oil is doing'* to *'I can see exactly what's moving, why, and what
> to watch next' — all on one screen."*

---

### Appendix — cheat-sheet of every term, in plain English

| Term | One-line meaning |
|------|------------------|
| **Crude oil** | Raw oil from the ground; refined into fuels. |
| **Brent / WTI** | The global / US benchmark crude prices. |
| **Product / distillate** | Refined fuel — gasoline, diesel, heating oil, jet. |
| **RBOB** | Wholesale gasoline. **Heating Oil / Gas Oil** | Diesel-type fuels (US / Europe). |
| **Barrel (bbl)** | Standard oil volume = 42 US gallons. |
| **Bullish / Bearish** | Expecting prices up / down. |
| **Spread** | The price gap between two things. |
| **Crack spread** | A refinery's profit margin (products − crude). |
| **3:2:1 crack** | The standard margin recipe: 3 crude → 2 gasoline + 1 heating oil. |
| **Futures** | A contract to deliver oil on a future date. |
| **Forward curve** | The chain of futures prices, month by month. |
| **Contango** | Future prices > today → oversupply signal. |
| **Backwardation** | Today > future → tight-supply / bullish signal. |
| **Calendar spread** | Gap between two delivery months of the same commodity. |
| **Correlation** | How tightly two prices move together (0 to 1). |
| **OPEC+** | The cartel of oil producers that sets output quotas. |
| **Compliance** | Whether members are honouring their production cap. |
| **Rig count** | Active drilling rigs — a clue to future supply. |
| **Build / Draw** | Inventory rose (bearish) / fell (bullish). |
| **Spare capacity** | Extra oil OPEC could pump in a crisis. |
| **Inventory / stocks** | Oil sitting in storage; the supply gauge. |
| **Cushing** | The Oklahoma tank hub where WTI is delivered. |
| **SPR** | US government emergency oil reserve. |
| **PADD** | One of the 5 US regional petroleum districts. |
| **Refinery utilization** | How hard refineries are running (% of capacity). |
| **Tanker rate (VLCC/Suezmax/Aframax)** | Daily cost to ship crude by sea. |
| **HDD / CDD** | Heating / cooling demand vs normal temperatures. |
| **DXY** | US Dollar Index — strong dollar usually weighs on oil. |
| **VIX** | The stock market's "fear gauge." |
| **EIA / API** | Official / industry sources for US oil inventory data. |
