# Our morning Proj vs ETR's first upload, against ADP

Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's first file; the top 60 by ADP graded (40 on a 4-drafter slate), in four groups: the elite (ETR's top 2-4, cut at the biggest drop), then next / middle / 6th round on by morning ADP: under 19, 19-31 and 32 on with 6 drafters; under 13, 13-20 and 21 on with 4. 10 slates, 2026-10-28 to 2026-11-08. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board averages their last 3 ETR nights from 2026-11-07.

## Season

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 27 | 0.82 | 21/21 (100%) | 11/11 (100%) | - | 11 (41%) | 0.07 / 0.07 | - (0) |
| next | 135 | 0.72 | 57/68 (84%) | 6/7 (86%) | 15/15 (100%) | 31 (23%) | 0.17 / 0.45 | +1.5 (8) |
| middle | 117 | 0.77 | 44/46 (96%) | 9/9 (100%) | 8/8 (100%) | 27 (23%) | 0.39 / 0.62 | +3.0 (11) |
| 6th round on | 258 | 0.83 | 123/140 (88%) | 21/23 (91%) | 27/27 (100%) | 62 (24%) | 0.12 / 0.22 | +1.5 (11) |
| **all** | 537 | 0.82 | 245/275 (89%) | 47/50 (94%) | 50/50 (100%) | 131 (24%) | 0.19 / 0.32 | +2.0 (30) |

## Last 7 slates

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 19 | 0.87 | 15/15 (100%) | 8/8 (100%) | - | 7 (37%) | 0.15 / 0.05 | - (0) |
| next | 93 | 0.72 | 43/50 (86%) | 5/5 (100%) | 11/11 (100%) | 25 (27%) | 0.19 / 0.47 | +1.1 (4) |
| middle | 85 | 0.80 | 29/30 (97%) | 7/7 (100%) | 5/5 (100%) | 21 (25%) | 0.39 / 0.61 | +3.0 (11) |
| 6th round on | 180 | 0.82 | 88/103 (85%) | 14/15 (93%) | 19/19 (100%) | 49 (27%) | 0.10 / 0.22 | +0.9 (7) |
| **all** | 377 | 0.81 | 175/198 (88%) | 34/35 (97%) | 35/35 (100%) | 102 (27%) | 0.20 / 0.32 | +2.0 (22) |

## Rookies (no last season), before and after the last-3 average

| | n | ETR minus ours | big misses |
|---|---|---|---|
| before 2026-11-07 | 21 | +2.74 | 9 |
| from 2026-11-07 | 9 | +0.36 | 3 |

## By slate

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| 2026-10-28 (6 drafters) | 60 | 0.86 | 27/30 (90%) | 5/5 (100%) | 5/5 (100%) | 18 (30%) | 0.07 / 0.19 | +3.3 (3) |
| 2026-10-29 (4 drafters) | 40 | 0.84 | 15/17 (88%) | 4/5 (80%) | 5/5 (100%) | 3 (8%) | 0.27 / 0.42 | +2.9 (2) |
| 2026-10-31 (6 drafters) | 60 | 0.80 | 28/30 (93%) | 4/5 (80%) | 5/5 (100%) | 8 (13%) | 0.29 / 0.50 | +0.6 (3) |
| 2026-11-01 (4 drafters) | 40 | 0.73 | 16/20 (80%) | 5/5 (100%) | 5/5 (100%) | 12 (30%) | 0.30 / 0.37 | +2.5 (2) |
| 2026-11-02 (6 drafters) | 60 | 0.74 | 27/28 (96%) | 5/5 (100%) | 5/5 (100%) | 13 (22%) | 0.17 / 0.32 | +3.5 (4) |
| 2026-11-04 (6 drafters) | 60 | 0.70 | 25/29 (86%) | 5/5 (100%) | 5/5 (100%) | 20 (33%) | 0.19 / 0.41 | +5.2 (3) |
| 2026-11-05 (4 drafters) | 40 | 0.82 | 20/25 (80%) | 4/5 (80%) | 5/5 (100%) | 11 (28%) | 0.30 / 0.31 | +1.9 (1) |
| 2026-11-06 (6 drafters) | 60 | 0.86 | 23/26 (88%) | 5/5 (100%) | 5/5 (100%) | 13 (22%) | 0.12 / 0.17 | +1.2 (3) |
| 2026-11-07 (6 drafters) | 60 | 0.86 | 34/36 (94%) | 5/5 (100%) | 5/5 (100%) | 14 (23%) | 0.34 / 0.39 | +0.0 (4) |
| 2026-11-08 (6 drafters) | 57 | 0.84 | 30/34 (88%) | 5/5 (100%) | 5/5 (100%) | 19 (33%) | 0.14 / 0.40 | +0.6 (5) |

## Biggest misses, 2026-11-08

| player | ADP | ours vs ADP | ETR vs ADP | usual min | min | tag |
|---|---|---|---|---|---|---|
| Payton Pritchard BOS | 34.3 | +7.2 | -1.3 | 26.3 | 29.0 |  |
| Nolan Traore BKN | 32.3 | -7.4 | +0.1 | 22.2 | 21.0 |  |
| Walter Clayton Jr. DAL | 35.8 | -14.6 | -7.3 | 12.5 | 16.0 |  |
| Brook Lopez LAC | 34.9 | -2.1 | +5.2 | 23.6 | 26.0 |  |
| Domantas Sabonis SAC | 3.9 | -1.5 | -7.7 | 35.6 | 0.0 | Questionable |
| Ryan Rollins MIL | 36.0 | +10.3 | +4.3 | 23.7 | 20.0 |  |
| Lauri Markkanen UTA | 21.4 | +6.1 | +0.3 | 30.9 | 0.0 | Questionable / Out |
| Brayden Burries MIL (rookie) | 35.4 | -6.5 | -1.1 | 20.1 | 29.0 |  |
| Keaton Wagler LAC (rookie) | 35.6 | +2.6 | -2.8 | 23.9 | 18.0 |  |
| Jeremiah Fears NOP | 22.6 | -5.1 | +0.1 | 28.9 | 29.0 |  |

## Missed the same way on 3+ of the last 10 slates

- Nolan Traore: ETR above ours by 6.8, 4.4, 7.5
- Domantas Sabonis: ETR below ours by 3.2, 4.7, 6.2, 6.2
- Caleb Wilson: ETR above ours by 5.1, 3.1, 6.3
- Joel Embiid: ETR below ours by 4.0, 3.9, 5.0
- Luka Doncic: ETR above ours by 4.2, 3.6, 3.7
- LaMelo Ball: ETR below ours by 3.8, 3.7, 3.1
