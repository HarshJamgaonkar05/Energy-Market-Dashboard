# Trade Log — Phase-3 backtest (RV mean-reversion + shock absorption, intraday)

_Strategy: RV mean-reversion + cost gate + shock absorption (Phase-2 idea, intraday). Data: **local**. Regime: **Balanced · High Vol**. Base 1 unit/trade (shock-aware sizing), gross (slippage 0)._

**5 trades · gross $15 · win 40% · PF 1.132 · Sharpe 6.663 · max DD $-2**

Each trade: the setup, the legs with fills, the signal, the exit and the gross PnL.

---

### 1. Brent-WTI arb (Aug) — LONG  (+17 USD)
- **Setup:** dislocated to -2.28sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 80/100 · entry severity 0.13 · size 0.87u
- **Legs (entry->exit):** CO_Q26 86.92->86.76, CL_Q26 82.92->82.74
- **In:** 2026-06-12 15:45 @ 4.0   **Out:** 2026-06-12 20:45 @ 4.02 (z n/a, session_end)
- **Held:** 20 bars (300 min)   **MAE/MFE:** -35 / +61

### 2. WTI Aug/Sep (M2-M3) — LONG  (+114 USD)
- **Setup:** dislocated to -2.25sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 75/100 · entry severity 0.37 · size 0.63u
- **Legs (entry->exit):** CL_Q26 78.76->79.08, CL_U26 77.73->77.87
- **In:** 2026-06-15 10:00 @ 1.03   **Out:** 2026-06-15 13:30 @ 1.21 (z +1.98, target)
- **Held:** 14 bars (210 min)   **MAE/MFE:** +0 / +114

### 3. Brent-WTI arb (Aug) — LONG  (-8 USD)
- **Setup:** dislocated to -2.01sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 77/100 · entry severity 0.16 · size 0.84u
- **Legs (entry->exit):** CO_Q26 83.04->83.02, CL_Q26 79.09->79.08
- **In:** 2026-06-15 10:30 @ 3.95   **Out:** 2026-06-15 13:30 @ 3.94 (z -1.27, shock_flat)
- **Held:** 12 bars (180 min)   **MAE/MFE:** -25 / +127

### 4. WTI Aug/Sep (M2-M3) — SHORT  (-62 USD)
- **Setup:** dislocated to +2.31sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 76/100 · entry severity 0.22 · size 0.78u
- **Legs (entry->exit):** CL_Q26 79.23->79.55, CL_U26 77.99->78.23
- **In:** 2026-06-15 15:00 @ 1.24   **Out:** 2026-06-15 18:15 @ 1.32 (z +2.10, shock_flat)
- **Held:** 13 bars (195 min)   **MAE/MFE:** -62 / +31

### 5. Brent-WTI arb (Aug) — LONG  (-46 USD)
- **Setup:** dislocated to -2.49sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 83/100 · entry severity 0.09 · size 0.91u
- **Legs (entry->exit):** CO_Q26 83.38->83.48, CL_Q26 79.66->79.81
- **In:** 2026-06-15 18:30 @ 3.72   **Out:** 2026-06-15 20:45 @ 3.67 (z n/a, session_end)
- **Held:** 9 bars (135 min)   **MAE/MFE:** -73 / +46
