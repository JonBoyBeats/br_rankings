# NBA grade by combined tier

Written by scripts/nba_tier_grade.py from tier_history.csv. Decision pairs (same tier, ADP within 4 at the lock); a player who sat is scored with his swap. Each cell: points per pair (80% range from resampling slates), pairs, and the evidence level. Head to head: positive = your board beat the source on the pairs you ordered differently.

## 6-drafter AM, primary (Lock AM on our Proj, 10-28 on)

### Your board against each source

| Tier | Nights | Ours | ADP |
|---|---|---|---|
| T1 | 7 | -18.0, not enough yet (2); 50% right; breaker 0 of 1 | +17.0, not enough yet (4); 75% right; breaker 3 of 3 |
| T2 | 7 | +3.8 (+0.6 to +7.8), 41 pairs, LEAN +; 63% right; breaker 7 of 12 | +1.1 (-2.9 to +4.7), 40 pairs, no lean; 50% right; breaker 6 of 12 |
| T3/T4 (middle) | 7 | -1.4 (-2.6 to +0.1), 67 pairs, LEAN -; 42% right; breaker 10 of 18 | +1.3 (-1.4 to +4.2), 141 pairs, no lean; 52% right; breaker 29 of 44 |
| T3 | 7 | -2.3, not enough yet (26); 38% right; breaker 4 of 7 | -1.0, not enough yet (38); 53% right; breaker 9 of 13 |
| T4 | 7 | -2.6, not enough yet (36); 39% right; breaker 5 of 10 | +1.0 (-2.0 to +4.2), 74 pairs, no lean; 54% right; breaker 16 of 23 |
| T5 | 7 | +4.1 (-1.1 to +7.8), 100 pairs, LEAN +; 60% right; breaker 20 of 39 | -3.0 (-4.1 to -1.6), 365 pairs, LEAN - (RULE numbers, check pending); 42% right; breaker 57 of 136 |
| Across T1/T2 | 7 | +13.2, not enough yet (2); 100% right | - |
| Across T2/T3 | 7 | -5.0, not enough yet (7); 29% right; breaker 1 of 4 | -0.4, not enough yet (13); 54% right; breaker 2 of 7 |
| Across T3/T4 | 7 | +12.2, not enough yet (5); 80% right; breaker 1 of 1 | +4.9, not enough yet (29); 48% right; breaker 4 of 8 |
| Across T4/T5 | 7 | -2.0, not enough yet (10); 50% right; breaker 0 of 2 | -2.4 (-5.2 to +1.4), 48 pairs, no lean; 33% right; breaker 6 of 16 |

### The flag test (positive: VALUE outscored its partners / PRICEY lagged them)

| Tier | VALUE | PRICEY |
|---|---|---|
| T1 | - | +1.8, not enough yet (8) |
| T2 | -1.1, not enough yet (7) | +3.5 (-2.2 to +9.1), 42 pairs, no lean |
| T3/T4 (middle) | +2.5 (-0.4 to +5.8), 167 pairs, LEAN + | -0.7 (-2.5 to +1.7), 198 pairs, no lean |
| T3 | +3.0 (-3.3 to +8.0), 52 pairs, no lean | -2.6 (-6.8 to +2.6), 53 pairs, no lean |
| T4 | +4.1 (+0.6 to +6.7), 73 pairs, LEAN + | +1.6 (-1.9 to +4.6), 85 pairs, no lean |
| T5 | +4.4 (+2.9 to +6.6), 342 pairs, LEAN + (RULE numbers, check pending) | - |
| Across T1/T2 | -18.6, not enough yet (7) | +2.6, not enough yet (11) |
| Across T2/T3 | -2.4, not enough yet (15) | -0.1, not enough yet (28) |
| Across T3/T4 | -1.0 (-7.5 to +6.4), 42 pairs, no lean | -2.2 (-7.5 to +3.2), 60 pairs, no lean |
| Across T4/T5 | +2.1 (-1.5 to +6.0), 228 pairs, no lean | +2.6, not enough yet (19) |

### Each source inside the tier (error = mean |actual - projection|; bias = actual - projection; rank correlation per slate, averaged)

| Tier | Ours | ADP |
|---|---|---|
| T1 | err 13.6, bias -9.4, rank corr 0.20 (4 slates) | rank corr 0.20 (4 slates) |
| T2 | err 11.4, bias -8.0, rank corr 0.12 (7 slates) | rank corr 0.19 (7 slates) |
| T3/T4 | err 11.7, bias -9.4, rank corr 0.12 (7 slates) | rank corr 0.06 (7 slates) |
| T5 (priced) | err 9.4, bias -5.4, rank corr 0.41 (7 slates) | rank corr 0.32 (7 slates) |

## 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board)

### Your board against each source

| Tier | Nights | Ours | ADP |
|---|---|---|---|
| T1 | 7 | -0.1, not enough yet (11); 55% right; breaker 1 of 3 | -5.5, not enough yet (5); 40% right; breaker 1 of 2 |
| T2 | 7 | +4.2 (-0.1 to +7.6), 63 pairs, LEAN +; 60% right; breaker 16 of 25 | +1.5 (-0.9 to +3.2), 64 pairs, no lean; 56% right; breaker 16 of 18 |
| T3/T4 (middle) | 7 | +4.3 (+2.7 to +6.2), 104 pairs, LEAN + (RULE numbers, check pending); 64% right; breaker 20 of 28 | -0.9 (-3.6 to +2.0), 114 pairs, no lean; 49% right; breaker 17 of 35 |
| T3 | 7 | +4.2 (+1.6 to +7.7), 41 pairs, LEAN +; 66% right; breaker 7 of 11 | +2.1, not enough yet (38); 61% right; breaker 8 of 11 |
| T4 | 7 | +10.0, not enough yet (30); 73% right; breaker 10 of 13 | -0.4 (-3.9 to +2.8), 45 pairs, no lean; 44% right; breaker 8 of 17 |
| T5 | 7 | -0.1 (-2.0 to +1.9), 259 pairs, no lean; 52% right; breaker 39 of 66 | +0.4 (-0.9 to +1.7), 421 pairs, no lean; 52% right; breaker 51 of 95 |
| Across T1/T2 | 7 | -12.1, not enough yet (5); 20% right; breaker 0 of 1 | -14.9, not enough yet (3); 0% right |
| Across T2/T3 | 7 | +12.5, not enough yet (18); 78% right; breaker 8 of 8 | +7.3, not enough yet (19); 68% right; breaker 6 of 6 |
| Across T3/T4 | 7 | -0.7, not enough yet (33); 55% right; breaker 3 of 4 | -5.3, not enough yet (31); 42% right; breaker 1 of 7 |
| Across T4/T5 | 7 | -3.3, not enough yet (39); 46% right; breaker 5 of 15 | -0.1 (-2.3 to +2.4), 43 pairs, no lean; 56% right; breaker 6 of 12 |

### The flag test (positive: VALUE outscored its partners / PRICEY lagged them)

| Tier | VALUE | PRICEY |
|---|---|---|
| T1 | - | +0.2, not enough yet (22) |
| T2 | - | -2.9 (-6.0 to +0.2), 69 pairs, LEAN - |
| T3/T4 (middle) | -3.6 (-5.1 to -2.3), 124 pairs, LEAN - (RULE numbers, check pending) | -1.2 (-4.0 to +1.3), 128 pairs, no lean |
| T3 | +1.9, not enough yet (39) | -2.5, not enough yet (37) |
| T4 | -7.0 (-9.9 to -3.9), 49 pairs, LEAN - | +0.2, not enough yet (36) |
| T5 | +3.8 (+2.7 to +4.8), 243 pairs, LEAN + (RULE numbers, check pending) | - |
| Across T1/T2 | - | -3.3, not enough yet (20) |
| Across T2/T3 | +1.0, not enough yet (9) | -1.5, not enough yet (38) |
| Across T3/T4 | -4.9, not enough yet (36) | -1.3 (-4.0 to +1.1), 55 pairs, no lean |
| Across T4/T5 | +7.1 (+2.0 to +10.2), 93 pairs, LEAN + | -3.4, not enough yet (21) |

### Each source inside the tier (error = mean |actual - projection|; bias = actual - projection; rank correlation per slate, averaged)

| Tier | Ours | ADP |
|---|---|---|
| T1 | err 9.0, bias -1.4, rank corr 0.20 (3 slates) | rank corr 0.23 (3 slates) |
| T2 | err 9.8, bias -1.8, rank corr 0.10 (7 slates) | rank corr 0.28 (7 slates) |
| T3/T4 | err 9.5, bias -1.9, rank corr -0.13 (7 slates) | rank corr 0.15 (7 slates) |
| T5 (priced) | err 8.9, bias -2.0, rank corr 0.30 (7 slates) | rank corr 0.24 (7 slates) |

## 6-drafter PM

### Your board against each source

| Tier | Nights | ETR | Ours PM | ADP |
|---|---|---|---|---|
| T1 | 14 | -11.2, not enough yet (4); 25% right; breaker 0 of 1 | -4.0, not enough yet (6); 33% right; breaker 1 of 3 | +9.5, not enough yet (9); 67% right; breaker 4 of 4 |
| T2 | 14 | -1.5 (-4.1 to +1.1), 77 pairs, no lean; 49% right; breaker 13 of 28 | -0.1 (-2.1 to +2.3), 52 pairs, no lean; 52% right; breaker 13 of 23 | +2.3 (-0.2 to +4.6), 106 pairs, LEAN +; 55% right; breaker 31 of 38 |
| T3/T4 (middle) | 14 | +2.8 (+0.4 to +4.9), 113 pairs, LEAN +; 63% right; breaker 19 of 32 | +0.3 (-2.6 to +3.0), 114 pairs, no lean; 54% right; breaker 16 of 36 | +2.7 (+0.7 to +4.9), 244 pairs, RULE +; 59% right; breaker 38 of 68 |
| T3 | 14 | +1.1 (-1.5 to +4.2), 51 pairs, no lean; 57% right; breaker 9 of 12 | +5.0, not enough yet (24); 54% right; breaker 5 of 6 | +5.5 (+2.5 to +8.2), 119 pairs, RULE +; 61% right; breaker 25 of 32 |
| T4 | 14 | +1.9 (-2.2 to +4.6), 49 pairs, no lean; 59% right; breaker 5 of 15 | -1.9 (-4.5 to +1.4), 62 pairs, no lean; 50% right; breaker 4 of 18 | -0.7 (-2.7 to +1.1), 104 pairs, no lean; 53% right; breaker 9 of 29 |
| T5 | 14 | -1.2 (-3.1 to +1.2), 268 pairs, no lean; 50% right; breaker 39 of 91 | -0.7 (-2.2 to +1.0), 286 pairs, no lean; 47% right; breaker 38 of 95 | -2.3 (-3.7 to -0.8), 728 pairs, RULE -; 44% right; breaker 93 of 223 |
| Across T1/T2 | 14 | +2.3, not enough yet (3); 33% right | - | -19.8, not enough yet (2); 0% right |
| Across T2/T3 | 14 | +7.2, not enough yet (18); 72% right; breaker 1 of 2 | +6.1, not enough yet (15); 67% right; breaker 3 of 4 | -1.2, not enough yet (23); 57% right; breaker 0 of 3 |
| Across T3/T4 | 14 | +12.5, not enough yet (13); 100% right; breaker 5 of 5 | +1.4, not enough yet (28); 61% right; breaker 7 of 12 | +4.3, not enough yet (21); 76% right; breaker 4 of 7 |
| Across T4/T5 | 14 | -4.5, not enough yet (24); 38% right; breaker 1 of 10 | -8.5, not enough yet (19); 21% right; breaker 2 of 6 | -1.3 (-6.0 to +3.2), 52 pairs, no lean; 48% right; breaker 15 of 28 |

### The flag test (positive: VALUE outscored its partners / PRICEY lagged them)

| Tier | VALUE | PRICEY |
|---|---|---|
| T1 | - | +9.9, not enough yet (33) |
| T2 | +4.8, not enough yet (6) | +3.1 (-0.0 to +6.2), 92 pairs, LEAN + |
| T3/T4 (middle) | +2.6 (-0.3 to +5.9), 253 pairs, LEAN + | +0.6 (-2.3 to +3.8), 230 pairs, no lean |
| T3 | +6.4 (-0.5 to +13.2), 90 pairs, LEAN + | +5.8 (+1.0 to +10.2), 101 pairs, LEAN + |
| T4 | +1.9 (-0.5 to +4.5), 102 pairs, LEAN + | -3.3 (-7.2 to +1.3), 99 pairs, LEAN - |
| T5 | +3.5 (+0.7 to +6.1), 512 pairs, LEAN + | - |
| Across T1/T2 | -16.4, not enough yet (6) | -3.0, not enough yet (35) |
| Across T2/T3 | -5.7, not enough yet (33) | -1.9 (-7.1 to +2.8), 64 pairs, no lean |
| Across T3/T4 | -1.7 (-4.5 to +2.3), 61 pairs, no lean | -4.4, not enough yet (30) |
| Across T4/T5 | -0.6 (-5.0 to +4.0), 173 pairs, no lean | -5.6 (-10.7 to +3.8), 40 pairs, no lean |

### Each source inside the tier (error = mean |actual - projection|; bias = actual - projection; rank correlation per slate, averaged)

| Tier | ETR | Ours PM | ADP |
|---|---|---|---|
| T1 | err 11.2, bias -8.4, rank corr 0.54 (7 slates) | err 12.2, bias -7.7, rank corr 0.47 (4 slates) | rank corr 0.42 (7 slates) |
| T2 | err 10.8, bias -7.2, rank corr 0.17 (14 slates) | err 10.0, bias -7.0, rank corr 0.14 (6 slates) | rank corr 0.14 (14 slates) |
| T3/T4 | err 11.5, bias -9.0, rank corr 0.02 (14 slates) | err 12.1, bias -9.4, rank corr 0.01 (6 slates) | rank corr 0.03 (14 slates) |
| T5 (priced) | err 9.7, bias -6.0, rank corr 0.39 (14 slates) | err 9.5, bias -5.2, rank corr 0.37 (6 slates) | rank corr 0.28 (14 slates) |

## 4-drafter AM (small slates)

### Your board against each source

| Tier | Nights | Ours | ADP |
|---|---|---|---|
| T1 | 4 | -13.9, not enough yet (1); 0% right; breaker 0 of 1 | - |
| T2 | 4 | -0.5, not enough yet (7); 57% right; breaker 2 of 4 | -7.0, not enough yet (15); 27% right; breaker 2 of 5 |
| T3/T4 (middle) | 4 | +0.8, not enough yet (7); 57% right; breaker 3 of 5 | +2.2, not enough yet (30); 70% right; breaker 10 of 13 |
| T3 | 4 | -0.1, not enough yet (4); 50% right; breaker 1 of 3 | -16.6, not enough yet (6); 17% right; breaker 1 of 3 |
| T4 | 4 | +2.7, not enough yet (2); 50% right; breaker 1 of 1 | +7.1, not enough yet (23); 83% right; breaker 8 of 9 |
| T5 | 4 | +4.8, not enough yet (26); 62% right; breaker 9 of 11 | +2.2 (-1.1 to +8.7), 77 pairs, no lean; 55% right; breaker 12 of 26 |
| Across T1/T2 | 4 | - | - |
| Across T2/T3 | 4 | -5.5, not enough yet (3); 33% right; breaker 1 of 2 | +0.5, not enough yet (8); 50% right; breaker 3 of 4 |
| Across T3/T4 | 4 | +1.0, not enough yet (1); 100% right; breaker 1 of 1 | +1.0, not enough yet (1); 100% right; breaker 1 of 1 |
| Across T4/T5 | 4 | +5.8, not enough yet (8); 62% right; breaker 2 of 4 | +1.3, not enough yet (17); 47% right; breaker 2 of 4 |

### The flag test (positive: VALUE outscored its partners / PRICEY lagged them)

| Tier | VALUE | PRICEY |
|---|---|---|
| T1 | - | +16.7, not enough yet (6) |
| T2 | +13.5, not enough yet (4) | -1.5, not enough yet (14) |
| T3/T4 (middle) | +4.5, not enough yet (34) | +6.8 (+3.8 to +9.4), 43 pairs, LEAN + |
| T3 | -4.5, not enough yet (10) | -1.4, not enough yet (10) |
| T4 | +8.9, not enough yet (19) | +6.7, not enough yet (19) |
| T5 | +2.4 (+0.4 to +4.6), 55 pairs, LEAN + | - |
| Across T1/T2 | +18.7, not enough yet (2) | +10.5, not enough yet (8) |
| Across T2/T3 | +1.3, not enough yet (11) | +1.4, not enough yet (9) |
| Across T3/T4 | +6.0, not enough yet (5) | +12.6, not enough yet (14) |
| Across T4/T5 | -0.5, not enough yet (32) | -1.1, not enough yet (18) |

### Each source inside the tier (error = mean |actual - projection|; bias = actual - projection; rank correlation per slate, averaged)

| Tier | Ours | ADP |
|---|---|---|
| T1 | err 11.2, bias -8.8, rank corr 0.40 (1 slates) | rank corr 0.20 (1 slates) |
| T2 | err 10.9, bias -6.1, rank corr 0.05 (4 slates) | rank corr 0.35 (4 slates) |
| T3/T4 | err 8.7, bias -5.1, rank corr 0.36 (4 slates) | rank corr 0.35 (4 slates) |
| T5 (priced) | err 11.7, bias -3.4, rank corr 0.18 (4 slates) | rank corr 0.13 (4 slates) |

## 4-drafter PM (small slates)

### Your board against each source

| Tier | Nights | ETR | Ours PM | ADP |
|---|---|---|---|---|
| T1 | 4 | -13.9, not enough yet (1); 0% right; breaker 0 of 1 | -10.1, not enough yet (2); 0% right; breaker 0 of 1 | -6.4, not enough yet (1); 0% right |
| T2 | 4 | +3.3, not enough yet (7); 57% right; breaker 0 of 1 | +8.7, not enough yet (12); 75% right; breaker 3 of 3 | -4.1, not enough yet (15); 40% right; breaker 2 of 3 |
| T3/T4 (middle) | 4 | -1.9, not enough yet (14); 43% right; breaker 3 of 6 | +2.7, not enough yet (20); 70% right; breaker 7 of 8 | +4.3, not enough yet (37); 81% right; breaker 12 of 14 |
| T3 | 4 | -10.5, not enough yet (4); 25% right; breaker 1 of 3 | +0.2, not enough yet (5); 60% right; breaker 1 of 2 | -2.7, not enough yet (7); 57% right; breaker 2 of 2 |
| T4 | 4 | -0.5, not enough yet (9); 44% right; breaker 1 of 2 | +1.2, not enough yet (14); 71% right; breaker 5 of 5 | +6.6, not enough yet (23); 87% right; breaker 9 of 10 |
| T5 | 4 | +2.8, not enough yet (22); 59% right; breaker 1 of 2 | +0.3 (-11.7 to +4.0), 48 pairs, no lean; 58% right; breaker 20 of 23 | -0.1 (-2.5 to +8.7), 44 pairs, no lean; 50% right; breaker 10 of 11 |
| Across T1/T2 | 4 | - | -13.2, not enough yet (1); 0% right; breaker 0 of 1 | - |
| Across T2/T3 | 4 | -3.2, not enough yet (2); 50% right | +4.0, not enough yet (5); 60% right; breaker 3 of 4 | +8.6, not enough yet (7); 71% right; breaker 3 of 4 |
| Across T3/T4 | 4 | +19.4, not enough yet (1); 100% right; breaker 1 of 1 | +36.3, not enough yet (1); 100% right; breaker 1 of 1 | +3.8, not enough yet (7); 86% right; breaker 1 of 2 |
| Across T4/T5 | 4 | -8.3, not enough yet (3); 33% right; breaker 0 of 1 | +5.4, not enough yet (7); 71% right; breaker 4 of 4 | +1.8, not enough yet (9); 56% right; breaker 3 of 4 |

### The flag test (positive: VALUE outscored its partners / PRICEY lagged them)

| Tier | VALUE | PRICEY |
|---|---|---|
| T1 | - | +18.0, not enough yet (5) |
| T2 | - | +1.2, not enough yet (16) |
| T3/T4 (middle) | -1.2, not enough yet (25) | +6.3, not enough yet (34) |
| T3 | +2.3, not enough yet (6) | +10.5, not enough yet (7) |
| T4 | -2.3, not enough yet (11) | +3.4, not enough yet (20) |
| T5 | +6.7, not enough yet (21) | - |
| Across T1/T2 | - | +11.2, not enough yet (6) |
| Across T2/T3 | +15.6, not enough yet (6) | +10.5, not enough yet (13) |
| Across T3/T4 | -2.3, not enough yet (8) | +10.4, not enough yet (7) |
| Across T4/T5 | +8.4, not enough yet (7) | -0.2, not enough yet (18) |

### Each source inside the tier (error = mean |actual - projection|; bias = actual - projection; rank correlation per slate, averaged)

| Tier | ETR | Ours PM | ADP |
|---|---|---|---|
| T1 | err 11.2, bias -9.3, rank corr 0.40 (1 slates) | err 11.2, bias -8.8, rank corr 0.40 (1 slates) | rank corr 0.20 (1 slates) |
| T2 | err 11.5, bias -7.8, rank corr 0.23 (4 slates) | err 11.9, bias -8.1, rank corr 0.08 (3 slates) | rank corr 0.44 (4 slates) |
| T3/T4 | err 8.4, bias -5.4, rank corr 0.64 (4 slates) | err 7.7, bias -3.4, rank corr 0.41 (3 slates) | rank corr 0.41 (4 slates) |
| T5 (priced) | err 10.9, bias -3.5, rank corr 0.21 (4 slates) | err 12.6, bias -3.5, rank corr 0.05 (3 slates) | rank corr 0.07 (4 slates) |

## How many of these could be chance

199 cells were graded (67 with 40+ pairs, so testable). The 80% LEAN bar means about 80% of resamples on one side, which a cell with no real effect clears about 40% of the time (|mean| at least 0.84 standard errors, either side). So with 67 testable cells, about 27 leans would appear by chance alone; 29 did. Treat any single lean as a candidate, and weigh the ones that repeat in both windows or across tiers.

## Leans under the evidence policy (2026-11-09)

A lean is ADOPTED (used as a tiebreak) only if it holds in both windows (the same test, tier and side in the AM primary sample and in PM), was listed as a candidate before testing, or hit the RULE numbers and waits on its check; every other lean is a CANDIDATE, forward-tested only. Adopted leans are recorded in leans.json.

| Cut | Tier | Test | Pairs | Label | Policy |
|---|---|---|---|---|---|
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T2 | your board vs Ours | 41 | LEAN + | CANDIDATE |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T3/T4 (middle) | your board vs Ours | 67 | LEAN - | CANDIDATE |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T5 | your board vs Ours | 100 | LEAN + | CANDIDATE |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T5 | your board vs ADP | 365 | LEAN - (RULE numbers, check pending) | ADOPTED (both windows) |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T3/T4 (middle) | VALUE flag | 167 | LEAN + | ADOPTED (both windows) |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T4 | VALUE flag | 73 | LEAN + | ADOPTED (both windows) |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T5 | VALUE flag | 342 | LEAN + (RULE numbers, check pending) | ADOPTED (both windows) |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T2 | your board vs Ours | 63 | LEAN + | CONTEXT (secondary AM sample, not adopted on its own) |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T3/T4 (middle) | your board vs Ours | 104 | LEAN + (RULE numbers, check pending) | CONTEXT (secondary AM sample, not adopted on its own) |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T3 | your board vs Ours | 41 | LEAN + | CONTEXT (secondary AM sample, not adopted on its own) |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T2 | PRICEY flag | 69 | LEAN - | CONTEXT (secondary AM sample, not adopted on its own) |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T3/T4 (middle) | VALUE flag | 124 | LEAN - (RULE numbers, check pending) | CONTEXT (secondary AM sample, not adopted on its own) |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T4 | VALUE flag | 49 | LEAN - | CONTEXT (secondary AM sample, not adopted on its own) |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T5 | VALUE flag | 243 | LEAN + (RULE numbers, check pending) | CONTEXT (secondary AM sample, not adopted on its own) |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | Across T4/T5 | VALUE flag | 93 | LEAN + | CONTEXT (secondary AM sample, not adopted on its own) |
| 6-drafter PM | T2 | your board vs ADP | 106 | LEAN + | CANDIDATE |
| 6-drafter PM | T3/T4 (middle) | your board vs ETR | 113 | LEAN + | CANDIDATE |
| 6-drafter PM | T3/T4 (middle) | your board vs ADP | 244 | RULE + | RULE |
| 6-drafter PM | T3 | your board vs ADP | 119 | RULE + | RULE |
| 6-drafter PM | T5 | your board vs ADP | 728 | RULE - | ADOPTED (both windows) |
| 6-drafter PM | T2 | PRICEY flag | 92 | LEAN + | CANDIDATE |
| 6-drafter PM | T3/T4 (middle) | VALUE flag | 253 | LEAN + | ADOPTED (both windows) |
| 6-drafter PM | T3 | VALUE flag | 90 | LEAN + | CANDIDATE |
| 6-drafter PM | T3 | PRICEY flag | 101 | LEAN + | CANDIDATE |
| 6-drafter PM | T4 | VALUE flag | 102 | LEAN + | ADOPTED (both windows) |
| 6-drafter PM | T4 | PRICEY flag | 99 | LEAN - | CANDIDATE |
| 6-drafter PM | T5 | VALUE flag | 512 | LEAN + | ADOPTED (both windows) |
| 4-drafter AM (small slates) | T3/T4 (middle) | PRICEY flag | 43 | LEAN + | CANDIDATE |
| 4-drafter AM (small slates) | T5 | VALUE flag | 55 | LEAN + | CANDIDATE |

## The RULE bar, part by part

| Cut | Tier | Test | Pairs | Label | Parts |
|---|---|---|---|---|---|
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T5 | your board vs ADP | 365 | LEAN - (RULE numbers, check pending) | 80+ pairs: yes; 90% range clear of 0: yes; check slates: can't yet (7 slates, needs 14); drop one player: holds |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T5 | VALUE flag | 342 | LEAN + (RULE numbers, check pending) | 80+ pairs: yes; 90% range clear of 0: yes; check slates: can't yet (6 slates, needs 14); drop one player: holds |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T3/T4 (middle) | your board vs Ours | 104 | LEAN + (RULE numbers, check pending) | 80+ pairs: yes; 90% range clear of 0: yes; check slates: can't yet (6 slates, needs 14); drop one player: holds |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T3/T4 (middle) | VALUE flag | 124 | LEAN - (RULE numbers, check pending) | 80+ pairs: yes; 90% range clear of 0: yes; check slates: can't yet (7 slates, needs 14); drop one player: holds |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T5 | VALUE flag | 243 | LEAN + (RULE numbers, check pending) | 80+ pairs: yes; 90% range clear of 0: yes; check slates: can't yet (6 slates, needs 14); drop one player: holds |
| 6-drafter PM | T3/T4 (middle) | your board vs ADP | 244 | RULE + | 80+ pairs: yes; 90% range clear of 0: yes; check slates (last 5) same side: yes; drop one player: holds |
| 6-drafter PM | T3 | your board vs ADP | 119 | RULE + | 80+ pairs: yes; 90% range clear of 0: yes; check slates (last 5) same side: yes; drop one player: holds |
| 6-drafter PM | T5 | your board vs ADP | 728 | RULE - | 80+ pairs: yes; 90% range clear of 0: yes; check slates (last 5) same side: yes; drop one player: holds |
