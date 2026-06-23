# Voltaire Energy Terminal — Project Submission

### An energy-markets intelligence terminal with a regime-driven trading strategy

This is the standalone submission document. It is written to be read on its own, **assuming no
prior knowledge** of trading — it starts from "what is oil," builds the vocabulary, then explains
what was built and what the results mean. The deep companions are `docs/PROJECT_REPORT.md`,
`docs/STRATEGY.md`, `docs/FINAL_BACKTESTING_REPORT.md`, and `Backtesting/IDEATION.md`.

---

## 1. A five-minute primer (assume you know nothing)

- **Oil isn't one price.** Two benchmark crudes dominate — **WTI** (American, code `CL`) and
  **Brent** (global, code `CO`) — and each is traded not just for today but for delivery in
  specific *future months*. Each "month" is a **futures contract**; one contract is **1,000
  barrels**, so a $1.00 move is worth **$1,000**.
- **The forward curve** is those monthly prices in order. Near months pricier than far months =
  **backwardation** (tight supply); cheaper = **contango** (glut). 2021–2026 was mostly
  backwardated.
- **A spread is the gap between two related prices**, and it's what we trade. We **buy one leg
  and sell another at the same time**, so the oil-price swings cancel out and only the *gap*
  remains — far easier to predict than the direction of oil. We trade three shapes: **calendars**
  (same oil, two months), **butterflies** (a three-month combination isolating the middle
  month), and **Brent-WTI** (the gap between the two crudes).
- **Volatility** is how violently prices move (calm vs stormy) — and it changes what a given move
  *means*: a $0.10 stretch is huge in calm markets, noise in stormy ones.
- **Mean reversion is the engine.** A spread is like a **rubber band**: stretch it too far and it
  tends to **snap back**. *When a spread is unusually stretched, bet it returns to normal.* The
  whole project is about doing that carefully — and "carefully" means reading the market's state
  first.

---

## 2. What was built

A three-phase platform:

1. **Phase 1 — Live dashboard.** A React + Node terminal aggregating free/open data (Yahoo
   Finance prices and forward curves, EIA fundamentals, weather, news) into real-time panels. The
   backend stays thin: heavy statistics are precomputed offline and served as static JSON.
2. **Phase 2 — Regime model.** An offline analytics layer that classifies the market's daily
   *regime* (its state — principally **inventory × volatility**), fits a **walk-forward
   fundamentals fair-value model** for each spread (tested only on data it hadn't seen), and
   ranks which spreads look mispriced now.
3. **Phase 3 — Regime-driven strategy.** A relative-value mean-reversion strategy in which the
   Phase-2 regime model **drives every decision**, backtested daily (5y), intraday (5y), and live
   on the company feed.

---

## 3. The headline design decision

The first version of Phase 3 used the regime model only as a *label* and priced spreads off a
plain rolling average. The redesign — responding directly to mentor feedback — makes the regime
model **drive** the strategy:

- **Model-based fair value.** Daily fair value = the Phase-2 fundamentals regression
  (walk-forward / out-of-sample). Intraday fair value = a **regime-parameterized adaptive moving
  average** whose memory length tracks the regime's *measured* reversion speed — not a fixed
  window. (This corrected a v1 error that confused the *daily fundamentals regression*, which
  truly can't run intraday, with the *regime model*, which can.)
- **The regime drives the trade.** Per volatility state it sets the "stretched" ruler (the wiggle
  it divides by), the entry/exit/stop thresholds (a *deeper* stretch is required in stormy
  markets), the holding time (a multiple of the regime's reversion half-life), and the
  **position size** (constant-risk vol-targeting — stormy regimes are sized down automatically).
- **Shock absorption** as a first-class feature: a *severity* detector (volatility jumps, regime
  step-ups, stop-breaches) that **de-levers, stands aside, and flattens** through stress.
- **A regime-blind control** runs alongside every engine — the *same* fair value and spreads with
  the regime layer switched off — so the head-to-head isolates exactly what the regime model
  contributes. We read it **risk-first**, not by gross profit.

---

## 4. Headline results

**Read risk-first** — the comparison is regime-aware vs an identical regime-blind baseline.
("Sharpe" = return per unit of risk; "drawdown" = the worst peak-to-valley fall; "CVaR" = the
average loss on the worst 5% of days.)

| | Daily 5y (aware → blind) | Intraday 5y (aware → blind) |
|---|---|---|
| Sharpe | **0.82 → 0.38** | 5.4 → 6.8 |
| Calmar | **0.69 → 0.28** | 27.9 → 73.3 |
| Max drawdown | **−21% → −61%** | −$10k → −$92k |
| Tail risk (CVaR 5%) | **−$5.7k → −$15.5k** | −$1.9k → −$5.0k |
| Net P&L | $274k → $321k | $1.55M → $7.68M |

- **Daily:** the regime model **more than doubles the Sharpe** and **cuts drawdown by
  two-thirds** vs the naive baseline (much of it by concentrating size in the clean low-vol
  regime and sizing the negative-edge high-vol fades down hard).
- **Intraday:** the naive baseline is already excellent, so the regime model **slashes tail
  risk** rather than adding return, and avoids the structurally-losing structures.
- **Shock absorption:** across 28 data-driven shock windows the regime book has a shallower
  drawdown in **100%** of them; under a ×3 synthetic stress the blind book's worst drawdown blows
  out to **−$1.95M** while the regime book stays near **−$0.09M**.
- **Robustness:** profitable in **6/6 years**, t-statistic ≈ **12** (the edge is real, not luck),
  and it passes a five-test battery (per-year, significance, Monte-Carlo, walk-forward, parameter
  sensitivity).
- **Live:** a small, honest **+$520** (deploying the after-cost-validated Brent-WTI arb), which
  beats its blind twin — a freshness check on a few-day window, with the 5-year backtests
  carrying the statistical weight.

---

## 5. Integrity (why the numbers can be trusted)

- **Look-ahead-free** signal path: walk-forward fair value, trailing reversion half-lives,
  expanding same-state dispersion, regime labels built from same-day/backward-looking inputs, and
  point-in-time shock dates — independently audited.
- **Gross vs net discipline:** gross profit shows the *signal works*; net (after realistic costs)
  decides what's *deployable*, which is why the live book trades only Brent-WTI and merely
  evaluates the rest.
- **One disclosed in-sample choice:** the daily *universe* (which spreads to include) is gated on
  full-sample out-of-sample accuracy, but applied identically to both arms, so it can't bias the
  comparison.
- **The dollar scale is a sizing choice:** the intraday/live book runs at a conservative 4×
  leverage, which scales the dollars and the dollar risk equally and leaves every ratio
  unchanged.

---

## 6. How to run it

```
# Dashboard
npm install && npm run dev:all

# Analytics (Phase 2 + Phase 3) — uses the repo-root .venv
.venv\Scripts\python analytics/run.py        # full pipeline -> server/data/*.json
python Backtesting/engine.py                  # live strategy pass (--live to loop)

# Rebuild the explanatory PDFs from their markdown sources
.venv\Scripts\python make_reports.py
```

---

## 7. Glossary

- **Crude / WTI / Brent** — oil; the US (`CL`) and global (`CO`) benchmark grades.
- **Futures contract / forward curve** — prices for delivery in future months, in order.
- **Backwardation / contango** — near months pricier (tight) / cheaper (glut) than far months.
- **Spread (calendar / butterfly / Brent-WTI)** — the gap between two related prices, traded as
  one bet.
- **Regime** — the market's state (inventory × volatility).
- **Fair value** — a spread's "normal" level.
- **z-score / stretch** — how unusual the current level is, in same-regime wiggles.
- **Mean reversion** — the tendency of a stretched spread to snap back (the rubber band).
- **Vol-target sizing** — betting so each trade risks ~constant dollars.
- **Shock absorption** — automatically pulling risk in when the market gets stressed.
- **Regime-blind control** — the same strategy with the regime layer off; the baseline.
- **Sharpe / Calmar / drawdown / CVaR** — risk and risk-adjusted-return measures.
- **Gross vs net** — results before vs after trading costs.
- **Deployable** — a structure with a validated after-cost edge; the live book trades only these.
