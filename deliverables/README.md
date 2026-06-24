# Crude Inventory Market-Impact Framework — Deliverables

A framework + live engine to assess the market impact of the **EIA weekly crude
inventory release** (Wednesday 10:30 a.m. ET). Deep-dive on **U.S. crude**, with
gasoline & distillate cross-checked.

## What's here

| File | What it is |
|---|---|
| **`Crude_Inventory_Framework.pdf`** | The plain-English deliverable: the framework, the bullish/bearish/neutral call, the products/spreads affected, the top-3 factors, and how the live pipeline works. **Start here.** |
| **`notebook/Crude_Inventory_Framework.ipynb`** | The same analysis as an executed, step-by-step notebook — every step explained, charts + tables inline. |
| **`figures/*.png`** | The seven charts (seasonal band, expected-vs-actual, event study, conditioning R², spread sensitivity, Cushing, hit-rate). |
| **`research/research_brief.md`** | The fact-checked research brief (release mechanics, historical episodes, seasonality, Cushing/PADD mechanics, amplifiers/offsets, June-2026 backdrop) with sources. |
| **`research/inventory_analysis.json`** | All computed results (event study, conditioning, hit-rates, current read, verdict). |
| **`research/weekly_frame.csv`** | The full weekly analysis frame (stocks, WoW, expected, surprise, reactions, regime). |

## The code (in `../analytics/`)

| File | Role |
|---|---|
| **`run_all.py`** | **The single entry point — runs the whole pipeline and saves every output.** |
| `inventory_lib.py` | The shared brain: expected-build model, surprise, event study, regime/season/alignment conditioning, hit-rate, verdict logic. **Leak-free** (walk-forward; prior-years seasonality; market state read pre-release). |
| `run_inventory_analysis.py` | Stage 1: tables, the 7 figures, the results + signal JSON. |
| `inventory_engine.py` | Stage 2 — the engine: computes the surprise + verdict and cross-checks against the live WTI move. |
| `build_notebook.py` / `build_pdf.py` | Stages 3 & 4: regenerate the notebook / PDF. |

## Run it — ONE command

```bash
python analytics/run_all.py            # build every output from the latest EIA data
python analytics/run_all.py --watch    # Wednesday morning: wait for the 10:30 ET release, then build
```
On Windows, just double-click **`run_all.bat`** in the repo root. It runs all four stages in order,
saves everything to `deliverables/` and `server/data/`, and prints a checklist of what it wrote.
(Each stage above can also be run on its own.)

## Live on the dashboard

The engine writes `server/data/inventory_signal.json`; the server serves it at
**`/api/inventory-signal`**, and the **Inventories → "Inventory Release Signal"**
panel renders it live (hot-reloads). *A brand-new server route needs one server
restart (`npm run server`) to register.*
