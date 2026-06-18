# The Trading Strategy — explained simply, in depth

### What the strategy does and why, in plain words and worked examples

This is the full guide to the trading idea behind `Backtesting/engine.py`. It goes step by
step with real numbers, but keeps the language simple. If you can picture a stretched rubber
band snapping back, you can follow all of it.

The whole journey in one line: **work out what's normal → spot when a price gap is stretched
too far → fade it → ride the snap-back → get out at the right moment.**

---

## 1. The big idea (in one minute)

We trade **spreads** — the *gap* between two related oil prices. For example, the price of oil
for July delivery minus the price for August delivery. That gap might be **$0.74**.

We do **not** bet on whether oil goes up or down. We only bet on whether that **gap returns to
normal** after it gets stretched.

Picture the gap as a rubber band. Most of the time it rests at a comfortable length. Now and
then a burst of buying or selling **stretches** it — too wide or too narrow. History shows it
usually **snaps back**. So when we see a stretched gap, we bet on the snap-back. That's the
whole strategy:

> **When the gap is unusually stretched, bet that it returns to normal.**

Everything else is about doing that carefully — measuring "stretched" honestly, and getting in
and out at sensible points.

**Why bet on the gap, not on oil itself?** Because we buy one month and sell another at the
same time, so the big swings in the *overall* oil price cancel out. What's left is a small,
steady, well-behaved relationship — far easier to predict than "will oil go up?"

---

## 2. What we actually trade

Seven gaps, all built from **WTI** (American oil) and **Brent** (global oil) futures, in three
shapes:

- **Calendar gaps** — the same oil, two different months (e.g. July vs August WTI). A pure bet
  on whether near-term oil is getting tighter or looser than later oil.
- **Butterflies** — a three-month combination that checks whether the *middle* month is out of
  line with its neighbours. The most surgical, market-neutral of the three.
- **Brent vs WTI** — the gap between the two kinds of oil, driven by shipping and regional
  supply differences.

In every case we **buy one contract and sell another at the same time**, so we own no outright
oil — only the gap. One contract is 1,000 barrels.

---

## 3. The key question — what is "fair value," and can we borrow Phase 2's model?

To know whether a gap is stretched, we need a reference: its **fair value** (its "normal"
level). The project already built a clever fair-value model in **Phase 2** — a statistical
model that predicts each spread from real-world causes (oil stockpiles, the US dollar, market
fear, the season). The obvious question: **can we just reuse that here?**

We looked carefully, and the answer is **no** — for three solid reasons:

1. **Its ingredients aren't in this data.** The Phase 2 model needs fundamentals — inventory
   levels, refinery activity, the dollar, the fear gauge. The intraday feed we're trading
   contains **only oil prices** — none of those ingredients. So the model simply **can't be
   computed** here.
2. **Its number is out of date.** Phase 2's fair value for the WTI July–August gap is about
   **2.18**. That same gap is trading at about **0.74** today — the contracts have re-priced
   since. Forcing the old number on would scream "this gap is cheap by 1.4!" *forever* — a
   permanent false signal, not a real one.
3. **It barely moves intraday.** Those fundamentals update daily (or weekly), so over a few
   days the model is basically a flat line. It can't explain the minute-by-minute wiggles we're
   actually trading, which come from order flow, not from slow fundamentals.

**So we estimate fair value from the gap's own recent behaviour** — see the next section. This
isn't a step *down* from Phase 2; it's the *right tool for the timeframe*. Phase 2 still
contributes: its proven track record for each gap (how often that gap historically snapped
back) is carried in as a **confidence score** on every trade. We just don't use its *price* as
the reference, because it can't be one here.

---

## 4. Step one — work out what "normal" looks like

We look at the gap's recent history — the **last 24 readings, about six hours** of trading —
and take their **average**. That average is our "normal" (the fair value) for right now. As new
readings arrive, the average rolls forward, so "normal" keeps up with a slowly drifting gap.

We also measure how much the gap **normally wiggles** — its typical jiggle from reading to
reading. Call one of those a "**wiggle**." A gap that normally jumps around a lot needs to move
*a lot* to count as stretched; a calm gap needs only a little. Measuring in wiggles puts every
gap — calm or jumpy — on the **same fair ruler**.

---

## 5. Step two — measure how stretched it is

We turn "how far from normal" into one number, counted in wiggles. Traders call it a
**z-score**; you can read it as *"how many normal wiggles away from normal are we?"*

- Around **0** = sitting right at normal.
- **+2 or more** = unusually **high** — the gap is "**rich**" (too wide).
- **−2 or less** = unusually **low** — the gap is "**cheap**" (too narrow).

> **Worked example.** Normal is `0.74`, one wiggle is `0.05`, and right now the gap is `0.84`.
> Distance from normal = `0.10`. In wiggles: `0.10 ÷ 0.05 = 2.0`. So the stretch reading is
> **+2.0** — stretched wide, right at our trigger.

---

## 6. Step three — the entry rule

Simple and strict: **fade the gap once it is stretched to 2 wiggles or more.**

- If it's **rich** (stretched wide, +2 or more) → **sell** the gap, betting it narrows back.
- If it's **cheap** (stretched narrow, −2 or less) → **buy** the gap, betting it widens back.

That's the only entry condition. We picked **2 wiggles** because it's a genuinely unusual
stretch — unusual enough that the snap-back is a real edge, but common enough to give a decent
number of trades. (Lower, like 1, trades more but on weaker, noisier signals; higher, like 3,
waits for rare extremes.)

---

## 7. Step four — the exit rules

Once we're in, we leave for the **first** of four reasons:

1. **It worked — take profit.** The gap snapped back to normal (within a quarter of a wiggle of
   it). We take the win. We wait for the **full** snap-back, not just a sliver — we want the
   whole move.
2. **We were wrong — stop loss.** Instead of snapping back, the gap stretched **further against
   us**, to 3.5 wiggles. We accept we're wrong and cut it.
3. **It's taking too long — time stop.** If a trade hasn't resolved within **about 12 hours**,
   we stop waiting and close it. This avoids sitting in dead trades that drift nowhere.
4. **The day is ending — flatten.** We never hold through the overnight or weekend gap (too much
   can happen while the market is closed). We close out before the break.

> **The shape of the bet.** We enter at 2 wiggles, aim for a snap-back to 0 (a **1.75-wiggle**
> reward) and cut at 3.5 (a **1.5-wiggle** risk). So the reward is a touch bigger than the risk,
> *and* mean-reversion wins more often than it loses — that combination is the edge.

---

## 8. Step five — how big is each trade?

**One unit per trade. Always. Simple.**

This is a deliberate choice. The point of this backtest is to answer *"does the signal work?"*
— so we keep the size fixed and small, and report the **raw per-unit result**. One contract is
1,000 barrels, so a `$1` move in a gap is worth `$1,000`.

> **An honest note.** An earlier version tried clever position-sizing (risking a fixed 1% of a
> $250,000 account per trade). It technically worked, but it multiplied every position ~100×,
> which blew the profit *and* the losses up into scary six-figure numbers that obscured whether
> the underlying signal was any good. So we stripped it back out. **Sizing is a separate
> decision** you layer on *after* you trust the signal — not part of testing the signal. Here we
> test the signal, cleanly, at one unit.

We keep a pretend $250,000 only as a starting line for the running profit/loss chart.

---

## 9. A full trade, start to finish

1. **A gap gets stretched.** WTI July–August normally rests near `0.74`. A burst of buying
   pushes it to `0.84` — a stretch of about **+2.0 wiggles**, rich. ✅ It's past our trigger.
2. **We enter — SELL the gap at 0.84**, betting it falls back toward `0.74`.
3. **The confidence score** is set from Phase 2's track record for this gap (WTI calendars
   reverted ~75% of the time historically) plus how stretched it is — here, a solid ~80/100.
4. **It snaps back.** A few hours later the gap is back to `0.74` — within a quarter-wiggle of
   normal. That's our take-profit. **We close and pocket the difference** (the gap fell `0.10`,
   × $1,000 per unit per $1 = a small win).

A **losing** trade differs only at the end: the gap pushes *up* to 3.5 wiggles instead, our
stop fires, and we take a small, pre-planned loss. Or it stalls and the 12-hour time stop closes
it near break-even.

---

## 10. How we keep score

For every trade we record: which gap, buy or sell, the in/out prices and times, why we exited,
how long we held, the profit or loss, and the worst/best point it passed through.

From all the trades together, three numbers matter most:

- **Profit factor** — total dollars won ÷ total dollars lost. Above **1.0** = making money;
  **3.0** = won three dollars for every one lost. The fairest single score, because a
  "win-often-lose-big" trick can fake a high win rate but **cannot** fake a high profit factor.
- **Expectancy** — the average profit per trade. The real bottom line.
- **Biggest dip (drawdown)** — the worst peak-to-valley fall in the running total; the "pain"
  measure.

---

## 11. The cost check — does it survive trading fees?

By default we run **before costs** (the pure signal). But we can also charge **realistic
trading costs** (the small fee on every buy and sell).

The honest finding: **the gross signal is solid, but it's a high-frequency, small-edge
strategy, so realistic costs eat most of it** — net of a typical fee it thins to roughly
break-even. That's not a failure; it's the truth about this kind of strategy: *the prediction
works, but the moves are small enough that execution cost is the deciding factor.* The fix would
be to trade only the highest-conviction setups (fewer, bigger), but we report the honest gross
and net rather than dress it up.

---

## 12. The results (latest live data)

On the live company feed (~350 fifteen-minute bars, 12–18 June 2026):

| Measure | Result | What it means |
|---|---|---|
| **Trades** | 76 | 76 stretched-gap opportunities taken |
| **Gross profit** | **+$4,270** | total per-unit dollars made (before costs) |
| **Win rate** | **78%** | 78% of trades were profitable |
| **Profit factor** | **3.03** | won $3.03 for every $1 lost |
| **Expectancy** | **+$56 / trade** | the average trade made $56 |
| **Max drawdown** | **−$1,450** | worst dip along the way |
| **Net (after a 1¢/leg fee)** | ~break-even | costs eat the small intraday edge |

Per gap, most were positive (the butterflies and Brent–WTI strongest); one — Brent Sep–Oct —
actually **lost** money, which we show plainly rather than hide. These are small, honest,
per-unit numbers — the raw signal, not a leveraged book.

---

## 13. The honest limits

1. **Not much data yet.** A few days of trading. It's a working method, not a final verdict —
   feed it more days to really trust the numbers.
2. **"Normal" is a simple average.** A single sharp spike can tug the average a little; a more
   robust measure is a possible refinement.
3. **Costs decide it.** Gross looks good; net is roughly break-even. Real profitability needs
   either lower costs or pickier, higher-conviction trades.
4. **Oil only.** The data is WTI and Brent crude — no diesel, petrol, or other products.
5. **One-unit sizing.** This is the raw signal, not a sized portfolio; sizing and risk limits
   are a separate layer on top.

---

## 14. Mini-glossary (plain words)

- **Spread / gap** — the price difference between two related contracts, traded as one bet.
- **Rich / cheap** — a gap that's unusually wide (rich) or narrow (cheap) versus normal.
- **Normal / fair value** — the gap's recent resting level (here, the average of recent readings).
- **Wiggle** — the gap's typical jiggle; the unit we measure "stretch" in.
- **Stretch / z-score** — how many wiggles away from normal we are right now.
- **Fade** — to bet *against* a move (sell what just jumped up, buy what just dropped).
- **Snap-back / mean reversion** — the tendency of a stretched gap to return to normal.
- **Stop loss** — the pre-set point where we admit we're wrong and cut the trade.
- **Take profit** — closing a winning trade once it has snapped back.
- **Profit factor** — dollars won ÷ dollars lost (above 1 = profitable).
- **Drawdown** — the worst drop from a high point to a later low; the "pain" measure.
- **Gross vs net** — results before costs (gross) versus after costs (net).

---

## 15. How to run it

```bash
python Backtesting/engine.py            # before costs (the pure signal)
python Backtesting/engine.py --slip 0.01  # charge a per-leg fee; reports net too
python Backtesting/engine.py --live       # keep re-running on the latest data
```

Each run writes the full trade-by-trade story to `out/trades_log.md`, a spreadsheet to
`out/trades.csv`, and feeds the live dashboard. The plain-English overview of the whole project
is in [`../PROJECT_REPORT.md`](../PROJECT_REPORT.md); the engine's methodology is in
[`IDEATION.md`](IDEATION.md).
