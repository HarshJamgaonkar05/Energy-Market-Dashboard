# Trade Log — Phase-2 strategy backtested on the provided 15-min data

_Strategy: Regime-conditioned RV mean-reversion (Phase 2). Data: **live**. Regime: **Balanced · High Vol**. Gross basis (slippage 0)._

**71 trades · gross $3,460 · win 83% · PF 4.567 · max DD $-240**

Each trade names the strategy, the setup, the legs with fills, the signal, the exit and the gross PnL.

---

### 1. WTI Jul/Aug (M1-M2) — SHORT  (+130 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 78/100
- **Setup:** dislocated to +2.10sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 87.03->84.49, CL_Q26 85.36->82.95
- **In:** 2026-06-12 13:45 @ 1.67   **Out:** 2026-06-12 16:00 @ 1.54 (z -0.12, target)
- **Held:** 9 bars (135 min)   **MAE/MFE:** +0 / +200

### 2. WTI Aug/Sep (M2-M3) — SHORT  (+130 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 84/100
- **Setup:** dislocated to +3.15sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 85.36->83.13, CL_U26 83.73->81.63
- **In:** 2026-06-12 13:45 @ 1.63   **Out:** 2026-06-12 15:00 @ 1.5 (z +0.15, target)
- **Held:** 5 bars (75 min)   **MAE/MFE:** +0 / +130

### 3. WTI Jul/Aug/Sep fly — LONG  (-120 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 77/100
- **Setup:** dislocated to -1.69sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 87.03->84.36, CL_Q26 85.36->82.86, CL_U26 83.73->81.28
- **In:** 2026-06-12 13:45 @ 0.04   **Out:** 2026-06-12 18:30 @ -0.08 (z +0.04, target)
- **Held:** 19 bars (285 min)   **MAE/MFE:** -210 / +0

### 4. Brent Aug/Sep (M1-M2) — SHORT  (+130 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 82/100
- **Setup:** dislocated to +2.78sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 89.65->89.17, CO_U26 88.31->87.96
- **In:** 2026-06-12 13:45 @ 1.34   **Out:** 2026-06-12 14:30 @ 1.21 (z +0.15, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +130

### 5. Brent Sep/Oct (M2-M3) — SHORT  (+80 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 76/100
- **Setup:** dislocated to +2.10sigma (rich) -> fade
- **Legs (entry->exit):** CO_U26 88.31->86.21, CO_V26 86.93->84.91
- **In:** 2026-06-12 13:45 @ 1.38   **Out:** 2026-06-12 18:00 @ 1.3 (z -0.22, target)
- **Held:** 17 bars (255 min)   **MAE/MFE:** -20 / +130

### 6. Brent Aug/Sep/Oct fly — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 80/100
- **Setup:** dislocated to -1.90sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 89.26->86.74, CO_U26 88.03->85.6, CO_V26 86.63->84.33
- **In:** 2026-06-12 14:15 @ -0.17   **Out:** 2026-06-12 21:30 @ -0.13 (z +0.23, target)
- **Held:** 29 bars (435 min)   **MAE/MFE:** -30 / +80

### 7. Brent-WTI arb (Aug) — LONG  (-120 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 83/100
- **Setup:** dislocated to -2.06sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 87.66->86.91, CL_Q26 83.49->82.86
- **In:** 2026-06-12 14:45 @ 4.17   **Out:** 2026-06-12 18:30 @ 4.05 (z +0.18, target)
- **Held:** 15 bars (225 min)   **MAE/MFE:** -210 / +0

### 8. Brent Aug/Sep (M1-M2) — LONG  (+110 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -1.67sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 86.92->87.29, CO_U26 85.85->86.11
- **In:** 2026-06-12 15:45 @ 1.07   **Out:** 2026-06-12 16:30 @ 1.18 (z +0.01, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +110

### 9. WTI Aug/Sep (M2-M3) — SHORT  (+110 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 74/100
- **Setup:** dislocated to +1.77sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 83.41->82.86, CL_U26 81.72->81.28
- **In:** 2026-06-12 18:00 @ 1.69   **Out:** 2026-06-12 18:30 @ 1.58 (z -0.22, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +110

### 10. Brent Sep/Oct (M2-M3) — LONG  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 70/100
- **Setup:** dislocated to -1.65sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 85.76->85.58, CO_V26 84.52->84.29
- **In:** 2026-06-12 18:30 @ 1.24   **Out:** 2026-06-12 21:45 @ 1.29 (z +0.28, session_end)
- **Held:** 13 bars (195 min)   **MAE/MFE:** +0 / +100

### 11. WTI Jul/Aug (M1-M2) — SHORT  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 77/100
- **Setup:** dislocated to +2.04sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 84.52->84.56, CL_Q26 82.95->83.04
- **In:** 2026-06-12 19:00 @ 1.57   **Out:** 2026-06-12 19:30 @ 1.52 (z -0.16, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +50

### 12. WTI Jul/Aug/Sep fly — SHORT  (-60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 74/100
- **Setup:** dislocated to +1.53sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 84.52->84.29, CL_Q26 82.95->82.74, CL_U26 81.38->81.25
- **In:** 2026-06-12 19:00 @ 0.0   **Out:** 2026-06-12 20:45 @ 0.06 (z +2.11, session_end)
- **Held:** 7 bars (105 min)   **MAE/MFE:** -60 / +110

### 13. WTI Aug/Sep (M2-M3) — LONG  (+50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 72/100
- **Setup:** dislocated to -1.67sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 82.76->82.79, CL_U26 81.22->81.2
- **In:** 2026-06-12 19:45 @ 1.54   **Out:** 2026-06-12 20:30 @ 1.59 (z -0.23, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +50

### 14. Brent Aug/Sep (M1-M2) — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 73/100
- **Setup:** dislocated to -1.91sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 86.78->86.8, CO_U26 85.67->85.65
- **In:** 2026-06-12 19:45 @ 1.11   **Out:** 2026-06-12 21:15 @ 1.15 (z -0.11, target)
- **Held:** 6 bars (90 min)   **MAE/MFE:** +0 / +40

### 15. WTI Jul/Aug (M1-M2) — LONG  (+70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 71/100
- **Setup:** dislocated to -1.55sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 84.27->84.29, CL_Q26 82.79->82.74
- **In:** 2026-06-12 20:30 @ 1.48   **Out:** 2026-06-12 20:45 @ 1.55 (z +1.08, session_end)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +70

### 16. WTI Aug/Sep (M2-M3) — LONG  (-240 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 76/100
- **Setup:** dislocated to -1.95sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 82.74->79.19, CL_U26 81.25->77.94
- **In:** 2026-06-12 20:45 @ 1.49   **Out:** 2026-06-15 04:00 @ 1.25 (z +0.21, target)
- **Held:** 25 bars (3315 min)   **MAE/MFE:** -330 / +0

### 17. Brent Aug/Sep (M1-M2) — SHORT  (+240 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 77/100
- **Setup:** dislocated to +2.17sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 86.8->83.55, CO_U26 85.58->82.57
- **In:** 2026-06-12 21:45 @ 1.22   **Out:** 2026-06-15 00:00 @ 0.98 (z -3.10, stop)
- **Held:** 1 bars (3015 min)   **MAE/MFE:** +0 / +240

### 18. Brent Aug/Sep/Oct fly — SHORT  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 80/100
- **Setup:** dislocated to +1.95sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 86.8->83.87, CO_U26 85.58->82.92, CO_V26 84.29->81.84
- **In:** 2026-06-12 21:45 @ -0.07   **Out:** 2026-06-15 00:45 @ -0.13 (z +0.02, target)
- **Held:** 4 bars (3060 min)   **MAE/MFE:** +0 / +90

### 19. WTI Jul/Aug (M1-M2) — LONG  (-30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 84/100
- **Setup:** dislocated to -3.32sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.96->80.9, CL_Q26 79.63->79.6
- **In:** 2026-06-14 22:00 @ 1.33   **Out:** 2026-06-15 06:00 @ 1.3 (z -0.06, target)
- **Held:** 32 bars (480 min)   **MAE/MFE:** -190 / +90

### 20. WTI Jul/Aug/Sep fly — SHORT  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 78/100
- **Setup:** dislocated to +1.76sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 80.66->80.85, CL_Q26 79.35->79.58, CL_U26 78.1->78.28
- **In:** 2026-06-15 00:00 @ 0.06   **Out:** 2026-06-15 00:15 @ -0.03 (z -0.13, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +90

### 21. Brent Sep/Oct (M2-M3) — LONG  (+20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 82/100
- **Setup:** dislocated to -3.39sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.57->82.47, CO_V26 81.51->81.39
- **In:** 2026-06-15 00:00 @ 1.06   **Out:** 2026-06-15 03:30 @ 1.08 (z +0.19, target)
- **Held:** 14 bars (210 min)   **MAE/MFE:** -70 / +70

### 22. Brent-WTI arb (Aug) — SHORT  (+10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 89/100
- **Setup:** dislocated to +3.22sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.55->83.67, CL_Q26 79.35->79.48
- **In:** 2026-06-15 00:00 @ 4.2   **Out:** 2026-06-15 05:30 @ 4.19 (z +0.24, target)
- **Held:** 22 bars (330 min)   **MAE/MFE:** -110 / +140

### 23. Brent Aug/Sep (M1-M2) — LONG  (-100 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 81/100
- **Setup:** dislocated to -2.43sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.8->83.67, CO_U26 82.83->82.8
- **In:** 2026-06-15 00:15 @ 0.97   **Out:** 2026-06-15 05:30 @ 0.87 (z +0.21, target)
- **Held:** 21 bars (315 min)   **MAE/MFE:** -160 / +50

### 24. WTI Jul/Aug/Sep fly — SHORT  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 78/100
- **Setup:** dislocated to +1.78sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 80.85->80.6, CL_Q26 79.58->79.37, CL_U26 78.39->78.13
- **In:** 2026-06-15 01:00 @ 0.08   **Out:** 2026-06-15 01:15 @ -0.01 (z +0.05, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +90

### 25. Brent Aug/Sep/Oct fly — SHORT  (+70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 81/100
- **Setup:** dislocated to +1.98sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.58->83.64, CO_U26 82.61->82.73, CO_V26 81.59->81.7
- **In:** 2026-06-15 01:15 @ -0.05   **Out:** 2026-06-15 02:00 @ -0.12 (z +0.02, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +70

### 26. WTI Jul/Aug/Sep fly — LONG  (+150 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 75/100
- **Setup:** dislocated to -1.56sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.16->80.73, CL_Q26 79.01->79.44, CL_U26 77.77->78.21
- **In:** 2026-06-15 02:30 @ -0.09   **Out:** 2026-06-15 06:15 @ 0.06 (z -0.22, target)
- **Held:** 15 bars (225 min)   **MAE/MFE:** +0 / +270

### 27. Brent Aug/Sep/Oct fly — LONG  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 78/100
- **Setup:** dislocated to -1.78sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.11->83.55, CO_U26 82.3->82.71, CO_V26 81.3->81.71
- **In:** 2026-06-15 03:15 @ -0.19   **Out:** 2026-06-15 05:15 @ -0.16 (z -0.24, target)
- **Held:** 8 bars (120 min)   **MAE/MFE:** -30 / +90

### 28. Brent Sep/Oct (M2-M3) — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 68/100
- **Setup:** dislocated to -1.51sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.42->82.69, CO_V26 81.44->81.67
- **In:** 2026-06-15 04:00 @ 0.98   **Out:** 2026-06-15 05:00 @ 1.02 (z +0.06, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** -20 / +40

### 29. WTI Aug/Sep (M2-M3) — SHORT  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 81/100
- **Setup:** dislocated to +2.26sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 79.42->79.4, CL_U26 78.12->78.16
- **In:** 2026-06-15 05:00 @ 1.3   **Out:** 2026-06-15 05:15 @ 1.24 (z +0.19, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +60

### 30. WTI Aug/Sep (M2-M3) — LONG  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 73/100
- **Setup:** dislocated to -1.75sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 79.17->78.97, CL_U26 78.01->77.78
- **In:** 2026-06-15 06:45 @ 1.16   **Out:** 2026-06-15 08:45 @ 1.19 (z -0.06, target)
- **Held:** 8 bars (120 min)   **MAE/MFE:** -60 / +30

### 31. Brent Sep/Oct (M2-M3) — LONG  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 68/100
- **Setup:** dislocated to -1.54sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.6->82.75, CO_V26 81.65->81.77
- **In:** 2026-06-15 06:45 @ 0.95   **Out:** 2026-06-15 08:00 @ 0.98 (z +0.06, target)
- **Held:** 5 bars (75 min)   **MAE/MFE:** -40 / +40

### 32. WTI Jul/Aug/Sep fly — SHORT  (-70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 80/100
- **Setup:** dislocated to +1.93sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 79.85->80.59, CL_Q26 78.55->79.2, CL_U26 77.45->78.08
- **In:** 2026-06-15 07:15 @ 0.2   **Out:** 2026-06-15 10:45 @ 0.27 (z -0.00, target)
- **Held:** 14 bars (210 min)   **MAE/MFE:** -230 / +20

### 33. Brent Aug/Sep (M1-M2) — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 75/100
- **Setup:** dislocated to -2.02sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.78->83.04, CO_U26 82.0->82.22
- **In:** 2026-06-15 07:15 @ 0.78   **Out:** 2026-06-15 08:15 @ 0.82 (z -0.21, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** -10 / +70

### 34. WTI Jul/Aug (M1-M2) — SHORT  (+70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 79/100
- **Setup:** dislocated to +2.15sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 80.49->80.12, CL_Q26 79.04->78.74
- **In:** 2026-06-15 07:45 @ 1.45   **Out:** 2026-06-15 09:15 @ 1.38 (z +0.14, target)
- **Held:** 6 bars (90 min)   **MAE/MFE:** -10 / +70

### 35. Brent Aug/Sep/Oct fly — LONG  (+70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 84/100
- **Setup:** dislocated to -2.22sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.52->83.05, CO_U26 82.75->82.26, CO_V26 81.77->81.33
- **In:** 2026-06-15 08:00 @ -0.21   **Out:** 2026-06-15 08:45 @ -0.14 (z +0.06, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +150

### 36. Brent Sep/Oct (M2-M3) — LONG  (+0 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 79/100
- **Setup:** dislocated to -2.28sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.22->82.44, CO_V26 81.34->81.56
- **In:** 2026-06-15 08:15 @ 0.88   **Out:** 2026-06-15 10:45 @ 0.88 (z +0.12, target)
- **Held:** 10 bars (150 min)   **MAE/MFE:** -120 / +50

### 37. Brent-WTI arb (Aug) — LONG  (-50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 83/100
- **Setup:** dislocated to -2.06sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.05->83.03, CL_Q26 78.97->79.0
- **In:** 2026-06-15 08:45 @ 4.08   **Out:** 2026-06-15 12:00 @ 4.03 (z +0.06, target)
- **Held:** 13 bars (195 min)   **MAE/MFE:** -160 / +20

### 38. WTI Aug/Sep (M2-M3) — LONG  (+10 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 71/100
- **Setup:** dislocated to -1.55sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 78.93->79.2, CL_U26 77.82->78.08
- **In:** 2026-06-15 09:00 @ 1.11   **Out:** 2026-06-15 10:45 @ 1.12 (z -0.10, target)
- **Held:** 7 bars (105 min)   **MAE/MFE:** -80 / +20

### 39. Brent Aug/Sep (M1-M2) — LONG  (+80 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 82/100
- **Setup:** dislocated to -2.91sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.95->83.2, CO_U26 82.27->82.44
- **In:** 2026-06-15 09:00 @ 0.68   **Out:** 2026-06-15 10:45 @ 0.76 (z +0.22, target)
- **Held:** 7 bars (105 min)   **MAE/MFE:** -40 / +80

### 40. WTI Jul/Aug (M1-M2) — LONG  (+20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 76/100
- **Setup:** dislocated to -1.91sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.2->79.91, CL_Q26 78.91->78.6
- **In:** 2026-06-15 11:00 @ 1.29   **Out:** 2026-06-15 14:15 @ 1.31 (z -0.19, target)
- **Held:** 13 bars (195 min)   **MAE/MFE:** -80 / +140

### 41. WTI Jul/Aug/Sep fly — LONG  (+80 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 74/100
- **Setup:** dislocated to -1.50sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.3->80.46, CL_Q26 79.0->79.08, CL_U26 77.87->77.95
- **In:** 2026-06-15 12:00 @ 0.17   **Out:** 2026-06-15 13:00 @ 0.25 (z +0.18, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** -50 / +80

### 42. Brent-WTI arb (Aug) — SHORT  (+100 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 76/100
- **Setup:** dislocated to +1.56sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 82.9->82.6, CL_Q26 78.8->78.6
- **In:** 2026-06-15 12:30 @ 4.1   **Out:** 2026-06-15 14:30 @ 4.0 (z -0.05, target)
- **Held:** 8 bars (120 min)   **MAE/MFE:** +0 / +190

### 43. WTI Aug/Sep (M2-M3) — SHORT  (-70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 75/100
- **Setup:** dislocated to +1.85sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 79.03->79.18, CL_U26 77.88->77.96
- **In:** 2026-06-15 12:45 @ 1.15   **Out:** 2026-06-15 17:15 @ 1.22 (z +0.13, target)
- **Held:** 18 bars (270 min)   **MAE/MFE:** -120 / +40

### 44. Brent Aug/Sep (M1-M2) — SHORT  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 68/100
- **Setup:** dislocated to +1.56sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.12->82.51, CO_U26 82.39->81.81
- **In:** 2026-06-15 12:45 @ 0.73   **Out:** 2026-06-15 14:15 @ 0.7 (z -0.22, target)
- **Held:** 6 bars (90 min)   **MAE/MFE:** -10 / +30

### 45. Brent Sep/Oct (M2-M3) — SHORT  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 69/100
- **Setup:** dislocated to +1.63sigma (rich) -> fade
- **Legs (entry->exit):** CO_U26 82.47->82.12, CO_V26 81.6->81.29
- **In:** 2026-06-15 13:15 @ 0.87   **Out:** 2026-06-15 14:00 @ 0.83 (z +0.10, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +40

### 46. Brent Aug/Sep/Oct fly — SHORT  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 84/100
- **Setup:** dislocated to +2.20sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 82.86->82.51, CO_U26 82.12->81.81, CO_V26 81.29->80.99
- **In:** 2026-06-15 14:00 @ -0.09   **Out:** 2026-06-15 14:15 @ -0.12 (z +0.05, target)
- **Held:** 1 bars (15 min)   **MAE/MFE:** +0 / +30

### 47. Brent Aug/Sep/Oct fly — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 76/100
- **Setup:** dislocated to -1.65sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 82.6->83.03, CO_U26 81.87->82.17, CO_V26 81.0->81.21
- **In:** 2026-06-15 14:30 @ -0.14   **Out:** 2026-06-15 15:30 @ -0.1 (z +0.15, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +110

### 48. Brent Aug/Sep (M1-M2) — SHORT  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 82/100
- **Setup:** dislocated to +2.88sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.14->82.7, CO_U26 82.28->81.9
- **In:** 2026-06-15 14:45 @ 0.86   **Out:** 2026-06-15 16:15 @ 0.8 (z +0.16, target)
- **Held:** 6 bars (90 min)   **MAE/MFE:** -50 / +60

### 49. Brent Sep/Oct (M2-M3) — SHORT  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 79/100
- **Setup:** dislocated to +2.32sigma (rich) -> fade
- **Legs (entry->exit):** CO_U26 82.28->81.9, CO_V26 81.36->81.01
- **In:** 2026-06-15 14:45 @ 0.92   **Out:** 2026-06-15 16:15 @ 0.89 (z +0.12, target)
- **Held:** 6 bars (90 min)   **MAE/MFE:** -40 / +30

### 50. WTI Jul/Aug/Sep fly — LONG  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 77/100
- **Setup:** dislocated to -1.70sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.5->80.45, CL_Q26 79.13->79.11, CL_U26 77.87->77.91
- **In:** 2026-06-15 15:30 @ 0.11   **Out:** 2026-06-15 17:30 @ 0.14 (z +0.01, target)
- **Held:** 8 bars (120 min)   **MAE/MFE:** -60 / +50

### 51. Brent-WTI arb (Aug) — LONG  (+70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 76/100
- **Setup:** dislocated to -1.58sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.03->83.08, CL_Q26 79.13->79.11
- **In:** 2026-06-15 15:30 @ 3.9   **Out:** 2026-06-15 17:30 @ 3.97 (z -0.00, target)
- **Held:** 8 bars (120 min)   **MAE/MFE:** -30 / +160

### 52. Brent Sep/Oct (M2-M3) — SHORT  (+30 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 74/100
- **Setup:** dislocated to +1.94sigma (rich) -> fade
- **Legs (entry->exit):** CO_U26 82.18->82.18, CO_V26 81.18->81.21
- **In:** 2026-06-15 16:30 @ 1.0   **Out:** 2026-06-15 18:00 @ 0.97 (z +0.16, target)
- **Held:** 6 bars (90 min)   **MAE/MFE:** -50 / +30

### 53. Brent Aug/Sep/Oct fly — LONG  (+90 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 86/100
- **Setup:** dislocated to -2.39sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.08->83.38, CO_U26 82.24->82.47, CO_V26 81.22->81.47
- **In:** 2026-06-15 17:30 @ -0.18   **Out:** 2026-06-15 18:30 @ -0.09 (z -0.13, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +130

### 54. WTI Aug/Sep (M2-M3) — SHORT  (+70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 76/100
- **Setup:** dislocated to +1.93sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 79.55->79.59, CL_U26 78.23->78.34
- **In:** 2026-06-15 18:15 @ 1.32   **Out:** 2026-06-15 18:45 @ 1.25 (z +0.15, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +70

### 55. WTI Jul/Aug/Sep fly — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 82/100
- **Setup:** dislocated to -2.04sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.9->81.2, CL_Q26 79.55->79.85, CL_U26 78.23->78.57
- **In:** 2026-06-15 18:15 @ 0.03   **Out:** 2026-06-15 20:30 @ 0.07 (z -0.06, target)
- **Held:** 9 bars (135 min)   **MAE/MFE:** -30 / +40

### 56. Brent-WTI arb (Aug) — LONG  (-50 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 89/100
- **Setup:** dislocated to -2.77sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.27->83.48, CL_Q26 79.55->79.81
- **In:** 2026-06-15 18:15 @ 3.72   **Out:** 2026-06-15 20:45 @ 3.67 (z -0.83, session_end)
- **Held:** 10 bars (150 min)   **MAE/MFE:** -80 / +50

### 57. WTI Jul/Aug (M1-M2) — LONG  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 75/100
- **Setup:** dislocated to -1.84sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 80.88->81.2, CL_Q26 79.59->79.85
- **In:** 2026-06-15 18:45 @ 1.29   **Out:** 2026-06-15 20:30 @ 1.35 (z +0.17, target)
- **Held:** 7 bars (105 min)   **MAE/MFE:** -30 / +90

### 58. WTI Aug/Sep (M2-M3) — SHORT  (+60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 74/100
- **Setup:** dislocated to +1.76sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 79.95->79.85, CL_U26 78.61->78.57
- **In:** 2026-06-15 19:45 @ 1.34   **Out:** 2026-06-15 20:30 @ 1.28 (z +0.18, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** +0 / +60

### 59. Brent Aug/Sep/Oct fly — LONG  (+70 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 83/100
- **Setup:** dislocated to -2.13sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.59->83.63, CO_U26 82.74->82.72, CO_V26 81.71->81.7
- **In:** 2026-06-15 19:45 @ -0.18   **Out:** 2026-06-15 20:15 @ -0.11 (z -0.16, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +110

### 60. Brent Sep/Oct (M2-M3) — LONG  (+20 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 69/100
- **Setup:** dislocated to -1.58sigma (cheap) -> fade
- **Legs (entry->exit):** CO_U26 82.59->82.64, CO_V26 81.62->81.65
- **In:** 2026-06-15 20:45 @ 0.97   **Out:** 2026-06-15 21:45 @ 0.99 (z -0.34, session_end)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +20

### 61. Brent Aug/Sep (M1-M2) — SHORT  (+240 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 73/100
- **Setup:** dislocated to +1.90sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.6->83.36, CO_U26 82.64->82.64
- **In:** 2026-06-15 21:15 @ 0.96   **Out:** 2026-06-15 21:45 @ 0.72 (z -3.03, stop)
- **Held:** 2 bars (30 min)   **MAE/MFE:** -30 / +240

### 62. Brent Aug/Sep/Oct fly — SHORT  (+240 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 77/100
- **Setup:** dislocated to +1.72sigma (rich) -> fade
- **Legs (entry->exit):** CO_Q26 83.6->83.36, CO_U26 82.64->82.64, CO_V26 81.65->81.65
- **In:** 2026-06-15 21:15 @ -0.03   **Out:** 2026-06-15 21:45 @ -0.27 (z -2.81, session_end)
- **Held:** 2 bars (30 min)   **MAE/MFE:** -30 / +240

### 63. WTI Aug/Sep (M2-M3) — SHORT  (+110 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 82/100
- **Setup:** dislocated to +2.36sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 79.78->80.14, CL_U26 78.35->78.82
- **In:** 2026-06-15 22:00 @ 1.43   **Out:** 2026-06-15 23:45 @ 1.32 (z -0.15, target)
- **Held:** 7 bars (105 min)   **MAE/MFE:** +0 / +160

### 64. WTI Jul/Aug/Sep fly — LONG  (+110 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 85/100
- **Setup:** dislocated to -2.27sigma (cheap) -> fade
- **Legs (entry->exit):** CL_N26 81.12->81.31, CL_Q26 79.78->79.99, CL_U26 78.35->78.69
- **In:** 2026-06-15 22:00 @ -0.09   **Out:** 2026-06-16 00:45 @ 0.02 (z -0.18, target)
- **Held:** 11 bars (165 min)   **MAE/MFE:** +0 / +180

### 65. WTI Jul/Aug (M1-M2) — SHORT  (+120 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 73/100
- **Setup:** dislocated to +1.75sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 81.42->80.17, CL_Q26 80.01->78.88
- **In:** 2026-06-15 23:15 @ 1.41   **Out:** 2026-06-16 07:00 @ 1.29 (z +0.12, target)
- **Held:** 31 bars (465 min)   **MAE/MFE:** +0 / +160

### 66. Brent Sep/Oct (M2-M3) — SHORT  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 72% · confidence 77/100
- **Setup:** dislocated to +2.19sigma (rich) -> fade
- **Legs (entry->exit):** CO_U26 82.66->82.46, CO_V26 81.62->81.46
- **In:** 2026-06-16 00:00 @ 1.04   **Out:** 2026-06-16 01:15 @ 1.0 (z -0.17, target)
- **Held:** 5 bars (75 min)   **MAE/MFE:** +0 / +50

### 67. Brent Aug/Sep/Oct fly — LONG  (+110 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 74/100
- **Setup:** dislocated to -1.51sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.63->83.63, CO_U26 82.81->82.74, CO_V26 81.78->81.75
- **In:** 2026-06-16 00:15 @ -0.21   **Out:** 2026-06-16 00:45 @ -0.1 (z +0.18, target)
- **Held:** 2 bars (30 min)   **MAE/MFE:** +0 / +110

### 68. WTI Aug/Sep (M2-M3) — SHORT  (+110 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 73/100
- **Setup:** dislocated to +1.71sigma (rich) -> fade
- **Legs (entry->exit):** CL_Q26 79.84->79.37, CL_U26 78.42->78.06
- **In:** 2026-06-16 01:00 @ 1.42   **Out:** 2026-06-16 03:00 @ 1.31 (z +0.16, target)
- **Held:** 8 bars (120 min)   **MAE/MFE:** +0 / +280

### 69. WTI Jul/Aug/Sep fly — SHORT  (+160 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 82% · confidence 88/100
- **Setup:** dislocated to +2.56sigma (rich) -> fade
- **Legs (entry->exit):** CL_N26 80.92->80.72, CL_Q26 79.59->79.42, CL_U26 78.45->78.15
- **In:** 2026-06-16 01:45 @ 0.19   **Out:** 2026-06-16 02:45 @ 0.03 (z -0.18, target)
- **Held:** 4 bars (60 min)   **MAE/MFE:** +0 / +170

### 70. Brent-WTI arb (Aug) — LONG  (-60 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 83% · confidence 82/100
- **Setup:** dislocated to -1.99sigma (cheap) -> fade
- **Legs (entry->exit):** CO_Q26 83.22->82.77, CL_Q26 79.6->79.21
- **In:** 2026-06-16 02:30 @ 3.62   **Out:** 2026-06-16 05:30 @ 3.56 (z -0.24, target)
- **Held:** 12 bars (180 min)   **MAE/MFE:** -120 / +0

### 71. WTI Aug/Sep (M2-M3) — LONG  (+40 USD)
- **Strategy:** Regime-conditioned RV mean-reversion (Phase 2) · regime Balanced · High Vol · hist. edge 75% · confidence 70/100
- **Setup:** dislocated to -1.51sigma (cheap) -> fade
- **Legs (entry->exit):** CL_Q26 79.2->79.22, CL_U26 77.98->77.96
- **In:** 2026-06-16 05:45 @ 1.22   **Out:** 2026-06-16 06:30 @ 1.26 (z +0.00, target)
- **Held:** 3 bars (45 min)   **MAE/MFE:** -20 / +40
