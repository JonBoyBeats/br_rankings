# Our morning Proj vs ETR's first upload, against ADP

Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's first file; the top 60 by ADP graded (40 on a 4-drafter slate), in four groups: the elite (ETR's top 2-4, cut at the biggest drop), then next / middle / 6th round on by morning ADP: under 19, 19-31 and 32 on with 6 drafters; under 13, 13-20 and 21 on with 4. 15 slates, 2026-10-28 to 2026-11-12. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board averages their last 3 ETR nights from 2026-11-07.

## Season

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 39 | 0.81 | 33/33 (100%) | 15/15 (100%) | - | 12 (31%) | 0.14 / 0.11 | - (0) |
| next | 210 | 0.70 | 85/99 (86%) | 11/12 (92%) | 20/21 (95%) | 47 (22%) | 0.21 / 0.48 | +1.2 (10) |
| middle | 187 | 0.77 | 64/67 (96%) | 9/9 (100%) | 8/8 (100%) | 40 (21%) | 0.28 / 0.52 | +2.0 (19) |
| 6th round on | 401 | 0.85 | 205/226 (91%) | 37/39 (95%) | 46/46 (100%) | 95 (24%) | 0.15 / 0.23 | +1.0 (19) |
| **all** | 837 | 0.82 | 387/425 (91%) | 72/75 (96%) | 74/75 (99%) | 194 (23%) | 0.17 / 0.29 | +1.4 (48) |

## Last 7 slates

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 16 | 0.74 | 15/15 (100%) | 7/7 (100%) | - | 4 (25%) | 0.01 / -0.11 | - (0) |
| next | 106 | 0.72 | 47/53 (89%) | 5/5 (100%) | 10/11 (91%) | 23 (22%) | 0.22 / 0.48 | -0.5 (4) |
| middle | 95 | 0.81 | 25/25 (100%) | 2/2 (100%) | - | 17 (18%) | 0.24 / 0.51 | +0.4 (9) |
| 6th round on | 200 | 0.87 | 111/120 (92%) | 21/21 (100%) | 24/24 (100%) | 51 (26%) | 0.15 / 0.25 | +0.6 (13) |
| **all** | 417 | 0.84 | 198/213 (93%) | 35/35 (100%) | 34/35 (97%) | 95 (23%) | 0.16 / 0.27 | +0.4 (26) |

## Rookies (no last season), before and after the last-3 average

| | n | ETR minus ours | big misses |
|---|---|---|---|
| before 2026-11-07 | 25 | +2.54 | 10 |
| from 2026-11-07 | 23 | +0.27 | 4 |

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
| 2026-11-12 (6 drafters) | 60 | 0.67 | 26/29 (90%) | 5/5 (100%) | 4/5 (80%) | 15 (25%) | 0.10 / 0.34 | -1.1 (2) |

## Biggest misses, 2026-11-12

| player | ADP | ours vs ADP | ETR vs ADP | usual min | min | tag |
|---|---|---|---|---|---|---|
| Max Christie DAL | 35.9 | -0.9 | -12.6 | 19.8 | 7.0 |  |
| Walter Clayton Jr. DAL | 36.0 | -9.0 | +0.2 | 16.5 | 22.0 |  |
| Paul Reed DET | 16.7 | +0.4 | -7.6 | 26.0 | 38.0 |  |
| Daniss Jenkins DET | 23.5 | -4.9 | +1.3 | 25.9 | 42.0 |  |
| Moussa Diabate CHA | 33.7 | +8.1 | +2.4 | 25.6 | 32.0 | Probable |
| Zaccharie Risacher DAL | 35.9 | +1.6 | -3.1 | 24.0 | 25.0 |  |
| Naji Marshall DAL | 36.0 | +12.9 | +8.7 | 22.0 | 23.0 |  |
| Kyrie Irving DAL | 8.3 | -2.9 | +1.3 | 30.6 | 27.0 |  |
| RJ Barrett TOR | 9.6 | +2.2 | -1.8 | 33.8 | 37.0 |  |
| Cade Cunningham DET | 2.2 | +8.7 | +4.7 | 33.3 | 48.0 |  |

## Missed the same way on 3+ of the last 10 slates

- Domantas Sabonis: ETR below ours by 4.7, 6.2, 6.2, 4.6
- Deni Avdija: ETR above ours by 3.3, 4.8, 6.0
- Pascal Siakam: ETR below ours by 4.6, 4.7, 3.7
- Jeremiah Fears: ETR above ours by 5.2, 3.1, 4.5
- Lauri Markkanen: ETR below ours by 3.5, 5.8, 3.2, 4.1
- Jalen Johnson: ETR below ours by 3.8, 3.9, 3.8
