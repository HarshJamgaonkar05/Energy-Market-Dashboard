# Phase 3 — Live Signal Engine (the Phase-2 framework, running live)

Working/ideation notes on the move **from historical validation to a live analysis
engine**. We take the Phase-2 regime/relative-value framework and run it continuously
on live market data, **generating and journaling every opportunity** it would trade —
with timestamp, regime, instrument, rationale, a confidence score, and the trade's
**subsequent performance** tracked forward. Below is exactly what it does and every
assumption, so the numbers are interpretable.

---

## The objective (mentor brief)

> Run the framework on **live market data**; add a **signal log** recording every
> opportunity the model generates — *timestamp, regime, instrument, rationale,
> confidence score, and subsequent performance* — so we can clearly track what the
> framework would be trading in the **current market environment**.

This is delivered by three pieces, all visible on the **Live Signal Engine** page:
1. **The engine** runs live (the `--live` loop, §0) and, each bar, evaluates the
   framework's relative-value signals on the freshest data.
2. **The Signal Log** (§0b) — an append-only journal of every opportunity ever
   generated, each scored and tracked from generation through its outcome.
3. **Live Now** — the open positions and current dislocation of every structure right
   now, so the "current market environment" is explicit.

---

## 0b. The Signal Log — what it records and how

Every time a spread crosses the entry threshold (|z| ≥ 1.5σ from its rolling fair
value), the framework **generates an opportunity**. Each one is written to a
persistent, append-only journal (`server/data/signal_log.json`) keyed by
`instrument@entry-time`, so it is recorded **once at generation** and then **updated
forward** as the trade plays out. Fields (exactly the brief's):

| Field | Meaning |
|---|---|
| **timestamp** | the bar the opportunity was generated on |
| **regime** | the prevailing Phase-2 market regime at generation (e.g. *Balanced · High Vol*) |
| **instrument** | the spread/structure (e.g. `WTI_M2M3`, `BRENT_WTI`) |
| **direction** | LONG (faded a cheap dislocation) / SHORT (faded a rich one) |
| **rationale** | why it fired — the dislocation, the regime, and the historical edge, in words |
| **confidence** | 0–100 score (see below) |
| **status** | `OPEN` (still live) or `CLOSED` |
| **performance** | subsequent PnL — *unrealised* while open, *realised* once closed — plus the `outcome` (reverted-win / stopped-loss / open) |

**Confidence score (0–100).** Grounds each *live* signal in the *historical*
validation — the bridge from Phase 2 to live:

```
edge = historical reversion hit-rate of this structure
       (Phase-2 daily backtest if available, else this session's intraday rate, else 0.6)
confidence = 100 × ( 0.65 · edge  +  0.35 · min(1, |z| / 2.5) )
```

So confidence is **mostly the proven historical edge**, lifted by **how far the
spread is dislocated now**. A structure that reverted ~80% of the time historically,
dislocated 2σ today, scores high; a weakly-validated structure barely past the
threshold scores low.

**Persistence.** The journal survives restarts and data-window changes — a signal
generated earlier stays in the log even after its bars scroll away, with its final
outcome preserved. Because the strategy is deterministic on the data, each `--live`
pass reproduces the full set and the journal simply upserts (adds new opportunities,
refreshes the performance/status of existing ones).

---

## 0. Live mode (data source)

The bars are written **live** by a Lightstreamer collector into a SQLite DB on a
network folder (`I:\Public\Summer Interns Energy\DB\bars_15min_*.db`). The data is
**15-minute bars** (a new bar every 15 min; the current bar updates as ticks arrive)
— *not* 15-second.

The freshest bars live in the DB's **write-ahead log (WAL)**, which a plain
read-only connection can't see while the collector holds the file. So the engine
**snapshots** the DB — copies `.db` + `.db-wal` (the `-shm` is locked, SQLite rebuilds
it) to a temp file and checkpoints it — to read right up to the latest bar.

- **`python BackTesting/backtest.py`** — one run from the live folder if reachable,
  else the local `Raw Data/` copies. (`mode: "live"` vs `"local"` is recorded in the
  feed and shown on the dashboard.)
- **`python BackTesting/backtest.py --live [seconds]`** — re-runs every N seconds
  (default 60) against the freshest live data, refreshing the dashboard feed each
  time. The **Strategy Backtest** page polls fast and shows a **LIVE** badge + the
  latest bar time. Run this alongside the dashboard to keep the panel live.

> Live mode only works **locally**, where the `I:` feed is mounted and this loop is
> running. The deployed Space serves the last committed snapshot.

**Completed trades vs live state.** The trade *log* only contains **finished**
round-trips (entry + exit). A position still on at the latest bar is **not** a
closed trade — it's reported separately as a **live open position** (with its
unrealised PnL), and every structure's **current dislocation (z)** is reported in a
**signal board** (|z| ≥ 1.5 = a live entry). So "nothing new in the trade log" just
means no trade has *completed* recently — open positions and fresh signals show up in
the **Live Now** panel, not the completed-trade log. The freshest readable bar is
also typically a few minutes behind wall-clock, because a 15-minute bar is only
finalised when it closes and the collector commits it.

---

## 1. What we have (the data)

`BackTesting/Raw Data/bars_15min_20260612.db` — a SQLite DB of **15-minute OHLCV
bars**, one table per futures contract, named `{PRODUCT}_{TENOR}`:

- **CL_** = WTI (CME), **CO_** = Brent (ICE).
- Tenors as month codes: `N26`=Jul-26, `Q26`=Aug-26, `U26`=Sep-26, `V26`=Oct-26,
  `X26`=Nov-26, `Z26`=Dec-26, `F27`=Jan-27, …
- Span: **2026-06-12 10:00 → 2026-06-15 05:00 UTC** (~73 active 15-min bars for the
  liquid fronts — a Friday session + the Sunday-night/Monday open across a weekend gap).
- Columns: `timestamp` (UTC bar open), `open, high, low, close, volume`. Rows only
  exist where trades occurred.

**Liquid contracts** (≈73/69 bars): WTI `N26,Q26,U26,V26,X26,Z26`, Brent
`Q26,U26,V26,X26,Z26`. Deferred `*27` contracts are sparse → not traded.

**Key implication:** this is **crude-only**. So we can backtest the Phase-2 *crude*
relative-value structures, **not** the product cracks (HO/RBOB/Gas-Oil aren't here).

---

## 2. What the Phase-2 strategy actually is

From the dashboard: a **regime-conditioned relative-value mean-reversion** strategy.
For each spread/structure it (a) classifies the market regime, (b) estimates a
*fair value*, (c) flags when the spread is dislocated (|z| ≥ ~1.5σ from fair value),
and (d) bets on **mean-reversion** — validated by the Phase-2 backtest, which showed
1.5σ dislocations reverted **67–83%** of the time with positive edge.

The engine is therefore: **fade statistically rich/cheap spreads, expect reversion.**

---

## 3. How we translate it to this intraday data (the honest mapping)

The Phase-2 models are **daily** and were fit on history ending 2026-05-22; their
fair-value *levels* are stale and the wrong frequency to anchor an intraday trade on
2026-06-12. So we backtest the **strategy's logic and parameters**, not its stale daily
levels:

- **Fair value (intraday)** = a **rolling mean** of the spread over `LOOKBACK` bars —
  the intraday analogue of the Phase-2 regime fair value.
- **Signal** = rolling **z-score** `z = (spread − rollmean) / rollstd`.
- **Entry** = fade when `|z| ≥ Z_ENTRY` (rich → short the spread, cheap → long it).
- **Exit** = reversion to `|z| ≤ Z_TARGET` (take profit), or `|z| ≥ Z_STOP` (stop),
  or a session/data-end time stop.
- Thresholds inherit the Phase-2 logic (entry 1.5σ; the Phase-2 backtest justifies it).
- **Phase-2 context is logged on every trade**: the current regime label (from
  `server/data/regimes.json`) and the structure's Phase-2 key, so the intraday test is
  explicitly tied back to the dashboard strategy.

This tests the question: *does the Phase-2 mean-reversion edge hold on real intraday
crude-spread tick data?*

---

## 4. Tradeable structures (map to Phase-2 keys)

| Structure | Legs (qty) | Phase-2 key |
|---|---|---|
| `WTI_M1M2` | +CL_N26 −CL_Q26 | `wti_m1m2` |
| `WTI_M2M3` | +CL_Q26 −CL_U26 | (calendar) |
| `WTI_FLY` | +CL_N26 −2·CL_Q26 +CL_U26 | `wti_fly` |
| `BRENT_M1M2` | +CO_Q26 −CO_U26 | `brent_m1m2` |
| `BRENT_M2M3` | +CO_U26 −CO_V26 | (calendar) |
| `BRENT_FLY` | +CO_Q26 −2·CO_U26 +CO_V26 | (fly analogue) |
| `BRENT_WTI` | +CO_Q26 −CL_Q26 (same Aug month) | `brent_wti` |

Each trades independently (its own position), but all share one capital base so the
portfolio equity curve, drawdown and Sharpe are computed jointly.

---

## 5. Execution model — GROSS basis (costs OFF)

We backtest on a **pure gross basis**: no slippage, no commission. PnL is the raw
strategy edge, isolating the single question *does the Phase-2 mean-reversion signal
work on intraday crude spreads?* (The cost model is still in the engine and can be
re-enabled by setting `SLIP_PER_LEG`/`COMM_PER_CONTRACT` > 0 — earlier runs showed
costs are the binding constraint on these small intraday moves, so gross isolates the
signal from the execution problem.)

- **Contract multiplier**: 1,000 bbl → a $1.00/bbl move = **$1,000 per contract**.
- **Size**: fixed **1 spread unit** per signal (1 contract per leg, scaled by fly
  ratios). Transparent; can later be scaled by Phase-2 confidence.
- **Fills**: at the bar **mid** (close). With costs off, entry/exit fills = mid.
- **Session/weekend guard**: if the gap to the next bar > 90 min, open positions are
  flattened at the current close (`SESSION_END`) — no unrealistic weekend holds.

**Defaults** (all configurable at the top of `backtest.py`):
`LOOKBACK=16` (4h), `Z_ENTRY=1.5`, `Z_TARGET=0.25`, `Z_STOP=3.0`,
`INITIAL_CAPITAL=$250,000`, `MULT=1000`, `SLIP_PER_LEG=0` (off), `COMM_PER_CONTRACT=0` (off).

---

## 6. What we log (outputs in `BackTesting/out/`)

- **`trades.csv`** — one row per trade, *everything*: ids, structure, **strategy +
  strategy description**, legs & per-leg entry/exit prices, direction, entry/exit time
  & z, entry/exit spread, holding bars/minutes, gross PnL, MAE/MFE ($), exit reason,
  regime, Phase-2 fair-value context, running equity.
- **`trades_log.md`** — the **readable, trade-by-trade log**: each trade names the
  strategy, the setup (why it fired), the legs with entry→exit fills, the signal,
  the exit, and the gross PnL.
- **`equity_curve.csv`** — per-bar mark-to-market equity (realised + unrealised),
  for drawdown and Sharpe.
- **`by_structure.csv`** — bifurcation per structure: trades, win rate, gross/net PnL,
  avg win/loss, profit factor, avg hold, total slippage & commission.
- **`summary.json`** — portfolio aggregates: net PnL, win rate, profit factor,
  expectancy, Sharpe, Sortino, max drawdown, total slippage/commission, exposure,
  turnover, frequency of each trade type (by structure, direction, exit reason).
- **`report.md`** — human-readable summary of the above.

---

## 7. Honest caveats (read before trusting any number)

1. **Tiny sample.** ~73 bars over ~1 session ⇒ few trades. This is a *working engine*
   and a *methodology demonstration*, not a statistically conclusive backtest. Drop more
   daily `.db` files into `Raw Data/` and re-run to accumulate significance — the engine
   auto-loads every `.db` it finds.
2. **Intraday adaptation.** We test the strategy's mean-reversion *logic* with an
   intraday rolling fair value, not the literal stale daily Phase-2 levels (see §3).
3. **Gross basis** — slippage & commission are OFF, so this measures the raw signal
   edge, not net tradeable PnL. Re-enable the cost knobs to stress-test execution.
4. **No funding/margin/borrow**; fills assume the mid is tradeable at 1 tick of slippage.
5. **Front-month roll/expiry** within the window is not modeled (the window is short).
