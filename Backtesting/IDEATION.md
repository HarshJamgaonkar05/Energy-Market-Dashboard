# Phase 3 — Strategy Backtest (methodology)

We take the Phase-2 idea — **relative-value mean-reversion on crude spreads** — and
**backtest it over the intraday 15-minute bars** in the mentor's live company feed,
logging every trade in full. One clean engine ([`engine.py`](engine.py)); the main
output is the **trade log**.

---

## 1. The data

The live feed at `I:\Public\Summer Interns Energy\DB\bars_15min_*.db` — a SQLite DB of
15-minute OHLCV bars, one table per contract (`CL_*` = WTI, `CO_*` = Brent). The freshest
bars live in the **write-ahead log (WAL)**, so the engine snapshots `.db`+`.db-wal` and
checkpoints before reading. (A committed copy in `Backtesting/Data/` is the offline
fallback; the engine uses whichever source is deeper.)

- Span at time of writing: **2026-06-12 → 2026-06-18**, ~350 fifteen-minute bars.
- **Crude-only** (WTI + Brent across the curve), so we trade the crude relative-value
  structures — calendars, butterflies, Brent-WTI — not the product cracks.

---

## 2. Fair value — why it is estimated from the data, not the Phase-2 model

This was the central design question, and the answer is decisive: **the Phase-2 fair-value
model cannot be used to price these intraday spreads.** Three independent reasons:

1. **Its inputs aren't in the feed.** The Phase-2 regression is a function of *fundamentals*
   — crude/distillate inventories, refinery utilisation, DXY, VIX, momentum, seasonality.
   The intraday feed contains **only crude futures prices** — none of those features — so the
   model literally cannot be evaluated here.
2. **Its output level is stale.** Phase-2's daily fair value for WTI M1-M2 is ~**2.18**; the
   spread now trades at ~**0.74**. Forcing the old level on would flag a permanent fake
   "cheap" — pure basis, not signal.
3. **Fundamentals are daily, so it's ~constant intraday.** Over a few days the regression
   barely moves and cannot explain intraday spread moves, which are driven by order flow.

So **fair value = a rolling mean of the spread over `LOOKBACK = 24` bars (~6h)** — estimated
from the very series being traded. The dislocation is the **z-score**
`z = (spread − rolling mean) / rolling std`.

> Phase 2 is **not discarded** — it contributes as *context*: its validated per-structure
> reversion hit-rates and the current regime label are carried in as the **confidence** and
> the **rationale** on every trade. They are priors/labels, never the price reference.

---

## 3. The strategy (deliberately simple)

- **Fair value** — rolling mean of the spread (`LOOKBACK = 24` bars).
- **Signal** — z-score off that mean.
- **Entry** — fade when `|z| ≥ 2.0` (rich → short the spread, cheap → long it).
- **Exit** — the first of:
  - **target**: reverted through to fair, `|z| ≤ 0.25` (directional — capture the whole move);
  - **stop**: stretched further to `|z| ≥ 3.5`;
  - **time stop**: held `MAX_HOLD_BARS = 48` bars (~12h) without resolving;
  - **session break**: a >90-min gap to the next bar (no overnight/weekend holds).
- **Size** — a fixed **1 unit per trade**. This reports the *raw per-unit signal*, not a
  leveraged book; dollar figures stay small and honest. (Position sizing is a separate
  concern, deliberately left out so the backtest measures the signal, not the leverage.)

A position still on at the **last bar** is reported as a live **open position** (unrealised
PnL), not a closed trade.

> Note on the 3-6 day window: Phase-2's regimes are daily/fundamental, so over a few days the
> regime is constant — its conditioning is dormant here by construction, and the strategy
> reduces to its mean-reversion core. An honest property of running a daily framework
> intraday, not something engineered around.

---

## 4. Structures backtested

| Structure | Legs | Phase-2 edge key |
|---|---|---|
| `WTI_M1M2` | +CL_N26 −CL_Q26 | `wti_m1m2` |
| `WTI_M2M3` | +CL_Q26 −CL_U26 | `wti_m1m2` |
| `WTI_FLY` | +CL_N26 −2·CL_Q26 +CL_U26 | `wti_fly` |
| `BRENT_M1M2` | +CO_Q26 −CO_U26 | `brent_m1m2` |
| `BRENT_M2M3` | +CO_U26 −CO_V26 | `brent_m1m2` |
| `BRENT_FLY` | +CO_Q26 −2·CO_U26 +CO_V26 | `wti_fly` |
| `BRENT_WTI` | +CO_Q26 −CL_Q26 | `brent_wti` |

M1/M2/M3 = 1st/2nd/3rd nearest contract during this June-2026 window. Each trades
independently but all share one capital base, so the equity curve, drawdown and stats are
portfolio-level.

---

## 5. Execution model

- **Gross by default** (slippage 0, per the brief) — isolates the raw signal. Fills at the
  bar close. `--slip <price/leg>` charges `slip × 2 × legs × 1,000` per round turn and reports
  **net** alongside gross (no other behaviour changes).
- **Multiplier** 1,000 bbl → $1.00/bbl = **$1,000 per contract**.
- `INITIAL_CAPITAL = $250,000` is the equity-curve baseline only (size is fixed 1 unit).

---

## 6. Confidence (0-100)

```
edge       = the structure's Phase-2 reversion hit-rate (backtest.json) if validated, else 0.60
confidence = 100 · ( 0.6 · edge  +  0.4 · min(1, |z_entry| / 3.0) )
```

Mostly the validated historical hit-rate, lifted by how stretched the spread is at entry.

---

## 7. Outputs

- **`out/trades.csv`** — one row per trade + running equity (machine-readable).
- **`out/trades_log.md`** — the readable, trade-by-trade log (the main output).
- **`out/by_structure.csv`** — per-structure trades / win / PnL / PF / edge.
- **`server/data/signal_engine.json`** — the dashboard feed (summary, equity curve, full trade
  list, per-structure, open positions, signal log).
- **`server/data/signal_log.json`** — the persistent opportunity journal.

```
python Backtesting/engine.py            # one backtest pass (gross)
python Backtesting/engine.py --slip 0.01  # charge per-leg slippage; report net too
python Backtesting/engine.py --live       # re-run every 60s on the freshest data
```

---

## 8. Honest caveats

1. **Small sample** (~350 bars / a few sessions) — a working engine and methodology, not a
   statistically conclusive backtest. Drop more daily `.db` files into `Data/` (or let the
   live feed accumulate) and re-run to build significance.
2. **Costs.** Gross by default; with realistic slippage (`--slip 0.01`) the high-frequency
   edge thins to roughly break-even — these small intraday moves are where costs bite hardest.
   The honest read is gross = "does the signal work", net = "is it cheap enough to trade".
3. **Crude-only** — the feed is WTI + Brent, so the product cracks aren't backtested here.
4. **Fixed 1-unit sizing** — reports the raw per-unit signal, not a sized/leveraged portfolio.
   Position sizing and portfolio risk limits are a separate layer on top.
5. **Daily framework, intraday window** — the regime conditioning is dormant over a few days
   (§3); what's tested is the mean-reversion core with Phase-2 hit-rates as priors.
