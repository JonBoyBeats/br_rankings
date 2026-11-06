# Our morning Proj vs ETR's first upload, against ADP

Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's first file; the top 60 by ADP graded (40 on a 4-drafter slate), in four groups: the elite (ETR's top 2-4, cut at the biggest drop), then next / middle / 6th round on by morning ADP: under 19, 19-31 and 32 on with 6 drafters; under 13, 13-20 and 21 on with 4. 8 slates, 2026-10-28 to 2026-11-05. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board averages their last 3 ETR nights from 2026-11-07.

## Season

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 23 | 0.83 | 18/18 (100%) | 8/8 (100%) | - | 8 (35%) | 0.21 / 0.24 | - (0) |
| next | 103 | 0.69 | 38/46 (83%) | 6/7 (86%) | 9/9 (100%) | 24 (23%) | 0.22 / 0.50 | +2.2 (6) |
| middle | 92 | 0.77 | 39/42 (93%) | 7/7 (100%) | 10/10 (100%) | 24 (26%) | 0.37 / 0.59 | +3.4 (10) |
| 6th round on | 202 | 0.82 | 90/105 (86%) | 16/18 (89%) | 21/21 (100%) | 45 (22%) | 0.14 / 0.20 | +2.5 (5) |
| **all** | 420 | 0.80 | 185/211 (88%) | 37/40 (92%) | 40/40 (100%) | 101 (24%) | 0.22 / 0.33 | +2.9 (21) |

## Last 7 slates

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 20 | 0.87 | 15/15 (100%) | 7/7 (100%) | - | 6 (30%) | 0.22 / 0.25 | - (0) |
| next | 88 | 0.68 | 34/41 (83%) | 5/6 (83%) | 8/8 (100%) | 22 (25%) | 0.21 / 0.53 | +2.2 (6) |
| middle | 79 | 0.80 | 34/36 (94%) | 7/7 (100%) | 9/9 (100%) | 20 (25%) | 0.42 / 0.64 | +3.4 (10) |
| 6th round on | 173 | 0.79 | 75/89 (84%) | 13/15 (87%) | 18/18 (100%) | 35 (20%) | 0.13 / 0.20 | +1.3 (2) |
| **all** | 360 | 0.79 | 158/181 (87%) | 32/35 (91%) | 35/35 (100%) | 83 (23%) | 0.25 / 0.36 | +2.8 (18) |

## Rookies (no last season), before and after the last-3 average

| | n | ETR minus ours | big misses |
|---|---|---|---|
| before 2026-11-07 | 21 | +2.87 | 9 |
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

## Biggest misses, 2026-11-05

| player | ADP | ours vs ADP | ETR vs ADP | usual min | min | tag |
|---|---|---|---|---|---|---|
| Will Richard GSW | 24.0 | -2.4 | +5.9 | 17.9 | 16.0 |  |
| Goga Bitadze ORL | 24.0 | +2.1 | -3.8 | 6.6 | 8.0 |  |
| Jevon Carter ORL | 24.0 | -1.0 | -6.5 | 7.6 | 3.0 |  |
| Anthony Black ORL | 9.9 | -2.1 | +2.3 | 28.0 | 31.0 |  |
| Colin Castleton ORL | 24.0 | -5.3 | -9.4 | 1.6 | 2.0 |  |
| Khaman Maluach PHX | 23.6 | +7.9 | +4.5 | 19.5 | 22.0 |  |
| Bobby Portis MIA | 21.6 | +2.7 | -0.7 | 21.6 | 14.0 |  |
| Stephen Curry GSW | 2.1 | -3.9 | -0.6 | 29.0 | 28.0 |  |
| Jase Richardson ORL | 23.8 | +2.2 | +5.5 | 21.0 | 26.0 |  |
| Giannis Antetokounmpo MIA | 1.1 | +15.4 | +12.2 | 33.0 | 31.0 |  |

## Missed the same way on 3+ of the last 10 slates

- Caleb Wilson: ETR above ours by 5.1, 3.1, 6.3
- Darius Garland: ETR above ours by 4.7, 3.0, 4.6
- Paul Reed: ETR above ours by 4.6, 3.9, 3.4
