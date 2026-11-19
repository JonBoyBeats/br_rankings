# Our morning Proj vs ETR's final upload, against ADP

Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's last upload before lock (its first carries a random multiplier); the top 60 by ADP graded (40 on a 4-drafter slate), in four groups: the elite (ETR's top 2-4, cut at the biggest drop), then next / middle / 6th round on by morning ADP: under 19, 19-31 and 32 on with 6 drafters; under 13, 13-20 and 21 on with 4. 19 slates, 2026-10-28 to 2026-11-18. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board averages their last 3 ETR nights from 2026-11-07.

## Season

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 52 | 0.81 | 37/38 (97%) | 24/24 (100%) | - | 15 (29%) | 0.17 / 0.09 | - (0) |
| next | 260 | 0.63 | 100/124 (81%) | 11/11 (100%) | 16/19 (84%) | 60 (23%) | 0.19 / 0.55 | +1.5 (17) |
| middle | 228 | 0.63 | 78/87 (90%) | 5/6 (83%) | 10/10 (100%) | 53 (23%) | 0.19 / 0.52 | +2.3 (21) |
| 6th round on | 537 | 0.80 | 256/299 (86%) | 49/54 (91%) | 66/66 (100%) | 143 (27%) | 0.09 / 0.26 | +1.1 (26) |
| **all** | 1077 | 0.77 | 471/548 (86%) | 89/95 (94%) | 92/95 (97%) | 271 (25%) | 0.12 / 0.31 | +1.6 (64) |

## Last 7 slates

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 17 | 0.81 | 15/15 (100%) | 8/8 (100%) | - | 5 (29%) | 0.36 / 0.16 | - (0) |
| next | 104 | 0.65 | 38/49 (78%) | 5/5 (100%) | 5/6 (83%) | 22 (21%) | 0.22 / 0.59 | +1.6 (8) |
| middle | 88 | 0.56 | 26/32 (81%) | - | 3/3 (100%) | 22 (25%) | -0.09 / 0.31 | +1.9 (7) |
| 6th round on | 211 | 0.77 | 97/113 (86%) | 21/22 (95%) | 26/26 (100%) | 61 (29%) | 0.07 / 0.26 | +0.3 (12) |
| **all** | 420 | 0.76 | 176/209 (84%) | 34/35 (97%) | 34/35 (97%) | 110 (26%) | 0.05 / 0.27 | +1.1 (27) |

## Rookies (no last season), before and after the last-3 average

| | n | ETR minus ours | big misses |
|---|---|---|---|
| before 2026-11-07 | 25 | +2.78 | 9 |
| from 2026-11-07 | 39 | +0.88 | 10 |

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
| 2026-11-17 (6 drafters) | 60 | 0.86 | 31/38 (82%) | 5/5 (100%) | 5/5 (100%) | 14 (23%) | 0.05 / 0.22 | +0.7 (3) |
| 2026-11-18 (6 drafters) | 60 | 0.56 | 23/30 (77%) | 5/5 (100%) | 5/5 (100%) | 22 (37%) | -0.08 / 0.19 | +1.7 (5) |

## Biggest misses, 2026-11-18

| player | ADP | ours vs ADP | ETR vs ADP | usual min | min | tag |
|---|---|---|---|---|---|---|
| Paul Reed DET | 35.9 | +10.4 | +0.1 | 28.0 | 20.0 |  |
| Mo Bamba UTA | 35.9 | -10.9 | -2.6 | 18.3 | 23.0 |  |
| Nickeil Alexander-Walker ATL | 35.1 | +4.3 | -3.9 | 32.7 | 32.0 |  |
| Quentin Grimes LAL | 35.8 | -12.2 | -4.3 | 28.8 | 35.0 |  |
| Onyeka Okongwu ATL | 35.9 | +4.6 | -3.0 | 32.0 | 36.0 |  |
| Dyson Daniels ATL | 32.2 | +3.1 | -3.2 | 31.2 | 37.0 |  |
| Cedric Coward MEM | 32.4 | -9.0 | -3.0 | 28.2 | 33.0 |  |
| Immanuel Quickley TOR | 35.9 | +1.0 | +7.0 | 32.5 | 34.0 |  |
| Bam Adebayo MIA | 17.2 | +2.6 | -3.2 | 33.2 | 30.0 | Probable |
| Trae Young WAS | 35.8 | +5.2 | +0.2 | 34.7 | 32.0 |  |

## Missed the same way on 3+ of the last 10 slates

- Paul Reed: ETR below ours by 5.6, 8.4, 10.2, 10.2
- Jamal Shead: ETR above ours by 11.5, 6.3, 4.6
- Jeremiah Fears: ETR above ours by 5.2, 6.7, 4.6, 8.3, 3.9
- Domantas Sabonis: ETR below ours by 6.2, 4.1, 3.2
- Davion Mitchell: ETR above ours by 3.0, 6.6, 3.2
- Desmond Bane: ETR below ours by 3.5, 3.6, 5.6
- Rudy Gobert: ETR below ours by 3.4, 5.8, 3.2
- Trae Young: ETR below ours by 3.2, 4.1, 3.1, 5.0
- Isaiah Hartenstein: ETR below ours by 4.0, 3.6, 3.8
