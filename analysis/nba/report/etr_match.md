# Our morning Proj vs ETR's final upload, against ADP

Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's last upload before lock (its first carries a random multiplier); the top 60 by ADP graded (40 on a 4-drafter slate), in four groups: the elite (ETR's top 2-4, cut at the biggest drop), then next / middle / 6th round on by morning ADP: under 19, 19-31 and 32 on with 6 drafters; under 13, 13-20 and 21 on with 4. 15 slates, 2026-10-28 to 2026-11-12. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board averages their last 3 ETR nights from 2026-11-07.

## Season

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 43 | 0.79 | 29/30 (97%) | 19/19 (100%) | - | 11 (26%) | 0.07 / 0.09 | - (0) |
| next | 199 | 0.61 | 78/96 (81%) | 9/9 (100%) | 12/15 (80%) | 51 (26%) | 0.20 / 0.56 | +1.1 (10) |
| middle | 179 | 0.64 | 61/67 (91%) | 5/6 (83%) | 8/8 (100%) | 40 (22%) | 0.24 / 0.58 | +2.3 (19) |
| 6th round on | 416 | 0.82 | 204/235 (87%) | 37/41 (90%) | 52/52 (100%) | 102 (25%) | 0.14 / 0.26 | +1.3 (20) |
| **all** | 837 | 0.78 | 372/428 (87%) | 70/75 (93%) | 72/75 (96%) | 204 (24%) | 0.15 / 0.33 | +1.7 (49) |

## Last 7 slates

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 18 | 0.69 | 14/14 (100%) | 8/8 (100%) | - | 5 (28%) | -0.07 / 0.08 | - (0) |
| next | 100 | 0.67 | 44/53 (83%) | 4/4 (100%) | 5/6 (83%) | 24 (24%) | 0.21 / 0.57 | -0.7 (4) |
| middle | 92 | 0.69 | 29/32 (91%) | 3/3 (100%) | 3/3 (100%) | 20 (22%) | 0.25 / 0.61 | +1.2 (9) |
| 6th round on | 207 | 0.85 | 111/124 (90%) | 19/20 (95%) | 26/26 (100%) | 52 (25%) | 0.14 / 0.27 | +0.6 (14) |
| **all** | 417 | 0.81 | 198/223 (89%) | 34/35 (97%) | 34/35 (97%) | 101 (24%) | 0.15 / 0.32 | +0.6 (27) |

## Rookies (no last season), before and after the last-3 average

| | n | ETR minus ours | big misses |
|---|---|---|---|
| before 2026-11-07 | 25 | +2.78 | 9 |
| from 2026-11-07 | 24 | +0.51 | 7 |

## By slate

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| 2026-10-28 (6 drafters) | 60 | 0.79 | 20/22 (91%) | 4/5 (80%) | 5/5 (100%) | 15 (25%) | 0.07 / 0.38 | +4.8 (3) |
| 2026-10-29 (4 drafters) | 40 | 0.79 | 18/21 (86%) | 4/5 (80%) | 5/5 (100%) | 6 (15%) | 0.29 / 0.45 | +2.6 (2) |
| 2026-10-30 (6 drafters) | 60 | 0.81 | 30/34 (88%) | 5/5 (100%) | 5/5 (100%) | 16 (27%) | 0.35 / 0.39 | +2.7 (4) |
| 2026-10-31 (6 drafters) | 60 | 0.64 | 26/30 (87%) | 5/5 (100%) | 5/5 (100%) | 12 (20%) | 0.21 / 0.30 | +1.0 (3) |
| 2026-11-01 (4 drafters) | 40 | 0.73 | 16/20 (80%) | 5/5 (100%) | 5/5 (100%) | 12 (30%) | 0.30 / 0.37 | +2.5 (2) |
| 2026-11-02 (6 drafters) | 60 | 0.63 | 24/29 (83%) | 5/5 (100%) | 4/5 (80%) | 15 (25%) | 0.14 / 0.34 | +3.0 (4) |
| 2026-11-04 (6 drafters) | 60 | 0.54 | 21/25 (84%) | 4/5 (80%) | 4/5 (80%) | 18 (30%) | 0.02 / 0.47 | +4.4 (3) |
| 2026-11-05 (4 drafters) | 40 | 0.80 | 19/24 (79%) | 4/5 (80%) | 5/5 (100%) | 9 (22%) | 0.31 / 0.30 | +1.5 (1) |
| 2026-11-06 (6 drafters) | 60 | 0.85 | 24/28 (86%) | 5/5 (100%) | 5/5 (100%) | 10 (17%) | 0.13 / 0.21 | +1.2 (3) |
| 2026-11-07 (6 drafters) | 60 | 0.86 | 34/36 (94%) | 5/5 (100%) | 5/5 (100%) | 14 (23%) | 0.34 / 0.39 | +0.0 (4) |
| 2026-11-08 (6 drafters) | 57 | 0.84 | 30/34 (88%) | 5/5 (100%) | 5/5 (100%) | 19 (33%) | 0.14 / 0.40 | +0.6 (5) |
| 2026-11-09 (6 drafters) | 60 | 0.81 | 33/36 (92%) | 4/5 (80%) | 5/5 (100%) | 15 (25%) | 0.04 / 0.30 | +0.6 (3) |
| 2026-11-10 (6 drafters) | 60 | 0.88 | 25/29 (86%) | 5/5 (100%) | 5/5 (100%) | 12 (20%) | 0.12 / 0.28 | +1.1 (4) |
| 2026-11-11 (6 drafters) | 60 | 0.80 | 28/31 (90%) | 5/5 (100%) | 5/5 (100%) | 13 (22%) | 0.07 / 0.30 | +0.8 (6) |
| 2026-11-12 (6 drafters) | 60 | 0.62 | 24/29 (83%) | 5/5 (100%) | 4/5 (80%) | 18 (30%) | 0.07 / 0.43 | -0.9 (2) |

## Biggest misses, 2026-11-12

| player | ADP | ours vs ADP | ETR vs ADP | usual min | min | tag |
|---|---|---|---|---|---|---|
| Max Christie DAL | 35.9 | -0.9 | -12.4 | 19.8 | 7.0 |  |
| Walter Clayton Jr. DAL | 36.0 | -9.0 | +0.1 | 16.5 | 22.0 |  |
| Paul Reed DET | 16.7 | +1.4 | -7.0 | 26.0 | 38.0 |  |
| Daniss Jenkins DET | 23.5 | -4.9 | +1.7 | 25.9 | 42.0 |  |
| Moussa Diabate CHA | 33.7 | +8.1 | +2.0 | 25.6 | 32.0 | Probable |
| VJ Edgecombe PHI | 17.0 | -9.5 | -3.7 | 33.2 | 36.0 |  |
| Naji Marshall DAL | 36.0 | +12.9 | +7.4 | 22.0 | 23.0 |  |
| Zaccharie Risacher DAL | 35.9 | +1.6 | -3.4 | 24.0 | 25.0 |  |
| Jamal Shead TOR | 35.5 | -4.9 | -0.3 | 24.8 | 22.0 |  |
| LaMelo Ball MIN | 5.3 | +1.9 | -2.6 | 27.7 | 25.0 |  |

## Missed the same way on 3+ of the last 10 slates

- Jamal Shead: ETR above ours by 11.5, 6.3, 4.6
- Domantas Sabonis: ETR below ours by 3.4, 6.8, 6.0, 6.2, 4.1
- Jeremiah Fears: ETR above ours by 4.0, 5.2, 6.7, 4.6
- Deni Avdija: ETR above ours by 3.9, 5.0, 5.7
- Ayo Dosunmu: ETR above ours by 4.0, 5.3, 4.8
- Pascal Siakam: ETR below ours by 4.6, 3.7, 3.5
- Trae Young: ETR below ours by 3.2, 4.1, 3.1
