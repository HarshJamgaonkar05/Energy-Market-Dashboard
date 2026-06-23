# Trade Log — Phase-3 backtest (RV mean-reversion + shock absorption, intraday)

_Strategy: RV mean-reversion + cost gate + shock absorption (Phase-2 idea, intraday). Data: **live**. Regime: **Balanced · High Vol**. Base 1 unit/trade (shock-aware sizing), gross (slippage 0)._

**27 trades · gross $1,211 · win 70% · PF 3.057 · Sharpe 9.287 · max DD $-152**

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

### 6. WTI Aug/Sep (M2-M3) — LONG  (-110 USD)
- **Setup:** dislocated to -2.53sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 79/100 · entry severity 0.00 · size 1.00u
- **Legs (entry->exit):** CL_Q26 78.15->77.54, CL_U26 77.07->76.57
- **In:** 2026-06-16 07:45 @ 1.08   **Out:** 2026-06-16 08:00 @ 0.97 (z -3.10, shock_flat)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -110 / +0

### 7. Brent-WTI arb (Aug) — SHORT  (+57 USD)
- **Setup:** dislocated to +2.31sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 81/100 · entry severity 0.06 · size 0.94u
- **Legs (entry->exit):** CO_Q26 81.87->81.14, CL_Q26 78.15->77.48
- **In:** 2026-06-16 07:45 @ 3.72   **Out:** 2026-06-16 08:45 @ 3.66 (z +0.81, shock_flat)
- **Held:** 4 bars (60 min)   **MAE/MFE:** -47 / +57

### 8. WTI Jul/Aug/Sep fly — SHORT  (+56 USD)
- **Setup:** dislocated to +2.61sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 84/100 · entry severity 0.62 · size 0.40u
- **Legs (entry->exit):** CL_N26 78.73->77.12, CL_Q26 77.54->76.2, CL_U26 76.57->75.36
- **In:** 2026-06-16 08:00 @ 0.22   **Out:** 2026-06-16 12:30 @ 0.08 (z -2.04, target)
- **Held:** 18 bars (270 min)   **MAE/MFE:** -12 / +56

### 9. WTI Aug/Sep (M2-M3) — LONG  (-228 USD)
- **Setup:** dislocated to -2.21sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 75/100 · entry severity 0.19 · size 0.81u
- **Legs (entry->exit):** CL_Q26 77.44->76.21, CL_U26 76.43->75.48
- **In:** 2026-06-16 08:15 @ 1.01   **Out:** 2026-06-16 14:30 @ 0.73 (z -2.12, shock_flat)
- **Held:** 25 bars (375 min)   **MAE/MFE:** -228 / +0

### 10. Brent-WTI arb (Aug) — LONG  (+75 USD)
- **Setup:** dislocated to -2.31sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 81/100 · entry severity 0.17 · size 0.83u
- **Legs (entry->exit):** CO_Q26 79.51->79.5, CL_Q26 75.93->75.83
- **In:** 2026-06-16 19:00 @ 3.58   **Out:** 2026-06-16 20:45 @ 3.67 (z +0.08, shock_flat)
- **Held:** 7 bars (105 min)   **MAE/MFE:** -50 / +75

### 11. WTI Aug/Sep (M2-M3) — LONG  (+60 USD)
- **Setup:** dislocated to -2.15sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 74/100 · entry severity 0.00 · size 1.00u
- **Legs (entry->exit):** CL_Q26 75.38->75.36, CL_U26 74.73->74.65
- **In:** 2026-06-17 02:15 @ 0.65   **Out:** 2026-06-17 02:30 @ 0.71 (z -0.50, shock_flat)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +60

### 12. WTI Aug/Sep (M2-M3) — LONG  (+68 USD)
- **Setup:** dislocated to -2.03sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 72/100 · entry severity 0.02 · size 0.98u
- **Legs (entry->exit):** CL_Q26 75.01->75.03, CL_U26 74.39->74.34
- **In:** 2026-06-17 03:15 @ 0.62   **Out:** 2026-06-17 04:00 @ 0.69 (z -0.21, shock_flat)
- **Held:** 3 bars (45 min)   **MAE/MFE:** -10 / +68

### 13. WTI Aug/Sep (M2-M3) — LONG  (+99 USD)
- **Setup:** dislocated to -2.16sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 74/100 · entry severity 0.01 · size 0.99u
- **Legs (entry->exit):** CL_Q26 74.79->75.0, CL_U26 74.25->74.36
- **In:** 2026-06-17 06:45 @ 0.54   **Out:** 2026-06-17 07:45 @ 0.64 (z +0.33, shock_flat)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +99

### 14. Brent-WTI arb (Aug) — SHORT  (+101 USD)
- **Setup:** dislocated to +2.11sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 78/100 · entry severity 0.41 · size 0.59u
- **Legs (entry->exit):** CO_Q26 79.38->79.17, CL_Q26 75.66->75.62
- **In:** 2026-06-17 08:30 @ 3.72   **Out:** 2026-06-17 10:15 @ 3.55 (z -1.40, shock_flat)
- **Held:** 7 bars (105 min)   **MAE/MFE:** +0 / +101

### 15. Brent-WTI arb (Aug) — SHORT  (+75 USD)
- **Setup:** dislocated to +2.27sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 80/100 · entry severity 0.17 · size 0.83u
- **Legs (entry->exit):** CO_Q26 79.72->79.52, CL_Q26 75.91->75.8
- **In:** 2026-06-17 12:15 @ 3.81   **Out:** 2026-06-17 12:30 @ 3.72 (z +0.95, shock_flat)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +75

### 16. WTI Aug/Sep (M2-M3) — SHORT  (-35 USD)
- **Setup:** dislocated to +2.34sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 76/100 · entry severity 0.50 · size 0.50u
- **Legs (entry->exit):** CL_Q26 76.37->76.55, CL_U26 75.54->75.65
- **In:** 2026-06-17 13:45 @ 0.83   **Out:** 2026-06-17 14:15 @ 0.9 (z +2.66, shock_flat)
- **Held:** 2 bars (30 min)   **MAE/MFE:** -35 / +0

### 17. WTI Aug/Sep (M2-M3) — SHORT  (+63 USD)
- **Setup:** dislocated to +2.56sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 79/100 · entry severity 0.30 · size 0.70u
- **Legs (entry->exit):** CL_Q26 77.02->76.1, CL_U26 76.03->75.2
- **In:** 2026-06-17 14:45 @ 0.99   **Out:** 2026-06-17 15:15 @ 0.9 (z +1.21, shock_flat)
- **Held:** 2 bars (30 min)   **MAE/MFE:** -7 / +63

### 18. WTI Jul/Aug/Sep fly — LONG  (+70 USD)
- **Setup:** dislocated to -3.07sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 89/100 · entry severity 0.50 · size 0.50u
- **Legs (entry->exit):** CL_N26 77.83->76.96, CL_Q26 77.02->76.1, CL_U26 76.03->75.2
- **In:** 2026-06-17 14:45 @ -0.18   **Out:** 2026-06-17 15:15 @ -0.04 (z -0.43, shock_flat)
- **Held:** 2 bars (30 min)   **MAE/MFE:** -15 / +70

### 19. Brent-WTI arb (Aug) — SHORT  (-52 USD)
- **Setup:** dislocated to +2.63sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 85/100 · entry severity 0.85 · size 0.40u
- **Legs (entry->exit):** CO_Q26 77.88->78.12, CL_Q26 74.06->74.17
- **In:** 2026-06-18 09:00 @ 3.82   **Out:** 2026-06-18 09:30 @ 3.95 (z +3.10, shock_flat)
- **Held:** 2 bars (30 min)   **MAE/MFE:** -52 / +0

### 20. Brent-WTI arb (Aug) — SHORT  (+139 USD)
- **Setup:** dislocated to +2.74sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 83% · confidence 87/100 · entry severity 0.08 · size 0.92u
- **Legs (entry->exit):** CO_Q26 77.68->77.79, CL_Q26 73.7->73.96
- **In:** 2026-06-18 09:45 @ 3.98   **Out:** 2026-06-18 10:00 @ 3.83 (z +1.02, shock_flat)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +139

### 21. WTI Jul/Aug/Sep fly — SHORT  (-48 USD)
- **Setup:** dislocated to +2.60sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 84/100 · entry severity 0.68 · size 0.40u
- **Legs (entry->exit):** CL_N26 74.11->74.17, CL_Q26 73.3->73.22, CL_U26 72.66->72.56
- **In:** 2026-06-18 14:45 @ 0.17   **Out:** 2026-06-18 15:00 @ 0.29 (z +3.12, shock_flat)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -48 / +0

### 22. WTI Jul/Aug/Sep fly — SHORT  (+184 USD)
- **Setup:** dislocated to +2.76sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 86/100 · entry severity 0.23 · size 0.77u
- **Legs (entry->exit):** CL_N26 74.52->74.64, CL_Q26 73.5->73.8, CL_U26 72.81->73.05
- **In:** 2026-06-18 15:15 @ 0.33   **Out:** 2026-06-18 15:30 @ 0.09 (z +0.60, shock_flat)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +184

### 23. WTI Aug/Sep (M2-M3) — SHORT  (+68 USD)
- **Setup:** dislocated to +2.23sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 75% · confidence 75/100 · entry severity 0.25 · size 0.75u
- **Legs (entry->exit):** CL_Q26 74.39->75.86, CL_U26 73.56->75.12
- **In:** 2026-06-18 17:15 @ 0.83   **Out:** 2026-06-18 18:15 @ 0.74 (z +0.31, shock_flat)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +68

### 24. WTI Jul/Aug/Sep fly — SHORT  (+88 USD)
- **Setup:** dislocated to +2.22sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 79/100 · entry severity 0.62 · size 0.40u
- **Legs (entry->exit):** CL_N26 76.85->76.59, CL_Q26 75.66->75.62, CL_U26 74.86->74.82
- **In:** 2026-06-18 19:15 @ 0.39   **Out:** 2026-06-18 19:30 @ 0.17 (z +0.33, shock_flat)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +88

### 25. WTI Jul/Aug/Sep fly — SHORT  (+263 USD)
- **Setup:** dislocated to +2.34sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 80/100 · entry severity 0.51 · size 0.49u
- **Legs (entry->exit):** CL_N26 76.86->76.32, CL_Q26 75.42->75.38, CL_U26 74.61->74.53
- **In:** 2026-06-18 22:30 @ 0.63   **Out:** 2026-06-18 22:45 @ 0.09 (z -0.72, shock_flat)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +263

### 26. WTI Jul/Aug/Sep fly — LONG  (+80 USD)
- **Setup:** dislocated to -2.25sigma (cheap) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 79/100 · entry severity 0.60 · size 0.40u
- **Legs (entry->exit):** CL_N26 76.14->76.14, CL_Q26 75.75->75.59, CL_U26 74.9->74.78
- **In:** 2026-06-19 02:00 @ -0.46   **Out:** 2026-06-19 02:15 @ -0.26 (z -1.36, shock_flat)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +80

### 27. WTI Jul/Aug/Sep fly — SHORT  (+124 USD)
- **Setup:** dislocated to +2.30sigma (rich) -> fade · regime Balanced · High Vol · hist. edge 82% · confidence 80/100 · entry severity 0.80 · size 0.40u
- **Legs (entry->exit):** CL_N26 77.23->77.34, CL_Q26 75.95->76.31, CL_U26 75.1->75.4
- **In:** 2026-06-19 05:15 @ 0.43   **Out:** 2026-06-19 05:30 @ 0.12 (z +0.68, shock_flat)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +124
