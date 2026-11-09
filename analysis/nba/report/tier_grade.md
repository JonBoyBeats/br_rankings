# NBA grade by combined tier

Written by scripts/nba_tier_grade.py from tier_history.csv. Decision pairs (same tier, ADP within 4 at the lock); a player who sat is scored with his swap. Each cell: points per pair (80% range from resampling slates), pairs, and the evidence level. Head to head: positive = your board beat the source on the pairs you ordered differently.

## 6-drafter AM, primary (Lock AM on our Proj, 10-28 on)

### Your board against each source

| Tier | Nights | Ours | ADP |
|---|---|---|---|
| T1 | 7 | -9.8, not enough yet (3); 67% right; breaker 0 of 1 | +24.8, not enough yet (3); 100% right; breaker 3 of 3 |
| T2 | 7 | +4.1 (+1.4 to +8.0), 47 pairs, LEAN +; 64% right; breaker 9 of 13 | +1.7 (-1.9 to +4.7), 45 pairs, no lean; 51% right; breaker 7 of 11 |
| T3/T4 (middle) | 7 | -1.7 (-3.2 to -0.0), 65 pairs, LEAN -; 46% right; breaker 10 of 19 | +0.5 (-1.7 to +3.1), 146 pairs, no lean; 53% right; breaker 26 of 45 |
| T3 | 7 | -1.7, not enough yet (25); 48% right; breaker 5 of 8 | -1.0 (-3.0 to +1.0), 45 pairs, no lean; 56% right; breaker 10 of 13 |
| T4 | 7 | -2.1, not enough yet (35); 46% right; breaker 4 of 10 | +1.1 (-2.0 to +4.3), 78 pairs, no lean; 56% right; breaker 15 of 27 |
| T5 | 7 | +4.0 (-2.0 to +8.1), 92 pairs, LEAN +; 59% right; breaker 22 of 38 | -2.7 (-3.8 to -1.4), 356 pairs, LEAN - (RULE numbers, check pending); 44% right; breaker 63 of 133 |
| Across T1/T2 | 7 | +13.2, not enough yet (2); 100% right | - |
| Across T2/T3 | 7 | -1.6, not enough yet (9); 44% right; breaker 1 of 4 | +1.1, not enough yet (14); 64% right; breaker 2 of 7 |
| Across T3/T4 | 7 | +1.6, not enough yet (5); 40% right; breaker 1 of 1 | +1.6, not enough yet (23); 39% right; breaker 1 of 5 |
| Across T4/T5 | 7 | -5.5, not enough yet (9); 44% right; breaker 0 of 3 | -3.3 (-6.6 to -0.5), 67 pairs, LEAN -; 34% right; breaker 7 of 19 |

### The flag test (positive: VALUE outscored its partners / PRICEY lagged them)

| Tier | VALUE | PRICEY |
|---|---|---|
| T1 | - | +1.8, not enough yet (8) |
| T2 | -1.1, not enough yet (7) | +3.5 (-2.2 to +9.1), 42 pairs, no lean |
| T3/T4 (middle) | +1.4 (-1.5 to +4.7), 171 pairs, no lean | -1.6 (-3.0 to +0.3), 202 pairs, LEAN - |
| T3 | +1.5 (-5.1 to +7.5), 57 pairs, no lean | -2.9 (-6.8 to +1.8), 58 pairs, no lean |
| T4 | +3.3 (+0.3 to +5.5), 72 pairs, LEAN + | +0.8 (-2.5 to +3.5), 87 pairs, no lean |
| T5 | +5.6 (+3.8 to +7.8), 344 pairs, LEAN + (RULE numbers, check pending) | - |
| Across T1/T2 | -18.6, not enough yet (7) | +2.6, not enough yet (11) |
| Across T2/T3 | -4.8, not enough yet (18) | +0.3, not enough yet (31) |
| Across T3/T4 | -1.8 (-9.2 to +5.9), 42 pairs, no lean | -3.7 (-8.4 to +1.9), 57 pairs, LEAN - |
| Across T4/T5 | +1.2 (-3.6 to +6.0), 258 pairs, no lean | -0.4, not enough yet (37) |

### Each source inside the tier (error = mean |actual - projection|; bias = actual - projection; rank correlation per slate, averaged)

| Tier | Ours | ADP |
|---|---|---|
| T1 | err 13.6, bias -9.4, rank corr 0.20 (4 slates) | rank corr 0.20 (4 slates) |
| T2 | err 11.4, bias -8.0, rank corr 0.12 (7 slates) | rank corr 0.19 (7 slates) |
| T3/T4 | err 11.9, bias -9.6, rank corr 0.07 (7 slates) | rank corr 0.07 (7 slates) |
| T5 (priced) | err 9.4, bias -5.3, rank corr 0.44 (7 slates) | rank corr 0.35 (7 slates) |

## 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board)

### Your board against each source

| Tier | Nights | Ours | ADP |
|---|---|---|---|
| T1 | 7 | -15.4, not enough yet (6); 17% right; breaker 0 of 2 | -21.0, not enough yet (3); 0% right; breaker 0 of 1 |
| T2 | 7 | +5.5, not enough yet (37); 59% right; breaker 7 of 11 | +2.6 (+1.0 to +4.2), 44 pairs, LEAN +; 59% right; breaker 12 of 13 |
| T3/T4 (middle) | 7 | +4.4 (+1.6 to +7.8), 54 pairs, LEAN +; 70% right; breaker 8 of 14 | +0.1 (-3.1 to +3.9), 62 pairs, no lean; 47% right; breaker 11 of 18 |
| T3 | 7 | +0.9, not enough yet (19); 63% right; breaker 0 of 4 | +1.9, not enough yet (25); 56% right; breaker 4 of 6 |
| T4 | 7 | +8.6, not enough yet (20); 85% right; breaker 6 of 7 | -6.1, not enough yet (20); 25% right; breaker 3 of 8 |
| T5 | 7 | +0.5 (-0.4 to +2.1), 147 pairs, no lean; 50% right; breaker 21 of 29 | +0.1 (-1.3 to +1.4), 246 pairs, no lean; 50% right; breaker 33 of 53 |
| Across T1/T2 | 7 | -7.7, not enough yet (4); 25% right | -7.7, not enough yet (4); 25% right |
| Across T2/T3 | 7 | +17.0, not enough yet (7); 86% right; breaker 5 of 5 | +16.5, not enough yet (4); 75% right; breaker 2 of 2 |
| Across T3/T4 | 7 | +3.3, not enough yet (15); 60% right; breaker 2 of 3 | +4.6, not enough yet (17); 59% right; breaker 4 of 4 |
| Across T4/T5 | 7 | +1.7, not enough yet (38); 63% right; breaker 8 of 8 | +2.3, not enough yet (36); 64% right; breaker 8 of 8 |

### The flag test (positive: VALUE outscored its partners / PRICEY lagged them)

| Tier | VALUE | PRICEY |
|---|---|---|
| T1 | - | +2.4, not enough yet (24) |
| T2 | - | -2.2 (-5.6 to +1.0), 70 pairs, no lean |
| T3/T4 (middle) | -3.4 (-4.9 to -1.9), 135 pairs, LEAN - (RULE numbers, check pending) | -1.1 (-3.7 to +1.1), 132 pairs, no lean |
| T3 | +1.2 (-1.7 to +4.2), 41 pairs, no lean | -2.4, not enough yet (36) |
| T4 | -7.1 (-10.0 to -3.9), 55 pairs, LEAN - | -2.4, not enough yet (36) |
| T5 | +3.2 (+1.8 to +4.4), 268 pairs, LEAN + (RULE numbers, check pending) | - |
| Across T1/T2 | - | -0.1, not enough yet (23) |
| Across T2/T3 | -0.6, not enough yet (8) | -0.0, not enough yet (33) |
| Across T3/T4 | -3.0, not enough yet (39) | +0.5 (-2.3 to +3.5), 60 pairs, no lean |
| Across T4/T5 | +4.2 (+0.1 to +7.7), 111 pairs, LEAN + | -0.1, not enough yet (22) |

### Each source inside the tier (error = mean |actual - projection|; bias = actual - projection; rank correlation per slate, averaged)

| Tier | Ours | ADP |
|---|---|---|
| T1 | err 10.1, bias -4.1, rank corr 0.35 (4 slates) | rank corr 0.42 (4 slates) |
| T2 | err 9.3, bias -1.0, rank corr 0.15 (7 slates) | rank corr 0.33 (7 slates) |
| T3/T4 | err 9.8, bias -2.5, rank corr -0.17 (7 slates) | rank corr 0.17 (7 slates) |
| T5 (priced) | err 8.7, bias -1.1, rank corr 0.26 (7 slates) | rank corr 0.19 (7 slates) |

## 6-drafter PM

### Your board against each source

| Tier | Nights | ETR | Ours PM | ADP |
|---|---|---|---|---|
| T1 | 14 | -11.2, not enough yet (4); 25% right; breaker 0 of 1 | -4.0, not enough yet (6); 33% right; breaker 1 of 3 | +9.5, not enough yet (9); 67% right; breaker 4 of 4 |
| T2 | 14 | -1.5 (-4.1 to +1.1), 77 pairs, no lean; 49% right; breaker 13 of 28 | -0.1 (-2.1 to +2.3), 52 pairs, no lean; 52% right; breaker 13 of 23 | +2.3 (-0.2 to +4.6), 106 pairs, LEAN +; 55% right; breaker 31 of 38 |
| T3/T4 (middle) | 14 | +2.8 (+0.4 to +4.9), 113 pairs, LEAN +; 63% right; breaker 19 of 32 | +0.3 (-2.6 to +3.0), 114 pairs, no lean; 54% right; breaker 16 of 36 | +2.8 (+0.8 to +4.9), 245 pairs, RULE +; 59% right; breaker 38 of 68 |
| T3 | 14 | +1.1 (-1.5 to +4.2), 51 pairs, no lean; 57% right; breaker 9 of 12 | +5.0, not enough yet (24); 54% right; breaker 5 of 6 | +5.5 (+2.6 to +8.3), 119 pairs, RULE +; 61% right; breaker 25 of 32 |
| T4 | 14 | +1.9 (-2.2 to +4.6), 49 pairs, no lean; 59% right; breaker 5 of 15 | -1.9 (-4.5 to +1.4), 62 pairs, no lean; 50% right; breaker 4 of 18 | -0.7 (-2.6 to +1.1), 105 pairs, no lean; 53% right; breaker 9 of 29 |
| T5 | 14 | -1.2 (-3.1 to +1.2), 268 pairs, no lean; 50% right; breaker 39 of 92 | -0.7 (-2.2 to +1.0), 286 pairs, no lean; 47% right; breaker 38 of 95 | -2.2 (-3.7 to -0.6), 728 pairs, RULE -; 44% right; breaker 99 of 229 |
| Across T1/T2 | 14 | +2.3, not enough yet (3); 33% right | - | -19.8, not enough yet (2); 0% right |
| Across T2/T3 | 14 | +7.2, not enough yet (18); 72% right; breaker 1 of 2 | +6.1, not enough yet (15); 67% right; breaker 3 of 4 | -1.2, not enough yet (23); 57% right; breaker 0 of 3 |
| Across T3/T4 | 14 | +12.5, not enough yet (13); 100% right; breaker 5 of 5 | +1.4, not enough yet (28); 61% right; breaker 7 of 12 | +4.3, not enough yet (21); 76% right; breaker 4 of 7 |
| Across T4/T5 | 14 | -4.5, not enough yet (24); 38% right; breaker 1 of 10 | -8.5, not enough yet (19); 21% right; breaker 2 of 6 | -1.3 (-6.0 to +3.2), 52 pairs, no lean; 48% right; breaker 15 of 28 |

### The flag test (positive: VALUE outscored its partners / PRICEY lagged them)

| Tier | VALUE | PRICEY |
|---|---|---|
| T1 | - | +9.9, not enough yet (33) |
| T2 | +4.8, not enough yet (6) | +3.1 (-0.0 to +6.2), 92 pairs, LEAN + |
| T3/T4 (middle) | +2.8 (-0.1 to +5.9), 254 pairs, LEAN + | +0.6 (-2.3 to +3.8), 230 pairs, no lean |
| T3 | +6.7 (-0.1 to +13.3), 90 pairs, LEAN + | +5.8 (+1.1 to +10.2), 101 pairs, LEAN + |
| T4 | +1.9 (-0.4 to +4.5), 103 pairs, LEAN + | -3.2 (-7.2 to +1.3), 99 pairs, LEAN - |
| T5 | +3.5 (+0.7 to +6.1), 512 pairs, LEAN + | - |
| Across T1/T2 | -16.4, not enough yet (6) | -3.0, not enough yet (35) |
| Across T2/T3 | -5.7, not enough yet (33) | -2.0 (-7.1 to +2.6), 64 pairs, no lean |
| Across T3/T4 | -1.7 (-4.5 to +2.3), 61 pairs, no lean | -4.4, not enough yet (30) |
| Across T4/T5 | -0.6 (-5.0 to +4.0), 173 pairs, no lean | -5.6 (-10.7 to +3.8), 40 pairs, no lean |

### Each source inside the tier (error = mean |actual - projection|; bias = actual - projection; rank correlation per slate, averaged)

| Tier | ETR | Ours PM | ADP |
|---|---|---|---|
| T1 | err 11.2, bias -8.4, rank corr 0.54 (7 slates) | err 12.2, bias -7.7, rank corr 0.47 (4 slates) | rank corr 0.42 (7 slates) |
| T2 | err 10.8, bias -7.2, rank corr 0.17 (14 slates) | err 10.0, bias -7.0, rank corr 0.14 (6 slates) | rank corr 0.14 (14 slates) |
| T3/T4 | err 11.6, bias -9.0, rank corr 0.02 (14 slates) | err 12.1, bias -9.4, rank corr 0.01 (6 slates) | rank corr 0.03 (14 slates) |
| T5 (priced) | err 9.7, bias -6.0, rank corr 0.39 (14 slates) | err 9.5, bias -5.2, rank corr 0.36 (6 slates) | rank corr 0.27 (14 slates) |

## 4-drafter AM (small slates)

### Your board against each source

| Tier | Nights | Ours | ADP |
|---|---|---|---|
| T1 | 4 | -13.9, not enough yet (1); 0% right; breaker 0 of 1 | - |
| T2 | 4 | +1.3, not enough yet (4); 75% right; breaker 1 of 2 | -8.8, not enough yet (10); 20% right; breaker 1 of 4 |
| T3/T4 (middle) | 4 | +6.2, not enough yet (5); 60% right; breaker 2 of 3 | +4.4, not enough yet (26); 73% right; breaker 8 of 10 |
| T3 | 4 | +8.5, not enough yet (3); 67% right; breaker 1 of 2 | -12.1, not enough yet (4); 25% right; breaker 1 of 2 |
| T4 | 4 | +2.7, not enough yet (2); 50% right; breaker 1 of 1 | +7.4, not enough yet (22); 82% right; breaker 7 of 8 |
| T5 | 4 | +1.4, not enough yet (16); 50% right; breaker 3 of 5 | +2.0 (-2.0 to +10.0), 66 pairs, no lean; 53% right; breaker 10 of 23 |
| Across T1/T2 | 4 | - | - |
| Across T2/T3 | 4 | -5.5, not enough yet (3); 33% right; breaker 1 of 2 | +0.5, not enough yet (8); 50% right; breaker 3 of 4 |
| Across T3/T4 | 4 | - | - |
| Across T4/T5 | 4 | +7.4, not enough yet (7); 71% right; breaker 2 of 4 | -6.1, not enough yet (11); 18% right; breaker 0 of 2 |

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
| T5 (priced) | err 11.6, bias -3.3, rank corr 0.21 (4 slates) | rank corr 0.16 (4 slates) |

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

197 cells were graded (65 with 40+ pairs, so testable). The 80% LEAN bar means about 80% of resamples on one side, which a cell with no real effect clears about 40% of the time (|mean| at least 0.84 standard errors, either side). So with 65 testable cells, about 26 leans would appear by chance alone; 29 did. Treat any single lean as a candidate, and weigh the ones that repeat in both windows or across tiers.

## Leans under the evidence policy (2026-11-09)

A lean is ADOPTED (used as a tiebreak) only if it holds in both windows (the same test, tier and side in the AM primary sample and in PM), was listed as a candidate before testing, or hit the RULE numbers and waits on its check; every other lean is a CANDIDATE, forward-tested only. Adopted leans are recorded in leans.json.

| Cut | Tier | Test | Pairs | Label | Policy |
|---|---|---|---|---|---|
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T2 | your board vs Ours | 47 | LEAN + | CANDIDATE |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T3/T4 (middle) | your board vs Ours | 65 | LEAN - | CANDIDATE |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T5 | your board vs Ours | 92 | LEAN + | CANDIDATE |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T5 | your board vs ADP | 356 | LEAN - (RULE numbers, check pending) | ADOPTED (both windows) |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | Across T4/T5 | your board vs ADP | 67 | LEAN - | CANDIDATE |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T3/T4 (middle) | PRICEY flag | 202 | LEAN - | CANDIDATE |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T4 | VALUE flag | 72 | LEAN + | ADOPTED (both windows) |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T5 | VALUE flag | 344 | LEAN + (RULE numbers, check pending) | ADOPTED (both windows) |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | Across T3/T4 | PRICEY flag | 57 | LEAN - | CANDIDATE |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T2 | your board vs ADP | 44 | LEAN + | CONTEXT (secondary AM sample, not adopted on its own) |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T3/T4 (middle) | your board vs Ours | 54 | LEAN + | CONTEXT (secondary AM sample, not adopted on its own) |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T3/T4 (middle) | VALUE flag | 135 | LEAN - (RULE numbers, check pending) | CONTEXT (secondary AM sample, not adopted on its own) |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T4 | VALUE flag | 55 | LEAN - | CONTEXT (secondary AM sample, not adopted on its own) |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T5 | VALUE flag | 268 | LEAN + (RULE numbers, check pending) | CONTEXT (secondary AM sample, not adopted on its own) |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | Across T4/T5 | VALUE flag | 111 | LEAN + | CONTEXT (secondary AM sample, not adopted on its own) |
| 6-drafter PM | T2 | your board vs ADP | 106 | LEAN + | CANDIDATE |
| 6-drafter PM | T3/T4 (middle) | your board vs ETR | 113 | LEAN + | CANDIDATE |
| 6-drafter PM | T3/T4 (middle) | your board vs ADP | 245 | RULE + | RULE |
| 6-drafter PM | T3 | your board vs ADP | 119 | RULE + | RULE |
| 6-drafter PM | T5 | your board vs ADP | 728 | RULE - | ADOPTED (both windows) |
| 6-drafter PM | T2 | PRICEY flag | 92 | LEAN + | CANDIDATE |
| 6-drafter PM | T3/T4 (middle) | VALUE flag | 254 | LEAN + | CANDIDATE |
| 6-drafter PM | T3 | VALUE flag | 90 | LEAN + | CANDIDATE |
| 6-drafter PM | T3 | PRICEY flag | 101 | LEAN + | CANDIDATE |
| 6-drafter PM | T4 | VALUE flag | 103 | LEAN + | ADOPTED (both windows) |
| 6-drafter PM | T4 | PRICEY flag | 99 | LEAN - | CANDIDATE |
| 6-drafter PM | T5 | VALUE flag | 512 | LEAN + | ADOPTED (both windows) |
| 4-drafter AM (small slates) | T3/T4 (middle) | PRICEY flag | 43 | LEAN + | CANDIDATE |
| 4-drafter AM (small slates) | T5 | VALUE flag | 55 | LEAN + | CANDIDATE |

## The RULE bar, part by part

| Cut | Tier | Test | Pairs | Label | Parts |
|---|---|---|---|---|---|
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T5 | your board vs ADP | 356 | LEAN - (RULE numbers, check pending) | 80+ pairs: yes; 90% range clear of 0: yes; check slates: can't yet (7 slates, needs 14); drop one player: holds |
| 6-drafter AM, primary (Lock AM on our Proj, 10-28 on) | T5 | VALUE flag | 344 | LEAN + (RULE numbers, check pending) | 80+ pairs: yes; 90% range clear of 0: yes; check slates: can't yet (6 slates, needs 14); drop one player: holds |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T3/T4 (middle) | VALUE flag | 135 | LEAN - (RULE numbers, check pending) | 80+ pairs: yes; 90% range clear of 0: yes; check slates: can't yet (7 slates, needs 14); drop one player: holds |
| 6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board) | T5 | VALUE flag | 268 | LEAN + (RULE numbers, check pending) | 80+ pairs: yes; 90% range clear of 0: yes; check slates: can't yet (6 slates, needs 14); drop one player: holds |
| 6-drafter PM | T3/T4 (middle) | your board vs ADP | 245 | RULE + | 80+ pairs: yes; 90% range clear of 0: yes; check slates (last 5) same side: yes; drop one player: holds |
| 6-drafter PM | T3 | your board vs ADP | 119 | RULE + | 80+ pairs: yes; 90% range clear of 0: yes; check slates (last 5) same side: yes; drop one player: holds |
| 6-drafter PM | T5 | your board vs ADP | 728 | RULE - | 80+ pairs: yes; 90% range clear of 0: yes; check slates (last 5) same side: yes; drop one player: holds |
