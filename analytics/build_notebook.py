"""
build_notebook.py — assemble (and execute) the explained Jupyter notebook
`deliverables/notebook/Crude_Inventory_Framework.ipynb`.

Every analytical step is preceded by a plain-English markdown cell so a non-specialist
can follow the whole framework. We build the cells with nbformat, then run them with
nbconvert so the outputs (tables + charts) are embedded in the saved file.

Run:  python analytics/build_notebook.py
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "deliverables" / "notebook"
OUT.mkdir(parents=True, exist_ok=True)
NB_PATH = OUT / "Crude_Inventory_Framework.ipynb"

cells = []
def md(t): cells.append(new_markdown_cell(t))
def code(t): cells.append(new_code_cell(t.strip()))


# ---------------------------------------------------------------------------
md(r"""# Crude Oil Inventory — Market-Impact Framework
### A step-by-step, plain-English notebook · *Wednesday assignment*

**The job.** Every Wednesday at 10:30 a.m. ET the U.S. Energy Information Administration (EIA)
tells the world how much crude oil sits in U.S. tanks. This notebook builds a *framework* to
answer one question before each release: **is the upcoming print likely bullish, bearish, or
neutral for oil — and which products/spreads will feel it most?**

**The one idea you must keep in mind.** The market does **not** react to the raw inventory
number. It reacts to the **surprise** — how far the number lands from what traders already
*expected*. A 5-million-barrel draw is *bearish* if everyone expected a 10-million draw, and
*bullish* if everyone expected a build. So the whole framework is built around measuring the
surprise and then judging how much that surprise should move the market **given the conditions
of the day**.

**What this notebook walks through (each section is explained before any code runs):**
1. How the EIA release actually works (timing, what's in it).
2. Building an **expected** build/draw — our stand-in for the paywalled analyst consensus.
3. The **surprise**, and an **event study**: does the surprise actually move WTI?
4. **When inventories mattered and when they didn't** (the heart of the assignment).
5. **Seasonality** — why a build can still be bullish.
6. **Cushing & composition** — why *where* the barrels are matters more than the headline.
7. **Other drivers** that amplify or offset the inventory signal.
8. **Which products/spreads** react most.
9. The **current read** and the **verdict**.
10. The **live engine** and how the whole pipeline fits together.

> Everything here is deliberately *interpretable*: every number can be traced back to the
> driver that produced it.""")

md(r"""## 0 · Setup — what we load and why

We pull three things:
- **EIA weekly data** — crude stocks, Cushing, refinery utilization, and the supply/demand flows
  (production, imports, exports, refinery runs). This is the fundamental picture.
- **Fresh daily oil prices** (WTI, Brent) from Yahoo Finance — so we can measure how oil *moved*
  on each release day.
- **A pre-built daily price/spread panel** (2021→today) — so we can also test calendar spreads
  and crack spreads, not just the outright price.

The single function `lib.analyze(...)` runs the **entire** pipeline (expected build → surprise →
event study → conditioning → hit-rate) and hands back the results. The same function powers the
live engine and the batch report, so the notebook can never disagree with them.""")

code(r"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from IPython.display import Image, display

# Find the repo + analytics package no matter where this notebook is opened from.
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'analytics' / 'inventory_lib.py').exists())
sys.path.insert(0, str(ROOT / 'analytics'))
import inventory_lib as lib

plt.rcParams.update({'figure.figsize': (9, 4), 'figure.dpi': 110, 'axes.grid': True,
                     'grid.alpha': .25, 'axes.spines.top': False, 'axes.spines.right': False})
pd.set_option('display.float_format', lambda x: f'{x:,.2f}')

# Pull the data and run the whole framework in one call.
weekly = lib.fetch_weekly(length=600)
prices = lib.fetch_prices()
panel  = lib.load_panel()
A = lib.analyze(weekly, prices, panel)
f, es = A['frame'], A['event_study']

print(f"EIA weekly data : {len(weekly)} weeks  ({weekly.index.min().date()} -> {weekly.index.max().date()})")
print(f"Prices          : {list(prices.columns)}  through {prices.index.max().date()}")
print(f"Event-study set  : {len(A['es_df'])} releases  ({A['es_df']['period'].min().date()} -> {A['es_df']['period'].max().date()})")
""")

md(r"""## 1 · How the EIA release works

- **What:** the *Weekly Petroleum Status Report (WPSR)* — the official count of U.S. crude and
  product stocks, plus the flows behind them (production, imports, exports, refinery runs).
- **When:** **Wednesdays at 10:30 a.m. ET**. (When a Monday holiday falls in the week it slips to
  **Thursday**.) The numbers refer to the week that ended the **prior Friday**, so there is a ~5-day lag.
- **The night before:** a private body, the **American Petroleum Institute (API)**, publishes its
  own estimate ~4:30 p.m. ET Tuesday. Traders use it as a *preview*, so part of the EIA surprise is
  often already absorbed before 10:30 Wednesday.
- **Why it moves markets:** inventories are the cleanest weekly read on whether the U.S. oil
  market is *tightening* (draws) or *loosening* (builds).

Below are the most recent weeks. **Negative WoW = a draw (bullish), positive = a build (bearish).**""")

code(r"""
cols = ['period', 'crude', 'crude_wow', 'cushing', 'cushing_wow', 'refutil', 'season']
display(f[cols].dropna(subset=['crude_wow']).tail(8).set_index('period').round(1))
""")

md(r"""## 2 · The "expected" build — our consensus proxy

The real analyst consensus (Reuters/Bloomberg polls) is **paywalled**, so we rebuild an
*expectation* from information available the **day before** the release — no peeking at the answer:

> **expected change = walk-forward regression of**  (seasonal-normal change, last week's change, last
> week's supply/demand balance).

- **Seasonal-normal change** — what this calendar week *usually* does (averaged over the prior 5
  years). Crude has a strong seasonal rhythm.
- **Last week's change** — draws and builds cluster; momentum persists.
- **Last week's balance** — the flows (production + imports − refinery runs − exports) are sticky
  week to week, so last week's balance forecasts this week's draw/build.

The model is fit **walk-forward** (each week is predicted using only earlier weeks), so it never
cheats. The **surprise = actual − expected**. The chart shows the last ~6 months: blue dots are
what the model expected; bars are what actually happened (green = draw, red = build). The *gap*
between them is the surprise.""")

code(r"""
recent = f.dropna(subset=['crude_wow']).tail(26)
fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(recent['period'], recent['crude_wow'], width=4,
       color=['#16a34a' if v < 0 else '#dc2626' for v in recent['crude_wow']], alpha=.55, label='Actual WoW change')
ax.plot(recent['period'], recent['expected'], color='#2563eb', marker='o', ms=4, lw=1.5, label='Model expected')
ax.axhline(0, color='#94a3b8', lw=.8)
ax.set_title('Actual vs Expected weekly crude change (MMbbl)  ·  green = draw (bullish), red = build')
ax.legend(); plt.show()

s = f.dropna(subset=['surprise']).iloc[-1]
print(f"Latest week {s['period'].date()}:  expected {s['expected']:+.1f},  actual {s['crude_wow']:+.1f}"
      f"  ->  SURPRISE {s['surprise']:+.1f} MMbbl  ({s['surprise_z']:+.1f} sigma)")
""")

md(r"""## 3 · Event study — does the surprise actually move WTI?

For **every** historical release we measure WTI's **release-day return** (the move from the prior
close to the release-day close) and plot it against the surprise. If inventories drive price, a
**bigger-than-expected build** (positive surprise, right side) should push price **down**, so the
cloud should slope **downward** and the regression line should have a **negative slope**.""")

code(r"""
es_df = A['es_df']; o = es['overall']
fig, ax = plt.subplots(figsize=(7.5, 5))
ax.scatter(es_df['surprise'], es_df['rxn_wti'] * 100, s=16, alpha=.5, color='#2563eb', edgecolor='none')
xs = np.linspace(es_df['surprise'].min(), es_df['surprise'].max(), 50)
ax.plot(xs, (o['intercept'] + o['beta'] * xs) * 100, color='#dc2626', lw=2,
        label=f"slope {o['beta']*100:.3f}%/MMbbl · R²={o['r2']:.3f} · t={o['t_stat']:.1f}")
ax.axhline(0, color='#cbd5e1', lw=.7); ax.axvline(0, color='#cbd5e1', lw=.7)
ax.set_xlabel('Surprise = actual − expected  (MMbbl;  ◄ draw   build ►)')
ax.set_ylabel('Release-day WTI return (%)')
ax.set_title('Event study: WTI reaction vs inventory surprise'); ax.legend(); plt.show()
print(f"Overall: n={o['n']}, slope={o['beta']*100:.3f}%/MMbbl, R²={o['r2']:.3f}, corr={o['corr']:.2f}, t={o['t_stat']:.1f}")
""")

md(r"""**How to read this.** The slope is **negative** (correct sign: bigger builds → lower prices),
but the **R² is tiny (~1%)** and the t-stat is weak. In plain English: *on an average day, the
headline crude surprise explains almost none of WTI's move.* That is not a bug — it is the central,
honest finding. Most days, **macro, OPEC headlines and positioning swamp the inventory signal.**
The framework's value is knowing **when** the signal cuts through — which is the next section.""")

md(r"""## 4 · When did inventories matter — and when didn't they?

We slice the same relationship by the **market conditions** known *before* each release. Two lenses:

- **R²** — how much of the day's move the surprise explains (higher = stronger driver).
- **Directional hit-rate** — on *material* surprises (≥ ~half a normal miss), how often did WTI move
  the way the surprise predicted? 50% is a coin-flip; above 50% is a real edge.""")

code(r"""
def tbl(d):
    return pd.DataFrame({k: {'n': v['n'], 'corr': round(v['corr'], 2), 'R2': round(v['r2'], 3),
                             'slope %/MMbbl': round(v['beta'] * 100, 3)} for k, v in d.items()}).T
print('Reaction-vs-surprise by SEASON:');           display(tbl(es['by_season']))
print('Reaction-vs-surprise by VOLATILITY regime:'); display(tbl(es['by_vol_regime']))
print('Reaction-vs-surprise by PRODUCT ALIGNMENT:'); display(tbl(es['by_alignment']))
""")

code(r"""
h = A['hit_rate']
print('Directional hit-rate on material surprises (|z| >= 0.5).  Overall:',
      {k: h['overall'][k] for k in ('n_material', 'hit_rate', 'edge_vs_coinflip')})
def htbl(d):
    return pd.DataFrame({k: {'n': v['n_material'], 'hit_rate': v['hit_rate'],
                             'edge_vs_50%': v['edge_vs_coinflip'], 'avg_fav_%': v['avg_fav_move_pct']}
                         for k, v in d.items()}).T
print('\nBy SEASON:');    display(htbl(h['by_season']))
print('By ALIGNMENT:');   display(htbl(h['by_alignment']))
display(Image(str(ROOT / 'deliverables' / 'figures' / '07_hit_rate.png')))
""")

md(r"""**The verdict of this section (the assignment's core).** Inventories are a **conditional**
signal:

- **They matter** in **heating season** (winter), when **crude *and* products draw/build together**
  (a clean, corroborated signal), and in **normal-volatility** regimes — hit-rates of **65-71%**.
- **They get ignored** in **summer driving season**, when **crude and products diverge** ("mixed"),
  and in **high-volatility** regimes where macro/geopolitics dominate — hit-rates near a **coin-flip**.

So the framework's rule of thumb: *trust the inventory print most when the season is heating, the
products agree, and volatility is normal; discount it when it's summer, the signals diverge, or
the tape is being driven by something bigger.*""")

md(r"""## 5 · Seasonality — why a build can still be bullish

Crude stocks follow a calendar: they tend to **build in winter/early spring** (refineries slow for
maintenance) and **draw through summer** (refineries run flat-out for gasoline). So the right
question is never "did stocks rise?" but "did they rise **more or less than the season says they
should?**" Our `crude_z` measures exactly that: today's level versus the 5-year norm for this week.
Below, the red **last-3-months** line shows where we sit inside the normal seasonal envelope.""")

code(r"""
display(Image(str(ROOT / 'deliverables' / 'figures' / '01_crude_seasonal_band.png')))
last = f.dropna(subset=['crude_wow']).iloc[-1]
print(f"Crude now: {last['crude']:.0f} MMbbl, which is {last['crude_z']:+.2f} sigma vs the 5-year "
      f"seasonal norm  ->  {'TIGHTER (bullish)' if last['crude_z'] < 0 else 'LOOSER (bearish)'} than normal.")
""")

md(r"""## 6 · Cushing & composition — *where* the barrels are matters more than the headline

A draw is not a draw. **Two questions decide what it means:**

1. **Where?** **Cushing, Oklahoma** is the physical delivery point for NYMEX **WTI** futures. When
   Cushing drains toward tank-bottoms (~20 MMbbl), WTI's nearby time-spreads tighten
   (backwardation) — a powerful, *structural* WTI signal independent of the headline.
2. **Why?** A build from **weak refining** (bearish demand) is very different from a build from
   **strong imports** or **low exports**. The flows tell us which.

Below: the Cushing trend, then the weekly flow decomposition that explains each build/draw.""")

code(r"""
display(Image(str(ROOT / 'deliverables' / 'figures' / '06_cushing_trend.png')))
flows = ['period', 'production', 'imports', 'runs', 'exports', 'implied_balance', 'crude_wow']
have = [c for c in flows if c in f.columns]
print('Weekly crude flows (kbd) and the implied balance (MMbbl) behind the build/draw:')
display(f[have].dropna().tail(6).set_index('period').round(1))
""")

md(r"""## 7 · Other drivers that amplify or offset the inventory signal

Inventories are one input. On any given day these can **magnify** or **cancel** the read:

| Driver | Amplifies when… | Offsets when… |
|---|---|---|
| **OPEC+ policy** | a surprise build lands while OPEC is *adding* barrels | a draw is dismissed because OPEC just signalled more supply |
| **Geopolitics** (Middle East, Russia, Hormuz) | a risk premium is already bidding crude | a ceasefire/de-escalation overwhelms a bullish draw |
| **Macro** (US dollar, Fed, China demand, equities) | a weak dollar / risk-on day reinforces a draw | a strong dollar / risk-off day buries a draw |
| **Product cracks** | crude **and** gasoline/distillate move together | crude draws but products build (mixed = muddy) |
| **Positioning** (CFTC managed money) | stretched longs/shorts force an exaggerated move | light positioning mutes the reaction |

This is why our verdict is **damped by the regime**: the same surprise is worth more on a quiet,
heating-season, aligned day than on a noisy, summer, macro-driven one.""")

md(r"""## 8 · Which products and spreads react most?

We rank every instrument by how strongly its release-day move correlates with the crude surprise.
**WTI outright** reacts most (it is the U.S. crude benchmark); Brent slightly less; the **spreads**
(Brent-WTI, WTI calendar, the 3-2-1 crack) barely move on the *headline crude* number — they
respond more to **Cushing** and to the **product** surprises. That tells us where to express a view.""")

code(r"""
sdic = A['spread_sensitivity']
display(pd.DataFrame({k: {'n': v['n'], 'corr_with_surprise': v['corr'], 'R2': v['r2']}
                      for k, v in sdic.items() if k not in ('panel_wti', 'panel_brent')}).T)
""")

md(r"""## 9 · The current read and the verdict

Putting it together for the **upcoming** release. Before the number lands we have no surprise yet,
so the lean comes from the **structural backdrop** — where stocks sit vs the seasonal norm, the
recent draw/build momentum, the Cushing trend, the season, and product alignment. The verdict
separates two layers most people conflate:
- the **structural lean** (is the backdrop bullish or bearish?), and
- the **release-day catalyst strength** (will *this print* actually move the tape, given the regime?).""")

code(r"""
last = f.dropna(subset=['crude_wow']).iloc[-1]
rel_r2, rel_n, rel_beta = lib.reliability_for(es, last['vol_regime'])
sens_top = [k for k in A['spread_sensitivity'] if k not in ('panel_wti', 'panel_brent')][:5]
ctx = {'vol_regime': last['vol_regime'], 'wti_struct': last['wti_struct'],
       'product_alignment': last['product_alignment'], 'products': sens_top}
v = lib.forward_base_case(f, ctx, rel_r2, rel_n)

print(f"Regime: {last['vol_regime']} vol / {last['wti_struct']} / {last['season']} / align={last['product_alignment']}")
print(f"Reliability (R² of reaction~surprise in this regime): {rel_r2:.2f}  (n={rel_n})\n")
print(f">>> VERDICT: {v.direction}   (confidence {v.confidence})\n")
print(v.headline + "\n")
print("Top factors:")
for i, fac in enumerate(v.factors, 1):
    print(f"  {i}. {fac}")
print("\nMost-affected products/spreads:", ", ".join(sens_top))
""")

md(r"""## 10 · The live engine & the pipeline

The same framework runs **live**. `analytics/inventory_engine.py`:
1. polls the EIA API around Wednesday 10:30 ET (`--watch`),
2. the moment a **new** print lands, computes the **surprise** and a **verdict**,
3. **cross-checks** the call against the **live WTI move** (confirmed / contradicted), and
4. writes `server/data/inventory_signal.json`, which the dashboard's **Inventory Release Signal**
   panel reads, and appends to a track-record log.

Below is the current engine snapshot (the pre-release base case for the next release, plus the last
published print scored against the market).""")

code(r"""
sig = json.load(open(ROOT / 'server' / 'data' / 'inventory_signal.json'))
print('stage           :', sig['stage'])
print('next release est :', sig['next_release_est'])
fwd = sig['forward']
print(f"forward verdict  : {fwd['direction']}  (confidence {fwd['confidence']})")
lp = sig.get('last_print')
if lp:
    cc = lp['crosscheck']
    print(f"last print       : {lp['period']}  surprise {lp['surprise']:+.1f} MMbbl ({lp['surprise_z']:+.1f}σ)"
          f"  ->  verdict {lp['verdict']['direction']}")
    print(f"market crosscheck: {cc['status'].upper()}  (WTI {cc['wti_reaction_pct']:+.2f}% on the print)")
""")

md(r"""## Deliverables & how to run everything

**Deliverables (for Thursday):**
- **Expectation:** bullish / bearish / neutral — produced by the framework (Section 9) and live engine.
- **Products/spreads most affected:** ranked in Section 8 (WTI outright first; Cushing drives WTI
  calendar; products drive the cracks).
- **Top-3 factors:** the verdict's factor list (Section 9).
- **The framework itself:** Sections 1-7 — surprise vs consensus, conditioned on regime/season/alignment.

**How to run the pipeline:**
```text
python analytics/run_inventory_analysis.py   # rebuild tables + figures + the signal JSON
python analytics/inventory_engine.py          # one-shot assessment (pre-release base case + last print)
python analytics/inventory_engine.py --watch  # poll EIA on Wed ~10:30 ET, assess + cross-check live
python analytics/build_notebook.py            # rebuild this notebook
```
The dashboard panel (**Inventories → Inventory Release Signal**) reads the engine's JSON live and
hot-reloads. A scheduled routine runs the `--watch` engine automatically each Wednesday morning.""")


# ---------------------------------------------------------------------------
nb = new_notebook(cells=cells)
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nb.metadata["language_info"] = {"name": "python"}

nbf.write(nb, NB_PATH)
print(f"Wrote {NB_PATH} ({len(cells)} cells). Executing ...")

# Execute so outputs (tables + charts) are embedded.
from nbconvert.preprocessors import ExecutePreprocessor
ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
ep.preprocess(nb, {"metadata": {"path": str(ROOT)}})
nbf.write(nb, NB_PATH)
print(f"Executed and saved {NB_PATH}")
