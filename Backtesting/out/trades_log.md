# Trade Log — Phase-2 strategy backtested on the provided 15-min data

_Strategy: Regime-conditioned RV mean-reversion (Phase 2). Data: **live**. Regime: **Balanced · High Vol**. Gross basis (slippage 0)._

**208 trades · gross $6,380 · win 65% · PF 2.724 · max DD $-650**

Each trade names the strategy, the setup, the legs with fills, the signal, the exit and the gross PnL.

---

### 1. WTI Jul/Aug (M1-M2) — SHORT  (+130 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 92/100
- **Setup:** dislocated to +2.47sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 87.03->86.42, CL_Q26 85.36->84.88
- **In:** 2026-06-12 13:45 @ 1.67   **Out:** 2026-06-12 14:00 @ 1.54 (z -0.45, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +130

### 2. WTI Aug/Sep (M2-M3) — SHORT  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 92/100
- **Setup:** dislocated to +4.05sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 85.36->84.88, CL_U26 83.73->83.3
- **In:** 2026-06-12 13:45 @ 1.63   **Out:** 2026-06-12 14:00 @ 1.58 (z +2.92, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +50

### 3. Brent Aug/Sep (M1-M2) — SHORT  (+200 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 90/100
- **Setup:** dislocated to +3.91sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 89.65->87.66, CO_U26 88.31->86.52
- **In:** 2026-06-12 13:45 @ 1.34   **Out:** 2026-06-12 14:45 @ 1.14 (z -1.24, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +200

### 4. Brent Sep/Oct (M2-M3) — SHORT  (+100 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 80/100
- **Setup:** dislocated to +1.83sigma (rich) -> fade
- **Legs (entry->exit):** CO_U26 88.31->86.52, CO_V26 86.93->85.24
- **In:** 2026-06-12 13:45 @ 1.38   **Out:** 2026-06-12 14:45 @ 1.28 (z -0.42, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** -20 / +100

### 5. WTI Jul/Aug/Sep fly — LONG  (-20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 76/100
- **Setup:** dislocated to -2.79sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 86.42->86.46, CL_Q26 84.88->84.93, CL_U26 83.3->83.34
- **In:** 2026-06-12 14:00 @ -0.04   **Out:** 2026-06-12 14:15 @ -0.06 (z -2.78, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -20 / +0

### 6. WTI Aug/Sep (M2-M3) — SHORT  (+0 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 92/100
- **Setup:** dislocated to +3.15sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 84.93->84.91, CL_U26 83.34->83.32
- **In:** 2026-06-12 14:15 @ 1.59   **Out:** 2026-06-12 14:30 @ 1.59 (z +2.70, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +0

### 7. Brent Aug/Sep/Oct fly — LONG  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 66/100
- **Setup:** dislocated to -1.80sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 89.26->87.29, CO_U26 88.03->86.11, CO_V26 86.63->84.81
- **In:** 2026-06-12 14:15 @ -0.17   **Out:** 2026-06-12 16:30 @ -0.12 (z +0.81, target)
- **Held:** 9 bars (135 min)   **MAE/MFE:** -20 / +50

### 8. WTI Jul/Aug/Sep fly — LONG  (-40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 71/100
- **Setup:** dislocated to -2.17sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 86.44->84.91, CL_Q26 84.91->83.36, CL_U26 83.32->81.71
- **In:** 2026-06-12 14:30 @ -0.06   **Out:** 2026-06-12 17:45 @ -0.1 (z -0.77, time_stop)
- **Held:** 13 bars (195 min)   **MAE/MFE:** -90 / +80

### 9. Brent-WTI arb (Aug) — LONG  (-40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 77/100
- **Setup:** dislocated to -2.55sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 87.66->87.26, CL_Q26 83.49->83.13
- **In:** 2026-06-12 14:45 @ 4.17   **Out:** 2026-06-12 15:00 @ 4.13 (z -3.15, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -40 / +0

### 10. Brent-WTI arb (Aug) — LONG  (-20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 77/100
- **Setup:** dislocated to -2.80sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 87.0->86.91, CL_Q26 82.93->82.86
- **In:** 2026-06-12 15:15 @ 4.07   **Out:** 2026-06-12 18:30 @ 4.05 (z +0.58, target)
- **Held:** 13 bars (195 min)   **MAE/MFE:** -110 / +70

### 11. Brent Aug/Sep (M1-M2) — LONG  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 59/100
- **Setup:** dislocated to -1.77sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 86.92->87.25, CO_U26 85.85->86.09
- **In:** 2026-06-12 15:45 @ 1.07   **Out:** 2026-06-12 16:15 @ 1.16 (z -0.07, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +90

### 12. WTI Aug/Sep (M2-M3) — SHORT  (+110 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 78/100
- **Setup:** dislocated to +1.52sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 83.41->82.86, CL_U26 81.72->81.28
- **In:** 2026-06-12 18:00 @ 1.69   **Out:** 2026-06-12 18:30 @ 1.58 (z -0.67, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +110

### 13. WTI Jul/Aug/Sep fly — LONG  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 68/100
- **Setup:** dislocated to -1.93sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 84.93->84.36, CL_Q26 83.41->82.86, CL_U26 81.72->81.28
- **In:** 2026-06-12 18:00 @ -0.17   **Out:** 2026-06-12 18:30 @ -0.08 (z +0.17, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +90

### 14. Brent Aug/Sep/Oct fly — SHORT  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 96/100
- **Setup:** dislocated to +2.47sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 87.41->86.93, CO_U26 86.21->85.8, CO_V26 84.91->84.51
- **In:** 2026-06-12 18:00 @ -0.1   **Out:** 2026-06-12 19:15 @ -0.16 (z -0.40, target)
- **Held:** 5 bars (75 min)   **MAE/MFE:** -10 / +60

### 15. Brent Sep/Oct (M2-M3) — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 58/100
- **Setup:** dislocated to -1.69sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 85.76->85.65, CO_V26 84.52->84.37
- **In:** 2026-06-12 18:30 @ 1.24   **Out:** 2026-06-12 20:30 @ 1.28 (z +0.00, target)
- **Held:** 8 bars (120 min)   **MAE/MFE:** +0 / +50

### 16. WTI Jul/Aug (M1-M2) — SHORT  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 80/100
- **Setup:** dislocated to +1.69sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 84.52->84.56, CL_Q26 82.95->83.04
- **In:** 2026-06-12 19:00 @ 1.57   **Out:** 2026-06-12 19:30 @ 1.52 (z -0.00, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +50

### 17. WTI Jul/Aug/Sep fly — SHORT  (+110 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 85/100
- **Setup:** dislocated to +1.73sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 84.52->84.27, CL_Q26 82.95->82.79, CL_U26 81.38->81.2
- **In:** 2026-06-12 19:00 @ 0.0   **Out:** 2026-06-12 20:30 @ -0.11 (z -0.34, target)
- **Held:** 6 bars (90 min)   **MAE/MFE:** +0 / +110

### 18. Brent Aug/Sep (M1-M2) — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 66/100
- **Setup:** dislocated to -2.25sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 86.78->86.8, CO_U26 85.67->85.65
- **In:** 2026-06-12 19:45 @ 1.11   **Out:** 2026-06-12 21:15 @ 1.15 (z +0.00, target)
- **Held:** 6 bars (90 min)   **MAE/MFE:** +0 / +40

### 19. WTI Aug/Sep (M2-M3) — LONG  (-130 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 63/100
- **Setup:** dislocated to -1.83sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 82.74->79.63, CL_U26 81.25->78.27
- **In:** 2026-06-12 20:45 @ 1.49   **Out:** 2026-06-14 22:00 @ 1.36 (z -4.14, stop)
- **Held:** 1 bars (2955 min)   **MAE/MFE:** -130 / +0

### 20. WTI Jul/Aug/Sep fly — SHORT  (+120 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 92/100
- **Setup:** dislocated to +2.19sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 84.29->81.27, CL_Q26 82.74->80.0, CL_U26 81.25->78.67
- **In:** 2026-06-12 20:45 @ 0.06   **Out:** 2026-06-14 22:45 @ -0.06 (z -0.45, target)
- **Held:** 4 bars (3000 min)   **MAE/MFE:** +0 / +120

### 21. Brent Sep/Oct (M2-M3) — SHORT  (+70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 83/100
- **Setup:** dislocated to +2.02sigma (rich) -> fade
- **Legs (entry->exit):** CO_U26 85.72->85.65, CO_V26 84.38->84.38
- **In:** 2026-06-12 21:00 @ 1.34   **Out:** 2026-06-12 21:15 @ 1.27 (z -0.45, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +70

### 22. Brent Aug/Sep/Oct fly — LONG  (+80 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 69/100
- **Setup:** dislocated to -2.02sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 86.86->86.8, CO_U26 85.72->85.65, CO_V26 84.38->84.38
- **In:** 2026-06-12 21:00 @ -0.2   **Out:** 2026-06-12 21:15 @ -0.12 (z +0.51, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +80

### 23. Brent Aug/Sep (M1-M2) — SHORT  (+240 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 90/100
- **Setup:** dislocated to +3.37sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 86.8->83.55, CO_U26 85.58->82.57
- **In:** 2026-06-12 21:45 @ 1.22   **Out:** 2026-06-15 00:00 @ 0.98 (z -7.19, target)
- **Held:** 1 bars (3015 min)   **MAE/MFE:** +0 / +240

### 24. Brent Aug/Sep/Oct fly — SHORT  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 89/100
- **Setup:** dislocated to +2.02sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 86.8->83.8, CO_U26 85.58->82.83, CO_V26 84.29->81.7
- **In:** 2026-06-12 21:45 @ -0.07   **Out:** 2026-06-15 00:15 @ -0.16 (z -1.01, target)
- **Held:** 2 bars (3030 min)   **MAE/MFE:** +0 / +90

### 25. WTI Jul/Aug (M1-M2) — LONG  (-10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -6.41sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.96->81.35, CL_Q26 79.63->80.03
- **In:** 2026-06-14 22:00 @ 1.33   **Out:** 2026-06-14 22:15 @ 1.32 (z -6.74, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -10 / +0

### 26. WTI Aug/Sep (M2-M3) — LONG  (-10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -4.95sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 80.03->80.21, CL_U26 78.68->78.87
- **In:** 2026-06-14 22:15 @ 1.35   **Out:** 2026-06-14 22:30 @ 1.34 (z -5.06, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -10 / +0

### 27. WTI Jul/Aug (M1-M2) — LONG  (-90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -4.32sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 81.57->81.27, CL_Q26 80.21->80.0
- **In:** 2026-06-14 22:30 @ 1.36   **Out:** 2026-06-14 22:45 @ 1.27 (z -6.61, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -90 / +0

### 28. WTI Aug/Sep (M2-M3) — LONG  (-20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -3.79sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 80.0->79.79, CL_U26 78.67->78.48
- **In:** 2026-06-14 22:45 @ 1.33   **Out:** 2026-06-14 23:15 @ 1.31 (z -3.10, stop)
- **Held:** 2 bars (30 min)   **MAE/MFE:** -20 / +40

### 29. WTI Jul/Aug (M1-M2) — LONG  (-70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -4.34sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.91->80.58, CL_Q26 79.63->79.37
- **In:** 2026-06-14 23:00 @ 1.28   **Out:** 2026-06-15 02:00 @ 1.21 (z -2.53, stop)
- **Held:** 12 bars (180 min)   **MAE/MFE:** -70 / +50

### 30. WTI Jul/Aug/Sep fly — SHORT  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 95/100
- **Setup:** dislocated to +2.43sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 80.66->80.85, CL_Q26 79.35->79.58, CL_U26 78.1->78.28
- **In:** 2026-06-15 00:00 @ 0.06   **Out:** 2026-06-15 00:15 @ -0.03 (z +0.00, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +90

### 31. Brent Sep/Oct (M2-M3) — LONG  (+70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -14.50sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.57->82.83, CO_V26 81.51->81.7
- **In:** 2026-06-15 00:00 @ 1.06   **Out:** 2026-06-15 00:15 @ 1.13 (z -9.44, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +70

### 32. Brent-WTI arb (Aug) — SHORT  (-20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 97/100
- **Setup:** dislocated to +8.09sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.55->83.8, CL_Q26 79.35->79.58
- **In:** 2026-06-15 00:00 @ 4.2   **Out:** 2026-06-15 00:15 @ 4.22 (z +8.99, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -20 / +0

### 33. Brent Aug/Sep (M1-M2) — LONG  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -7.64sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.8->84.05, CO_U26 82.83->83.03
- **In:** 2026-06-15 00:15 @ 0.97   **Out:** 2026-06-15 00:30 @ 1.02 (z -5.17, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +50

### 34. Brent Sep/Oct (M2-M3) — LONG  (-30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -10.79sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 83.03->82.92, CO_V26 81.92->81.84
- **In:** 2026-06-15 00:30 @ 1.11   **Out:** 2026-06-15 00:45 @ 1.08 (z -12.82, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -30 / +0

### 35. Brent-WTI arb (Aug) — SHORT  (+20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 97/100
- **Setup:** dislocated to +5.26sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 84.05->83.87, CL_Q26 79.83->79.67
- **In:** 2026-06-15 00:30 @ 4.22   **Out:** 2026-06-15 00:45 @ 4.2 (z +4.72, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +20

### 36. Brent Aug/Sep (M1-M2) — LONG  (-30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -6.07sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.87->83.82, CO_U26 82.92->82.9
- **In:** 2026-06-15 00:45 @ 0.95   **Out:** 2026-06-15 01:00 @ 0.92 (z -6.91, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -30 / +0

### 37. WTI Aug/Sep (M2-M3) — LONG  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -3.26sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 79.58->78.87, CL_U26 78.39->77.62
- **In:** 2026-06-15 01:00 @ 1.19   **Out:** 2026-06-15 02:45 @ 1.25 (z +0.00, target)
- **Held:** 7 bars (105 min)   **MAE/MFE:** +0 / +60

### 38. WTI Jul/Aug/Sep fly — SHORT  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 88/100
- **Setup:** dislocated to +1.93sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 80.85->80.6, CL_Q26 79.58->79.37, CL_U26 78.39->78.13
- **In:** 2026-06-15 01:00 @ 0.08   **Out:** 2026-06-15 01:15 @ -0.01 (z +0.00, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +90

### 39. Brent Sep/Oct (M2-M3) — LONG  (-40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -9.44sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.9->82.61, CO_V26 81.84->81.59
- **In:** 2026-06-15 01:00 @ 1.06   **Out:** 2026-06-15 01:15 @ 1.02 (z -8.26, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -40 / +0

### 40. Brent-WTI arb (Aug) — SHORT  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 97/100
- **Setup:** dislocated to +5.40sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.82->83.58, CL_Q26 79.58->79.37
- **In:** 2026-06-15 01:00 @ 4.24   **Out:** 2026-06-15 01:15 @ 4.21 (z +3.60, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +30

### 41. Brent Aug/Sep (M1-M2) — LONG  (-160 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -2.89sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.58->83.11, CO_U26 82.61->82.3
- **In:** 2026-06-15 01:15 @ 0.97   **Out:** 2026-06-15 03:15 @ 0.81 (z -2.60, stop)
- **Held:** 8 bars (120 min)   **MAE/MFE:** -160 / +0

### 42. Brent Aug/Sep/Oct fly — SHORT  (+70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 96/100
- **Setup:** dislocated to +2.70sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.58->83.4, CO_U26 82.61->82.47, CO_V26 81.59->81.42
- **In:** 2026-06-15 01:15 @ -0.05   **Out:** 2026-06-15 02:15 @ -0.12 (z +0.00, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +70

### 43. Brent Sep/Oct (M2-M3) — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -2.70sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.83->82.47, CO_V26 81.79->81.39
- **In:** 2026-06-15 01:30 @ 1.04   **Out:** 2026-06-15 03:30 @ 1.08 (z +0.67, target)
- **Held:** 8 bars (120 min)   **MAE/MFE:** -50 / +40

### 44. Brent-WTI arb (Aug) — SHORT  (+10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 91/100
- **Setup:** dislocated to +2.08sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.77->83.17, CL_Q26 79.54->78.95
- **In:** 2026-06-15 01:30 @ 4.23   **Out:** 2026-06-15 03:00 @ 4.22 (z +0.00, target)
- **Held:** 6 bars (90 min)   **MAE/MFE:** -80 / +10

### 45. WTI Jul/Aug/Sep fly — SHORT  (+80 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 84/100
- **Setup:** dislocated to +1.62sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 80.91->80.58, CL_Q26 79.64->79.37, CL_U26 78.42->78.13
- **In:** 2026-06-15 01:45 @ 0.05   **Out:** 2026-06-15 02:00 @ -0.03 (z -0.54, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +80

### 46. WTI Jul/Aug (M1-M2) — LONG  (+150 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 60/100
- **Setup:** dislocated to -1.69sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.34->80.56, CL_Q26 79.14->79.21
- **In:** 2026-06-15 02:15 @ 1.2   **Out:** 2026-06-15 03:30 @ 1.35 (z +1.50, target)
- **Held:** 5 bars (75 min)   **MAE/MFE:** -60 / +150

### 47. WTI Jul/Aug/Sep fly — LONG  (+130 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 66/100
- **Setup:** dislocated to -1.80sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.16->80.13, CL_Q26 79.01->78.93, CL_U26 77.77->77.77
- **In:** 2026-06-15 02:30 @ -0.09   **Out:** 2026-06-15 03:15 @ 0.04 (z +1.35, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +130

### 48. WTI Aug/Sep (M2-M3) — LONG  (+100 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 67/100
- **Setup:** dislocated to -2.16sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 78.93->79.21, CL_U26 77.77->77.95
- **In:** 2026-06-15 03:15 @ 1.16   **Out:** 2026-06-15 03:30 @ 1.26 (z +0.67, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +100

### 49. Brent Aug/Sep/Oct fly — LONG  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 66/100
- **Setup:** dislocated to -1.75sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.11->83.24, CO_U26 82.3->82.38, CO_V26 81.3->81.42
- **In:** 2026-06-15 03:15 @ -0.19   **Out:** 2026-06-15 04:45 @ -0.1 (z +1.12, target)
- **Held:** 6 bars (90 min)   **MAE/MFE:** -30 / +90

### 50. WTI Jul/Aug/Sep fly — SHORT  (-10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 96/100
- **Setup:** dislocated to +2.70sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 80.56->80.9, CL_Q26 79.21->79.6, CL_U26 77.95->78.4
- **In:** 2026-06-15 03:30 @ 0.09   **Out:** 2026-06-15 06:00 @ 0.1 (z +0.08, target)
- **Held:** 10 bars (150 min)   **MAE/MFE:** -90 / +10

### 51. Brent-WTI arb (Aug) — LONG  (-10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 77/100
- **Setup:** dislocated to -3.37sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.33->83.29, CL_Q26 79.21->79.18
- **In:** 2026-06-15 03:30 @ 4.12   **Out:** 2026-06-15 03:45 @ 4.11 (z -3.71, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -10 / +0

### 52. Brent Aug/Sep (M1-M2) — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 57/100
- **Setup:** dislocated to -1.57sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.29->83.24, CO_U26 82.47->82.38
- **In:** 2026-06-15 03:45 @ 0.82   **Out:** 2026-06-15 04:45 @ 0.86 (z -0.07, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** -10 / +40

### 53. Brent Sep/Oct (M2-M3) — LONG  (+20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 56/100
- **Setup:** dislocated to -1.52sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.47->82.69, CO_V26 81.47->81.67
- **In:** 2026-06-15 03:45 @ 1.0   **Out:** 2026-06-15 05:00 @ 1.02 (z +0.00, target)
- **Held:** 5 bars (75 min)   **MAE/MFE:** -40 / +20

### 54. Brent-WTI arb (Aug) — LONG  (+10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 77/100
- **Setup:** dislocated to -3.60sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.25->83.3, CL_Q26 79.19->79.23
- **In:** 2026-06-15 04:00 @ 4.06   **Out:** 2026-06-15 04:15 @ 4.07 (z -2.53, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +10

### 55. WTI Jul/Aug (M1-M2) — SHORT  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 80/100
- **Setup:** dislocated to +1.62sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 80.59->80.79, CL_Q26 79.22->79.46
- **In:** 2026-06-15 04:30 @ 1.37   **Out:** 2026-06-15 05:45 @ 1.33 (z -0.22, target)
- **Held:** 5 bars (75 min)   **MAE/MFE:** -50 / +40

### 56. Brent-WTI arb (Aug) — LONG  (+130 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 71/100
- **Setup:** dislocated to -2.09sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.28->83.67, CL_Q26 79.22->79.48
- **In:** 2026-06-15 04:30 @ 4.06   **Out:** 2026-06-15 05:30 @ 4.19 (z +0.22, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +130

### 57. WTI Aug/Sep (M2-M3) — SHORT  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 92/100
- **Setup:** dislocated to +4.05sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 79.42->79.4, CL_U26 78.12->78.16
- **In:** 2026-06-15 05:00 @ 1.3   **Out:** 2026-06-15 05:15 @ 1.24 (z +0.00, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +60

### 58. WTI Aug/Sep (M2-M3) — SHORT  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 85/100
- **Setup:** dislocated to +2.02sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 79.48->79.46, CL_U26 78.21->78.24
- **In:** 2026-06-15 05:30 @ 1.27   **Out:** 2026-06-15 05:45 @ 1.22 (z -1.35, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +50

### 59. WTI Aug/Sep (M2-M3) — LONG  (-100 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 62/100
- **Setup:** dislocated to -1.80sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 79.6->78.55, CL_U26 78.4->77.45
- **In:** 2026-06-15 06:00 @ 1.2   **Out:** 2026-06-15 07:15 @ 1.1 (z -3.51, stop)
- **Held:** 5 bars (75 min)   **MAE/MFE:** -100 / +30

### 60. Brent Sep/Oct (M2-M3) — LONG  (-10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -2.70sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.68->82.6, CO_V26 81.72->81.65
- **In:** 2026-06-15 06:30 @ 0.96   **Out:** 2026-06-15 06:45 @ 0.95 (z -3.04, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -10 / +0

### 61. Brent Sep/Oct (M2-M3) — LONG  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -2.92sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.45->82.45, CO_V26 81.52->81.46
- **In:** 2026-06-15 07:00 @ 0.93   **Out:** 2026-06-15 07:45 @ 0.99 (z +0.00, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** -20 / +60

### 62. Brent Aug/Sep/Oct fly — SHORT  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 83/100
- **Setup:** dislocated to +1.57sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.26->83.52, CO_U26 82.45->82.75, CO_V26 81.52->81.77
- **In:** 2026-06-15 07:00 @ -0.12   **Out:** 2026-06-15 08:00 @ -0.21 (z -2.70, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +90

### 63. WTI Jul/Aug/Sep fly — SHORT  (-100 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 85/100
- **Setup:** dislocated to +1.69sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 79.85->80.31, CL_Q26 78.55->78.87, CL_U26 77.45->77.73
- **In:** 2026-06-15 07:15 @ 0.2   **Out:** 2026-06-15 08:15 @ 0.3 (z +2.89, stop)
- **Held:** 4 bars (60 min)   **MAE/MFE:** -100 / +20

### 64. Brent Aug/Sep (M1-M2) — LONG  (+70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 58/100
- **Setup:** dislocated to -1.69sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.78->83.3, CO_U26 82.0->82.45
- **In:** 2026-06-15 07:15 @ 0.78   **Out:** 2026-06-15 07:45 @ 0.85 (z +0.67, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +70

### 65. WTI Aug/Sep (M2-M3) — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 65/100
- **Setup:** dislocated to -2.02sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 78.76->78.97, CL_U26 77.61->77.78
- **In:** 2026-06-15 07:30 @ 1.15   **Out:** 2026-06-15 08:45 @ 1.19 (z +0.00, target)
- **Held:** 5 bars (75 min)   **MAE/MFE:** -10 / +40

### 66. WTI Jul/Aug (M1-M2) — SHORT  (+80 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 88/100
- **Setup:** dislocated to +2.22sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 80.49->80.36, CL_Q26 79.04->78.99
- **In:** 2026-06-15 07:45 @ 1.45   **Out:** 2026-06-15 10:15 @ 1.37 (z -0.18, target)
- **Held:** 10 bars (150 min)   **MAE/MFE:** -10 / +90

### 67. Brent Aug/Sep (M1-M2) — LONG  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 69/100
- **Setup:** dislocated to -2.47sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.52->83.04, CO_U26 82.75->82.22
- **In:** 2026-06-15 08:00 @ 0.77   **Out:** 2026-06-15 08:15 @ 0.82 (z +0.00, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +50

### 68. Brent Sep/Oct (M2-M3) — LONG  (-70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -2.83sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.22->82.27, CO_V26 81.34->81.46
- **In:** 2026-06-15 08:15 @ 0.88   **Out:** 2026-06-15 09:00 @ 0.81 (z -2.79, stop)
- **Held:** 3 bars (45 min)   **MAE/MFE:** -70 / +50

### 69. Brent Aug/Sep/Oct fly — SHORT  (+80 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 96/100
- **Setup:** dislocated to +3.82sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.04->83.05, CO_U26 82.22->82.26, CO_V26 81.34->81.33
- **In:** 2026-06-15 08:15 @ -0.06   **Out:** 2026-06-15 08:45 @ -0.14 (z +0.00, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +80

### 70. WTI Jul/Aug/Sep fly — SHORT  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 94/100
- **Setup:** dislocated to +2.32sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 80.32->80.59, CL_Q26 78.86->79.2, CL_U26 77.71->78.08
- **In:** 2026-06-15 08:30 @ 0.31   **Out:** 2026-06-15 10:45 @ 0.27 (z -0.22, target)
- **Held:** 9 bars (135 min)   **MAE/MFE:** -120 / +80

### 71. Brent-WTI arb (Aug) — LONG  (-100 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 65/100
- **Setup:** dislocated to -1.64sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.98->82.95, CL_Q26 78.86->78.93
- **In:** 2026-06-15 08:30 @ 4.12   **Out:** 2026-06-15 09:00 @ 4.02 (z -3.57, stop)
- **Held:** 2 bars (30 min)   **MAE/MFE:** -100 / +0

### 72. WTI Aug/Sep (M2-M3) — LONG  (-10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 58/100
- **Setup:** dislocated to -1.54sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 78.93->79.13, CL_U26 77.82->78.03
- **In:** 2026-06-15 09:00 @ 1.11   **Out:** 2026-06-15 11:45 @ 1.1 (z -0.00, target)
- **Held:** 11 bars (165 min)   **MAE/MFE:** -80 / +20

### 73. Brent Aug/Sep (M1-M2) — LONG  (-10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -4.55sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.95->82.78, CO_U26 82.27->82.11
- **In:** 2026-06-15 09:00 @ 0.68   **Out:** 2026-06-15 09:15 @ 0.67 (z -4.72, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -10 / +0

### 74. Brent Sep/Oct (M2-M3) — LONG  (-30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -2.70sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.11->82.36, CO_V26 81.32->81.6
- **In:** 2026-06-15 09:15 @ 0.79   **Out:** 2026-06-15 09:30 @ 0.76 (z -2.70, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -30 / +0

### 75. Brent-WTI arb (Aug) — LONG  (-10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 77/100
- **Setup:** dislocated to -3.18sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.78->83.03, CL_Q26 78.74->79.0
- **In:** 2026-06-15 09:15 @ 4.04   **Out:** 2026-06-15 12:00 @ 4.03 (z +0.06, target)
- **Held:** 11 bars (165 min)   **MAE/MFE:** -120 / +60

### 76. Brent Aug/Sep (M1-M2) — LONG  (+10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -5.06sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.02->82.92, CO_U26 82.36->82.25
- **In:** 2026-06-15 09:30 @ 0.66   **Out:** 2026-06-15 09:45 @ 0.67 (z -4.55, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +10

### 77. Brent Aug/Sep/Oct fly — SHORT  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 83/100
- **Setup:** dislocated to +1.57sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.02->82.86, CO_U26 82.36->82.22, CO_V26 81.6->81.43
- **In:** 2026-06-15 09:30 @ -0.1   **Out:** 2026-06-15 10:00 @ -0.15 (z -1.35, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +50

### 78. Brent Sep/Oct (M2-M3) — LONG  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 61/100
- **Setup:** dislocated to -1.89sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.25->82.44, CO_V26 81.46->81.56
- **In:** 2026-06-15 09:45 @ 0.79   **Out:** 2026-06-15 10:45 @ 0.88 (z +0.00, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +90

### 79. Brent Aug/Sep (M1-M2) — LONG  (+120 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -4.18sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.86->83.2, CO_U26 82.22->82.44
- **In:** 2026-06-15 10:00 @ 0.64   **Out:** 2026-06-15 10:45 @ 0.76 (z -0.06, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +120

### 80. WTI Jul/Aug (M1-M2) — LONG  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 60/100
- **Setup:** dislocated to -1.69sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.2->80.46, CL_Q26 78.91->79.08
- **In:** 2026-06-15 11:00 @ 1.29   **Out:** 2026-06-15 13:00 @ 1.38 (z +0.61, target)
- **Held:** 8 bars (120 min)   **MAE/MFE:** -80 / +90

### 81. WTI Jul/Aug/Sep fly — LONG  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 66/100
- **Setup:** dislocated to -1.80sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.16->80.46, CL_Q26 78.89->79.08, CL_U26 77.82->77.95
- **In:** 2026-06-15 11:15 @ 0.2   **Out:** 2026-06-15 13:00 @ 0.25 (z +0.28, target)
- **Held:** 7 bars (105 min)   **MAE/MFE:** -80 / +50

### 82. WTI Aug/Sep (M2-M3) — SHORT  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 83/100
- **Setup:** dislocated to +1.85sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 79.03->78.6, CL_U26 77.88->77.49
- **In:** 2026-06-15 12:45 @ 1.15   **Out:** 2026-06-15 14:30 @ 1.11 (z -0.40, target)
- **Held:** 7 bars (105 min)   **MAE/MFE:** -60 / +40

### 83. Brent Aug/Sep (M1-M2) — SHORT  (-10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 89/100
- **Setup:** dislocated to +2.47sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.12->83.16, CO_U26 82.39->82.42
- **In:** 2026-06-15 12:45 @ 0.73   **Out:** 2026-06-15 13:00 @ 0.74 (z +2.92, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -10 / +0

### 84. Brent Sep/Oct (M2-M3) — SHORT  (-10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 90/100
- **Setup:** dislocated to +2.70sigma (rich) -> fade
- **Legs (entry->exit):** CO_U26 82.39->82.42, CO_V26 81.55->81.57
- **In:** 2026-06-15 12:45 @ 0.84   **Out:** 2026-06-15 13:00 @ 0.85 (z +3.37, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -10 / +0

### 85. Brent Sep/Oct (M2-M3) — SHORT  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 90/100
- **Setup:** dislocated to +3.15sigma (rich) -> fade
- **Legs (entry->exit):** CO_U26 82.47->81.81, CO_V26 81.6->80.99
- **In:** 2026-06-15 13:15 @ 0.87   **Out:** 2026-06-15 14:15 @ 0.82 (z -0.13, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +50

### 86. Brent Aug/Sep/Oct fly — SHORT  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 89/100
- **Setup:** dislocated to +2.02sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 82.86->82.51, CO_U26 82.12->81.81, CO_V26 81.29->80.99
- **In:** 2026-06-15 14:00 @ -0.09   **Out:** 2026-06-15 14:15 @ -0.12 (z +0.00, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +30

### 87. Brent Aug/Sep/Oct fly — LONG  (+80 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 76/100
- **Setup:** dislocated to -2.70sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.6->83.14, CO_U26 81.87->82.28, CO_V26 81.0->81.36
- **In:** 2026-06-15 14:30 @ -0.14   **Out:** 2026-06-15 14:45 @ -0.06 (z +4.05, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +80

### 88. Brent Aug/Sep (M1-M2) — SHORT  (-50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 90/100
- **Setup:** dislocated to +3.91sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.14->83.22, CO_U26 82.28->82.31
- **In:** 2026-06-15 14:45 @ 0.86   **Out:** 2026-06-15 15:00 @ 0.91 (z +4.05, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -50 / +0

### 89. Brent Sep/Oct (M2-M3) — SHORT  (-40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 85/100
- **Setup:** dislocated to +2.14sigma (rich) -> fade
- **Legs (entry->exit):** CO_U26 82.28->82.27, CO_V26 81.36->81.31
- **In:** 2026-06-15 14:45 @ 0.92   **Out:** 2026-06-15 15:15 @ 0.96 (z +2.59, stop)
- **Held:** 2 bars (30 min)   **MAE/MFE:** -40 / +0

### 90. WTI Aug/Sep (M2-M3) — SHORT  (+20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 84/100
- **Setup:** dislocated to +1.93sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 79.23->79.18, CL_U26 77.99->77.96
- **In:** 2026-06-15 15:00 @ 1.24   **Out:** 2026-06-15 17:15 @ 1.22 (z +0.08, target)
- **Held:** 9 bars (135 min)   **MAE/MFE:** -30 / +40

### 91. Brent Aug/Sep/Oct fly — SHORT  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 96/100
- **Setup:** dislocated to +6.07sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.22->83.17, CO_U26 82.31->82.27, CO_V26 81.37->81.31
- **In:** 2026-06-15 15:00 @ -0.03   **Out:** 2026-06-15 15:15 @ -0.06 (z +4.05, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +30

### 92. Brent Aug/Sep (M1-M2) — SHORT  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 90/100
- **Setup:** dislocated to +3.18sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.17->83.08, CO_U26 82.27->82.24
- **In:** 2026-06-15 15:15 @ 0.9   **Out:** 2026-06-15 17:30 @ 0.84 (z -0.25, target)
- **Held:** 9 bars (135 min)   **MAE/MFE:** -60 / +100

### 93. Brent Sep/Oct (M2-M3) — SHORT  (-40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 79/100
- **Setup:** dislocated to +1.77sigma (rich) -> fade
- **Legs (entry->exit):** CO_U26 82.17->82.54, CO_V26 81.21->81.54
- **In:** 2026-06-15 15:30 @ 0.96   **Out:** 2026-06-15 19:00 @ 1.0 (z +0.00, target)
- **Held:** 14 bars (210 min)   **MAE/MFE:** -90 / +70

### 94. Brent-WTI arb (Aug) — LONG  (+140 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 64/100
- **Setup:** dislocated to -1.53sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.77->83.09, CL_Q26 78.9->79.08
- **In:** 2026-06-15 15:45 @ 3.87   **Out:** 2026-06-15 16:30 @ 4.01 (z +0.42, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +140

### 95. Brent Aug/Sep/Oct fly — SHORT  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 85/100
- **Setup:** dislocated to +1.69sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 82.73->83.2, CO_U26 81.87->82.27, CO_V26 80.95->81.23
- **In:** 2026-06-15 16:00 @ -0.06   **Out:** 2026-06-15 16:45 @ -0.11 (z -0.40, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +50

### 96. Brent Aug/Sep/Oct fly — LONG  (+100 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 75/100
- **Setup:** dislocated to -2.43sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.08->83.07, CO_U26 82.24->82.18, CO_V26 81.22->81.21
- **In:** 2026-06-15 17:30 @ -0.18   **Out:** 2026-06-15 18:00 @ -0.08 (z +0.27, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +100

### 97. WTI Aug/Sep (M2-M3) — SHORT  (+70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 85/100
- **Setup:** dislocated to +2.02sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 79.55->79.59, CL_U26 78.23->78.34
- **In:** 2026-06-15 18:15 @ 1.32   **Out:** 2026-06-15 18:45 @ 1.25 (z +0.00, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +70

### 98. WTI Jul/Aug/Sep fly — LONG  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 73/100
- **Setup:** dislocated to -2.25sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.9->81.43, CL_Q26 79.55->80.05, CL_U26 78.23->78.73
- **In:** 2026-06-15 18:15 @ 0.03   **Out:** 2026-06-15 20:00 @ 0.06 (z -0.00, target)
- **Held:** 7 bars (105 min)   **MAE/MFE:** -30 / +30

### 99. Brent-WTI arb (Aug) — LONG  (-50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 77/100
- **Setup:** dislocated to -3.57sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.27->83.48, CL_Q26 79.55->79.81
- **In:** 2026-06-15 18:15 @ 3.72   **Out:** 2026-06-15 20:45 @ 3.67 (z -0.67, session_end)
- **Held:** 10 bars (150 min)   **MAE/MFE:** -80 / +50

### 100. WTI Jul/Aug (M1-M2) — LONG  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 67/100
- **Setup:** dislocated to -2.16sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.93->81.09, CL_Q26 79.67->79.74
- **In:** 2026-06-15 19:00 @ 1.26   **Out:** 2026-06-15 19:15 @ 1.35 (z +0.34, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +90

### 101. Brent Aug/Sep/Oct fly — LONG  (+110 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 76/100
- **Setup:** dislocated to -3.82sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.59->83.71, CO_U26 82.74->82.8, CO_V26 81.71->81.82
- **In:** 2026-06-15 19:45 @ -0.18   **Out:** 2026-06-15 20:00 @ -0.07 (z +1.12, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +110

### 102. Brent Sep/Oct (M2-M3) — LONG  (+20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 57/100
- **Setup:** dislocated to -1.57sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.59->82.64, CO_V26 81.62->81.65
- **In:** 2026-06-15 20:45 @ 0.97   **Out:** 2026-06-15 21:45 @ 0.99 (z -0.00, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +20

### 103. Brent Aug/Sep (M1-M2) — SHORT  (-30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 90/100
- **Setup:** dislocated to +4.05sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.6->83.63, CO_U26 82.64->82.64
- **In:** 2026-06-15 21:15 @ 0.96   **Out:** 2026-06-15 21:30 @ 0.99 (z +6.07, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -30 / +0

### 104. Brent Aug/Sep/Oct fly — SHORT  (-30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 92/100
- **Setup:** dislocated to +2.19sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.6->83.63, CO_U26 82.64->82.64, CO_V26 81.65->81.65
- **In:** 2026-06-15 21:15 @ -0.03   **Out:** 2026-06-15 21:30 @ 0.0 (z +3.04, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -30 / +0

### 105. Brent Aug/Sep (M1-M2) — LONG  (+190 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -8.09sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.36->83.57, CO_U26 82.64->82.66
- **In:** 2026-06-15 21:45 @ 0.72   **Out:** 2026-06-16 00:00 @ 0.91 (z +0.22, target)
- **Held:** 1 bars (135 min)   **MAE/MFE:** +0 / +190

### 106. Brent Aug/Sep/Oct fly — LONG  (+170 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 76/100
- **Setup:** dislocated to -6.07sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.36->83.63, CO_U26 82.64->82.74, CO_V26 81.65->81.75
- **In:** 2026-06-15 21:45 @ -0.27   **Out:** 2026-06-16 00:45 @ -0.1 (z +0.00, target)
- **Held:** 4 bars (180 min)   **MAE/MFE:** +0 / +170

### 107. WTI Aug/Sep (M2-M3) — SHORT  (+160 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 92/100
- **Setup:** dislocated to +2.79sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 79.78->79.94, CL_U26 78.35->78.67
- **In:** 2026-06-15 22:00 @ 1.43   **Out:** 2026-06-15 22:15 @ 1.27 (z -0.29, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +160

### 108. WTI Jul/Aug/Sep fly — LONG  (+180 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 76/100
- **Setup:** dislocated to -3.91sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 81.12->81.3, CL_Q26 79.78->79.94, CL_U26 78.35->78.67
- **In:** 2026-06-15 22:00 @ -0.09   **Out:** 2026-06-15 22:15 @ 0.09 (z +0.94, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +180

### 109. WTI Jul/Aug (M1-M2) — SHORT  (-30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 85/100
- **Setup:** dislocated to +2.02sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 81.41->81.42, CL_Q26 80.03->80.01
- **In:** 2026-06-15 23:00 @ 1.38   **Out:** 2026-06-15 23:15 @ 1.41 (z +4.05, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -30 / +0

### 110. WTI Aug/Sep (M2-M3) — SHORT  (+80 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 80/100
- **Setup:** dislocated to +1.64sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 80.03->80.14, CL_U26 78.63->78.82
- **In:** 2026-06-15 23:00 @ 1.4   **Out:** 2026-06-15 23:45 @ 1.32 (z -0.11, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +80

### 111. WTI Jul/Aug (M1-M2) — SHORT  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 79/100
- **Setup:** dislocated to +1.57sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 81.51->81.29, CL_Q26 80.12->79.94
- **In:** 2026-06-15 23:30 @ 1.39   **Out:** 2026-06-16 00:00 @ 1.35 (z -0.67, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +40

### 112. WTI Jul/Aug/Sep fly — LONG  (+70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 65/100
- **Setup:** dislocated to -1.69sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 81.29->81.35, CL_Q26 79.94->79.97, CL_U26 78.59->78.66
- **In:** 2026-06-16 00:00 @ 0.0   **Out:** 2026-06-16 00:15 @ 0.07 (z +0.67, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +70

### 113. Brent Sep/Oct (M2-M3) — SHORT  (+10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 90/100
- **Setup:** dislocated to +6.07sigma (rich) -> fade
- **Legs (entry->exit):** CO_U26 82.66->82.81, CO_V26 81.62->81.78
- **In:** 2026-06-16 00:00 @ 1.04   **Out:** 2026-06-16 00:15 @ 1.03 (z +4.72, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +10

### 114. Brent Aug/Sep (M1-M2) — LONG  (+80 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -3.60sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.63->83.65, CO_U26 82.81->82.75
- **In:** 2026-06-16 00:15 @ 0.82   **Out:** 2026-06-16 00:30 @ 0.9 (z +0.00, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +80

### 115. Brent Sep/Oct (M2-M3) — SHORT  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 90/100
- **Setup:** dislocated to +3.04sigma (rich) -> fade
- **Legs (entry->exit):** CO_U26 82.75->82.74, CO_V26 81.71->81.75
- **In:** 2026-06-16 00:30 @ 1.04   **Out:** 2026-06-16 00:45 @ 0.99 (z -0.00, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +50

### 116. WTI Aug/Sep (M2-M3) — SHORT  (+120 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 89/100
- **Setup:** dislocated to +2.29sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 79.84->79.68, CL_U26 78.42->78.38
- **In:** 2026-06-16 01:00 @ 1.42   **Out:** 2026-06-16 01:15 @ 1.3 (z -0.67, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +120

### 117. Brent Aug/Sep (M1-M2) — SHORT  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 86/100
- **Setup:** dislocated to +2.25sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.54->83.35, CO_U26 82.59->82.46
- **In:** 2026-06-16 01:00 @ 0.95   **Out:** 2026-06-16 01:15 @ 0.89 (z -0.45, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +60

### 118. Brent Sep/Oct (M2-M3) — LONG  (-40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 60/100
- **Setup:** dislocated to -1.80sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.41->82.39, CO_V26 81.46->81.48
- **In:** 2026-06-16 01:30 @ 0.95   **Out:** 2026-06-16 01:45 @ 0.91 (z -3.60, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -40 / +0

### 119. WTI Aug/Sep (M2-M3) — LONG  (+170 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -5.13sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 79.59->79.37, CL_U26 78.45->78.06
- **In:** 2026-06-16 01:45 @ 1.14   **Out:** 2026-06-16 03:00 @ 1.31 (z -0.00, target)
- **Held:** 5 bars (75 min)   **MAE/MFE:** +0 / +170

### 120. WTI Jul/Aug/Sep fly — SHORT  (+170 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 96/100
- **Setup:** dislocated to +3.47sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 80.92->80.89, CL_Q26 79.59->79.6, CL_U26 78.45->78.33
- **In:** 2026-06-16 01:45 @ 0.19   **Out:** 2026-06-16 02:30 @ 0.02 (z -0.22, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +170

### 121. Brent Aug/Sep (M1-M2) — LONG  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 57/100
- **Setup:** dislocated to -1.57sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.25->83.22, CO_U26 82.39->82.33
- **In:** 2026-06-16 01:45 @ 0.86   **Out:** 2026-06-16 02:30 @ 0.89 (z +0.00, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +30

### 122. Brent Sep/Oct (M2-M3) — LONG  (-120 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -2.70sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.35->80.56, CO_V26 81.44->79.77
- **In:** 2026-06-16 02:00 @ 0.91   **Out:** 2026-06-16 08:00 @ 0.79 (z -3.04, stop)
- **Held:** 24 bars (360 min)   **MAE/MFE:** -120 / +40

### 123. Brent-WTI arb (Aug) — LONG  (-40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 77/100
- **Setup:** dislocated to -6.07sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.22->83.0, CL_Q26 79.6->79.42
- **In:** 2026-06-16 02:30 @ 3.62   **Out:** 2026-06-16 02:45 @ 3.58 (z -11.47, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -40 / +0

### 124. Brent-WTI arb (Aug) — LONG  (-30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 77/100
- **Setup:** dislocated to -6.41sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.94->82.93, CL_Q26 79.37->79.39
- **In:** 2026-06-16 03:00 @ 3.57   **Out:** 2026-06-16 03:15 @ 3.54 (z -4.05, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -30 / +0

### 125. WTI Aug/Sep (M2-M3) — LONG  (+80 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -2.56sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 79.33->79.32, CL_U26 78.12->78.03
- **In:** 2026-06-16 03:30 @ 1.21   **Out:** 2026-06-16 04:45 @ 1.29 (z +0.54, target)
- **Held:** 5 bars (75 min)   **MAE/MFE:** +0 / +80

### 126. Brent-WTI arb (Aug) — LONG  (-20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 76/100
- **Setup:** dislocated to -2.43sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.9->82.94, CL_Q26 79.33->79.39
- **In:** 2026-06-16 03:30 @ 3.57   **Out:** 2026-06-16 03:45 @ 3.55 (z -2.70, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -20 / +0

### 127. Brent-WTI arb (Aug) — LONG  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 64/100
- **Setup:** dislocated to -1.54sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.97->82.8, CL_Q26 79.4->79.2
- **In:** 2026-06-16 04:00 @ 3.57   **Out:** 2026-06-16 05:45 @ 3.6 (z +0.79, target)
- **Held:** 7 bars (105 min)   **MAE/MFE:** -70 / +30

### 128. Brent Aug/Sep/Oct fly — LONG  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 66/100
- **Setup:** dislocated to -1.80sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.93->82.93, CO_U26 82.11->82.09, CO_V26 81.19->81.2
- **In:** 2026-06-16 04:15 @ -0.1   **Out:** 2026-06-16 04:30 @ -0.05 (z +0.67, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +50

### 129. WTI Jul/Aug (M1-M2) — LONG  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -4.72sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.58->80.6, CL_Q26 79.32->79.29
- **In:** 2026-06-16 04:45 @ 1.26   **Out:** 2026-06-16 05:00 @ 1.31 (z +2.02, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +50

### 130. Brent Aug/Sep (M1-M2) — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 58/100
- **Setup:** dislocated to -1.69sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.82->82.75, CO_U26 82.01->81.9
- **In:** 2026-06-16 04:45 @ 0.81   **Out:** 2026-06-16 06:30 @ 0.85 (z +0.34, target)
- **Held:** 7 bars (105 min)   **MAE/MFE:** +0 / +40

### 131. Brent Aug/Sep/Oct fly — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 69/100
- **Setup:** dislocated to -2.02sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.82->82.82, CO_U26 82.01->81.98, CO_V26 81.11->81.09
- **In:** 2026-06-16 04:45 @ -0.09   **Out:** 2026-06-16 05:00 @ -0.05 (z +0.34, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +40

### 132. WTI Jul/Aug (M1-M2) — LONG  (-10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 65/100
- **Setup:** dislocated to -2.02sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.4->80.46, CL_Q26 79.14->79.21
- **In:** 2026-06-16 05:15 @ 1.26   **Out:** 2026-06-16 05:30 @ 1.25 (z -2.70, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -10 / +0

### 133. WTI Aug/Sep (M2-M3) — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 58/100
- **Setup:** dislocated to -1.52sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 79.2->79.22, CL_U26 77.98->77.96
- **In:** 2026-06-16 05:45 @ 1.22   **Out:** 2026-06-16 06:30 @ 1.26 (z +0.00, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** -20 / +40

### 134. WTI Jul/Aug (M1-M2) — SHORT  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 92/100
- **Setup:** dislocated to +2.70sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 80.55->80.17, CL_Q26 79.22->78.88
- **In:** 2026-06-16 06:30 @ 1.33   **Out:** 2026-06-16 07:00 @ 1.29 (z +0.00, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +40

### 135. WTI Aug/Sep (M2-M3) — LONG  (-100 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 67/100
- **Setup:** dislocated to -2.16sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 78.69->78.42, CL_U26 77.52->77.35
- **In:** 2026-06-16 07:15 @ 1.17   **Out:** 2026-06-16 07:30 @ 1.07 (z -4.86, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -100 / +0

### 136. Brent Aug/Sep (M1-M2) — LONG  (-50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 60/100
- **Setup:** dislocated to -1.80sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.27->81.29, CO_U26 81.49->80.56
- **In:** 2026-06-16 07:15 @ 0.78   **Out:** 2026-06-16 08:00 @ 0.73 (z -4.05, stop)
- **Held:** 3 bars (45 min)   **MAE/MFE:** -50 / +10

### 137. WTI Jul/Aug (M1-M2) — LONG  (-20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -4.05sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 79.65->79.36, CL_Q26 78.42->78.15
- **In:** 2026-06-16 07:30 @ 1.23   **Out:** 2026-06-16 07:45 @ 1.21 (z -2.53, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -20 / +0

### 138. Brent-WTI arb (Aug) — SHORT  (-20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 97/100
- **Setup:** dislocated to +4.18sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 82.12->81.87, CL_Q26 78.42->78.15
- **In:** 2026-06-16 07:30 @ 3.7   **Out:** 2026-06-16 07:45 @ 3.72 (z +4.59, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -20 / +0

### 139. WTI Aug/Sep (M2-M3) — LONG  (-110 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -2.99sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 78.15->77.54, CL_U26 77.07->76.57
- **In:** 2026-06-16 07:45 @ 1.08   **Out:** 2026-06-16 08:00 @ 0.97 (z -4.91, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -110 / +0

### 140. WTI Jul/Aug (M1-M2) — LONG  (+10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -3.04sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 78.73->78.63, CL_Q26 77.54->77.43
- **In:** 2026-06-16 08:00 @ 1.19   **Out:** 2026-06-16 10:15 @ 1.2 (z +0.10, target)
- **Held:** 9 bars (135 min)   **MAE/MFE:** -50 / +20

### 141. WTI Jul/Aug/Sep fly — SHORT  (+70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 89/100
- **Setup:** dislocated to +2.02sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 78.73->78.91, CL_Q26 77.54->77.77, CL_U26 76.57->76.78
- **In:** 2026-06-16 08:00 @ 0.22   **Out:** 2026-06-16 09:45 @ 0.15 (z +0.00, target)
- **Held:** 7 bars (105 min)   **MAE/MFE:** +0 / +70

### 142. Brent-WTI arb (Aug) — SHORT  (-20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 97/100
- **Setup:** dislocated to +4.50sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 81.29->81.21, CL_Q26 77.54->77.44
- **In:** 2026-06-16 08:00 @ 3.75   **Out:** 2026-06-16 08:15 @ 3.77 (z +4.05, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -20 / +0

### 143. WTI Aug/Sep (M2-M3) — LONG  (-120 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -2.70sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 77.44->77.26, CL_U26 76.43->76.37
- **In:** 2026-06-16 08:15 @ 1.01   **Out:** 2026-06-16 11:00 @ 0.89 (z -2.70, stop)
- **Held:** 11 bars (165 min)   **MAE/MFE:** -120 / +0

### 144. Brent Aug/Sep (M1-M2) — LONG  (-90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 67/100
- **Setup:** dislocated to -2.29sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 81.21->80.92, CO_U26 80.48->80.28
- **In:** 2026-06-16 08:15 @ 0.73   **Out:** 2026-06-16 10:30 @ 0.64 (z -3.10, stop)
- **Held:** 9 bars (135 min)   **MAE/MFE:** -90 / +40

### 145. Brent Sep/Oct (M2-M3) — LONG  (+20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 58/100
- **Setup:** dislocated to -1.69sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 80.48->80.71, CO_V26 79.66->79.87
- **In:** 2026-06-16 08:15 @ 0.82   **Out:** 2026-06-16 09:15 @ 0.84 (z +0.00, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** -10 / +20

### 146. Brent Aug/Sep/Oct fly — LONG  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 63/100
- **Setup:** dislocated to -1.57sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 81.23->81.14, CO_U26 80.48->80.37, CO_V26 79.64->79.56
- **In:** 2026-06-16 08:30 @ -0.09   **Out:** 2026-06-16 08:45 @ -0.04 (z +0.22, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +50

### 147. Brent-WTI arb (Aug) — SHORT  (+100 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 97/100
- **Setup:** dislocated to +2.77sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 81.23->81.21, CL_Q26 77.48->77.56
- **In:** 2026-06-16 08:30 @ 3.75   **Out:** 2026-06-16 10:00 @ 3.65 (z -0.74, target)
- **Held:** 6 bars (90 min)   **MAE/MFE:** -40 / +100

### 148. Brent Aug/Sep/Oct fly — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 65/100
- **Setup:** dislocated to -1.69sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 81.46->81.59, CO_U26 80.73->80.83, CO_V26 79.9->80.01
- **In:** 2026-06-16 09:00 @ -0.1   **Out:** 2026-06-16 09:30 @ -0.06 (z +0.00, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +40

### 149. WTI Jul/Aug/Sep fly — SHORT  (+70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 86/100
- **Setup:** dislocated to +1.75sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 78.74->78.3, CL_Q26 77.56->77.26, CL_U26 76.6->76.37
- **In:** 2026-06-16 10:00 @ 0.22   **Out:** 2026-06-16 11:00 @ 0.15 (z -0.54, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** -30 / +70

### 150. Brent Sep/Oct (M2-M3) — LONG  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 69/100
- **Setup:** dislocated to -2.47sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 80.54->80.41, CO_V26 79.77->79.59
- **In:** 2026-06-16 10:00 @ 0.77   **Out:** 2026-06-16 10:15 @ 0.82 (z -0.00, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +50

### 151. Brent Aug/Sep/Oct fly — LONG  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 67/100
- **Setup:** dislocated to -1.89sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 81.09->81.03, CO_U26 80.41->80.37, CO_V26 79.59->79.63
- **In:** 2026-06-16 10:15 @ -0.14   **Out:** 2026-06-16 10:45 @ -0.08 (z -0.00, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +60

### 152. Brent Sep/Oct (M2-M3) — LONG  (+0 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -2.70sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 80.28->80.37, CO_V26 79.54->79.63
- **In:** 2026-06-16 10:30 @ 0.74   **Out:** 2026-06-16 10:45 @ 0.74 (z -2.70, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +0

### 153. Brent Aug/Sep (M1-M2) — LONG  (-210 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 56/100
- **Setup:** dislocated to -1.54sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 81.03->79.94, CO_U26 80.37->79.49
- **In:** 2026-06-16 10:45 @ 0.66   **Out:** 2026-06-16 14:30 @ 0.45 (z -2.83, stop)
- **Held:** 15 bars (225 min)   **MAE/MFE:** -210 / +0

### 154. WTI Jul/Aug (M1-M2) — LONG  (-120 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -3.15sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 78.3->77.12, CL_Q26 77.26->76.2
- **In:** 2026-06-16 11:00 @ 1.04   **Out:** 2026-06-16 12:30 @ 0.92 (z -4.83, stop)
- **Held:** 6 bars (90 min)   **MAE/MFE:** -120 / +90

### 155. Brent Sep/Oct (M2-M3) — LONG  (+10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -3.20sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 80.39->80.24, CO_V26 79.67->79.51
- **In:** 2026-06-16 11:00 @ 0.72   **Out:** 2026-06-16 11:15 @ 0.73 (z -2.70, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +10

### 156. WTI Aug/Sep (M2-M3) — LONG  (-170 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 67/100
- **Setup:** dislocated to -2.16sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 77.18->75.65, CL_U26 76.27->74.91
- **In:** 2026-06-16 11:15 @ 0.91   **Out:** 2026-06-16 18:30 @ 0.74 (z +0.67, target)
- **Held:** 29 bars (435 min)   **MAE/MFE:** -290 / +30

### 157. Brent Sep/Oct (M2-M3) — LONG  (-110 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 61/100
- **Setup:** dislocated to -1.91sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 80.25->79.65, CO_V26 79.53->79.04
- **In:** 2026-06-16 11:30 @ 0.72   **Out:** 2026-06-16 12:00 @ 0.61 (z -2.62, stop)
- **Held:** 2 bars (30 min)   **MAE/MFE:** -110 / +10

### 158. Brent-WTI arb (Aug) — LONG  (-10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 77/100
- **Setup:** dislocated to -4.99sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 80.9->80.82, CL_Q26 77.35->77.28
- **In:** 2026-06-16 11:30 @ 3.55   **Out:** 2026-06-16 11:45 @ 3.54 (z -4.38, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -10 / +0

### 159. Brent Aug/Sep/Oct fly — SHORT  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 89/100
- **Setup:** dislocated to +2.02sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 80.21->80.48, CO_U26 79.65->79.92, CO_V26 79.04->79.27
- **In:** 2026-06-16 12:00 @ -0.05   **Out:** 2026-06-16 13:00 @ -0.09 (z -0.67, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +40

### 160. Brent-WTI arb (Aug) — LONG  (+240 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 77/100
- **Setup:** dislocated to -4.22sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 80.21->80.13, CL_Q26 76.73->76.41
- **In:** 2026-06-16 12:00 @ 3.48   **Out:** 2026-06-16 12:45 @ 3.72 (z +0.06, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +240

### 161. Brent Sep/Oct (M2-M3) — LONG  (+10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 58/100
- **Setup:** dislocated to -1.69sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 79.52->80.16, CO_V26 78.89->79.52
- **In:** 2026-06-16 12:15 @ 0.63   **Out:** 2026-06-16 14:00 @ 0.64 (z -0.07, target)
- **Held:** 7 bars (105 min)   **MAE/MFE:** -40 / +20

### 162. WTI Jul/Aug/Sep fly — LONG  (+20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 76/100
- **Setup:** dislocated to -2.70sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 77.12->76.99, CL_Q26 76.2->76.14, CL_U26 75.36->75.39
- **In:** 2026-06-16 12:30 @ 0.08   **Out:** 2026-06-16 15:15 @ 0.1 (z +0.11, target)
- **Held:** 11 bars (165 min)   **MAE/MFE:** -40 / +30

### 163. WTI Jul/Aug (M1-M2) — LONG  (+10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -4.72sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 77.33->77.62, CL_Q26 76.41->76.69
- **In:** 2026-06-16 12:45 @ 0.92   **Out:** 2026-06-16 13:00 @ 0.93 (z -3.29, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +10

### 164. WTI Jul/Aug (M1-M2) — LONG  (-110 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -2.70sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 77.61->75.86, CL_Q26 76.7->75.06
- **In:** 2026-06-16 13:15 @ 0.91   **Out:** 2026-06-16 17:45 @ 0.8 (z +0.22, target)
- **Held:** 18 bars (270 min)   **MAE/MFE:** -150 / +10

### 165. Brent Aug/Sep/Oct fly — SHORT  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 85/100
- **Setup:** dislocated to +1.69sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 80.57->80.69, CO_U26 80.03->80.16, CO_V26 79.44->79.52
- **In:** 2026-06-16 13:45 @ -0.05   **Out:** 2026-06-16 14:00 @ -0.11 (z -2.36, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +60

### 166. Brent Aug/Sep/Oct fly — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 74/100
- **Setup:** dislocated to -2.36sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 79.94->79.85, CO_U26 79.49->79.36, CO_V26 78.93->78.8
- **In:** 2026-06-16 14:30 @ -0.11   **Out:** 2026-06-16 15:15 @ -0.07 (z +0.00, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +40

### 167. Brent Aug/Sep (M1-M2) — LONG  (-260 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 58/100
- **Setup:** dislocated to -1.69sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 80.02->78.89, CO_U26 79.52->78.65
- **In:** 2026-06-16 14:45 @ 0.5   **Out:** 2026-06-16 17:00 @ 0.24 (z -3.31, stop)
- **Held:** 9 bars (135 min)   **MAE/MFE:** -260 / +0

### 168. WTI Jul/Aug/Sep fly — LONG  (+100 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 76/100
- **Setup:** dislocated to -3.15sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 75.97->75.86, CL_Q26 75.18->75.04, CL_U26 74.41->74.34
- **In:** 2026-06-16 16:00 @ 0.02   **Out:** 2026-06-16 16:15 @ 0.12 (z +1.35, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +100

### 169. Brent Aug/Sep/Oct fly — LONG  (-50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 76/100
- **Setup:** dislocated to -2.47sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 78.91->78.65, CO_U26 78.5->78.3, CO_V26 77.95->77.76
- **In:** 2026-06-16 16:00 @ -0.14   **Out:** 2026-06-16 16:30 @ -0.19 (z -3.37, stop)
- **Held:** 2 bars (30 min)   **MAE/MFE:** -50 / +10

### 170. Brent Sep/Oct (M2-M3) — LONG  (-40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 67/100
- **Setup:** dislocated to -2.29sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 78.33->78.65, CO_V26 77.83->78.19
- **In:** 2026-06-16 16:15 @ 0.5   **Out:** 2026-06-16 17:00 @ 0.46 (z -2.83, stop)
- **Held:** 3 bars (45 min)   **MAE/MFE:** -40 / +40

### 171. Brent Aug/Sep/Oct fly — LONG  (-70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 69/100
- **Setup:** dislocated to -2.02sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 78.74->78.89, CO_U26 78.37->78.65, CO_V26 77.85->78.19
- **In:** 2026-06-16 16:45 @ -0.15   **Out:** 2026-06-16 17:00 @ -0.22 (z -4.38, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -70 / +0

### 172. Brent-WTI arb (Aug) — LONG  (+150 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 77/100
- **Setup:** dislocated to -2.47sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 78.89->78.83, CL_Q26 75.27->75.06
- **In:** 2026-06-16 17:00 @ 3.62   **Out:** 2026-06-16 17:45 @ 3.77 (z +0.90, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +150

### 173. WTI Jul/Aug/Sep fly — SHORT  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 89/100
- **Setup:** dislocated to +2.02sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 75.79->76.05, CL_Q26 75.01->75.27, CL_U26 74.39->74.59
- **In:** 2026-06-16 17:15 @ 0.16   **Out:** 2026-06-16 18:15 @ 0.1 (z +0.10, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +60

### 174. Brent Aug/Sep (M1-M2) — LONG  (+0 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -2.92sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 78.69->78.56, CO_U26 78.48->78.35
- **In:** 2026-06-16 17:15 @ 0.21   **Out:** 2026-06-16 17:30 @ 0.21 (z -2.75, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +0

### 175. Brent Sep/Oct (M2-M3) — LONG  (+80 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 69/100
- **Setup:** dislocated to -2.43sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 78.48->78.68, CO_V26 78.01->78.13
- **In:** 2026-06-16 17:15 @ 0.47   **Out:** 2026-06-16 18:15 @ 0.55 (z +0.11, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +80

### 176. Brent Aug/Sep/Oct fly — LONG  (-20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 76/100
- **Setup:** dislocated to -3.60sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 78.69->78.56, CO_U26 78.48->78.35, CO_V26 78.01->77.86
- **In:** 2026-06-16 17:15 @ -0.26   **Out:** 2026-06-16 17:30 @ -0.28 (z -3.82, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -20 / +0

### 177. Brent Aug/Sep (M1-M2) — LONG  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 57/100
- **Setup:** dislocated to -1.57sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 78.83->79.33, CO_U26 78.54->78.98
- **In:** 2026-06-16 17:45 @ 0.29   **Out:** 2026-06-16 18:30 @ 0.35 (z -0.07, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** -30 / +60

### 178. Brent Aug/Sep/Oct fly — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 73/100
- **Setup:** dislocated to -2.25sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 78.83->79.48, CO_U26 78.54->79.13, CO_V26 78.03->78.6
- **In:** 2026-06-16 17:45 @ -0.22   **Out:** 2026-06-16 20:00 @ -0.18 (z +1.35, target)
- **Held:** 9 bars (135 min)   **MAE/MFE:** -100 / +40

### 179. Brent-WTI arb (Aug) — LONG  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 70/100
- **Setup:** dislocated to -2.02sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 79.51->79.5, CL_Q26 75.93->75.83
- **In:** 2026-06-16 19:00 @ 3.58   **Out:** 2026-06-16 20:45 @ 3.67 (z +0.56, target)
- **Held:** 7 bars (105 min)   **MAE/MFE:** -60 / +90

### 180. WTI Jul/Aug (M1-M2) — LONG  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 62/100
- **Setup:** dislocated to -1.80sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 77.06->76.68, CL_Q26 76.31->75.9
- **In:** 2026-06-16 19:15 @ 0.75   **Out:** 2026-06-16 20:30 @ 0.78 (z +0.00, target)
- **Held:** 5 bars (75 min)   **MAE/MFE:** -10 / +30

### 181. WTI Jul/Aug/Sep fly — LONG  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 65/100
- **Setup:** dislocated to -1.69sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 77.06->76.62, CL_Q26 76.31->75.83, CL_U26 75.55->75.09
- **In:** 2026-06-16 19:15 @ -0.01   **Out:** 2026-06-16 20:45 @ 0.05 (z -0.00, target)
- **Held:** 6 bars (90 min)   **MAE/MFE:** -10 / +60

### 182. Brent Sep/Oct (M2-M3) — SHORT  (+100 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 78/100
- **Setup:** dislocated to +1.64sigma (rich) -> fade
- **Legs (entry->exit):** CO_U26 79.6->79.13, CO_V26 78.97->78.6
- **In:** 2026-06-16 19:15 @ 0.63   **Out:** 2026-06-16 20:00 @ 0.53 (z -0.07, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +100

### 183. Brent Aug/Sep/Oct fly — SHORT  (+130 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 87/100
- **Setup:** dislocated to +1.89sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 79.45->79.5, CO_U26 79.05->79.22, CO_V26 78.47->78.63
- **In:** 2026-06-16 20:30 @ -0.18   **Out:** 2026-06-16 20:45 @ -0.31 (z -1.48, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +130

### 184. Brent Aug/Sep (M1-M2) — LONG  (+180 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -5.40sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 79.26->79.45, CO_U26 79.12->79.13
- **In:** 2026-06-16 21:15 @ 0.14   **Out:** 2026-06-16 21:30 @ 0.32 (z +0.22, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +180

### 185. Brent Aug/Sep/Oct fly — LONG  (-10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 76/100
- **Setup:** dislocated to -3.82sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 79.26->79.34, CO_U26 79.12->79.19, CO_V26 78.55->78.6
- **In:** 2026-06-16 21:15 @ -0.43   **Out:** 2026-06-16 21:45 @ -0.44 (z -3.28, stop)
- **Held:** 2 bars (30 min)   **MAE/MFE:** -10 / +160

### 186. Brent Aug/Sep (M1-M2) — LONG  (+180 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -3.60sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 79.34->79.52, CO_U26 79.19->79.19
- **In:** 2026-06-16 21:45 @ 0.15   **Out:** 2026-06-17 00:00 @ 0.33 (z +0.45, target)
- **Held:** 1 bars (135 min)   **MAE/MFE:** +0 / +180

### 187. WTI Aug/Sep (M2-M3) — SHORT  (+140 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 92/100
- **Setup:** dislocated to +3.04sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 76.0->76.0, CL_U26 75.17->75.31
- **In:** 2026-06-16 22:00 @ 0.83   **Out:** 2026-06-16 22:15 @ 0.69 (z -1.69, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +140

### 188. WTI Aug/Sep (M2-M3) — LONG  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -2.70sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 75.8->75.86, CL_U26 75.09->75.1
- **In:** 2026-06-16 23:15 @ 0.71   **Out:** 2026-06-16 23:45 @ 0.76 (z +0.67, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +50

### 189. Brent Sep/Oct (M2-M3) — SHORT  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 80/100
- **Setup:** dislocated to +1.80sigma (rich) -> fade
- **Legs (entry->exit):** CO_U26 79.19->79.24, CO_V26 78.57->78.65
- **In:** 2026-06-17 00:00 @ 0.62   **Out:** 2026-06-17 00:45 @ 0.59 (z +0.00, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +30

### 190. WTI Aug/Sep (M2-M3) — LONG  (-40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 68/100
- **Setup:** dislocated to -2.25sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 75.56->75.38, CL_U26 74.87->74.73
- **In:** 2026-06-17 01:15 @ 0.69   **Out:** 2026-06-17 02:15 @ 0.65 (z -2.70, stop)
- **Held:** 4 bars (60 min)   **MAE/MFE:** -40 / +30

### 191. Brent Aug/Sep (M1-M2) — LONG  (+20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 59/100
- **Setup:** dislocated to -1.75sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 79.19->78.67, CO_U26 78.96->78.42
- **In:** 2026-06-17 01:15 @ 0.23   **Out:** 2026-06-17 04:00 @ 0.25 (z +0.27, target)
- **Held:** 11 bars (165 min)   **MAE/MFE:** -30 / +30

### 192. Brent Aug/Sep/Oct fly — LONG  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 63/100
- **Setup:** dislocated to -1.57sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 79.19->79.16, CO_U26 78.96->78.91, CO_V26 78.36->78.38
- **In:** 2026-06-17 01:15 @ -0.37   **Out:** 2026-06-17 01:30 @ -0.28 (z +0.34, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +90

### 193. Brent Sep/Oct (M2-M3) — LONG  (-20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 63/100
- **Setup:** dislocated to -2.02sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 78.91->78.78, CO_V26 78.38->78.27
- **In:** 2026-06-17 01:30 @ 0.53   **Out:** 2026-06-17 01:45 @ 0.51 (z -2.70, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -20 / +0

### 194. WTI Jul/Aug (M1-M2) — LONG  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 62/100
- **Setup:** dislocated to -1.80sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 76.15->76.15, CL_Q26 75.43->75.4
- **In:** 2026-06-17 01:45 @ 0.72   **Out:** 2026-06-17 02:00 @ 0.75 (z +0.00, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +30

### 195. Brent Sep/Oct (M2-M3) — LONG  (-10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -3.71sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 78.78->78.74, CO_V26 78.3->78.27
- **In:** 2026-06-17 02:00 @ 0.48   **Out:** 2026-06-17 02:15 @ 0.47 (z -4.05, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -10 / +0

### 196. Brent Aug/Sep/Oct fly — SHORT  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 89/100
- **Setup:** dislocated to +2.02sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 79.0->78.71, CO_U26 78.74->78.5, CO_V26 78.27->77.99
- **In:** 2026-06-17 02:15 @ -0.21   **Out:** 2026-06-17 03:15 @ -0.3 (z -0.13, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +90

### 197. Brent Sep/Oct (M2-M3) — LONG  (+10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -2.97sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 78.74->78.27, CO_V26 78.26->77.78
- **In:** 2026-06-17 02:30 @ 0.48   **Out:** 2026-06-17 04:45 @ 0.49 (z +0.00, target)
- **Held:** 9 bars (135 min)   **MAE/MFE:** -30 / +30

### 198. WTI Aug/Sep (M2-M3) — LONG  (-40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 60/100
- **Setup:** dislocated to -1.62sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 75.35->75.01, CL_U26 74.69->74.39
- **In:** 2026-06-17 02:45 @ 0.66   **Out:** 2026-06-17 03:15 @ 0.62 (z -2.56, stop)
- **Held:** 2 bars (30 min)   **MAE/MFE:** -40 / +0

### 199. WTI Jul/Aug (M1-M2) — LONG  (-10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -3.15sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 75.67->75.74, CL_Q26 75.01->75.09
- **In:** 2026-06-17 03:15 @ 0.66   **Out:** 2026-06-17 03:30 @ 0.65 (z -3.60, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -10 / +0

### 200. Brent-WTI arb (Aug) — SHORT  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 97/100
- **Setup:** dislocated to +2.92sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 78.71->78.67, CL_Q26 75.01->75.03
- **In:** 2026-06-17 03:15 @ 3.7   **Out:** 2026-06-17 04:00 @ 3.64 (z +0.00, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +60

### 201. WTI Jul/Aug (M1-M2) — LONG  (-20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -4.95sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 75.42->75.63, CL_Q26 74.8->75.03
- **In:** 2026-06-17 03:45 @ 0.62   **Out:** 2026-06-17 04:00 @ 0.6 (z -5.62, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -20 / +0

### 202. WTI Jul/Aug/Sep fly — LONG  (+100 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 76/100
- **Setup:** dislocated to -2.92sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 75.63->75.16, CL_Q26 75.03->74.53, CL_U26 74.34->73.91
- **In:** 2026-06-17 04:00 @ -0.09   **Out:** 2026-06-17 05:15 @ 0.01 (z -0.00, target)
- **Held:** 5 bars (75 min)   **MAE/MFE:** +0 / +100

### 203. Brent Aug/Sep/Oct fly — SHORT  (+110 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 91/100
- **Setup:** dislocated to +2.16sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 78.67->78.7, CO_U26 78.42->78.51, CO_V26 77.97->78.01
- **In:** 2026-06-17 04:00 @ -0.2   **Out:** 2026-06-17 04:15 @ -0.31 (z -0.67, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +110

### 204. WTI Jul/Aug (M1-M2) — LONG  (-50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -4.05sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 75.71->75.57, CL_Q26 75.08->74.99
- **In:** 2026-06-17 04:15 @ 0.63   **Out:** 2026-06-17 04:30 @ 0.58 (z -3.78, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -50 / +0

### 205. WTI Jul/Aug (M1-M2) — LONG  (+80 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -2.59sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 75.49->76.14, CL_Q26 74.89->75.46
- **In:** 2026-06-17 04:45 @ 0.6   **Out:** 2026-06-17 05:45 @ 0.68 (z +0.67, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** -70 / +80

### 206. Brent Aug/Sep (M1-M2) — LONG  (-40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -2.70sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 78.13->78.5, CO_U26 77.98->78.39
- **In:** 2026-06-17 05:15 @ 0.15   **Out:** 2026-06-17 05:30 @ 0.11 (z -4.50, stop)
- **Held:** 1 bars (15 min)   **MAE/MFE:** -40 / +0

### 207. WTI Jul/Aug/Sep fly — LONG  (+170 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 69/100
- **Setup:** dislocated to -2.02sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 75.47->76.14, CL_Q26 74.94->75.46, CL_U26 74.3->74.84
- **In:** 2026-06-17 05:30 @ -0.11   **Out:** 2026-06-17 05:45 @ 0.06 (z +0.67, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +170

### 208. Brent Aug/Sep (M1-M2) — LONG  (-20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 63/100
- **Setup:** dislocated to -2.02sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 79.05->78.81, CO_U26 78.9->78.68
- **In:** 2026-06-17 05:45 @ 0.15   **Out:** 2026-06-17 06:15 @ 0.13 (z -2.53, stop)
- **Held:** 2 bars (30 min)   **MAE/MFE:** -20 / +10
