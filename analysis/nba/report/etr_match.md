# Our morning Proj vs ETR's first upload, against ADP

Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's first file; the top 60 by ADP graded (40 on a 4-drafter slate), in four groups: the elite (ETR's top 2-4, cut at the biggest drop), then next / middle / 6th round on by morning ADP: under 19, 19-31 and 32 on with 6 drafters; under 13, 13-20 and 21 on with 4. 9 slates, 2026-10-28 to 2026-11-06. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board averages their last 3 ETR nights from 2026-11-07.

## Season

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 25 | 0.82 | 20/20 (100%) | 10/10 (100%) | - | 9 (36%) | 0.20 / 0.20 | - (0) |
| next | 119 | 0.72 | 47/57 (82%) | 7/8 (88%) | 12/12 (100%) | 31 (26%) | 0.15 / 0.43 | +2.2 (6) |
| middle | 106 | 0.76 | 40/43 (93%) | 7/7 (100%) | 10/10 (100%) | 25 (24%) | 0.38 / 0.58 | +2.6 (12) |
| 6th round on | 230 | 0.83 | 102/117 (87%) | 18/20 (90%) | 23/23 (100%) | 51 (22%) | 0.15 / 0.20 | +2.2 (6) |
| **all** | 480 | 0.81 | 209/237 (88%) | 42/45 (93%) | 45/45 (100%) | 116 (24%) | 0.20 / 0.31 | +2.4 (24) |

## Last 7 slates

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 20 | 0.87 | 16/16 (100%) | 8/8 (100%) | - | 6 (30%) | 0.22 / 0.18 | - (0) |
| next | 93 | 0.71 | 40/47 (85%) | 6/6 (100%) | 9/9 (100%) | 28 (30%) | 0.10 / 0.40 | +1.9 (4) |
| middle | 86 | 0.79 | 33/35 (94%) | 7/7 (100%) | 8/8 (100%) | 20 (23%) | 0.42 / 0.63 | +2.6 (12) |
| 6th round on | 181 | 0.80 | 78/92 (85%) | 12/14 (86%) | 18/18 (100%) | 41 (23%) | 0.15 / 0.21 | +1.1 (3) |
| **all** | 380 | 0.79 | 167/190 (88%) | 33/35 (94%) | 35/35 (100%) | 95 (25%) | 0.23 / 0.32 | +2.2 (19) |

## Rookies (no last season), before and after the last-3 average

| | n | ETR minus ours | big misses |
|---|---|---|---|
| before 2026-11-07 | 24 | +2.41 | 9 |
| from 2026-11-07 | 0 | - | 0 |

## By slate

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| 2026-10-28 (6 drafters) | 60 | 0.86 | 27/30 (90%) | 5/5 (100%) | 5/5 (100%) | 18 (30%) | 0.07 / 0.19 | +3.3 (3) |
| 2026-10-29 (4 drafters) | 40 | 0.84 | 15/17 (88%) | 4/5 (80%) | 5/5 (100%) | 3 (8%) | 0.27 / 0.42 | +2.9 (2) |
| 2026-10-30 (6 drafters) | 60 | 0.85 | 26/30 (87%) | 5/5 (100%) | 5/5 (100%) | 14 (23%) | 0.40 / 0.39 | +2.2 (3) |
| 2026-10-31 (6 drafters) | 60 | 0.80 | 28/30 (93%) | 4/5 (80%) | 5/5 (100%) | 8 (13%) | 0.29 / 0.50 | +0.6 (3) |
| 2026-11-01 (4 drafters) | 40 | 0.73 | 16/20 (80%) | 5/5 (100%) | 5/5 (100%) | 12 (30%) | 0.30 / 0.37 | +2.5 (2) |
| 2026-11-02 (6 drafters) | 60 | 0.78 | 28/30 (93%) | 5/5 (100%) | 5/5 (100%) | 15 (25%) | 0.27 / 0.36 | +3.4 (4) |
| 2026-11-04 (6 drafters) | 60 | 0.70 | 25/29 (86%) | 5/5 (100%) | 5/5 (100%) | 20 (33%) | 0.19 / 0.41 | +5.2 (3) |
| 2026-11-05 (4 drafters) | 40 | 0.82 | 20/25 (80%) | 4/5 (80%) | 5/5 (100%) | 11 (28%) | 0.30 / 0.31 | +1.9 (1) |
| 2026-11-06 (6 drafters) | 60 | 0.85 | 24/26 (92%) | 5/5 (100%) | 5/5 (100%) | 15 (25%) | 0.13 / 0.16 | -0.8 (3) |

## Biggest misses, 2026-11-06

| player | ADP | ours vs ADP | ETR vs ADP | usual min | min | tag |
|---|---|---|---|---|---|---|
| Malik Monk SAC | 35.9 | -14.5 | -6.3 | 16.1 | 18.0 |  |
| Domantas Sabonis SAC | 9.2 | +2.7 | -3.5 | 36.1 | 31.0 |  |
| Kyrie Irving DAL | 11.8 | -8.4 | -3.3 | 30.0 | 28.0 |  |
| Tyrese Maxey PHI | 7.8 | -3.4 | +1.4 | 37.1 | 32.0 |  |
| Ayo Dosunmu MIN | 31.5 | -6.3 | -2.3 | 30.7 | 39.0 |  |
| Jalen Johnson ATL | 12.8 | +8.4 | +4.5 | 29.1 | 0.0 | Questionable / Questionable |
| Kyshawn George WAS | 35.7 | -5.1 | -1.3 | 32.8 | 39.0 |  |
| Luka Doncic LAL | 1.9 | +4.9 | +8.6 | 35.6 | 38.0 |  |
| Deni Avdija POR | 11.8 | -3.0 | +0.7 | 32.3 | 39.0 |  |
| Dyson Daniels ATL | 35.6 | +3.6 | +0.0 | 29.7 | 35.0 |  |

## Missed the same way on 3+ of the last 10 slates

- Caleb Wilson: ETR above ours by 5.1, 3.1, 6.3
- Domantas Sabonis: ETR below ours by 3.2, 4.7, 6.2
- Darius Garland: ETR above ours by 4.7, 3.0, 4.6
- Paul Reed: ETR above ours by 4.6, 3.9, 3.4
- Luka Doncic: ETR above ours by 4.2, 3.6, 3.7
- Kyrie Irving: ETR above ours by 3.0, 3.0, 5.0
- LaMelo Ball: ETR below ours by 3.8, 3.7, 3.1
