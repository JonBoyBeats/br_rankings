# Our morning Proj vs ETR's first upload, against ADP

Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's first file. 8 slates, 2026-10-28 to 2026-11-05. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board averages their last 3 ETR nights from 2026-11-07.

## Season

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| rounds 1-2 | 84 | 0.82 | 45/47 (96%) | 7/7 (100%) | 4/4 (100%) | 21 (25%) | 0.22 / 0.39 | +1.9 (4) |
| rounds 3-6 | 168 | 0.74 | 61/74 (82%) | 5/6 (83%) | 6/6 (100%) | 44 (26%) | 0.29 / 0.49 | +3.2 (14) |
| rounds 7+ | 309 | 0.84 | 172/191 (90%) | 25/27 (93%) | 30/30 (100%) | 84 (27%) | 0.22 / 0.23 | +1.3 (14) |
| **all** | 561 | 0.82 | 278/312 (89%) | 37/40 (92%) | 40/40 (100%) | 149 (27%) | 0.16 / 0.23 | +2.2 (32) |

## Last 7 slates

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| rounds 1-2 | 72 | 0.83 | 39/40 (98%) | 7/7 (100%) | 4/4 (100%) | 17 (24%) | 0.29 / 0.45 | +1.9 (4) |
| rounds 3-6 | 144 | 0.76 | 52/63 (83%) | 5/6 (83%) | 6/6 (100%) | 37 (26%) | 0.31 / 0.52 | +3.3 (12) |
| rounds 7+ | 251 | 0.83 | 137/155 (88%) | 20/22 (91%) | 25/25 (100%) | 68 (27%) | 0.22 / 0.22 | +1.4 (11) |
| **all** | 467 | 0.81 | 228/258 (88%) | 32/35 (91%) | 35/35 (100%) | 122 (26%) | 0.19 / 0.25 | +2.3 (27) |

## Rookies (no last season), before and after the last-3 average

| | n | ETR minus ours | big misses |
|---|---|---|---|
| before 2026-11-07 | 32 | +2.23 | 13 |
| from 2026-11-07 | 0 | - | 0 |

## By slate

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| 2026-10-28 | 94 | 0.85 | 50/54 (93%) | 5/5 (100%) | 5/5 (100%) | 27 (29%) | 0.06 / 0.14 | +1.7 (5) |
| 2026-10-29 | 47 | 0.72 | 18/21 (86%) | 4/5 (80%) | 5/5 (100%) | 9 (19%) | 0.22 / 0.38 | +3.8 (4) |
| 2026-10-30 | 81 | 0.86 | 37/42 (88%) | 5/5 (100%) | 5/5 (100%) | 17 (21%) | 0.34 / 0.36 | +1.3 (4) |
| 2026-10-31 | 65 | 0.79 | 30/32 (94%) | 4/5 (80%) | 5/5 (100%) | 9 (14%) | 0.28 / 0.49 | +0.0 (4) |
| 2026-11-01 | 47 | 0.70 | 21/25 (84%) | 5/5 (100%) | 5/5 (100%) | 16 (34%) | 0.27 / 0.31 | -0.7 (3) |
| 2026-11-02 | 93 | 0.88 | 54/58 (93%) | 5/5 (100%) | 5/5 (100%) | 22 (24%) | 0.17 / 0.21 | +3.0 (5) |
| 2026-11-04 | 91 | 0.80 | 46/53 (87%) | 5/5 (100%) | 5/5 (100%) | 36 (40%) | 0.11 / 0.18 | +4.0 (5) |
| 2026-11-05 | 43 | 0.81 | 22/27 (81%) | 4/5 (80%) | 5/5 (100%) | 13 (30%) | 0.30 / 0.31 | +4.6 (2) |

## Biggest misses, 2026-11-05

| player | round | ours vs ADP | ETR vs ADP | usual min | min | tag |
|---|---|---|---|---|---|---|
| Will Richard GSW | 10 | -2.4 | +5.9 | 17.9 | 16.0 |  |
| Ryan Conwell MIA (rookie) | 11 | -6.6 | +0.7 | 5.2 | 30.0 |  |
| Goga Bitadze ORL | 10 | +2.1 | -3.8 | 6.6 | 8.0 |  |
| Jevon Carter ORL | 9 | -1.0 | -6.5 | 7.6 | 3.0 |  |
| Dru Smith MIA | 11 | -1.7 | -6.9 | 6.2 | 1.0 |  |
| Anthony Black ORL | 3 | -2.1 | +2.3 | 28.0 | 31.0 |  |
| Colin Castleton ORL | 10 | -5.3 | -9.4 | 1.6 | 2.0 |  |
| Khaman Maluach PHX | 7 | +7.9 | +4.5 | 19.5 | 22.0 |  |
| Bobby Portis MIA | 6 | +2.7 | -0.7 | 21.6 | 14.0 |  |
| Stephen Curry GSW | 1 | -3.9 | -0.6 | 29.0 | 28.0 |  |

## Missed the same way on 3+ of the last 10 slates

- Caleb Wilson: ETR above ours by 5.1, 3.1, 6.3
- Lauri Markkanen: ETR below ours by 3.2, 7.0, 3.5
- Darius Garland: ETR above ours by 4.7, 3.0, 4.6
- Paul Reed: ETR above ours by 4.6, 3.9, 3.4
