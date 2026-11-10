# Our morning Proj vs ETR's first upload, against ADP

Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's first file; the top 60 by ADP graded (40 on a 4-drafter slate), in four groups: the elite (ETR's top 2-4, cut at the biggest drop), then next / middle / 6th round on by morning ADP: under 19, 19-31 and 32 on with 6 drafters; under 13, 13-20 and 21 on with 4. 12 slates, 2026-10-28 to 2026-11-09. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board averages their last 3 ETR nights from 2026-11-07.

## Season

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 32 | 0.83 | 26/26 (100%) | 13/13 (100%) | - | 11 (34%) | 0.12 / 0.11 | - (0) |
| next | 165 | 0.73 | 67/79 (85%) | 8/9 (89%) | 16/16 (100%) | 38 (23%) | 0.17 / 0.44 | +1.6 (9) |
| middle | 145 | 0.78 | 55/58 (95%) | 9/9 (100%) | 8/8 (100%) | 31 (21%) | 0.37 / 0.57 | +2.6 (14) |
| 6th round on | 315 | 0.85 | 158/176 (90%) | 27/29 (93%) | 36/36 (100%) | 76 (24%) | 0.11 / 0.22 | +1.4 (14) |
| **all** | 657 | 0.83 | 306/339 (90%) | 57/60 (95%) | 60/60 (100%) | 156 (24%) | 0.19 / 0.30 | +1.9 (37) |

## Last 7 slates

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 19 | 0.85 | 15/15 (100%) | 7/7 (100%) | - | 6 (32%) | 0.24 / 0.18 | - (0) |
| next | 97 | 0.74 | 45/52 (87%) | 5/5 (100%) | 10/10 (100%) | 25 (26%) | 0.18 / 0.45 | +0.6 (4) |
| middle | 92 | 0.79 | 28/29 (97%) | 6/6 (100%) | 3/3 (100%) | 21 (23%) | 0.34 / 0.55 | +2.9 (11) |
| 6th round on | 189 | 0.85 | 101/113 (89%) | 16/17 (94%) | 22/22 (100%) | 49 (26%) | 0.11 / 0.21 | +1.0 (8) |
| **all** | 397 | 0.83 | 189/209 (90%) | 34/35 (97%) | 35/35 (100%) | 101 (25%) | 0.19 / 0.29 | +1.8 (23) |

## Rookies (no last season), before and after the last-3 average

| | n | ETR minus ours | big misses |
|---|---|---|---|
| before 2026-11-07 | 25 | +2.54 | 10 |
| from 2026-11-07 | 12 | +0.55 | 3 |

## By slate

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| 2026-10-28 (6 drafters) | 60 | 0.86 | 27/30 (90%) | 5/5 (100%) | 5/5 (100%) | 18 (30%) | 0.07 / 0.19 | +3.3 (3) |
| 2026-10-29 (4 drafters) | 40 | 0.84 | 15/17 (88%) | 4/5 (80%) | 5/5 (100%) | 3 (8%) | 0.27 / 0.42 | +2.9 (2) |
| 2026-10-30 (6 drafters) | 60 | 0.85 | 31/33 (94%) | 5/5 (100%) | 5/5 (100%) | 14 (23%) | 0.34 / 0.39 | +1.5 (4) |
| 2026-10-31 (6 drafters) | 60 | 0.80 | 28/30 (93%) | 4/5 (80%) | 5/5 (100%) | 8 (13%) | 0.29 / 0.50 | +0.6 (3) |
| 2026-11-01 (4 drafters) | 40 | 0.73 | 16/20 (80%) | 5/5 (100%) | 5/5 (100%) | 12 (30%) | 0.30 / 0.37 | +2.5 (2) |
| 2026-11-02 (6 drafters) | 60 | 0.74 | 27/28 (96%) | 5/5 (100%) | 5/5 (100%) | 13 (22%) | 0.17 / 0.32 | +3.5 (4) |
| 2026-11-04 (6 drafters) | 60 | 0.70 | 25/29 (86%) | 5/5 (100%) | 5/5 (100%) | 20 (33%) | 0.19 / 0.41 | +5.2 (3) |
| 2026-11-05 (4 drafters) | 40 | 0.82 | 20/25 (80%) | 4/5 (80%) | 5/5 (100%) | 11 (28%) | 0.30 / 0.31 | +1.9 (1) |
| 2026-11-06 (6 drafters) | 60 | 0.86 | 23/26 (88%) | 5/5 (100%) | 5/5 (100%) | 13 (22%) | 0.12 / 0.17 | +1.2 (3) |
| 2026-11-07 (6 drafters) | 60 | 0.86 | 34/36 (94%) | 5/5 (100%) | 5/5 (100%) | 14 (23%) | 0.34 / 0.39 | +0.0 (4) |
| 2026-11-08 (6 drafters) | 57 | 0.84 | 30/34 (88%) | 5/5 (100%) | 5/5 (100%) | 19 (33%) | 0.14 / 0.40 | +0.6 (5) |
| 2026-11-09 (6 drafters) | 60 | 0.89 | 30/31 (97%) | 5/5 (100%) | 5/5 (100%) | 11 (18%) | 0.07 / 0.08 | +1.1 (3) |

## Biggest misses, 2026-11-09

| player | ADP | ours vs ADP | ETR vs ADP | usual min | min | tag |
|---|---|---|---|---|---|---|
| Duncan Robinson DET | 35.9 | -4.2 | +0.7 | 30.6 | 34.0 |  |
| Pascal Siakam IND | 19.9 | +3.4 | -1.3 | 32.0 | 35.0 |  |
| Ivica Zubac IND | 35.7 | -0.1 | -4.8 | 17.2 | 28.0 |  |
| Deandre Ayton WAS | 35.9 | -9.9 | -14.5 | 15.1 | 13.0 |  |
| Jarrett Allen CLE | 35.9 | +1.9 | -1.9 | 24.7 | 19.0 | Questionable |
| Cooper Flagg DAL | 5.1 | -0.9 | +3.0 | 33.7 | 39.0 |  |
| Alperen Sengun HOU | 7.9 | -2.4 | +1.1 | 34.8 | 35.0 |  |
| PJ Washington DAL | 35.9 | +5.1 | +8.5 | 33.7 | 35.0 |  |
| Jabari Smith Jr. HOU | 35.9 | +0.1 | +3.2 | 35.0 | 38.0 |  |
| Jeremiah Fears NOP | 33.3 | -5.8 | -2.7 | 28.9 | 29.0 |  |

## Missed the same way on 3+ of the last 10 slates

- Nolan Traore: ETR above ours by 6.8, 4.4, 7.5
- Domantas Sabonis: ETR below ours by 3.2, 4.7, 6.2, 6.2
- Cooper Flagg: ETR above ours by 3.4, 7.9, 3.8
- LaMelo Ball: ETR below ours by 3.8, 3.7, 3.1
