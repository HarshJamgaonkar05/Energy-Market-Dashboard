# Research Brief: A Framework to Assess the Market Impact of the EIA Weekly Crude Inventory Release

*Prepared as the source material for a plain-English PDF and a Jupyter notebook. Every claim below has been through a research pass and an adversarial fact-check; where the fact-checker corrected a figure, the corrected version is used and the original is flagged. Claims that could not be independently confirmed are marked **[unverified]** or **[single-source]**.*

*Context date: 24 June 2026.*

---

## The one-sentence idea

The EIA weekly crude number rarely moves oil by itself. What moves the market is the **surprise** (actual minus what the market expected), and even that only matters **when nothing bigger is happening**. A good framework therefore does two things at once: it measures the surprise *in seasonal context*, and it weights that surprise *by the regime* (quiet market vs. OPEC/geopolitical/macro shock).

---

## 1. How the EIA release works (mechanics and timing)

The **Weekly Petroleum Status Report (WPSR)** from the U.S. Energy Information Administration is the official government snapshot of the U.S. oil market. Its mechanics are deliberately predictable, which is exactly why traders build their week around it.

**When it comes out**
- In a normal week, the headline files (`wpsrsummary.pdf`, `overview.pdf`, and Tables 1–14 in CSV/XLS) post **after 10:30 a.m. Eastern Time on Wednesday**. The remaining PDF/HTML files follow **after 1:00 p.m. ET**.
- When a federal holiday falls in or near the reporting week (Memorial Day, July 4th, Labor Day, Thanksgiving, Christmas, New Year), the release **slips one business day, normally to Thursday** (New Year typically ~11:00 a.m.; most others ~12:00 p.m. Thursday).
- **Christmas week is the documented exception** that can slip further — to the following **Monday** (which is where the ~5:00 p.m. figure some sources quote comes from). Do not read "12:00 p.m.–5:00 p.m." as a single week's window; it conflates a normal Thursday holiday release with the Christmas-Monday case.

**What week the data describe (the lag)**
- The report covers the **week ending the prior Friday**, with the data cut off **as of 7:00 a.m. that Friday**. EIA labels every week by its Friday date (e.g., 06/12/26).
- So a Wednesday print is roughly **5 days behind** its most recent data point — timely, but still backward-looking.

**How fast it hits the wire**
- For these market-sensitive releases, EIA's dedicated **information-release server, `ir.eia.gov`, carries the numbers to-the-second at 10:30 a.m.** EIA explicitly recommends it for fastest access.
- The **EIA Open Data v2 API** updates continuously, but for the WPSR (and the weekly natural gas report) the data appear in the API **within about two hours** of the 10:30 release — *not* instantly. If you are building anything latency-sensitive, pull from `ir.eia.gov`, not the API.

**How reliable the numbers are**
- Weekly figures are **preliminary estimates**. EIA surveys roughly **90% of the industry and estimates the rest**.
- Several items — **especially crude production** — get re-benchmarked against the more accurate, survey-based monthly **Petroleum Supply Monthly**, and production can be re-anchored during the monthly **Short-Term Energy Outlook (STEO)** week. (A documented example re-benchmark was about +88,000 bbl/d, ~0.64%.) **The monthly data are the authoritative benchmark; the weekly is the fast, noisy proxy.**

**What series the report publishes (all by PAD District)**
Crude oil ex-SPR (commercial) stocks · Cushing, OK stocks · total motor gasoline · distillate fuel oil · refinery utilization (% operable capacity) and crude inputs/runs · domestic crude production · crude imports · crude exports · SPR stocks.

---

## 2. The surprise-vs-consensus principle, and how to proxy consensus

**The core principle:** markets price in expectations ahead of time, so what moves price on Wednesday is the **deviation of the actual number from consensus**, not the raw build or draw. A draw can send oil *down* if the market expected an even bigger draw; a build can send oil *up* if it expected a bigger build.

- A common market rule of thumb is that a **surprise of more than ~3 million barrels** versus expectations is enough to flip short-term WTI bias. Treat this as **illustrative, not a hard, validated rule** — it comes from explainer sources, not a quantitative study. **[unverified threshold]**
- A clean, fact-checked example of the surprise driving price in a quiet market: on **30 October 2019**, EIA reported a crude **build of 5.7 million barrels** against expectations of only **~494,000** — a large *bearish* surprise — and **WTI fell 88 cents (−1.6%) to $54.18**. (Note: an earlier draft of this research had this episode reversed as a bullish draw and a +2.4% rally; that was wrong and has been corrected — the surprise was a big build and the move was down.)

**How to proxy consensus (you need an expectation to measure a surprise):**

1. **The API (American Petroleum Institute) preview — the closest, fastest read.**
   - The API publishes its private **Weekly Statistical Bulletin (WSB)** on **Tuesday ~4:30 p.m. ET** (after the oil pit close), about **18 hours before EIA**. If Monday is a federal holiday it shifts to Wednesday.
   - It is a **voluntary survey**, available **only to paid subscribers** via **LSEG and ICE**. It covers crude, gasoline, jet, distillate and residual fuel — products making up **>90% of refinery output** — plus imports and refinery runs.
   - The two reports are **directionally aligned ~80% of the time** (StoneX). API's own figure: in **Q1 2025**, API and EIA crude/gasoline/distillate stocks were **within 1% of each other ~100% of the time** — but that is **API's self-reported, single-quarter** statistic, so treat it as a recent-period observation, not a long-run guarantee.
   - **Key distinction:** EIA's survey is **mandatory and enforced by law** (civil and criminal penalties for false reporting); API's is **voluntary**. That is why most traders weight EIA more heavily and use API only as a front-runner. A large API surprise often moves price Tuesday evening, *before* the EIA print.

2. **Polled analyst consensus** (e.g., wire-service surveys of bank/broker estimates) — the formal "expected" number quoted in press coverage. This is what "vs. expected" headlines compare against.

3. **The five-year seasonal band** (see Section 4) — a baseline expectation for *direction and magnitude* given the calendar week, used to judge whether even an "in-line" print is really bullish or bearish.

**Practical takeaway for the framework:** compute the surprise as `actual − consensus`, and have at least two consensus proxies (the API preview and a polled analyst median) so you can both *anticipate* the EIA print and *measure* the residual surprise it delivers.

---

## 3. Historical episodes — when inventories moved the market, and when they didn't

The record from 2018–2026 shows three regimes. **Inventories are high-signal only in the first.**

| Date | Event | What inventories did | Price reaction | Lesson for the framework |
|---|---|---|---|---|
| **3 Oct – late Dec 2018** | Q4 2018 oil crash — macro growth fears + record U.S. shale + OPEC+ pact breakdown | Crude was *building* on record production, reinforcing the bearish tone, but was **not the catalyst** | WTI **−40%**, from $76.40 (3 Oct) to annual lows ~$43 on 24 Dec (Brent ~$50) | In a multi-week macro/supply regime shift, weekly stocks are **confirming noise**. Down-weight surprises. |
| **30 Oct 2019** | A quiet, range-bound market; the report *was* the news | **Build of 5.7 Mbbl vs. ~0.5 Mbbl expected** — a large *bearish* surprise | **WTI −1.6% to $54.18**; Brent ~$60.21 | The textbook high-signal case: a large surprise against consensus in a quiet market moves price, in the **direction of the surprise**. |
| **9 Mar 2020** | Saudi–Russia price war; OPEC+ talks collapsed, Saudi cut official selling prices and signaled a surge | **Irrelevant that day** — a deliberate supply-policy rupture | Oil's **worst day since 1991**: intraday as much as ~30% down; WTI **settled −24.6% at $31.13**, Brent −24.1% at $34.36 | **OPEC supply-policy shocks are override events.** They move price an order of magnitude more than any print. |
| **20 Apr 2020** | Negative WTI — COVID demand collapse, no storage left | **Cushing filling fast: 76% of working capacity (~60 of 76 Mbbl) as of 17 Apr**; refinery runs −24% YoY to 12.8 Mb/d | Front-month WTI traded as low as roughly **−$37 to −$40.32/bbl** — first time ever below zero | **Storage capacity (esp. Cushing) is a non-linear tail risk.** As utilization nears physical limits, inventories *become the entire price*. Build a capacity-proximity trigger. |
| **7 Mar 2022** | Russia invades Ukraine; threat to remove a top-3 exporter | A **backdrop**, not the trigger — but **eight straight quarters of falling global stocks** left no cushion | **Brent $139.13** (highest since July 2008); WTI ~$130.50 (some sources cite up to $133.46); biggest weekly gain on record | Geopolitical supply-threat shocks override weekly data, **but pre-existing thin inventories amplify the move**. Pair the geopolitical override with an inventory-buffer gauge. |
| **31 Mar 2022** | Largest-ever SPR release announced | A **deliberate government inventory intervention**: 180 Mbbl over 6 months (~1 Mb/d) + ~60 Mbbl from IEA partners | Helped drive a steady decline from the June peak to Brent ~$75 by 8 Dec 2022; Treasury estimated coordinated releases cut gasoline **~17–42¢/gal** (point est. ~38¢) | **Separate policy-driven flow interventions (SPR) from organic weekly stock changes.** SPR is a sustained, weeks-to-months force, not a one-week surprise. |
| **2–3 Apr 2023** | Surprise OPEC+ voluntary cut of ~1.16 Mb/d, announced over a weekend | Weekly U.S. data was **secondary**; market had been near 15-month lows on banking-crisis demand fears | Gapped up overnight: **WTI +5.48% to ~$79.83, Brent +5.31% to ~$84.13** (CNN) | A scheduled inventory print can be **fully overridden** by an unscheduled OPEC+ surprise. Flag OPEC-meeting windows as low-inventory-weight conditions. |

**The synthesis:** weight inventory surprises **by regime**. They are high-signal in **quiet, supply-driven, well-supplied** markets; low-signal when a **supply-policy (OPEC), geopolitical, or macro** shock is active; and the storage-capacity tail (Cushing near full) overrides everything.

---

## 4. Seasonality of crude stocks

Stock levels mean almost nothing without seasonal context. U.S. commercial crude follows a **refinery-driven annual rhythm**:

- **Builds Feb–May** — spring refinery maintenance (turnarounds) reduces crude demand while runs are low.
- **Draws Jun–Aug** — summer driving season; refineries run hard and pull crude.
- **Builds Sep–Nov** — fall maintenance season.
- **Sharp draw in December** — see the tax effect below.
- **Peak: April–May. Trough: late summer.**

**The drivers, with verified figures:**

- **Refinery turnarounds cluster in Q1 and the fall (peaking Feb–March)**, precisely when total U.S. petroleum demand is at its seasonal lows — so crude backs up and builds. In a bad outage year, Gulf Coast (PADD 3) gasoline output fell anywhere from **8.2% to 33.0%** versus a good year. *(Note: that range is a cross-refinery best-year-vs-worst-year comparison, not a routine annual seasonal cut.)*
- **Refinery utilization peaks late spring through summer, most often Jun–Aug** (it was **~95.3% for the week ending 5 June 2026**). The driving season runs **Memorial Day to Labor Day**. *(Caution: an earlier draft claimed utilization "peaked Jun–Aug every year since 2003" — that is an overstatement; 2025 reportedly peaked in May. The summer-peak pattern is solid; the absolute window is not.)*
- **The December Gulf Coast draw is a tax artifact.** Parts of **Texas and Louisiana levy ad-valorem ("according to value") taxes on crude inventories held at year-end (~Dec 31)**, so firms cut imports, raise runs, and ship crude out before the assessment; LIFO accounting and rising prices add to the incentive. The effect is large and remarkably consistent: **Gulf Coast stocks fell in 30 of 31 Decembers from 1981–2011, averaging a decline of nearly 8 million barrels**, and preliminary **December 2012 showed a draw of more than 12.5 million barrels**. Many of the largest single-month inventory declines on record happen in December.

**How to use seasonality (this is the heart of the framework's context layer):**
- Compare the level to the **five-year average for that exact calendar week** (EIA publishes the min/max/average band in the WPSR). Example: **426.5 million barrels** for the week ending 5 June 2026 read as **~5% below the five-year average** — a bullish read for that time of year.
- **The same absolute level is bullish in August and bearish in April.** And a *build* can be **bullish** if it is smaller than the seasonal norm, while a *draw* can be **bearish** if it is smaller than normal. Always judge the print against the seasonal expectation, then judge the surprise against consensus on top of that.

---

## 5. Cushing / PADD / WTI mechanics — why the *composition* of a build matters

A national headline number hides the only number that sometimes sets the WTI price: **where** the crude actually is.

**Cushing, Oklahoma is the physical delivery point for the NYMEX WTI contract.** It has roughly **76 million barrels of working storage, about 13% of total U.S. capacity.** Because it is the delivery hub, **Cushing stocks drive the front of the WTI curve**:
- **Contango** (later months priced higher than the front) rewards storing barrels, so crude flows *into* Cushing.
- **Backwardation** (front priced higher) penalizes storage, so crude flows *out*.
- When Cushing fills toward its physical limit, the marginal barrel has nowhere to go and the front-month price can detach from everything else — this is exactly the mechanism behind **negative WTI on 20 April 2020** (Cushing at 76% and rising; see Section 3).

**PADD structure** — the U.S. is split into five Petroleum Administration for Defense Districts, and EIA reports stocks by district:
- **PADD 1** East Coast · **PADD 2** Midwest (contains Cushing) · **PADD 3** Gulf Coast (the refining/export heartland and the source of the December tax draw) · **PADD 4** Rocky Mountain · **PADD 5** West Coast.

**Why composition matters more than the headline:**
- A **national build concentrated at Cushing** is far more bearish for *WTI specifically* than the same build spread across coastal PADDs, because it directly pressures the delivery point and the front-month contract.
- A **build on the Gulf Coast (PADD 3)** may simply reflect crude staged for **export** or pre-positioned ahead of refinery runs — much less bearish, and sometimes a sign of strong export demand.
- A **draw driven by high refinery utilization** (crude being consumed into products) is a different signal from a **draw driven by heavy exports** (crude leaving the country) or a **draw driven by a supply outage**. Same headline number, three different meanings.
- **Therefore: read the build's components — Cushing vs. Gulf Coast vs. coasts, and the *cause* (runs, imports, exports, production) — before deciding whether it is bullish or bearish.** The framework should decompose every print, not just take the top line.

---

## 6. Amplifiers and offsets — what decides whether a print is amplified, ignored, or flipped

Six outside forces determine the inventory number's actual market impact on the day. When they are quiet, the surprise dominates; when one is active, it can swamp or even reverse the "expected" reaction.

1. **OPEC+ supply policy.** The group controls roughly **35% of global crude production and ~50% of internationally traded oil**, and meets monthly. **Direction sets the bias:** when OPEC+ is *adding* barrels, a bearish build is amplified and a bullish draw is muted; when it *surprises with cuts*, the same build is shrugged off (see 2–3 Apr 2023). Its **spare capacity is the market's shock absorber**: ample spare lets builds bite and disruptions get ignored; thin spare magnifies every draw and every scare into a **risk premium**. OPEC defines spare capacity as output that can come online within 30 days and be sustained for 90.

2. **Geopolitics.** Supply-threat shocks (wars, chokepoint closures, sanctions) override weekly data outright — but **pre-existing thin inventories amplify the move** (2022 Russia-Ukraine). When a major exporter or transit route is at risk, the weekly U.S. print becomes near-irrelevant until the threat clears.

3. **Macro.** Oil is priced in dollars, so a **stronger U.S. dollar (DXY) raises the cost for foreign buyers and offsets a bullish draw**; a weaker dollar amplifies it. **Fed rate cuts and risk-on equities** support price; **China demand** swings the global balance. On a risk-off day, even a strong draw can be ignored. *(Caution: specific "~50 bp of Fed cuts" and "~0.5 mb/d per 1% China demand" figures circulating in the research are **generic rules of thumb that were mis-attributed to a Kpler page that does not contain them** — use the directional logic, not those precise numbers.)*

4. **Product cracks (the cross-check).** Look at whether **crude, gasoline, and distillate agree**. A crude *build* alongside *falling* product stocks and *rising* crack spreads signals strong refinery demand and is read **bullishly**, neutralizing the headline build. **Divergence between crude and products is the tell.** *(One figure to drop: "distillate cracks hit record highs in 2026" is overstated — they were the **highest since 2022**, not all-time.)*

5. **Refinery runs, exports, and the SPR.** **High utilization** (e.g., 96.7% in mid-June 2026, crude inputs 17.2 Mb/d for the week ending 12 June 2026) means a crude draw reflects **heavy refining, not scarcity** — bullish for crude, bearish for products. **Heavy exports** drain crude stocks for reasons unrelated to domestic tightness. **The SPR is a two-way swing factor:** government *releases* add bearish supply (2022), while *refills* add bullish demand (the Trump administration prioritized refilling the SPR toward its ~714-million-barrel capacity). *(Note: a "~5.2 mb/d record U.S. crude exports" figure in the research **could not be corroborated**; EIA's full-year net-export forecast was ~4.2 mb/d.)*

6. **Positioning.** CFTC managed-money / Commitments of Traders data shows how stretched speculators are. **Extreme net length** makes a bearish build trigger **long-liquidation cascades**; **crowded shorts** make a draw spark a **short-covering rally**. Positioning doesn't start moves but it **amplifies** them. *(The specific June-2026 "net length ~172k contracts, a 33-week high" figure rests on a **single StoneX report and is uncorroborated** — treat as indicative only.)* **[single-source]**

---

## 7. Current backdrop — June 2026 (with explicit dates and unconfirmed flags)

> **Important caveat.** The June-2026 backdrop below is internally consistent and broadly corroborated across multiple outlets, **but several specific figures are single-source or could not be independently confirmed and are flagged accordingly.** The fact-checker verified these against the *available record*, not against ground truth. Treat the scenario as the working market narrative, not as settled fact.

**The dominant story is geopolitics, not inventories.**

- **28 Feb 2026 — Strait of Hormuz crisis begins.** U.S./Israel strikes on Iran reportedly led the IRGC to bar vessel passage through the Strait of Hormuz, a chokepoint that normally carries **~20 million barrels/day (~20% of seaborne oil)**. Ship traffic fell **~70%** within days; roughly **~10 mb/d of supply was shut in**. With a shock this large, **weekly EIA/API data became largely irrelevant.**
- **8 Mar 2026 — Brent tops $100**, then peaks **near $126**, in what is described as the **largest-ever monthly oil price increase**; the IEA reportedly recorded global supply plunging ~10.1 mb/d to ~97 mb/d, the largest disruption on record.
- **3 May 2026 — OPEC+ raises June quotas by 188,000 b/d.** Agreed by **seven members** (Saudi Arabia, Russia, Iraq, Kuwait, Kazakhstan, Algeria, Oman). It was the group's **first meeting after the UAE exited OPEC+** in late April 2026 — context that materially affects the spare-capacity picture. The hike's price impact was modest because the Hormuz disruption swamped the quota math. *(The per-country split of +62,000 b/d each for Saudi and Russia is **[unverified]**.)*
- **Spare capacity at record lows.** Effective **Middle East spare capacity reportedly collapsed to ~320,000 b/d in March 2026** (IEA) — note this is *Middle East*, not strictly OPEC+ — which is why the market priced such a large risk premium. **[confidence: medium]**
- **7 Jun 2026 — OPEC+ meeting** (next monthly meeting after the May decision).
- **12 Jun 2026 — reference week** for the most recent EIA print. Refinery utilization **96.7%**, crude inputs **17.2 mb/d** — heavy runs explaining crude draws. National crude stocks had recently been **~426.5 million barrels, ~5% below the five-year average** (week ending 5 June).
- **17 Jun 2026 — the read flips on diplomacy.** Hopes of a Hormuz reopening drove an **"entirely sentiment-driven"** (analyst Vandana Hari) **~$17/bbl four-session Brent slide to ~$78**, the lowest since 3 March, leaving Brent only ~7% above pre-war levels — **despite a bullish supply backdrop** (Q2 drawdown ~6.3 mb/d). A textbook case of the risk premium, not stocks, setting price.
- **17 Jun 2026 — most recent EIA WPSR released**, covering the week ending 12 June. The **next release is 24 June 2026** (today). Note: 24 June is a **normal Wednesday** because Juneteenth (19 June) fell on a Friday in 2026 and did not push the schedule.
- **22 Jun 2026 — whipsaw.** Iran's renewed Hormuz-closure threat and U.S. renewed-strike threats reversed the reopening rally: **Brent −3.3% to $77.90, WTI −2.3% to $74.82.** Two-way geopolitical risk, amplified by positioning, overwhelmed any inventory signal.
- **EIA June 2026 STEO backdrop:** OECD stocks falling (reportedly lowest since 2003), **Brent ~$105 around mid-2026**, Q2 average drawdown ~6.3 mb/d, with **normalization not expected until early 2027.** **[confidence: medium]**

**What this means for the framework right now (24 June 2026):** we are squarely in a **geopolitics-dominated regime**. Inventory surprises should be **heavily down-weighted** until the Hormuz situation resolves — the price is being set by the **risk premium and headlines**, with **positioning** amplifying each swing. The bullish underlying draws are real but currently subordinate. Keep the **Cushing capacity trigger** and the **OPEC-meeting-window** flag active, and watch the **dollar and product cracks** as the offsets most likely to matter when the geopolitical premium finally unwinds.

---

## How the seven dimensions assemble into a framework

1. **Compute the surprise** = `actual − consensus`, using the **API preview** (Tue) and a **polled analyst median** as the two consensus proxies.
2. **Put it in seasonal context** — judge both the level (vs. the **five-year band** for that week) and the surprise against the **seasonal norm**.
3. **Decompose it** — Cushing vs. Gulf Coast vs. coasts, and the *cause* (runs / imports / exports / production); cross-check crude against **product stocks and cracks**.
4. **Classify the regime** — quiet / OPEC-policy / geopolitical / macro shock / storage-tail — and **weight the surprise accordingly** (full weight when quiet; heavily discounted under an active override; *maximum* weight when Cushing nears capacity).
5. **Layer the amplifiers/offsets** — OPEC+ direction and spare capacity, the dollar, positioning extremes — to decide whether the regime-weighted surprise gets magnified or muted.

---

## Sources (most important)

**EIA primary (mechanics, seasonality, episodes, current outlook)**
- WPSR release schedule — https://www.eia.gov/petroleum/supply/weekly/schedule.php
- WPSR landing page — https://www.eia.gov/petroleum/supply/weekly/
- Weekly supply table (series, week labeling) — https://www.eia.gov/dnav/pet/pet_sum_sndw_dcus_nus_w.htm
- Open Data API FAQ (two-hour API lag; ir.eia.gov) — https://www.eia.gov/opendata/faqs.php
- Petroleum Supply Monthly (benchmark/revisions) — https://www.eia.gov/petroleum/supply/monthly/
- Refinery outages / seasonal maintenance — https://www.eia.gov/petroleum/articles/refoutagesindex.php
- December Gulf Coast tax-driven draw — https://www.eia.gov/todayinenergy/detail.php?id=10031
- Negative WTI / Cushing storage crisis (20 Apr 2020) — https://www.eia.gov/todayinenergy/detail.php?id=43495
- 2018 oil crash context — https://www.eia.gov/todayinenergy/detail.php?id=37852
- 2022 oil-year retrospective — https://www.eia.gov/todayinenergy/detail.php?id=55079
- OPEC spare capacity / risk premium — https://www.eia.gov/finance/markets/crudeoil/supply-opec.php
- June 2026 STEO (global oil) — https://www.eia.gov/outlooks/steo/report/global_oil.php

**Consensus, API preview, and positioning**
- API Weekly Statistical Bulletin — https://www.api.org/energy-insights/statistics/wsb
- StoneX, EIA vs. API comparison — https://futures.stonex.com/blog/eia-vs-api-weekly-crude-oil-inventory
- StoneX CoT positioning report — https://www.stonex.com/en/market-intelligence/commodity-futures-positioning-gold-silver-copper-wti-crude-cot-report/

**Episodes and amplifiers**
- U.S. Treasury, SPR release impact (2022) — https://home.treasury.gov/news/press-releases/jy0887
- CNN, surprise OPEC+ cut (Apr 2023) — https://edition.cnn.com/2023/04/02/business/opec-production-cuts/index.html
- CNBC, Russia-Ukraine price spike (Mar 2022) — https://www.cnbc.com/2022/03/06/us-crude-oil-jumps-to-125-a-barrel-a-13-year-high-on-possible-western-ban-of-russian-oil.html
- CNBC, Saudi-Russia price war (Mar 2020) — https://www.cnbc.com/2020/03/08/oil-plummets-30percent-as-opec-deal-failure-sparks-price-war-fears.html
- CNBC, Oct 2019 inventory print — https://www.cnbc.com/2019/10/31/oil-markets-us-crude-inventories-in-focus.html
- CRS, SPR policy — https://www.congress.gov/crs-product/IN12542

**June 2026 backdrop**
- Wikipedia, 2026 Strait of Hormuz crisis — https://en.wikipedia.org/wiki/2026_Strait_of_Hormuz_crisis
- IEA Oil Market Report, April 2026 (spare capacity) — https://www.iea.org/reports/oil-market-report-april-2026
- Al Jazeera, OPEC+ June hike during the crisis (3 May 2026) — https://www.aljazeera.com/news/2026/5/3/opec-announces-symbolic-oil-output-rise-during-strait-of-hormuz-closure
- Al Jazeera, sentiment-driven slide (17 Jun 2026) — https://www.aljazeera.com/economy/2026/6/17/oil-prices-continue-slide-amid-hopes-for-peace-opening-of-strait-of-hormuz
- CNBC, Hormuz whipsaw (22 Jun 2026) — https://www.cnbc.com/2026/06/22/oil-prices-wti-brent-crude-trump-iran-threat-strait-hormuz-closure.html
- IndexBox, WPSR week ending 12 Jun 2026 — https://www.indexbox.io/blog/us-weekly-petroleum-status-report-june-17-2026/

---

*Cushing storage figures (~76 Mbbl / ~13% of U.S. capacity) and the contango/backwardation storage logic are standard market knowledge corroborated via EIA-cited sources; the CME education page was referenced but timed out during verification. Where this brief flags a claim as unverified, single-source, or mis-attributed, the underlying economic logic still holds — only the precise figure is in doubt.*
