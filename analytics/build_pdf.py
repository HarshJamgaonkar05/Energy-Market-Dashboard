"""
build_pdf.py — generate the plain-English deliverable PDF:
  deliverables/Crude_Inventory_Framework.pdf

It loads the live computed numbers (deliverables/research/inventory_analysis.json +
server/data/inventory_signal.json), weaves in the fact-checked research brief, embeds
the seven figures (base64, so nothing can fail to resolve), and renders the whole thing
to PDF with markdown + xhtml2pdf — the same pure-Python toolchain the project already
uses for its reports.

Run:  python analytics/build_pdf.py
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

import markdown
from xhtml2pdf import pisa

from common import ROOT

DELIV = ROOT / "deliverables"
FIGS = DELIV / "figures"
A = json.loads((DELIV / "research" / "inventory_analysis.json").read_text())
SIG = json.loads((ROOT / "server" / "data" / "inventory_signal.json").read_text())

cur = A["current"]; es = A["event_study"]["overall"]; hits = A["hit_rate"]
lp = SIG.get("last_print") or {}
cc = (lp.get("crosscheck") or {})


def img(name: str, width: str = "16.5cm") -> str:
    """Embed a figure as a base64 data-URI <img> so the PDF never has path issues.
    xhtml2pdf needs an ABSOLUTE width (it rejects percentages), so we size to the A4
    content width (~17cm) by default and center via a wrapping block."""
    data = base64.b64encode((FIGS / name).read_bytes()).decode()
    return (f'<div style="text-align:center;">'
            f'<img src="data:image/png;base64,{data}" style="width:{width};" /></div>')


def fmt(x, d=1, sign=False):
    if x is None:
        return "n/a"
    s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    return s


# Pull a few hit-rate cells for the prose.
hs = hits["by_season"]; ha = hits["by_alignment"]
heat = hs.get("heating", {}); drive = hs.get("driving", {})
alldraw = ha.get("all-draw", {}); mixed = ha.get("mixed", {})

# ===========================================================================
# The document (markdown). Numbers are interpolated live so the PDF always
# matches the latest run.
# ===========================================================================
MD = f"""
# Crude Oil Inventory — Market-Impact Framework

**A plain-English guide to reading the EIA weekly crude release — and a live engine that cross-checks it the moment it drops.**

*Prepared 24 June 2026 · U.S. commercial crude oil stocks (EIA Weekly Petroleum Status Report) · deep-dive series: **Crude**, with gasoline & distillate cross-checked.*

<hr/>

## 0. Read this first — what you are looking at

Every Wednesday at **10:30 a.m. New York time**, the U.S. government (the EIA) publishes how much crude oil is sitting in the country's tanks. Traders watch it closely. This document explains a **framework** — a repeatable way of thinking — for answering, *before* each release:

> **Is the upcoming inventory number likely to push oil prices up (bullish), down (bearish), or nowhere (neutral) — and which products or spreads will feel it most?**

There is **one idea** at the centre of everything here, and if you remember only one thing, remember this:

> ### The market does not react to the inventory number. It reacts to the **surprise** — how far the number lands from what everyone already expected. And even the surprise only matters **when nothing bigger is happening** in the oil market.

A 5-million-barrel *draw* (a fall in stocks, normally bullish) is actually **bearish** if everyone expected a 10-million draw. A *build* (a rise, normally bearish) is **bullish** if everyone braced for a bigger one. So the entire framework is built to (1) measure the surprise properly, and (2) judge how much that surprise should matter **given the conditions of the day**.

<hr/>

## 1. The deliverable — our call for the 24 June 2026 release

**Expectation: structurally BULLISH backdrop, but the release itself is a LOW-IMPACT (≈ neutral) same-day catalyst this week — down-weight it.**

This sounds like a contradiction; it isn't. The framework deliberately separates two things most people blur together:

- **The structural backdrop is bullish.** U.S. crude stocks are **{fmt(cur['crude_stock'],1)} million barrels**, which is **{fmt(abs(cur['crude_z']),2)} standard deviations *below* the 5-year seasonal norm** — genuinely tight for the time of year. Stocks have drawn for four straight weeks, refineries are running flat-out (**{fmt(cur['refutil'],1)}% utilization**), and **Cushing — the delivery point for WTI futures — has drained to ~{fmt(cur['cushing'],1)} million barrels, near tank-bottom operating lows.** All bullish.
- **But the release is unlikely to be the thing that moves price this week.** We are in **summer driving season**, in a **high-volatility** regime, with **crude and products giving mixed signals** — empirically the *weakest* combination for inventory reactions (more on this below). On top of that, the oil market in June 2026 is being driven by a **geopolitical crisis (the Strait of Hormuz)**, not by weekly stocks. When a 10-million-barrel-a-day supply threat is in play, a weekly U.S. inventory wiggle is a rounding error.

**The asymmetry that matters:** the model already expects a **draw of about {fmt(cur['expected_next'],1)} million barrels**, so a draw is largely *priced in*. The bigger surprise risk is therefore a **build** (which would be cleanly bearish). A draw merely in line confirms the bullish structure but adds little new.

### The three factors driving this view

1. **Surprise-in-context, and it's largely priced.** Stocks are structurally tight ({fmt(cur['crude_z'],2)}σ below the seasonal norm), but the market expects a continued draw (~{fmt(cur['expected_next'],1)} MMbbl). A surprise only comes from *beating or missing* that expectation — and a draw is the consensus, so the bullish case is partly in the price already.
2. **The regime is hostile to the signal.** In **driving season** the inventory print has moved WTI the "right" way only **{fmt(drive.get('hit_rate',0)*100,0)}% of the time** (a coin-flip), versus **{fmt(heat.get('hit_rate',0)*100,0)}% in winter heating season**. Add high volatility and the **Strait-of-Hormuz risk premium**, and inventories are simply not the marginal driver this week. (Proof: the last print, released 17 June, was a bullish **{fmt(lp.get('surprise'),1)}-MMbbl draw beat — and WTI still fell {fmt(cc.get('wti_reaction_pct'),1)}%**, swamped by Hormuz-reopening headlines.)
3. **Composition is the one tradeable signal — via Cushing, not the headline.** The national number is noisy, but **Cushing draining toward operating lows** is a clean, structural bullish force for the **WTI front-month time-spread** (it pushes the curve into backwardation). That is where the inventory story is genuinely worth expressing right now. *(The regime at work: the last print, 17 June, was a bullish {fmt(lp.get('surprise'),1)}-MMbbl draw beat — and it moved WTI just {fmt(cc.get('wti_reaction_pct'),1)}% on the day, a footnote next to the multi-session, Hormuz-driven swings around it.)*

### Products / spreads most likely to be affected (ranked)

*Ranked by the measured release-day sensitivity to the crude surprise (from the event study):*

| Rank | Instrument | Why |
|---|---|---|
| 1 | **WTI outright** | The U.S. crude benchmark; most sensitive of any instrument tested (corr {fmt(es['corr'],2)} overall). |
| 2 | **Brent** | Reacts slightly less than WTI to a *U.S.* number (it is the global benchmark). |
| 3 | **HO / 3-2-1 cracks** | Respond more to the **product** surprises (gasoline, distillate) than to crude; watch when crude and products diverge. |
| — | **Brent–WTI** | Barely moves on the headline crude number; it is an arb/quality spread, not an inventory play. |

**Structural pick (not by headline correlation): the WTI M1–M2 calendar spread.** Its *same-day* correlation with the crude surprise is low, but it is the cleanest way to express the current **Cushing** draw without taking flat-price or geopolitical risk — which is why, in this regime, it is the most *tradeable* inventory signal even though the outright is the most *reactive*.

<hr/>

## 2. How the EIA release actually works

- **What:** the *Weekly Petroleum Status Report (WPSR)* — the official count of U.S. crude and product stocks plus the flows behind them (production, imports, exports, refinery runs).
- **When:** **Wednesday 10:30 a.m. ET.** A federal holiday in the week pushes it to **Thursday**. (This week, 24 June, is a normal Wednesday.)
- **Which week:** the data describe the week that **ended the prior Friday**, so a Wednesday print is ~5 days behind reality.
- **The night before:** a private body, the **American Petroleum Institute (API)**, publishes its own estimate ~**4:30 p.m. ET Tuesday**. Traders treat it as a preview, so part of the EIA surprise is often already absorbed before 10:30 Wednesday.
- **Fast vs. slow feeds:** the numbers hit EIA's release server `ir.eia.gov` to-the-second at 10:30; the **Open-Data API we poll updates within ~2 hours**. Our live engine accounts for this by polling until the new value appears.
- **Reliability:** weekly figures are **preliminary** (EIA surveys ~90% of industry and estimates the rest); they get re-benchmarked later against the monthly data. Treat the weekly as a *fast, noisy proxy*.

<hr/>

## 3. The framework, step by step

### Step 1 — Build an "expected" number (our stand-in for consensus)

The real analyst consensus is paywalled, so we **reconstruct an expectation** from information available the day before the release — with no peeking at the answer. We predict this week's change from three ingredients:

- the **seasonal-normal change** for this calendar week (averaged over the prior 5 years),
- **last week's change** (draws and builds cluster — momentum persists), and
- **last week's supply/demand balance** (the flows are sticky week to week).

The model is fit **walk-forward** (every week is predicted using only earlier weeks), so it never cheats. The **surprise = actual − expected.**

{img('02_actual_vs_expected.png')}

*Bars are what actually happened (green = draw, red = build); the blue line is what the model expected. The gap between them is the surprise.*

### Step 2 — Does the surprise actually move oil? (The event study)

For **every** historical release ({A['sample']['n_releases']} of them, {A['sample']['from']} → {A['sample']['to']}) we measure WTI's release-day move and plot it against the surprise. If inventories drive price, bigger-than-expected builds should push price down — a **downward slope**.

{img('03_event_study_scatter.png', '11.5cm')}

The slope **is** negative (correct direction), but the **R² is tiny (~{fmt(es['r2']*100,0)}%)**: on an *average* day, the headline crude surprise explains almost none of WTI's move. **This is the honest, central finding** — most days, macro, OPEC and geopolitics swamp the inventory signal. The framework's value is knowing **when** the signal cuts through.

### Step 3 — When inventories matter, and when they don't (the heart of it)

We slice the same relationship by the **market conditions known before each release**, using a **directional hit-rate**: on *material* surprises, how often did WTI move the way the surprise predicted? 50% is a coin-flip; above 50% is a real edge.

{img('07_hit_rate.png')}

The pattern is clear and consistent:

- **Inventories MATTER** in **winter heating season** ({fmt(heat.get('hit_rate',0)*100,0)}% hit-rate), when **crude and products draw/build together** (all-draw {fmt(alldraw.get('hit_rate',0)*100,0)}%), and in **normal-volatility** markets.
- **Inventories get IGNORED** in **summer driving season** ({fmt(drive.get('hit_rate',0)*100,0)}%), when crude and products **diverge** (mixed {fmt(mixed.get('hit_rate',0)*100,0)}%), and in **high-volatility / shock** regimes.

> **Rule of thumb:** trust the inventory print most when it's winter, the products agree, and volatility is normal. Discount it when it's summer, the signals diverge, or something bigger (OPEC, war, macro) is driving the tape.

### Step 4 — Seasonality: why a build can still be bullish

Crude stocks follow a calendar — they **build in winter/spring** (refineries slow for maintenance) and **draw through summer** (refineries run hard for gasoline). So the question is never "did stocks rise?" but "did they rise **more or less than the season says they should?**"

{img('01_crude_seasonal_band.png')}

*The red last-3-months line has plunged from the top of the normal 5-year band down through the average — a textbook bullish tightening for this time of year.*

### Step 5 — Composition: *where* the barrels are beats the headline

A build is not a build. Two questions decide what it means:

- **Where?** **Cushing, Oklahoma** is the delivery point for WTI futures (~76 MMbbl of storage, ~13% of U.S. capacity). When Cushing drains toward tank-bottoms, the WTI curve tightens into **backwardation** — a powerful, *structural* signal independent of the headline. When it fills toward its limit, the front-month price can detach entirely (this is what produced **negative WTI in April 2020**).
- **Why?** A build from **weak refining** (bearish demand) means something very different from a build from **strong imports** or **low exports**. The flows tell us which.

{img('06_cushing_trend.png')}

*Cushing has drained to ~{fmt(cur['cushing'],1)} MMbbl — into the operational-low zone. This is the single most bullish, most tradeable inventory signal right now.*

### Step 6 — Amplifiers and offsets

Inventories are one input. On any day these can magnify or cancel the read:

| Driver | Amplifies the signal when… | Offsets / flips it when… |
|---|---|---|
| **OPEC+ policy** | OPEC is adding barrels into a build | a surprise cut overrides a build |
| **Geopolitics** | a risk premium is already bidding crude | a war scare (or its unwind) swamps a draw |
| **US dollar / macro** | a weak dollar / risk-on day reinforces a draw | a strong dollar / risk-off day buries it |
| **Product cracks** | crude and products move together | crude draws while products build (mixed = muddy) |
| **Positioning (CFTC)** | stretched longs/shorts exaggerate the move | light positioning mutes it |

This is exactly why our verdict is **damped by the regime**: the same surprise is worth more on a quiet winter day than on a noisy, war-driven summer one.

<hr/>

## 4. The current backdrop — June 2026 (why we down-weight this release)

> The June-2026 picture below is the working market narrative, fact-checked against the available record; a few specific figures are single-source and flagged as such in the research appendix.

**The dominant story is geopolitics, not inventories.** A **Strait of Hormuz crisis** that began **28 February 2026** (a chokepoint that normally carries ~20% of seaborne oil) drove Brent from the $70s to a peak near **$126**. Since mid-June the market has whipsawed on diplomacy: a multi-session **~$17/bbl Brent slide** into 17 June on reopening hopes, then a reversal on **22 June** (Brent −3.3%, WTI −2.3%) on renewed closure threats. In this environment, **the weekly EIA print is being heavily overridden by the risk premium.** Our framework's own cross-check shows the regime at work: the **17 June draw beat moved WTI only {fmt(cc.get('wti_reaction_pct'),1)}% on release day** — a footnote next to those Hormuz-driven, multi-session swings. The fundamentals are quietly bullish but **subordinate to the headlines.**

The underlying fundamentals are quietly bullish (tight stocks, draining Cushing, ~{fmt(cur['refutil'],1)}% runs), but they are **subordinate to the headlines** until Hormuz resolves.

<hr/>

## 5. How the pipeline works

One command — `python analytics/run_all.py` (or double-click `run_all.bat`) — rebuilds the whole
framework end to end and saves every output:

```
   +---------------------------------------------------------------+
   |  EIA Open-Data API   (crude, Cushing, flows, gasoline, dist.) |
   |  Yahoo Finance       (live WTI / Brent / products)            |
   +-------------------------------+-------------------------------+
                                   |  fetch (fresh)
                                   v
        analytics/inventory_lib.py  ----  the shared brain  ----
          - expected build (walk-forward seasonal + balance + momentum)
          - surprise  +  event study  +  regime conditioning + hit-rate
                                   |
                           run_all.py  (one command: runs all four in order)
   +----------------------+----------------------+
            v                      v                      v
   run_inventory_         inventory_engine.py       build_notebook.py
   analysis.py            - one-shot, or --watch     build_pdf.py
   - tables + figures       to wait for the 10:30    - the explained
   - inventory_             ET release               Jupyter notebook
     analysis.json        - surprise + verdict      - this PDF
                          - CROSS-CHECK vs WTI
                          - writes inventory_signal.json + log
                                   |
                                   v
   server/index.js  ->  /api/inventory-signal  ->  Dashboard panel
                                                   "Inventory Release Signal"
                                                   (hot-reloads, live)
```

**The engine (`analytics/inventory_engine.py`)** is the live piece:
1. `--watch` polls the EIA API around Wednesday 10:30 ET until a **new** print lands;
2. it computes the **surprise** and a **verdict** (bullish/bearish/neutral), damped by how strongly inventories drive WTI in the current regime;
3. it **cross-checks** the call against the **live WTI move** (CONFIRMED / CONTRADICTED);
4. it writes `server/data/inventory_signal.json`, which the dashboard's **Inventory Release Signal** panel reads live, and appends to a track-record log.

**The most recent cross-check on record** (week of {lp.get('period','n/a')}): the inventory surprise (a **{fmt(lp.get('surprise'),1)}-MMbbl** draw beat) *implied* WTI should rise; on the release day WTI moved **{fmt(cc.get('wti_reaction_pct'),1)}%**, so the surprise read was **{(cc.get('status','n/a')).upper()}**. The framework's verdict was deliberately **{(lp.get('verdict') or {{}}).get('direction','n/a')}** (low-conviction) — because in this geopolitics-dominated regime the *multi-day* move (a ~$17/bbl Hormuz-driven slide that week) dwarfs whatever the print does on the day. The lesson: day-of confirmation is not a tradeable edge when a bigger force is in control.

### How to run the whole thing — ONE command

Everything (data -> analysis -> figures -> engine + cross-check -> notebook -> this PDF) is
rebuilt and saved by a single script:

```text
python analytics/run_all.py            # build every output from the latest EIA data
python analytics/run_all.py --watch    # Wednesday morning: wait for the 10:30 a.m. ET
                                       #   release, THEN build everything with the fresh print
```
On Windows you can just double-click **run_all.bat** in the repo root. It saves all outputs to
`deliverables/` and `server/data/`, then prints a checklist of exactly what it wrote. (Each stage
can still be run on its own — `run_inventory_analysis.py`, `inventory_engine.py`,
`build_notebook.py`, `build_pdf.py` — but `run_all.py` does all four in order.)

<hr/>

## 6. The deliverables, checklist

| Asked for | Where it is |
|---|---|
| **Bullish / bearish / neutral expectation** | Section 1 (and live in the engine / dashboard panel) |
| **Products / spreads most affected** | Section 1 ranked table (WTI outright, WTI calendar via Cushing, Brent, cracks) |
| **Top-3 factors** | Section 1 ("three factors driving this view") |
| **The framework explained** | Sections 2–3 (surprise vs consensus, conditioned on regime/season/alignment) |
| **A notebook with everything explained** | `deliverables/notebook/Crude_Inventory_Framework.ipynb` |
| **A live cross-check engine** | `analytics/inventory_engine.py` → dashboard panel (all rebuilt by `run_all.py`) |
| **This plain-English PDF** | you're reading it |

<hr/>

## Appendix — method, honesty, and limits

- **Sample:** {A['sample']['n_releases']} weekly releases, {A['sample']['from']} → {A['sample']['to']}; reactions measured as WTI's release-day close-to-close return (Yahoo continuous front).
- **Leak-free by construction:** the expected-build model is fit **walk-forward** (only past weeks); the seasonal norm uses **prior years only**; the regime context is read **as of the day before** each release. Nothing in the historical study can see its own future.
- **Why R² looks low:** we only have daily closes, so each reaction includes a full day of unrelated news. The *intraday* 10:30–11:00 window would show a much cleaner relationship — the daily figure *understates* the true release-moment effect. The **directional hit-rate** is the more robust, trader-relevant measure, and it shows a clear, conditional edge.
- **Consensus proxy:** our "expected" is a model, not the paywalled analyst median or the API preview. It is a transparent, reproducible stand-in; the live engine could be upgraded to ingest the API Tuesday print if a subscription is available.
- **Biggest caveat right now:** the June-2026 market is geopolitics-dominated. The framework *correctly* down-weights inventories in this regime — but that means the most important variable this month is not in the inventory data at all. The framework tells you *that*, which is the point.

*Research sources (mechanics, episodes, seasonality, current backdrop): EIA.gov (WPSR schedule, Today-in-Energy, STEO), API WSB, StoneX, U.S. Treasury, CNBC/CNN/Al Jazeera, IEA OMR. Full source list in `deliverables/research/research_brief.md`.*
"""


def build():
    # Normalise glyphs that base-14 Helvetica (WinAnsi) cannot render to safe
    # equivalents (Greek sigma, arrows). Em-dash / middot / bullet / superscript-2
    # are all in WinAnsi and render fine, so we keep them.
    md = (MD.replace("σ", " s.d.").replace("→", "->").replace("►", ">").replace("◄", "<"))
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
      pre {{ background: #0f172a; color: #e2e8f0; padding: 8px; border-radius: 4px; line-height: 1.25; }}
      img {{ margin: 6px 0; }}
      strong {{ color: #0f172a; }}
    </style></head><body>
      <div id="footerContent" style="text-align:center; font-size:8px; color:#94a3b8;">
        Crude Inventory Market-Impact Framework · generated {A['generatedAt'][:10]} · page <pdf:pagenumber>
      </div>
      {html_body}
    </body></html>"""

    out = DELIV / "Crude_Inventory_Framework.pdf"
    with open(out, "wb") as fh:
        result = pisa.CreatePDF(html, dest=fh)
    if result.err:
        print(f"  PDF had {result.err} error(s)")
    else:
        print(f"  -> {out}  ({round(out.stat().st_size/1024)} KB)")


if __name__ == "__main__":
    build()
