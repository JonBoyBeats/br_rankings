# Our morning Proj vs ETR's final upload, against ADP

Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's last upload before lock (its first carries a random multiplier); the top 60 by ADP graded (40 on a 4-drafter slate), in four groups: the elite (ETR's top 2-4, cut at the biggest drop), then next / middle / 6th round on by morning ADP: under 19, 19-31 and 32 on with 6 drafters; under 13, 13-20 and 21 on with 4. 18 slates, 2026-10-28 to 2026-11-17. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board averages their last 3 ETR nights from 2026-11-07.

## Season

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 49 | 0.80 | 35/36 (97%) | 23/23 (100%) | - | 13 (27%) | 0.04 / 0.01 | - (0) |
| next | 247 | 0.63 | 98/119 (82%) | 10/10 (100%) | 15/18 (83%) | 57 (23%) | 0.19 / 0.55 | +1.4 (16) |
| middle | 216 | 0.62 | 71/80 (89%) | 5/6 (83%) | 8/8 (100%) | 50 (23%) | 0.23 / 0.57 | +2.3 (19) |
| 6th round on | 505 | 0.81 | 244/283 (86%) | 46/51 (90%) | 64/64 (100%) | 129 (26%) | 0.11 / 0.25 | +1.2 (24) |
| **all** | 1017 | 0.78 | 448/518 (86%) | 84/90 (93%) | 87/90 (97%) | 249 (24%) | 0.13 / 0.31 | +1.6 (59) |

## Last 7 slates

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 17 | 0.74 | 14/14 (100%) | 8/8 (100%) | - | 4 (24%) | 0.08 / 0.19 | - (0) |
| next | 103 | 0.66 | 42/51 (82%) | 4/4 (100%) | 4/5 (80%) | 20 (19%) | 0.20 / 0.57 | +1.3 (8) |
| middle | 90 | 0.53 | 27/33 (82%) | 1/1 (100%) | 3/3 (100%) | 23 (26%) | -0.02 / 0.51 | +1.4 (6) |
| 6th round on | 210 | 0.81 | 103/117 (88%) | 20/22 (91%) | 27/27 (100%) | 56 (27%) | 0.10 / 0.25 | +0.3 (11) |
| **all** | 420 | 0.78 | 186/215 (87%) | 33/35 (94%) | 34/35 (97%) | 103 (25%) | 0.07 / 0.29 | +0.9 (25) |

## Rookies (no last season), before and after the last-3 average

| | n | ETR minus ours | big misses |
|---|---|---|---|
| before 2026-11-07 | 25 | +2.78 | 9 |
| from 2026-11-07 | 34 | +0.76 | 8 |

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

## Biggest misses, 2026-11-17

| player | ADP | ours vs ADP | ETR vs ADP | usual min | min | tag |
|---|---|---|---|---|---|---|
| Paul Reed DET | 32.7 | +10.0 | -0.2 | 27.8 | 25.0 |  |
| Brook Lopez LAC | 31.7 | -4.6 | +0.9 | 24.7 | 23.0 |  |
| Brandon Miller CHA | 13.6 | +1.7 | -3.6 | 31.9 | 32.0 |  |
| Jake LaRavia LAL | 35.9 | -1.8 | +3.5 | 27.4 | 23.0 |  |
| Mo Bamba UTA | 30.5 | -2.4 | +2.6 | 16.8 | 31.0 |  |
| Victor Wembanyama SAS | 1.4 | +6.7 | +11.6 | 29.4 | 34.0 |  |
| Cade Cunningham DET | 3.3 | +0.6 | -4.1 | 35.2 | 38.0 |  |
| Collin Murray-Boyles TOR | 33.8 | -1.7 | +3.0 | 25.4 | 33.0 |  |
| Kevin Huerter DET | 34.5 | -3.4 | +0.7 | 25.5 | 36.0 |  |
| John Collins DET | 35.9 | +11.2 | +7.2 | 26.1 | 23.0 |  |

## Missed the same way on 3+ of the last 10 slates

- Paul Reed: ETR below ours by 5.6, 8.4, 10.2
- Jamal Shead: ETR above ours by 11.5, 6.3, 4.6
- Jeremiah Fears: ETR above ours by 5.2, 6.7, 4.6, 8.3
- Domantas Sabonis: ETR below ours by 6.0, 6.2, 4.1
- Deni Avdija: ETR above ours by 3.9, 5.0, 5.7
- Davion Mitchell: ETR above ours by 3.0, 6.6, 3.2
- Desmond Bane: ETR below ours by 3.5, 3.6, 5.6
- Rudy Gobert: ETR below ours by 3.4, 5.8, 3.2
- Trae Young: ETR below ours by 3.2, 4.1, 3.1
