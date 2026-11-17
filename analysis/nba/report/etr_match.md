# Our morning Proj vs ETR's final upload, against ADP

Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's last upload before lock (its first carries a random multiplier); the top 60 by ADP graded (40 on a 4-drafter slate), in four groups: the elite (ETR's top 2-4, cut at the biggest drop), then next / middle / 6th round on by morning ADP: under 19, 19-31 and 32 on with 6 drafters; under 13, 13-20 and 21 on with 4. 17 slates, 2026-10-28 to 2026-11-16. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board averages their last 3 ETR nights from 2026-11-07.

## Season

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 47 | 0.78 | 33/34 (97%) | 21/21 (100%) | - | 12 (26%) | 0.09 / 0.09 | - (0) |
| next | 231 | 0.63 | 92/111 (83%) | 10/10 (100%) | 14/17 (82%) | 55 (24%) | 0.22 / 0.56 | +1.4 (15) |
| middle | 204 | 0.63 | 66/73 (90%) | 5/6 (83%) | 8/8 (100%) | 47 (23%) | 0.22 / 0.57 | +2.3 (19) |
| 6th round on | 475 | 0.80 | 226/262 (86%) | 43/48 (90%) | 60/60 (100%) | 121 (25%) | 0.11 / 0.26 | +1.3 (22) |
| **all** | 957 | 0.77 | 417/480 (87%) | 79/85 (93%) | 82/85 (96%) | 235 (25%) | 0.14 / 0.32 | +1.7 (56) |

## Last 7 slates

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 18 | 0.66 | 14/14 (100%) | 7/7 (100%) | - | 4 (22%) | 0.01 / 0.18 | - (0) |
| next | 101 | 0.64 | 41/49 (84%) | 4/4 (100%) | 4/5 (80%) | 21 (21%) | 0.29 / 0.62 | +1.1 (8) |
| middle | 91 | 0.59 | 27/31 (87%) | 2/2 (100%) | 3/3 (100%) | 25 (27%) | -0.03 / 0.49 | +1.2 (7) |
| 6th round on | 207 | 0.81 | 103/117 (88%) | 20/22 (91%) | 27/27 (100%) | 58 (28%) | 0.09 / 0.27 | +0.5 (12) |
| **all** | 417 | 0.78 | 185/211 (88%) | 33/35 (94%) | 34/35 (97%) | 108 (26%) | 0.08 / 0.32 | +0.9 (27) |

## Rookies (no last season), before and after the last-3 average

| | n | ETR minus ours | big misses |
|---|---|---|---|
| before 2026-11-07 | 25 | +2.78 | 9 |
| from 2026-11-07 | 31 | +0.76 | 8 |

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
| 2026-11-13 (6 drafters) | 60 | 0.64 | 20/23 (87%) | 4/5 (80%) | 5/5 (100%) | 20 (33%) | -0.08 / 0.33 | +1.7 (4) |
| 2026-11-16 (6 drafters) | 60 | 0.80 | 25/29 (86%) | 5/5 (100%) | 5/5 (100%) | 11 (18%) | 0.28 / 0.30 | +1.4 (3) |

## Biggest misses, 2026-11-16

| player | ADP | ours vs ADP | ETR vs ADP | usual min | min | tag |
|---|---|---|---|---|---|---|
| Jalen Green PHX | 35.8 | -3.9 | -10.0 | 26.9 | 27.0 |  |
| Rudy Gobert MIN | 35.6 | +3.3 | -2.5 | 28.7 | 32.0 |  |
| Klay Thompson MIA | 36.0 | -8.9 | -3.1 | 22.5 | 22.0 |  |
| Yaxel Lendeborg GSW (rookie) | 10.7 | -2.4 | +2.6 | 30.7 | 33.0 |  |
| Julius Randle BKN | 32.6 | +6.8 | +2.1 | 32.1 | 34.0 |  |
| VJ Edgecombe PHI | 35.8 | -0.5 | +3.8 | 33.6 | 33.0 |  |
| Cam Spencer MEM | 35.9 | -0.8 | +3.5 | 22.3 | 32.0 |  |
| Jalen Suggs ORL | 35.9 | +3.7 | -0.4 | 30.7 | 25.0 |  |
| Norman Powell CHI | 35.2 | -4.7 | -1.4 | 29.2 | 33.0 |  |
| Davion Mitchell MIA | 28.6 | -5.5 | -2.3 | 36.1 | 33.0 |  |

## Missed the same way on 3+ of the last 10 slates

- Jamal Shead: ETR above ours by 11.5, 6.3, 4.6
- Jeremiah Fears: ETR above ours by 5.2, 6.7, 4.6, 8.3
- Domantas Sabonis: ETR below ours by 6.0, 6.2, 4.1
- Deni Avdija: ETR above ours by 3.9, 5.0, 5.7
- Anthony Black: ETR above ours by 4.3, 4.9, 4.0
- Davion Mitchell: ETR above ours by 3.0, 6.6, 3.2
- Desmond Bane: ETR below ours by 3.5, 3.6, 5.6
- Trae Young: ETR below ours by 3.2, 4.1, 3.1
