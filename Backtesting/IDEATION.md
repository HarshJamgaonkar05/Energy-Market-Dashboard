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

If the mentor's live company feed (`I:\Public\Summer Interns Energy\DB\`) is
reachable and holds *more* bars than the local copy, the engine uses it instead —
so the same backtest runs on the freshest data as new 15-min bars arrive. The feed
records `mode: live` vs `local`. (The local `Data/` copy is only the offline
fallback.)

---

## 2. The strategy (Phase 2)

A **regime-conditioned relative-value mean-reversion** strategy: a spread has a
fair value; when it dislocates far enough from it, fade the move and bet on
reversion. The Phase-2 daily backtest validated this — 1.5σ dislocations reverted
**67–83%** of the time with positive edge.

Run intraday over this data:

- **Fair value** = a **robust** rolling center of the spread over `LOOKBACK = 16`
  bars (~4h): the rolling **median**, scaled by the **MAD** (×1.4826 → σ-equivalent).
  *Why robust and not a plain mean/std:* the mean and std are pulled by the very
  dislocation bar we want to fade, biasing the reference toward the move; the median/MAD
  are not. *Why estimated from the data and not Phase-2's stored fair value:* Phase-2's
  levels are daily and the contracts have since re-priced — live WTI M1-M2 sits ~1.3 vs
  Phase-2's 4.6, pure basis — so the reversion reference must be estimated from the data
  being traded. (Set `--no-robust` to fall back to mean/std.)
- **Signal** = robust z-score `z = (spread − median) / (1.4826 · MAD)`.
- **Entry** = fade when `|z| ≥ 1.5` (rich → short the spread, cheap → long it),
  **if the daily fundamentals model agrees** on the sign of the dislocation (see §5a)
  and, in NET mode, the expected reversion clears its trading cost (§4).
- **Exit** (improved geometry) = reversion **through to fair** (`|z| ≤ 0.1`, directional —
  capture the whole reversion, not just the first quarter); a **tighter `|z| ≥ 2.5` stop**
  (positive reward:risk vs the 1.5σ entry, was 3.0); an **OU half-life time stop** (bail
  after `3 ×` the spread's estimated mean-reversion half-life if unsettled — cuts the
  left tail of positions drifting toward the stop); or a session/weekend break
  (>90-min gap). The **regime label and validated per-structure edge are carried in from
  Phase 2**, so each trade still ties back to the framework.

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

## 4. Execution model — GROSS by default, NET on demand

- **GROSS (default):** slippage 0, commission 0, per the brief — isolates the raw
  signal edge. Fills at the bar close.
- **NET (`--slip <price/leg>`):** charges `slip × 2 × legs × 1,000` per round turn and,
  critically, **only takes a signal whose expected reversion to fair ≥ `--cost-mult`
  (default 2×) its round-turn cost** — so the engine stops paying to harvest moves
  smaller than the spread it crosses. Reports gross *and* net PnL / PF / win rate.
- **Multiplier** 1,000 bbl → $1.00/bbl = **$1,000 per contract**.
- **Size** fixed 1 spread unit per signal. `INITIAL_CAPITAL = $250,000`.

Why NET matters: the old exit took profit at `|z|≤0.25` against a far `3σ` stop —
a **high win rate but tiny average wins**, profit driven by frequency. Those wins do
not survive realistic transaction costs: on this data, `--slip 0.01` turns a +$2.7k
gross book **net-negative**, while adding the fundamentals gate (§5a) cuts to ~28
high-conviction trades that stay **net-positive with a fraction of the drawdown**.
The improved exit geometry (§2) and the cost/conviction gates trade win rate for
expectancy — the honest edge metric.

---

## 5. Confidence score (0–100)

Each trade carries a confidence grounding the live signal in the historical
validation:

```
edge       = the structure's Phase-2 reversion hit-rate (backtest.json), else 0.6
confidence = 100 × ( 0.65 · edge  +  0.35 · min(1, |z| / 2.5) )
```

Mostly the proven historical edge, lifted by how far the spread is dislocated, and
adjusted ±for the fundamentals agreement below.

### 5a. Fundamentals anchor (reconnecting the two fair-value engines)

The intraday rolling z says *"dislocated vs its own recent history"*; the Phase-2
**regression fair value** (`models.json`, drivers: inventories, refinery utilization,
vol, momentum, DXY/VIX/UST10Y, seasonality) says *"rich or cheap vs fundamentals"*.
We read the **sign** of the daily residual-z for each structure and require the
intraday fade to **agree** with it — the absolute daily *level* does not transfer
across the re-pricing, but the *direction* (rich/cheap) does. Agreement lifts
confidence; disagreement cuts it, and `--fund-gate` hard-skips contradicted fades.
This is the lever that turns the net book positive: it keeps the dislocations both
read-outs corroborate and drops the ones only the noise supports.

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
python Backtesting/engine.py                       # one GROSS pass (default)
python Backtesting/engine.py --slip 0.01           # NET: cost + expected-edge gate
python Backtesting/engine.py --slip 0.01 --fund-gate  # NET + fundamentals agreement gate
python Backtesting/engine.py --no-robust           # mean/std fair value (old reference)
python Backtesting/engine.py --live                # re-run every 60s on the freshest data
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
