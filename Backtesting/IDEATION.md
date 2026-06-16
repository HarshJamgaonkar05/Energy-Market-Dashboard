# Strategy Backtest — Phase-2 strategy, backtested on the provided data

We take the Phase-2 framework's strategy — **regime-conditioned relative-value
mean-reversion** — and **backtest it over the 15-minute crude bars in
`Backtesting/Data`**, logging every trade with full detail and gross PnL
(slippage 0). The main output is the **trade log**.

---

## 1. The data

`Backtesting/Data/bars_15min_20260612.db` — a SQLite DB of 15-minute OHLCV bars,
one table per contract (`{PRODUCT}_{TENOR}`: `CL_*` = WTI, `CO_*` = Brent). The
freshest bars live in the **write-ahead log (WAL)**, so the engine snapshots
`.db`+`.db-wal` and checkpoints to read every bar.

- Span: **2026-06-12 10:00 → 2026-06-16 00:45 UTC** (~156 bars: a Friday session,
  the weekend gap, the Monday open and into Tuesday).
- Liquid contracts: WTI `N26,Q26,U26,V26,X26,Z26`; Brent `Q26,U26,V26,X26,Z26`.
- **Crude-only**, so we backtest the Phase-2 *crude* relative-value structures
  (calendars, flies, Brent-WTI); the product cracks (HO/RBOB/Gas Oil) aren't here.

If the live feed (`I:\Public\Siddharth Raj\lightstreamer_data\`) is reachable and
holds *more* bars than the local copy, the engine uses it instead — so the same
backtest becomes live as new bars arrive. The feed records `mode: local` vs `live`.

---

## 2. The strategy (Phase 2)

A **regime-conditioned relative-value mean-reversion** strategy: a spread has a
fair value; when it dislocates far enough from it, fade the move and bet on
reversion. The Phase-2 daily backtest validated this — 1.5σ dislocations reverted
**67–83%** of the time with positive edge.

Run intraday over this data:

- **Fair value** = a rolling mean of the spread over `LOOKBACK = 16` bars (~4h).
  *Why a rolling mean and not Phase-2's stored fair value:* Phase-2's levels are
  daily and the contracts have since re-priced — live WTI M1-M2 sits ~1.3 vs
  Phase-2's 4.6, pure basis — so the reversion reference must be estimated from the
  data being traded. The **regime label and the validated per-structure edge are
  carried in from Phase 2**, so each trade is tied back to the framework.
- **Signal** = rolling z-score `z = (spread − mean) / std`.
- **Entry** = fade when `|z| ≥ 1.5` (rich → short the spread, cheap → long it).
- **Exit** = reversion to `|z| ≤ 0.25` (target), `|z| ≥ 3.0` (stop), or a
  session/weekend break (>90-min gap to the next bar) — no weekend holds.

A position still on at the **last bar** is reported as a live **open position**
(unrealised PnL), not a closed trade.

> Note on the 3-day window: Phase-2's regimes are daily/fundamental, so over a few
> days the regime is constant — its conditioning is dormant here by construction,
> and the strategy reduces to its mean-reversion core. That is an honest property of
> running a daily framework intraday, not something we engineer around.

---

## 3. Structures backtested

| Structure | Legs | Phase-2 edge key |
|---|---|---|
| `WTI_M1M2` | +CL_N26 −CL_Q26 | `wti_m1m2` |
| `WTI_M2M3` | +CL_Q26 −CL_U26 | `wti_m1m2` |
| `WTI_FLY` | +CL_N26 −2·CL_Q26 +CL_U26 | `wti_fly` |
| `BRENT_M1M2` | +CO_Q26 −CO_U26 | `brent_m1m2` |
| `BRENT_M2M3` | +CO_U26 −CO_V26 | `brent_m1m2` |
| `BRENT_FLY` | +CO_Q26 −2·CO_U26 +CO_V26 | `wti_fly` |
| `BRENT_WTI` | +CO_Q26 −CL_Q26 | `brent_wti` |

Each trades independently but all share one capital base, so the equity curve,
drawdown and stats are portfolio-level.

---

## 4. Execution model — GROSS (slippage 0)

- **Slippage = 0, commission = 0**, per the brief — isolates the raw signal edge.
  Fills at the bar close.
- **Multiplier** 1,000 bbl → $1.00/bbl = **$1,000 per contract**.
- **Size** fixed 1 spread unit per signal. `INITIAL_CAPITAL = $250,000`.

A note on the numbers: the take-profit (|z|≤0.25) is near and the stop (|z|≥3.0) is
far, which produces a **high win rate but small average wins** — so total PnL is
modest and driven by frequency, not size. The win rate is partly a function of that
exit geometry; expectancy and profit factor are the honest edge metrics.

---

## 5. Confidence score (0–100)

Each trade carries a confidence grounding the live signal in the historical
validation:

```
edge       = the structure's Phase-2 reversion hit-rate (backtest.json), else 0.6
confidence = 100 × ( 0.65 · edge  +  0.35 · min(1, |z| / 2.5) )
```

Mostly the proven historical edge, lifted by how far the spread is dislocated.

---

## 6. Outputs

- **`out/trades.csv`** — one row per trade, every field + running equity (machine).
- **`out/trades_log.md`** — the readable, trade-by-trade log (the main output).
- **`out/by_structure.csv`** — per-structure trades / win / PnL / PF / edge.
- **`server/data/signal_engine.json`** — the dashboard feed: summary, equity curve,
  full trade list, per-structure, open positions, and the persistent signal log.
- **`server/data/signal_log.json`** — the append-only opportunity journal
  (timestamp · regime · instrument · rationale · confidence · performance).

```
python Backtesting/engine.py            # one backtest pass
python Backtesting/engine.py --live      # re-run every 60s on the freshest data
```

---

## 7. Honest caveats

1. **Small sample** (~156 bars / a few sessions) — a working engine and methodology,
   not a statistically conclusive backtest. Drop more daily `.db` files into `Data/`
   and re-run to accumulate significance.
2. **Intraday adaptation** — the strategy's reversion logic on a rolling fair value,
   not Phase-2's stale daily levels (which don't transfer; §2).
3. **Gross basis** — slippage/commission off.
4. **Crude-only** — product cracks aren't in this feed.
