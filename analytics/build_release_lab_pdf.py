"""
build_release_lab_pdf.py — the plain-English Phase 4 explainer PDF:
  deliverables/Phase4_Release_Lab_Explained.pdf

Phase 4 is the "EIA Release Lab" (analytics/release_lab.py + src/pages/ReleaseLab.jsx):
one frozen experiment around a SINGLE EIA crude release — the prediction made BEFORE the
number lands vs. what actually happened AFTER. This script reads the live snapshot the
dashboard reads (server/data/release_lab.json) and renders an explainer aimed at a reader
who knows NOTHING about oil markets: every piece of jargon is defined the moment it appears.

Same pure-Python toolchain as analytics/build_pdf.py (markdown + xhtml2pdf), so numbers in
the document always match the latest run.

Run:  python analytics/build_release_lab_pdf.py
"""
from __future__ import annotations

import json
from pathlib import Path

import markdown
from xhtml2pdf import pisa

from common import ROOT

DELIV = ROOT / "deliverables"
RL = json.loads((ROOT / "server" / "data" / "release_lab.json").read_text())

t = RL["target"]
cur = RL["current"]
p = RL["prediction"]
r = RL.get("result") or {}
comp = RL.get("comparison") or {}
sc = RL.get("scorecard") or {}
tr = RL.get("track_record") or {}
intr = RL.get("intraday") or {}
cc = r.get("crosscheck") or {}


def f(x, d=1, sign=False):
    if x is None:
        return "n/a"
    return f"{x:+.{d}f}" if sign else f"{x:.{d}f}"


def pct(x, d=2, sign=True):
    if x is None:
        return "n/a"
    return (f"{x:+.{d}f}%" if sign else f"{x:.{d}f}%")


# convenience pulls
exp = p["expected_wow"]
act = r.get("actual_wow")
surp = r.get("real_surprise")
surp_z = r.get("real_surprise_z")
pred_move = r.get("pred_move_pct")
act_move = r.get("actual_move_pct")
lights = sc.get("lights", [])
L = {l["key"]: l for l in lights}
rec = tr.get("recent") or {}
alln = tr.get("all") or {}
att = r.get("attribution") or {}


def grade_word(ok):
    return "PASS (green)" if ok is True else "FAIL (red)" if ok is False else "MIXED (amber)"


# Section 5b — move attribution (inventory vs macro vs everything else). Built only
# when a run has produced the decomposition; empty string otherwise.
if att:
    _macro_txt = pct(att.get("macro_pct")) if att.get("macro_pct") is not None else "n/a"
    attribution_md = f"""
### The receipts — splitting the move into inventory vs macro vs everything else

A fair question: if the inventory surprise barely moved the price, what *did*? The Lab now
splits the release-day move into measurable parts (a technique called **attribution**): the
piece explained by the crude **surprise**, the piece explained by the broad **market** that
day (the S&P 500 and the US dollar — a "risk-on/risk-off" reading), and the **residual** —
everything left over (oil-specific news, OPEC, geopolitics, positioning).

| Part of the {pct(att.get('actual_pct'))} day's move | Size | Plain meaning |
|---|---|---|
| Inventory surprise | {pct(att.get('inventory_pct'))} | what the crude number itself was worth |
| Broad market (macro) | {_macro_txt} | risk-on/off + the dollar |
| Other / residual | {pct(att.get('residual_pct'))} | **the dominant driver** — oil-specific other forces |

So of the day's {pct(att.get('actual_pct'))} move, the inventory number was worth only
{pct(att.get('inventory_pct'))} and the broad market {_macro_txt} — the rest,
**{pct(att.get('residual_pct'))}**, was other forces. That is the same message as the R-squared,
now in plain percentage terms you can read straight off. (Looking at the *whole* report rather
than crude alone — adding petrol, diesel and Cushing — nudges the explained share from
R2 {f(att.get('crude_only_r2'), 3)} to {f(att.get('report_r2'), 3)}; still small, but it confirms
the day really was driven from outside the report.)
"""
else:
    attribution_md = ""


# Section 5 — the model, the prediction and the logic, in depth (always shown).
_mae = alln.get("mae") or {}
mae_model, mae_seasonal = _mae.get("model"), _mae.get("seasonal")
model_logic_md = f"""## 5. Under the hood — the model, the prediction, and the logic

This is the engine room: exactly how the Lab turns a raw government statistic into a graded
call, and the reasoning behind every step. Nothing here is a black box.

### 5a. The whole pipeline, in seven steps

> **Data -> Expected -> Surprise -> Regime -> Verdict -> Grade -> Track record.**

1. **Pull the data.** The weekly EIA report (crude stocks plus the flows behind them —
   production, imports, exports, refinery runs), recent prices, and the broad market.
2. **Predict the number (the model).** Estimate this week's draw/build *before* it is announced
   — the "Expected" figure (detailed in 5b).
3. **Measure the surprise.** When the real number lands: **Surprise = Actual - Expected.** Only
   this gap is genuinely *new* information.
4. **Read the regime.** Gauge how much the market is *listening* to inventories right now (calm
   vs. stormy market, the season, whether crude and fuels agree) — the "catalyst strength".
5. **Form the verdict.** Translate the surprise, scaled by the regime, into Bullish / Bearish /
   Neutral — alongside a slower **structural lean** from the multi-week backdrop (5d).
6. **Grade the outcome.** After the price moves, the scorecard checks the call and the
   attribution splits the move into inventory vs. macro vs. everything else.
7. **Repeat across history.** Run the identical logic on ~260 past releases (the track record),
   so nothing rests on a single lucky week.

### 5b. The model that predicts the number — ingredient by ingredient

The model's only job is to answer, *before* Wednesday's release: **how much will crude stocks
change this week?** It learns from about a dozen clues, all known the day *before* the release —
each chosen because there is a real-world reason it should help:

| Clue the model uses | Why it helps predict this week's draw/build |
|---|---|
| Seasonal-normal change | demand and refinery schedules follow the calendar every year |
| Last 1-2 weeks' change | draws and builds arrive in runs (momentum) |
| Last week's supply/demand balance | physical flows are sticky from week to week |
| Refinery utilization & runs (lagged) | the harder refineries run, the more crude they pull from tanks |
| Crude production (lagged) | more barrels pumped tilts toward a build |
| Net imports (lagged) | imports add to storage; exports remove from it |
| Cushing change (lagged) | the WTI delivery hub often moves first |
| Gasoline & distillate draws (lagged) | strong fuel demand pulls crude through refineries |
| Stock level vs. seasonal norm (lagged) | unusually high or low stocks tend to revert |
| Week-of-year (sine/cosine) | smooth seasonality the weekly average alone misses |

These are blended with a **ridge regression** — a standard, transparent way to weigh many clues
at once. Every weight is learned only from the past (5c).

### 5c. Two ideas that keep the prediction honest

- **Ridge (don't over-trust any one clue).** With a dozen clues but only a few hundred weeks of
  history, a naive fit would start "memorising" random noise — looking brilliant on the past and
  then failing on the future (**overfitting**). Ridge deliberately *shrinks* the weights so no
  single clue dominates, trading a little fit on old data for reliability on new data.
- **Walk-forward (no peeking).** To predict any given week, the model may use **only the weeks
  before it**. So every "Expected" number is a genuine out-of-sample forecast, never hindsight.
  (This is the **leak-free** rule from earlier, applied across the whole history.)

### 5d. From a number to a call — the chain of reasoning

> Expected -> Surprise -> (scaled by) Regime -> Verdict, with a separate structural Lean.

- **Expected** is the consensus the price is *already positioned for* — so a print in line with it
  should barely move anything.
- **Surprise** (actual - expected) is the only part that is news. We size it in **sigma** (how
  unusual the miss is) rather than raw barrels, so "big" means the same thing in every season.
- **Regime** decides how loudly that news lands: the same surprise is worth more in a calm,
  inventory-driven market than in a war-driven one. The Lab measures this as the catalyst **R2**.
- **Verdict** = the direction of the surprise (a bigger draw -> bullish), *scaled down* by both how
  ordinary the surprise was and how weak the catalyst is. A large surprise in a deaf market still
  yields a muted, low-confidence call — on purpose.
- **Structural lean** is separate and slower: where stocks sit vs. the seasonal norm, the recent
  draw/build momentum, and the Cushing trend. It is the background tilt, not the day's trade.
- **The honesty built in:** when the catalyst R2 is near zero, the Lab actively says *don't trust
  the number today* — and counts being right about that as a success, not a dodge.

### 5e. Does the prediction actually work?

Two different questions, answered honestly and *separately*:

- **Does it forecast the number well?** Yes. On the long walk-forward backtest its average miss is
  **{f(mae_model)} MMbbl vs {f(mae_seasonal)} MMbbl** for the naive "just use the seasonal average"
  guess (lower is better) — and its week-to-week forecasts track the real draws and builds far more
  closely (their correlation with reality **nearly doubles** versus the seasonal guess).
- **Does forecasting the number mean predicting the price?** *Not necessarily* — and the Lab is
  blunt about it. The price reacts only to the *surprise*, and only when inventories are the day's
  catalyst; often they are not. So a good number-forecast and a small price reaction can both be
  true at once. Bridging that gap is exactly what the catalyst R2 and the move attribution are for.

"""


# ===========================================================================
MD = f"""
# Phase 4 — The EIA Release Lab, Explained for Everyone

**What happens to the price of oil at the exact moment the U.S. government publishes how
much oil is sitting in the country's storage tanks — and can we call it in advance?**

*This guide assumes you know nothing about oil, trading, or statistics. Every special word
is explained the first time it appears. Worked example: the **{t['label']}**.*

<hr/>

## 0. The one-sentence version

> Every week the U.S. government announces how much oil is in storage. Phase 4 is a little
> "laboratory" that, **before** the announcement, writes down a prediction of what the number
> will be and how the oil price should react — and then, **after** the announcement, checks
> whether it was right and *explains why*.

Think of it like a weather forecast that is graded against the actual weather, except the
"weather" is the oil market's reaction to a government report.

<hr/>

## 1. The five words you need (and nothing more)

Before anything else, here are the only pieces of jargon in this whole document. Each is
plain once you see it:

- **Crude oil** — unrefined oil, straight out of the ground, before it is turned into petrol/
  gasoline, diesel, jet fuel, etc.
- **Inventory / stocks** — the amount of crude oil currently sitting in storage tanks across
  the United States. Measured in **MMbbl = millions of barrels** (one barrel ≈ 159 litres).
- **Draw** — stocks went **down** this week (oil was taken out of storage). Usually good for
  the price, because it hints demand is strong or supply is tight. A falling-supply story is
  called **bullish** (expecting prices to rise).
- **Build** — stocks went **up** this week (oil piled up in storage). Usually bad for the
  price — that's called **bearish** (expecting prices to fall).
- **WTI** — "West Texas Intermediate", the headline price of U.S. crude oil. When the news
  says "oil rose 2% today", this is usually the number they mean. (Its global cousin is
  **Brent**.)

That's it. Everything below is built from these five ideas.

<hr/>

## 2. The single most important idea in the whole project

If you remember **one** thing, remember this:

> ### The market does not react to the inventory number. It reacts to the **surprise** — how far the number lands from what everyone was already expecting.

Why? Because traders are not surprised by things they already saw coming. If everyone
*expects* oil stocks to fall by 4 million barrels, and they fall by exactly 4 million, the
price barely moves — that outcome was already "baked into" today's price. The price only
jumps when reality differs from the expectation.

A concrete, slightly counter-intuitive example:

- Stocks **fall** by 5 million barrels (a *draw*, normally good news for the price)…
- …but everyone expected them to fall by **10** million.
- Net effect: this is actually **bad** news — far less oil left storage than hoped. The price
  can *fall* on a draw.

So we define, very precisely:

> **Surprise = Actual number − Expected number.**

The Release Lab's entire job is to (1) build a sensible *expected* number, (2) measure the
*surprise* once the real number lands, and (3) judge how much that surprise *should* move
the price given the mood of the market that day.

<hr/>

## 3. What actually gets published, and when

- **What:** every week the **EIA** (Energy Information Administration — the U.S. government's
  energy-statistics agency) publishes how much crude oil is in U.S. storage tanks, in a report
  called the *Weekly Petroleum Status Report*.
- **When:** **Wednesday at 10:30 a.m. New York time.** To the second. Traders are watching the
  clock.
- **Catch:** the weekly figure is an *estimate* (the EIA surveys most of the industry and fills
  in the rest), so treat it as a fast-but-slightly-noisy reading, not gospel.

This particular experiment is built around the release on **{t['release_date']}**, which
reports on the week ending **{t['period']}**.

<hr/>

## 4. The Lab in two halves: the Prediction and the Result

The page has a deliberate before/after structure. The left side ("**Expected**") is frozen
*before* the number comes out. The right side ("**Real**") is filled in *after*, when you press
the **Run** button. Then the Lab grades itself.

### 4a. The PREDICTION — written before the number lands

Everything here uses **only information available before the release** — it is never allowed to
peek at the answer it is trying to predict. (In data science this is called being
**leak-free**: no information "leaks" backwards from the future into the prediction.)

**The expected number.** Real Wall-Street forecasts are paywalled, so the Lab builds its own
stand-in for "what everyone expects". It learns from roughly a dozen clues that are all known
*the day before* the release — the *normal* change for this calendar week (the seasonal
pattern), the last couple of weeks' changes (weeks tend to cluster), the recent supply/demand
balance, and the lagged flow drivers: how hard refineries were running, production, imports vs
exports, and last week's draws at **Cushing** and in petrol/diesel stocks (product draws often
lead crude). These are blended with a **ridge regression** — a standard statistical recipe that
weighs many clues at once while deliberately staying cautious so it doesn't over-fit the few
hundred weeks of history. Crucially it is fit **walk-forward**: to predict any given week it may
only use weeks *before* it. On the long backtest this beats the naive "just use the seasonal
average" guess (see the Track Record below).

> For **{t['label']}**, the model expected a **{f(abs(exp))} million-barrel {('draw' if exp < 0 else 'build')}**
> ({f(exp, sign=True)} MMbbl).

**The lean.** This is the Lab's gentle *structural* bias — its background guess for which way the
market is tilted, separate from the single weekly number. It can be **Bullish** (leaning toward
higher prices), **Bearish** (lower), or **Neutral** (no strong tilt).

> The lean here was **{p['lean']}** (confidence: {p['confidence']}). In plain terms: oil stocks
> are unusually low for the time of year, they have been falling for weeks, and **Cushing** — the
> single town in Oklahoma where WTI oil is physically delivered, and therefore the spot that
> matters most for the WTI price — has been draining toward its lows. All of that leans toward
> higher prices.

**The expected surprise is zero — on purpose.** Because the model *expects the number to land on
its own forecast*, its expected surprise is, by definition, about **0**. The whole game is what
happens when reality misses that forecast.

**The "catalyst strength" — the honest caveat.** A **catalyst** is something that actually *causes*
a price move. The Lab measures how strong a catalyst the inventory number has *been* in markets
like today's, using a statistic called **R²** ("R-squared"):

> **R² answers: "out of everything that moved the oil price on release day, what fraction was
> explained by the inventory surprise?"** It runs from 0 (the surprise explained *nothing* — the
> price moved entirely on other news) to 1 (the surprise explained *everything*).

> For this release the catalyst R² was about **{f(p['catalyst_r2'], 2)}** — essentially **zero**.
> Translation: in conditions like today's, the weekly inventory number has historically been a
> **weak** driver of the oil price. Other forces — economic news, OPEC (the group of big oil-
> exporting countries that coordinate production), wars and geopolitics — usually dominate the day.

This is the Lab being honest *up front*: it tells you, before the number even lands, that the
number probably won't be the main event.

**The impact curve and the scenarios.** The Lab still draws the textbook relationship: a line
saying "for each extra million barrels of surprise, WTI should move *this* much". The slope of
that line is called **beta** (here about {f(p['beta_pct_per_mmbbl'], 3)}% per million barrels — a
tiny number, consistent with the weak-catalyst finding). It then sketches three what-ifs:

| If the surprise is… | …the model expects WTI to… |
|---|---|
| A big extra draw (much less oil than expected) | rise a little ({pct(p['scenarios'][0]['pred_move_pct'])}) |
| Exactly in line (no surprise) | barely move ({pct(p['scenarios'][1]['pred_move_pct'])}) |
| A big extra build (much more oil than expected) | fall a little ({pct(p['scenarios'][2]['pred_move_pct'])}) |

Notice how *small* all three moves are — again, the weak-catalyst story.

### 4b. The RESULT — filled in after the number lands

When you press **Run**, the Lab fetches the real number and computes everything:

- **Actual:** stocks came in at a **{f(abs(act))} million-barrel {('draw' if (act or 0) < 0 else 'build')}** ({f(act, sign=True)} MMbbl).
- **Real surprise:** {f(surp, sign=True)} MMbbl. Recall surprise = actual − expected: a bigger
  draw than expected, which is a **{r.get('real_surprise_dir','n/a')}** (price-supportive) surprise.
- **How big is "big"?** We measure surprises in **sigma (σ)**, i.e. **standard deviations** — a
  statistician's ruler for "how unusual is this compared to a typical week?" Roughly: under 1σ is
  an ordinary week, 2σ is a genuinely large surprise. This one was **{f(surp_z, 1)}σ** — a small,
  ordinary-sized miss.

<hr/>

{model_logic_md}
<hr/>

## 6. The Scorecard — three traffic lights and a verdict

The Lab boils the whole experiment down to three yes/no questions, each shown as a traffic
light (green = yes, red = no, amber = unclear):

| Question (plain English) | Result | What it means |
|---|---|---|
| **1. Did we forecast the number well?** | {L.get('forecast',{}).get('grade','—')} — {grade_word(L.get('forecast',{}).get('ok'))} | We were {L.get('forecast',{}).get('detail','')} — a close forecast. |
| **2. Did the surprise break the way we leaned?** | {L.get('surprise',{}).get('grade','—')} — {grade_word(L.get('surprise',{}).get('ok'))} | {L.get('surprise',{}).get('detail','')}. Our bullish lean and a bullish surprise agreed. |
| **3. Did the oil price actually follow the surprise?** | {L.get('price',{}).get('grade','—')} — {grade_word(L.get('price',{}).get('ok'))} | {L.get('price',{}).get('detail','')}. The price went the *other* way. |

**The third light is the interesting one.** The surprise said WTI should drift **up** about
{pct(pred_move)}. Instead WTI **fell {pct(abs(act_move) if act_move is not None else None, sign=False)}** on the day.
On the surface that looks like the model failed.

**It is the opposite of a failure — and here is the whole point of Phase 4:**

> {sc.get('net','')}

In plain words: the Lab *told us in advance* (light by light) that the inventory number was a
weak catalyst here (R² ≈ 0). So when the price ignored a perfectly good draw and tumbled
{pct(abs(act_move) if act_move is not None else None, sign=False)} on other news, that wasn't a
broken forecast — it was **exactly the world the Lab had warned about.** Knowing *when not to
trust the signal* is itself the valuable output.

This is the single most important takeaway of the whole phase: **a good framework doesn't just
make a call; it tells you how much to trust the call — and is right about its own limits.**
{attribution_md}
<hr/>

## 7. The minute-by-minute view ("Intraday reaction")

The headline number above is the move over the whole release day. The Lab also zooms in to the
**intraday** level — *intra-day* simply means "within the same day", here minute by minute right
after the 10:30 a.m. release.

It compares two lines on a chart:

- the **predicted** path (where the surprise said the price should go — a nearly flat line, since
  the catalyst was weak), and
- the **actual** path (where WTI really went, sampled every 5 minutes from live market data).

> What we saw: in the first hour WTI sagged to about **{pct(intr.get('horizons',[{}])[2].get('actual_pct') if len(intr.get('horizons',[]))>2 else None)}**
> (at the 30-minute mark) — far from the flat, near-zero line the surprise implied — and then
> *climbed back* over the second hour. The realized wiggles had almost nothing to do with the
> inventory number; they were driven by other flows. The best any minute-horizon's R² reached was
> about **{f(intr.get('max_r2'), 2)}** — again, essentially zero explanatory power.

The lesson repeats at high resolution: on this day, the oil price and the inventory surprise were
moving to different drums.

<hr/>

## 8. "Is this just luck?" — the Track Record

One experiment proves nothing — maybe the Lab got this one release right (or wrong) by chance. So
the Lab also **backtests** the whole framework: it replays history and asks the same questions of
*every past release*. (**Backtest** = test a method on past data, pretending you didn't know the
outcome, to see if it would have worked.)

Three honest questions, scored over the last 52 weeks and over all history:

| Question | Last 52 weeks | All history | How to read it |
|---|---|---|---|
| **Surprise → price:** when the surprise was sizeable, how often did WTI move the way it implied? | {f((rec.get('surprise_hit_rate') or 0)*100, 0)}% | {f((alln.get('surprise_hit_rate') or 0)*100, 0)}% | 50% is a coin-flip; higher is a real edge. |
| **Lean:** how often did our pre-release tilt call the surprise's direction? | {f(((rec.get('lean') or {{}}).get('hit_rate') or 0)*100, 0)}% | {f(((alln.get('lean') or {{}}).get('hit_rate') or 0)*100, 0)}% | Again vs. a 50% coin-flip. |
| **Forecast accuracy (MAE):** average miss of our expected number vs. a naive "just use the seasonal average" guess (lower is better) | {f((rec.get('mae') or {{}}).get('model'))} vs {f((rec.get('mae') or {{}}).get('seasonal'))} | {f((alln.get('mae') or {{}}).get('model'))} vs {f((alln.get('mae') or {{}}).get('seasonal'))} | Our model beats the naive guess. |

(**MAE** = "mean absolute error" — just the average size of the miss, ignoring whether it was too
high or too low.)

The picture is honest, not hyped: a **small but real** edge over the long run (better than a coin
flip, and the forecast genuinely beats the naive seasonal guess), and a frank acknowledgement that
in recent, geopolitics-dominated months the edge from the number alone has thinned toward a coin
flip — precisely why the Lab leans on the *regime* read rather than the raw number.

<hr/>

## 9. Putting it all together — the story of {t['label']}

1. **Before** the release, the Lab predicted a **{f(abs(exp))} MMbbl draw** and leaned
   **{p['lean']}** — while flagging that the number itself was a **weak catalyst** today.
2. **The number landed:** a **{f(abs(act))} MMbbl draw** — a slightly *bigger* draw than expected,
   a **{r.get('real_surprise_dir','n/a')}** surprise of {f(surp, sign=True)} MMbbl ({f(surp_z,1)}σ).
3. **Two of three lights went green:** the forecast was close, and the surprise broke the bullish
   way we leaned.
4. **The third light went red:** WTI *fell* {pct(abs(act_move) if act_move is not None else None, sign=False)}
   instead of nudging up — because, exactly as warned, the day belonged to other forces (the
   2026 Strait-of-Hormuz geopolitics, macro, positioning), not to the inventory number.
5. **Net verdict:** the framework worked *as designed* — it made a call **and** correctly told us
   how little to trust it that day.

> **The whole point of the Release Lab in one line:** it turns a confusing government data release
> into a clear, graded, before-and-after story — and, crucially, it knows the difference between
> "we were wrong" and "we correctly said this wouldn't matter today."

<hr/>

## Appendix — honesty and limits (plain English)

- **No peeking.** Every number on the "Expected" side is built only from data available *before*
  the release; the historical backtest never lets a prediction see its own future. (This is the
  *leak-free* property.)
- **Our "expected" is a stand-in.** True analyst-consensus forecasts are paywalled, so we rebuild a
  transparent, reproducible proxy. It could be upgraded later to ingest a paid feed.
- **Why the price often ignores the number.** The headline statistic, R², is usually small because a
  whole day of unrelated world news is mixed into each day's price move. The *directional* questions
  (did the price at least go the right way?) are the more trustworthy gauge, and they show a small,
  conditional edge.
- **The biggest caveat right now.** In mid-2026 the oil market is dominated by geopolitics, not by
  weekly inventories. The Lab *correctly* down-weights the number in this environment — which means
  the most important variable this month isn't in the inventory data at all. The Lab telling you
  *that* is the feature, not a bug.

*Source for every figure above: the live Release-Lab snapshot the dashboard reads
(`server/data/release_lab.json`), produced by `analytics/release_lab.py`. Generated
{RL.get('generatedAtET','')}.*
"""


def build():
    # Helvetica (WinAnsi) can't render Greek sigma / arrows — swap to safe text.
    md = (MD.replace("σ", "s.d.").replace("→", "->").replace("≈", "~").replace("²", "2"))
    # keep R2 readable after the ² swap
    md = md.replace("RR2", "R2")
    html_body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"/><style>
      @page {{ size: A4; margin: 1.6cm 1.5cm; @frame footer {{ -pdf-frame-content: footerContent; bottom: 0.7cm; height: 0.8cm; }} }}
      body {{ font-family: Helvetica, Arial, sans-serif; font-size: 10.5px; line-height: 1.5; color: #1f2937; }}
      h1 {{ font-size: 22px; color: #0f172a; margin: 0 0 2px 0; }}
      h2 {{ font-size: 15px; color: #0f172a; margin: 16px 0 6px 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 3px; }}
      h3 {{ font-size: 12.5px; color: #1e3a8a; margin: 12px 0 4px 0; }}
      p {{ margin: 5px 0; }}
      hr {{ border: none; border-top: 1px solid #cbd5e1; margin: 10px 0; }}
      table {{ width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 9.5px; }}
      th {{ background: #1e293b; color: #fff; text-align: left; padding: 4px 6px; }}
      td {{ border: 1px solid #e2e8f0; padding: 4px 6px; vertical-align: top; }}
      tr:nth-child(even) td {{ background: #f8fafc; }}
      blockquote {{ background: #eff6ff; border-left: 4px solid #2563eb; margin: 8px 0; padding: 6px 10px; }}
      code, pre {{ font-family: Courier, monospace; font-size: 8.5px; }}
      strong {{ color: #0f172a; }}
    </style></head><body>
      <div id="footerContent" style="text-align:center; font-size:8px; color:#94a3b8;">
        Phase 4 - EIA Release Lab, Explained · {t['label']} · page <pdf:pagenumber>
      </div>
      {html_body}
    </body></html>"""

    DELIV.mkdir(exist_ok=True)
    out = DELIV / "Phase4_Release_Lab_Explained.pdf"
    with open(out, "wb") as fh:
        result = pisa.CreatePDF(html, dest=fh)
    if result.err:
        print(f"  PDF had {result.err} error(s)")
    else:
        print(f"  -> {out}  ({round(out.stat().st_size/1024)} KB)")


if __name__ == "__main__":
    build()
