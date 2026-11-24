# Our morning Proj vs ETR's final upload, against ADP

Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's last upload before lock (its first carries a random multiplier); the top 60 by ADP graded (40 on a 4-drafter slate), in four groups: the elite (ETR's top 2-4, cut at the biggest drop), then next / middle / 6th round on by morning ADP: under 19, 19-31 and 32 on with 6 drafters; under 13, 13-20 and 21 on with 4. 22 slates, 2026-10-28 to 2026-11-23. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board averages their last 3 ETR nights from 2026-11-07.

## Season

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 58 | 0.85 | 43/44 (98%) | 29/29 (100%) | - | 17 (29%) | 0.10 / 0.05 | - (0) |
| next | 305 | 0.62 | 121/147 (82%) | 13/13 (100%) | 19/22 (86%) | 71 (23%) | 0.18 / 0.52 | +1.1 (21) |
| middle | 264 | 0.60 | 90/102 (88%) | 6/7 (86%) | 11/11 (100%) | 61 (23%) | 0.18 / 0.53 | +2.3 (22) |
| 6th round on | 630 | 0.79 | 309/358 (86%) | 55/61 (90%) | 77/77 (100%) | 175 (28%) | 0.09 / 0.26 | +1.0 (32) |
| **all** | 1257 | 0.77 | 563/651 (86%) | 103/110 (94%) | 107/110 (97%) | 324 (26%) | 0.11 / 0.30 | +1.4 (75) |

## Last 7 slates

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 15 | 0.91 | 14/14 (100%) | 10/10 (100%) | - | 6 (40%) | 0.30 / 0.16 | - (0) |
| next | 106 | 0.66 | 43/51 (84%) | 4/4 (100%) | 7/7 (100%) | 20 (19%) | 0.13 / 0.44 | +1.2 (11) |
| middle | 85 | 0.52 | 29/35 (83%) | 1/1 (100%) | 3/3 (100%) | 21 (25%) | 0.04 / 0.43 | +2.2 (3) |
| 6th round on | 214 | 0.76 | 105/123 (85%) | 18/20 (90%) | 25/25 (100%) | 73 (34%) | 0.04 / 0.27 | +0.3 (12) |
| **all** | 420 | 0.76 | 191/223 (86%) | 33/35 (94%) | 35/35 (100%) | 120 (29%) | 0.04 / 0.26 | +0.9 (26) |

## Rookies (no last season), before and after the last-3 average

| | n | ETR minus ours | big misses |
|---|---|---|---|
| before 2026-11-07 | 25 | +2.78 | 9 |
| from 2026-11-07 | 50 | +0.72 | 12 |

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
| 2026-11-19 (6 drafters) | 60 | 0.72 | 31/39 (79%) | 4/5 (80%) | 5/5 (100%) | 23 (38%) | 0.01 / 0.29 | +0.3 (4) |
| 2026-11-20 (6 drafters) | 60 | 0.65 | 25/27 (93%) | 5/5 (100%) | 5/5 (100%) | 19 (32%) | 0.12 / 0.35 | -0.0 (3) |
| 2026-11-23 (6 drafters) | 60 | 0.92 | 36/37 (97%) | 5/5 (100%) | 5/5 (100%) | 11 (18%) | 0.12 / 0.26 | +0.1 (4) |

## Biggest misses, 2026-11-23

| player | ADP | ours vs ADP | ETR vs ADP | usual min | min | tag |
|---|---|---|---|---|---|---|
| Quentin Grimes LAL | 35.6 | -6.9 | -1.4 | 30.1 | 30.0 |  |
| LeBron James PHI | 26.4 | +1.7 | +7.1 | 32.4 | 30.0 |  |
| Kris Dunn LA | 35.9 | -1.6 | -6.7 | 23.8 | 23.0 |  |
| Scottie Barnes TOR | 4.0 | +0.0 | -4.1 | 34.8 | 38.0 |  |
| VJ Edgecombe PHI | 35.7 | -2.7 | +1.2 | 34.8 | 35.0 |  |
| Isaiah Collier UTA | 35.9 | -10.9 | -14.6 | 10.4 | 18.0 |  |
| Jalen Smith CHI | 33.6 | -0.2 | -3.6 | 26.7 | 25.0 |  |
| Brayden Burries MIL (rookie) | 35.6 | -7.7 | -11.0 | 26.5 | 29.0 |  |
| Amen Thompson HOU | 29.6 | -2.5 | -5.7 | 31.5 | 28.0 |  |
| Darius Garland LA | 35.7 | +3.7 | +0.5 | 33.4 | 34.0 |  |

## Missed the same way on 3+ of the last 10 slates

- Paul Reed: ETR below ours by 8.4, 10.2, 10.2, 6.5
- Quentin Grimes: ETR above ours by 7.9, 6.3, 5.5
- Mo Bamba: ETR above ours by 5.0, 8.4, 5.5
- Jeremiah Fears: ETR above ours by 4.6, 8.3, 3.9
- VJ Edgecombe: ETR above ours by 5.8, 4.3, 3.9
- Darius Garland: ETR below ours by 5.2, 5.5, 3.2
- Rudy Gobert: ETR below ours by 5.8, 3.2, 4.2
- Desmond Bane: ETR below ours by 3.5, 3.6, 5.6
- Darryn Peterson: ETR above ours by 4.1, 4.1, 4.4
- Trae Young: ETR below ours by 4.1, 3.1, 5.0
- Amen Thompson: ETR below ours by 5.4, 3.0, 3.2
- Jaylen Brown: ETR above ours by 4.4, 4.0, 3.0
- Stephon Castle: ETR below ours by 4.1, 3.9, 3.4
- Domantas Sabonis: ETR below ours by 4.1, 3.2, 3.4
- Isaiah Hartenstein: ETR below ours by 3.6, 3.8, 3.0
