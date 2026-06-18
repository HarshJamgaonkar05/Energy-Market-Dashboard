# Trade Log — Phase-3 backtest (RV mean-reversion, intraday)

_Strategy: RV mean-reversion + cost gate (Phase-2 idea, intraday). Data: **live**. Regime: **Balanced · High Vol**. Fixed 1 unit/trade, gross (slippage 0)._

**20 trades · gross $1,770 · win 85% · PF 3.642 · exp $88/trade · max DD $-320**

Each trade: the setup, the legs with fills, the signal, the exit and the gross PnL.

---

### 1. Brent-WTI arb (Aug) — LONG  (+20 USD)
- **Setup:** dislocated to -2.28sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 80/100
- **Legs (entry->exit):** CO_Q26 86.92->86.76, CL_Q26 82.92->82.74
- **In:** 2026-06-12 15:45 @ 4.0   **Out:** 2026-06-12 20:45 @ 4.02 (z -0.19, session_end)
- **Held:** 20 bars (300 min)   **MAE/MFE:** -40 / +70

### 2. WTI Aug/Sep (M2-M3) — LONG  (-60 USD)
- **Setup:** dislocated to -3.20sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 85/100
- **Legs (entry->exit):** CL_Q26 79.63->79.42, CL_U26 78.27->78.12
- **In:** 2026-06-14 22:00 @ 1.36   **Out:** 2026-06-15 05:00 @ 1.3 (z +1.01, target)
- **Held:** 28 bars (420 min)   **MAE/MFE:** -200 / +10

### 3. Brent-WTI arb (Aug) — SHORT  (+120 USD)
- **Setup:** dislocated to +3.16sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 90/100
- **Legs (entry->exit):** CO_Q26 83.55->83.05, CL_Q26 79.35->78.97
- **In:** 2026-06-15 00:00 @ 4.2   **Out:** 2026-06-15 08:45 @ 4.08 (z -1.30, target)
- **Held:** 35 bars (525 min)   **MAE/MFE:** -110 / +140

### 4. WTI Aug/Sep (M2-M3) — LONG  (+70 USD)
- **Setup:** dislocated to -2.96sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 85/100
- **Legs (entry->exit):** CL_Q26 78.55->79.13, CL_U26 77.45->77.96
- **In:** 2026-06-15 07:15 @ 1.1   **Out:** 2026-06-15 13:15 @ 1.17 (z +1.26, target)
- **Held:** 24 bars (360 min)   **MAE/MFE:** -70 / +90

### 5. WTI Jul/Aug/Sep fly — SHORT  (+310 USD)
- **Setup:** dislocated to +2.47sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 82/100
- **Legs (entry->exit):** CL_N26 80.22->80.23, CL_Q26 78.76->79.02, CL_U26 77.73->77.93
- **In:** 2026-06-15 10:00 @ 0.43   **Out:** 2026-06-15 12:15 @ 0.12 (z -1.60, target)
- **Held:** 9 bars (135 min)   **MAE/MFE:** +0 / +310

### 6. Brent-WTI arb (Aug) — LONG  (-290 USD)
- **Setup:** dislocated to -2.11sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 78/100
- **Legs (entry->exit):** CO_Q26 82.95->83.48, CL_Q26 78.99->79.81
- **In:** 2026-06-15 10:15 @ 3.96   **Out:** 2026-06-15 20:45 @ 3.67 (z -1.21, session_end)
- **Held:** 42 bars (630 min)   **MAE/MFE:** -320 / +140

### 7. WTI Aug/Sep (M2-M3) — SHORT  (+100 USD)
- **Setup:** dislocated to +2.31sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 76/100
- **Legs (entry->exit):** CL_Q26 79.23->79.59, CL_U26 77.99->78.45
- **In:** 2026-06-15 15:00 @ 1.24   **Out:** 2026-06-16 01:45 @ 1.14 (z -3.10, target)
- **Held:** 39 bars (645 min)   **MAE/MFE:** -190 / +100

### 8. WTI Jul/Aug/Sep fly — LONG  (+280 USD)
- **Setup:** dislocated to -2.74sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 86/100
- **Legs (entry->exit):** CL_N26 81.12->80.92, CL_Q26 79.78->79.59, CL_U26 78.35->78.45
- **In:** 2026-06-15 22:00 @ -0.09   **Out:** 2026-06-16 01:45 @ 0.19 (z +2.89, target)
- **Held:** 15 bars (225 min)   **MAE/MFE:** +0 / +280

### 9. Brent-WTI arb (Aug) — LONG  (+130 USD)
- **Setup:** dislocated to -2.06sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 77/100
- **Legs (entry->exit):** CO_Q26 82.94->82.12, CL_Q26 79.37->78.42
- **In:** 2026-06-16 03:00 @ 3.57   **Out:** 2026-06-16 07:30 @ 3.7 (z +2.21, target)
- **Held:** 18 bars (270 min)   **MAE/MFE:** -70 / +130

### 10. WTI Aug/Sep (M2-M3) — LONG  (-320 USD)
- **Setup:** dislocated to -3.01sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 85/100
- **Legs (entry->exit):** CL_Q26 78.42->76.24, CL_U26 77.35->75.49
- **In:** 2026-06-16 07:30 @ 1.07   **Out:** 2026-06-16 19:30 @ 0.75 (z +0.44, time_stop)
- **Held:** 48 bars (720 min)   **MAE/MFE:** -450 / +10

### 11. Brent-WTI arb (Aug) — SHORT  (+170 USD)
- **Setup:** dislocated to +2.31sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 81/100
- **Legs (entry->exit):** CO_Q26 81.87->80.9, CL_Q26 78.15->77.35
- **In:** 2026-06-16 07:45 @ 3.72   **Out:** 2026-06-16 11:30 @ 3.55 (z -1.29, target)
- **Held:** 15 bars (225 min)   **MAE/MFE:** -70 / +170

### 12. WTI Jul/Aug/Sep fly — SHORT  (+140 USD)
- **Setup:** dislocated to +2.61sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 84/100
- **Legs (entry->exit):** CL_N26 78.73->77.12, CL_Q26 77.54->76.2, CL_U26 76.57->75.36
- **In:** 2026-06-16 08:00 @ 0.22   **Out:** 2026-06-16 12:30 @ 0.08 (z -2.04, target)
- **Held:** 18 bars (270 min)   **MAE/MFE:** -30 / +140

### 13. Brent-WTI arb (Aug) — LONG  (+90 USD)
- **Setup:** dislocated to -2.31sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 81/100
- **Legs (entry->exit):** CO_Q26 79.51->79.5, CL_Q26 75.93->75.83
- **In:** 2026-06-16 19:00 @ 3.58   **Out:** 2026-06-16 20:45 @ 3.67 (z +0.08, session_end)
- **Held:** 7 bars (105 min)   **MAE/MFE:** -60 / +90

### 14. WTI Aug/Sep (M2-M3) — SHORT  (+140 USD)
- **Setup:** dislocated to +2.34sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 76/100
- **Legs (entry->exit):** CL_Q26 76.0->75.56, CL_U26 75.17->74.87
- **In:** 2026-06-16 22:00 @ 0.83   **Out:** 2026-06-17 01:15 @ 0.69 (z -1.85, target)
- **Held:** 13 bars (195 min)   **MAE/MFE:** +0 / +140

### 15. WTI Aug/Sep (M2-M3) — LONG  (+20 USD)
- **Setup:** dislocated to -2.15sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 74/100
- **Legs (entry->exit):** CL_Q26 75.38->75.66, CL_U26 74.73->74.99
- **In:** 2026-06-17 02:15 @ 0.65   **Out:** 2026-06-17 08:30 @ 0.67 (z +1.18, target)
- **Held:** 25 bars (375 min)   **MAE/MFE:** -130 / +60

### 16. Brent-WTI arb (Aug) — SHORT  (+170 USD)
- **Setup:** dislocated to +2.11sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 78/100
- **Legs (entry->exit):** CO_Q26 79.38->79.17, CL_Q26 75.66->75.62
- **In:** 2026-06-17 08:30 @ 3.72   **Out:** 2026-06-17 10:15 @ 3.55 (z -1.40, target)
- **Held:** 7 bars (105 min)   **MAE/MFE:** +0 / +170

### 17. Brent-WTI arb (Aug) — SHORT  (+260 USD)
- **Setup:** dislocated to +2.79sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 87/100
- **Legs (entry->exit):** CO_Q26 79.6->80.58, CL_Q26 75.78->77.02
- **In:** 2026-06-17 12:00 @ 3.82   **Out:** 2026-06-17 14:45 @ 3.56 (z -1.31, target)
- **Held:** 11 bars (165 min)   **MAE/MFE:** +0 / +260

### 18. WTI Aug/Sep (M2-M3) — SHORT  (+50 USD)
- **Setup:** dislocated to +2.34sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 76/100
- **Legs (entry->exit):** CL_Q26 76.37->75.4, CL_U26 75.54->74.62
- **In:** 2026-06-17 13:45 @ 0.83   **Out:** 2026-06-17 19:15 @ 0.78 (z -1.34, target)
- **Held:** 22 bars (330 min)   **MAE/MFE:** -170 / +50

### 19. WTI Jul/Aug/Sep fly — LONG  (+170 USD)
- **Setup:** dislocated to -3.07sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 89/100
- **Legs (entry->exit):** CL_N26 77.83->76.52, CL_Q26 77.02->75.71, CL_U26 76.03->74.89
- **In:** 2026-06-17 14:45 @ -0.18   **Out:** 2026-06-17 18:45 @ -0.01 (z +1.06, target)
- **Held:** 16 bars (240 min)   **MAE/MFE:** -30 / +170

### 20. Brent-WTI arb (Aug) — SHORT  (+200 USD)
- **Setup:** dislocated to +2.12sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 78/100
- **Legs (entry->exit):** CO_Q26 78.71->78.6, CL_Q26 75.01->75.1
- **In:** 2026-06-17 20:45 @ 3.7   **Out:** 2026-06-18 01:00 @ 3.5 (z -1.09, target)
- **Held:** 5 bars (255 min)   **MAE/MFE:** +0 / +200
