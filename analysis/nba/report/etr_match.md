# Our morning Proj vs ETR's first upload, against ADP

Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's first file; the top 60 by ADP graded (40 on a 4-drafter slate), in four groups: the elite (ETR's top 2-4, cut at the biggest drop), then next / middle / 6th round on by morning ADP: under 19, 19-31 and 32 on with 6 drafters; under 13, 13-20 and 21 on with 4. 14 slates, 2026-10-28 to 2026-11-11. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board averages their last 3 ETR nights from 2026-11-07.

## Season

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 37 | 0.83 | 31/31 (100%) | 15/15 (100%) | - | 11 (30%) | 0.11 / 0.10 | - (0) |
| next | 195 | 0.71 | 80/93 (86%) | 10/11 (91%) | 19/19 (100%) | 44 (23%) | 0.20 / 0.45 | +1.2 (10) |
| middle | 173 | 0.79 | 61/64 (95%) | 9/9 (100%) | 8/8 (100%) | 37 (21%) | 0.32 / 0.54 | +2.1 (18) |
| 6th round on | 372 | 0.86 | 189/208 (91%) | 33/35 (94%) | 43/43 (100%) | 87 (23%) | 0.13 / 0.23 | +1.2 (18) |
| **all** | 777 | 0.83 | 361/396 (91%) | 67/70 (96%) | 70/70 (100%) | 179 (23%) | 0.18 / 0.29 | +1.6 (46) |

## Last 7 slates

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 17 | 0.87 | 14/14 (100%) | 8/8 (100%) | - | 5 (29%) | 0.08 / -0.01 | - (0) |
| next | 100 | 0.73 | 45/51 (88%) | 4/4 (100%) | 9/9 (100%) | 21 (21%) | 0.21 / 0.41 | +0.0 (5) |
| middle | 90 | 0.85 | 25/25 (100%) | 2/2 (100%) | 1/1 (100%) | 14 (16%) | 0.32 / 0.49 | +0.5 (8) |
| 6th round on | 190 | 0.87 | 108/119 (91%) | 20/21 (95%) | 25/25 (100%) | 51 (27%) | 0.13 / 0.25 | +0.8 (12) |
| **all** | 397 | 0.86 | 192/209 (92%) | 34/35 (97%) | 35/35 (100%) | 91 (23%) | 0.17 / 0.26 | +0.6 (25) |

## Rookies (no last season), before and after the last-3 average

| | n | ETR minus ours | big misses |
|---|---|---|---|
| before 2026-11-07 | 25 | +2.54 | 10 |
| from 2026-11-07 | 21 | +0.40 | 4 |

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
| 2026-11-10 (6 drafters) | 60 | 0.89 | 28/29 (97%) | 5/5 (100%) | 5/5 (100%) | 11 (18%) | 0.10 / 0.20 | -0.1 (4) |
| 2026-11-11 (6 drafters) | 60 | 0.84 | 27/28 (96%) | 5/5 (100%) | 5/5 (100%) | 12 (20%) | 0.10 / 0.25 | +0.4 (5) |

## Biggest misses, 2026-11-11

| player | ADP | ours vs ADP | ETR vs ADP | usual min | min | tag |
|---|---|---|---|---|---|---|
| Deni Avdija POR | 13.4 | +0.5 | +6.5 | 32.3 | 35.0 |  |
| Jamal Shead TOR | 35.2 | -13.6 | -8.2 | 24.2 | 22.0 |  |
| Jeremiah Fears NOP | 34.6 | -1.5 | +3.0 | 29.7 | 28.0 |  |
| Stephon Castle SAS | 35.3 | +5.5 | +1.0 | 29.1 | 29.0 |  |
| Day'Ron Sharpe BKN | 35.7 | -3.1 | +1.1 | 23.7 | 19.0 |  |
| Lauri Markkanen UTA | 35.9 | +8.5 | +4.4 | 27.5 | 0.0 | Questionable / Questionable |
| Trae Young WAS | 24.3 | +5.7 | +1.7 | 35.2 | 34.0 |  |
| Ty Jerome MEM | 26.8 | +4.9 | +1.2 | 30.7 | 32.0 |  |
| Pascal Siakam IND | 15.9 | +3.3 | -0.4 | 32.3 | 32.0 |  |
| Michael Porter Jr. BKN | 25.4 | -1.6 | +1.7 | 33.0 | 28.0 |  |

## Missed the same way on 3+ of the last 10 slates

- Nolan Traore: ETR above ours by 6.8, 4.4, 7.5
- Domantas Sabonis: ETR below ours by 4.7, 6.2, 6.2, 4.6
- Deni Avdija: ETR above ours by 3.3, 4.8, 6.0
- Pascal Siakam: ETR below ours by 4.6, 4.7, 3.7
- Jeremiah Fears: ETR above ours by 5.2, 3.1, 4.5
- Lauri Markkanen: ETR below ours by 3.5, 5.8, 3.2, 4.1
- Jalen Johnson: ETR below ours by 3.8, 3.9, 3.8
