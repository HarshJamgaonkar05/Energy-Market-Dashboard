# Trade Log — Phase-3 backtest (RV mean-reversion, intraday)

_Strategy: RV mean-reversion + cost gate (Phase-2 idea, intraday). Data: **live**. Regime: **Balanced · High Vol**. Fixed 1 unit/trade, gross (slippage 0)._

**23 trades · gross $1,980 · win 83% · PF 2.768 · exp $86/trade · max DD $-330**

Each trade: the setup, the legs with fills, the signal, the exit and the gross PnL.

---

### 1. Brent-WTI arb (Aug) — LONG  (+20 USD)
- **Setup:** dislocated to -2.28sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 80/100
- **Legs (entry->exit):** CO_Q26 86.92->86.76, CL_Q26 82.92->82.74
- **In:** 2026-06-12 15:45 @ 4.0   **Out:** 2026-06-12 20:45 @ 4.02 (z -0.19, session_end)
- **Held:** 20 bars (300 min)   **MAE/MFE:** -40 / +70

### 2. WTI Aug/Sep (M2-M3) — LONG  (-330 USD)
- **Setup:** dislocated to -3.20sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 85/100
- **Legs (entry->exit):** CL_Q26 79.63->78.76, CL_U26 78.27->77.73
- **In:** 2026-06-14 22:00 @ 1.36   **Out:** 2026-06-15 10:00 @ 1.03 (z -2.25, time_stop)
- **Held:** 48 bars (720 min)   **MAE/MFE:** -330 / +10

### 3. Brent-WTI arb (Aug) — SHORT  (+180 USD)
- **Setup:** dislocated to +3.16sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 90/100
- **Legs (entry->exit):** CO_Q26 83.55->82.95, CL_Q26 79.35->78.93
- **In:** 2026-06-15 00:00 @ 4.2   **Out:** 2026-06-15 09:00 @ 4.02 (z -1.92, target)
- **Held:** 36 bars (540 min)   **MAE/MFE:** -110 / +180

### 4. WTI Jul/Aug/Sep fly — SHORT  (+310 USD)
- **Setup:** dislocated to +2.47sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 82/100
- **Legs (entry->exit):** CL_N26 80.22->80.23, CL_Q26 78.76->79.02, CL_U26 77.73->77.93
- **In:** 2026-06-15 10:00 @ 0.43   **Out:** 2026-06-15 12:15 @ 0.12 (z -1.60, target)
- **Held:** 9 bars (135 min)   **MAE/MFE:** +0 / +310

### 5. Brent-WTI arb (Aug) — LONG  (-290 USD)
- **Setup:** dislocated to -2.11sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 78/100
- **Legs (entry->exit):** CO_Q26 82.95->83.48, CL_Q26 78.99->79.81
- **In:** 2026-06-15 10:15 @ 3.96   **Out:** 2026-06-15 20:45 @ 3.67 (z -1.21, session_end)
- **Held:** 42 bars (630 min)   **MAE/MFE:** -320 / +140

### 6. WTI Aug/Sep (M2-M3) — SHORT  (+100 USD)
- **Setup:** dislocated to +2.31sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 76/100
- **Legs (entry->exit):** CL_Q26 79.23->79.59, CL_U26 77.99->78.45
- **In:** 2026-06-15 15:00 @ 1.24   **Out:** 2026-06-16 01:45 @ 1.14 (z -3.10, target)
- **Held:** 39 bars (645 min)   **MAE/MFE:** -190 / +100

### 7. WTI Jul/Aug/Sep fly — LONG  (+280 USD)
- **Setup:** dislocated to -2.74sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 86/100
- **Legs (entry->exit):** CL_N26 81.12->80.92, CL_Q26 79.78->79.59, CL_U26 78.35->78.45
- **In:** 2026-06-15 22:00 @ -0.09   **Out:** 2026-06-16 01:45 @ 0.19 (z +2.89, target)
- **Held:** 15 bars (225 min)   **MAE/MFE:** +0 / +280

### 8. Brent-WTI arb (Aug) — LONG  (+130 USD)
- **Setup:** dislocated to -2.06sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 77/100
- **Legs (entry->exit):** CO_Q26 82.94->82.12, CL_Q26 79.37->78.42
- **In:** 2026-06-16 03:00 @ 3.57   **Out:** 2026-06-16 07:30 @ 3.7 (z +2.21, target)
- **Held:** 18 bars (270 min)   **MAE/MFE:** -70 / +130

### 9. WTI Aug/Sep (M2-M3) — LONG  (-320 USD)
- **Setup:** dislocated to -3.01sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 85/100
- **Legs (entry->exit):** CL_Q26 78.42->76.24, CL_U26 77.35->75.49
- **In:** 2026-06-16 07:30 @ 1.07   **Out:** 2026-06-16 19:30 @ 0.75 (z +0.44, time_stop)
- **Held:** 48 bars (720 min)   **MAE/MFE:** -450 / +10

### 10. Brent-WTI arb (Aug) — SHORT  (+240 USD)
- **Setup:** dislocated to +2.31sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 81/100
- **Legs (entry->exit):** CO_Q26 81.87->80.21, CL_Q26 78.15->76.73
- **In:** 2026-06-16 07:45 @ 3.72   **Out:** 2026-06-16 12:00 @ 3.48 (z -1.87, target)
- **Held:** 17 bars (255 min)   **MAE/MFE:** -70 / +240

### 11. WTI Jul/Aug/Sep fly — SHORT  (+140 USD)
- **Setup:** dislocated to +2.61sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 84/100
- **Legs (entry->exit):** CL_N26 78.73->77.12, CL_Q26 77.54->76.2, CL_U26 76.57->75.36
- **In:** 2026-06-16 08:00 @ 0.22   **Out:** 2026-06-16 12:30 @ 0.08 (z -2.04, target)
- **Held:** 18 bars (270 min)   **MAE/MFE:** -30 / +140

### 12. Brent-WTI arb (Aug) — LONG  (+90 USD)
- **Setup:** dislocated to -2.31sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 81/100
- **Legs (entry->exit):** CO_Q26 79.51->79.5, CL_Q26 75.93->75.83
- **In:** 2026-06-16 19:00 @ 3.58   **Out:** 2026-06-16 20:45 @ 3.67 (z +0.08, session_end)
- **Held:** 7 bars (105 min)   **MAE/MFE:** -60 / +90

### 13. WTI Aug/Sep (M2-M3) — SHORT  (+140 USD)
- **Setup:** dislocated to +2.34sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 76/100
- **Legs (entry->exit):** CL_Q26 76.0->75.56, CL_U26 75.17->74.87
- **In:** 2026-06-16 22:00 @ 0.83   **Out:** 2026-06-17 01:15 @ 0.69 (z -1.85, target)
- **Held:** 13 bars (195 min)   **MAE/MFE:** +0 / +140

### 14. WTI Aug/Sep (M2-M3) — LONG  (+40 USD)
- **Setup:** dislocated to -2.15sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 74/100
- **Legs (entry->exit):** CL_Q26 75.38->75.59, CL_U26 74.73->74.9
- **In:** 2026-06-17 02:15 @ 0.65   **Out:** 2026-06-17 10:00 @ 0.69 (z +1.52, target)
- **Held:** 31 bars (465 min)   **MAE/MFE:** -130 / +60

### 15. Brent-WTI arb (Aug) — SHORT  (+190 USD)
- **Setup:** dislocated to +2.11sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 78/100
- **Legs (entry->exit):** CO_Q26 79.38->78.83, CL_Q26 75.66->75.3
- **In:** 2026-06-17 08:30 @ 3.72   **Out:** 2026-06-17 10:30 @ 3.53 (z -1.66, target)
- **Held:** 8 bars (120 min)   **MAE/MFE:** +0 / +190

### 16. Brent-WTI arb (Aug) — SHORT  (+300 USD)
- **Setup:** dislocated to +2.79sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 87/100
- **Legs (entry->exit):** CO_Q26 79.6->79.51, CL_Q26 75.78->75.99
- **In:** 2026-06-17 12:00 @ 3.82   **Out:** 2026-06-17 16:30 @ 3.52 (z -1.70, target)
- **Held:** 18 bars (270 min)   **MAE/MFE:** +0 / +300

### 17. WTI Aug/Sep (M2-M3) — SHORT  (+80 USD)
- **Setup:** dislocated to +2.34sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 76/100
- **Legs (entry->exit):** CL_Q26 76.37->75.36, CL_U26 75.54->74.61
- **In:** 2026-06-17 13:45 @ 0.83   **Out:** 2026-06-17 19:30 @ 0.75 (z -1.74, target)
- **Held:** 23 bars (345 min)   **MAE/MFE:** -170 / +80

### 18. WTI Jul/Aug/Sep fly — LONG  (+180 USD)
- **Setup:** dislocated to -3.07sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 89/100
- **Legs (entry->exit):** CL_N26 77.83->75.44, CL_Q26 77.02->74.7, CL_U26 76.03->73.96
- **In:** 2026-06-17 14:45 @ -0.18   **Out:** 2026-06-18 02:00 @ -0.0 (z +1.77, target)
- **Held:** 41 bars (675 min)   **MAE/MFE:** -30 / +180

### 19. Brent-WTI arb (Aug) — SHORT  (-180 USD)
- **Setup:** dislocated to +2.12sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 78/100
- **Legs (entry->exit):** CO_Q26 78.71->78.6, CL_Q26 75.01->74.72
- **In:** 2026-06-17 20:45 @ 3.7   **Out:** 2026-06-18 11:45 @ 3.88 (z +0.85, time_stop)
- **Held:** 48 bars (900 min)   **MAE/MFE:** -280 / +200

### 20. WTI Jul/Aug/Sep fly — SHORT  (+170 USD)
- **Setup:** dislocated to +2.70sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 85/100
- **Legs (entry->exit):** CL_N26 75.67->75.05, CL_Q26 74.8->74.37, CL_U26 74.04->73.63
- **In:** 2026-06-18 02:45 @ 0.11   **Out:** 2026-06-18 08:00 @ -0.06 (z -1.84, target)
- **Held:** 21 bars (315 min)   **MAE/MFE:** +0 / +170

### 21. WTI Aug/Sep (M2-M3) — LONG  (+130 USD)
- **Setup:** dislocated to -2.94sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 84/100
- **Legs (entry->exit):** CL_Q26 73.7->73.8, CL_U26 73.08->73.05
- **In:** 2026-06-18 09:45 @ 0.62   **Out:** 2026-06-18 15:30 @ 0.75 (z +1.75, target)
- **Held:** 23 bars (345 min)   **MAE/MFE:** +0 / +130

### 22. WTI Jul/Aug/Sep fly — SHORT  (+310 USD)
- **Setup:** dislocated to +2.60sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 84/100
- **Legs (entry->exit):** CL_N26 74.11->76.05, CL_Q26 73.3->75.38, CL_U26 72.66->74.57
- **In:** 2026-06-18 14:45 @ 0.17   **Out:** 2026-06-18 23:45 @ -0.14 (z -1.76, target)
- **Held:** 32 bars (540 min)   **MAE/MFE:** -530 / +310

### 23. WTI Aug/Sep (M2-M3) — SHORT  (+70 USD)
- **Setup:** dislocated to +2.30sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 76/100
- **Legs (entry->exit):** CL_Q26 74.29->75.08, CL_U26 73.49->74.35
- **In:** 2026-06-18 16:45 @ 0.8   **Out:** 2026-06-19 00:00 @ 0.73 (z -2.04, target)
- **Held:** 25 bars (435 min)   **MAE/MFE:** -50 / +70
