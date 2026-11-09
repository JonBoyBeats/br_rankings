# Our morning Proj vs ETR's first upload, against ADP

Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's first file; the top 60 by ADP graded (40 on a 4-drafter slate), in four groups: the elite (ETR's top 2-4, cut at the biggest drop), then next / middle / 6th round on by morning ADP: under 19, 19-31 and 32 on with 6 drafters; under 13, 13-20 and 21 on with 4. 11 slates, 2026-10-28 to 2026-11-08. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board averages their last 3 ETR nights from 2026-11-07.

## Season

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 30 | 0.82 | 24/24 (100%) | 12/12 (100%) | - | 11 (37%) | 0.17 / 0.14 | - (0) |
| next | 150 | 0.72 | 61/71 (86%) | 7/8 (88%) | 14/14 (100%) | 35 (23%) | 0.17 / 0.44 | +1.5 (8) |
| middle | 130 | 0.78 | 51/54 (94%) | 8/8 (100%) | 10/10 (100%) | 30 (23%) | 0.45 / 0.63 | +2.4 (13) |
| 6th round on | 290 | 0.81 | 135/154 (88%) | 25/27 (93%) | 31/31 (100%) | 72 (25%) | 0.12 / 0.20 | +1.9 (12) |
| **all** | 600 | 0.80 | 271/303 (89%) | 52/55 (95%) | 55/55 (100%) | 148 (25%) | 0.22 / 0.31 | +2.0 (33) |

## Last 7 slates

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 19 | 0.87 | 15/15 (100%) | 8/8 (100%) | - | 7 (37%) | 0.31 / 0.16 | - (0) |
| next | 94 | 0.71 | 43/49 (88%) | 5/5 (100%) | 10/10 (100%) | 25 (27%) | 0.14 / 0.42 | +1.0 (4) |
| middle | 84 | 0.81 | 29/30 (97%) | 6/6 (100%) | 5/5 (100%) | 20 (24%) | 0.44 / 0.61 | +2.5 (11) |
| 6th round on | 183 | 0.77 | 88/102 (86%) | 15/16 (94%) | 20/20 (100%) | 53 (29%) | 0.11 / 0.19 | +1.4 (7) |
| **all** | 380 | 0.79 | 175/196 (89%) | 34/35 (97%) | 35/35 (100%) | 105 (28%) | 0.22 / 0.30 | +1.9 (22) |

## Rookies (no last season), before and after the last-3 average

| | n | ETR minus ours | big misses |
|---|---|---|---|
| before 2026-11-07 | 24 | +2.41 | 9 |
| from 2026-11-07 | 9 | +0.87 | 3 |

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
| 2026-11-07 (6 drafters) | 60 | 0.86 | 34/36 (94%) | 5/5 (100%) | 5/5 (100%) | 14 (23%) | 0.34 / 0.39 | +0.0 (4) |
| 2026-11-08 (6 drafters) | 60 | 0.65 | 28/30 (93%) | 5/5 (100%) | 5/5 (100%) | 18 (30%) | 0.06 / 0.31 | +1.5 (5) |

## Biggest misses, 2026-11-08

| player | ADP | ours vs ADP | ETR vs ADP | usual min | min | tag |
|---|---|---|---|---|---|---|
| Derik Queen NOP | 33.3 | +4.3 | -3.3 | 22.6 | 21.0 |  |
| Precious Achiuwa SAC | 36.0 | +5.9 | -1.0 | 26.7 | 36.0 |  |
| Payton Pritchard BOS | 35.2 | +6.4 | +0.0 | 26.3 | 29.0 |  |
| Brook Lopez LAC | 33.8 | -1.7 | +4.5 | 23.6 | 26.0 |  |
| Domantas Sabonis SAC | 4.8 | -1.5 | -7.7 | 35.6 | 0.0 | Questionable |
| Nolan Traore BKN | 32.0 | -7.1 | -1.0 | 22.2 | 21.0 |  |
| Brayden Burries MIL (rookie) | 35.5 | -6.0 | -0.1 | 20.1 | 29.0 |  |
| Malik Monk SAC | 36.0 | +1.4 | +6.4 | 16.4 | 21.0 |  |
| Ayo Dosunmu MIN | 15.2 | -4.7 | +0.0 | 31.5 | 30.0 |  |
| Tim Hardaway Jr. MIA | 36.0 | -3.4 | -8.1 | 15.6 | 7.0 |  |

## Missed the same way on 3+ of the last 10 slates

- Nolan Traore: ETR above ours by 6.8, 4.4, 6.1
- Domantas Sabonis: ETR below ours by 3.2, 4.7, 6.2, 6.2
- Ayo Dosunmu: ETR above ours by 3.3, 3.9, 4.8
- LaMelo Ball: ETR below ours by 3.8, 3.7, 3.1
