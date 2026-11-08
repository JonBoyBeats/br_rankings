# Our morning Proj vs ETR's first upload, against ADP

Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's first file; the top 60 by ADP graded (40 on a 4-drafter slate), in four groups: the elite (ETR's top 2-4, cut at the biggest drop), then next / middle / 6th round on by morning ADP: under 19, 19-31 and 32 on with 6 drafters; under 13, 13-20 and 21 on with 4. 10 slates, 2026-10-28 to 2026-11-07. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board averages their last 3 ETR nights from 2026-11-07.

## Season

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 27 | 0.82 | 22/22 (100%) | 11/11 (100%) | - | 10 (37%) | 0.17 / 0.16 | - (0) |
| next | 135 | 0.73 | 56/66 (85%) | 7/8 (88%) | 13/13 (100%) | 32 (24%) | 0.17 / 0.44 | +1.6 (7) |
| middle | 118 | 0.79 | 46/49 (94%) | 8/8 (100%) | 10/10 (100%) | 26 (22%) | 0.47 / 0.65 | +2.6 (12) |
| 6th round on | 260 | 0.83 | 119/136 (88%) | 21/23 (91%) | 27/27 (100%) | 62 (24%) | 0.13 / 0.20 | +1.7 (9) |
| **all** | 540 | 0.82 | 243/273 (89%) | 47/50 (94%) | 50/50 (100%) | 130 (24%) | 0.23 / 0.32 | +2.1 (28) |

## Last 7 slates

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 19 | 0.86 | 15/15 (100%) | 8/8 (100%) | - | 7 (37%) | 0.16 / 0.14 | - (0) |
| next | 95 | 0.73 | 45/52 (87%) | 5/5 (100%) | 10/10 (100%) | 25 (26%) | 0.08 / 0.38 | +1.1 (5) |
| middle | 84 | 0.82 | 32/33 (97%) | 8/8 (100%) | 6/6 (100%) | 17 (20%) | 0.49 / 0.68 | +2.7 (10) |
| 6th round on | 182 | 0.79 | 83/96 (86%) | 12/14 (86%) | 19/19 (100%) | 46 (25%) | 0.13 / 0.20 | +0.6 (5) |
| **all** | 380 | 0.80 | 175/196 (89%) | 33/35 (94%) | 35/35 (100%) | 95 (25%) | 0.24 / 0.33 | +1.8 (20) |

## Rookies (no last season), before and after the last-3 average

| | n | ETR minus ours | big misses |
|---|---|---|---|
| before 2026-11-07 | 24 | +2.41 | 9 |
| from 2026-11-07 | 4 | +0.01 | 1 |

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

## Biggest misses, 2026-11-07

| player | ADP | ours vs ADP | ETR vs ADP | usual min | min | tag |
|---|---|---|---|---|---|---|
| Thomas Bryant CLE | 36.0 | -18.9 | -9.0 | 5.0 | 15.0 |  |
| Jose Alvarado NYK | 36.0 | -11.6 | -18.7 | 11.2 | 0.0 |  |
| Bilal Coulibaly WAS | 36.0 | +2.2 | -3.5 | 26.4 | 20.0 |  |
| Anthony Black ORL | 35.2 | +1.3 | +6.2 | 28.6 | 38.0 |  |
| Nolan Traore BKN | 36.0 | +1.2 | +5.6 | 22.1 | 23.0 |  |
| Shai Gilgeous-Alexander OKC | 2.2 | +10.0 | +5.9 | 33.3 | 29.0 |  |
| Evan Mobley CLE | 18.2 | -3.5 | +0.6 | 32.8 | 33.0 |  |
| Isaiah Hartenstein OKC | 35.6 | +5.4 | +1.4 | 24.9 | 18.0 |  |
| Jalen Johnson ATL | 21.9 | +13.7 | +9.9 | 29.1 | 36.0 | Questionable |
| CJ McCollum ATL | 35.9 | +5.5 | +1.8 | 26.2 | 21.0 |  |

## Missed the same way on 3+ of the last 10 slates

- Caleb Wilson: ETR above ours by 5.1, 3.1, 6.3
- Domantas Sabonis: ETR below ours by 3.2, 4.7, 6.2
- Darius Garland: ETR above ours by 4.7, 3.0, 4.6
- Paul Reed: ETR above ours by 4.6, 3.9, 3.4
- Luka Doncic: ETR above ours by 4.2, 3.6, 3.7
- Kyrie Irving: ETR above ours by 3.0, 3.0, 5.0
- LaMelo Ball: ETR below ours by 3.8, 3.7, 3.1
