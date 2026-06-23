# Trade Log — Phase-3 LIVE (regime-driven RV mean-reversion, intraday)

_Strategy: Regime-driven RV mean-reversion (live, intraday). Data: **live**. Regime: **Balanced · High Vol**. Vol-target sizing, gross (slippage 0)._

**2 trades · gross $520 · win 50% · PF 4.218 · Sharpe 4.608 · max DD $-162**

---

### 1. Brent-WTI arb (Aug) — LONG  (-162 USD)
- **Setup:** -3.92sigma (cheap) -> fade · regime Balanced · High Vol · size 3.23 · confidence 59/100
- **Legs (entry->exit):** CO_Q26 83.27->83.48, CL_Q26 79.55->79.81
- **In:** 2026-06-15 18:15 @ 3.72   **Out:** 2026-06-15 20:45 @ 3.67 (z None, session_end)
- **Held:** 10 bars (150 min)   **MAE/MFE:** -259 / +162

### 2. Brent-WTI arb (Aug) — SHORT  (+682 USD)
- **Setup:** +2.57sigma (rich) -> fade · regime Balanced · High Vol · size 3.1 · confidence 52/100
- **Legs (entry->exit):** CO_Q26 78.12->77.65, CL_Q26 74.17->73.92
- **In:** 2026-06-18 09:30 @ 3.95   **Out:** 2026-06-18 15:45 @ 3.73 (z -0.15, time_stop)
- **Held:** 25 bars (375 min)   **MAE/MFE:** -279 / +774
