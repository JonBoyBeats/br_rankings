# Our morning Proj vs ETR's first upload, against ADP

Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's first file; the top 60 by ADP graded (40 on a 4-drafter slate), in four groups: the elite (ETR's top 2-4, cut at the biggest drop), then next / middle / 6th round on by morning ADP: under 19, 19-31 and 32 on with 6 drafters; under 13, 13-20 and 21 on with 4. 13 slates, 2026-10-28 to 2026-11-10. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board averages their last 3 ETR nights from 2026-11-07.

## Season

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 34 | 0.82 | 28/28 (100%) | 14/14 (100%) | - | 11 (32%) | 0.12 / 0.12 | - (0) |
| next | 181 | 0.72 | 72/85 (85%) | 9/10 (90%) | 17/17 (100%) | 42 (23%) | 0.19 / 0.45 | +1.2 (10) |
| middle | 159 | 0.79 | 59/62 (95%) | 9/9 (100%) | 8/8 (100%) | 32 (20%) | 0.35 / 0.55 | +2.4 (15) |
| 6th round on | 343 | 0.86 | 175/193 (91%) | 30/32 (94%) | 40/40 (100%) | 82 (24%) | 0.12 / 0.21 | +1.4 (16) |
| **all** | 717 | 0.83 | 334/368 (91%) | 62/65 (95%) | 65/65 (100%) | 167 (23%) | 0.18 / 0.29 | +1.7 (41) |

## Last 7 slates

| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | big misses (3+) | CLV ours / ETR | rookie gap (n) |
|---|---|---|---|---|---|---|---|---|
| elite | 18 | 0.86 | 14/14 (100%) | 7/7 (100%) | - | 6 (33%) | 0.14 / 0.06 | - (0) |
| next | 99 | 0.74 | 42/50 (84%) | 5/5 (100%) | 8/8 (100%) | 24 (24%) | 0.18 / 0.43 | +0.0 (5) |
| middle | 90 | 0.81 | 26/27 (96%) | 4/4 (100%) | 2/2 (100%) | 17 (19%) | 0.35 / 0.57 | +2.2 (8) |
| 6th round on | 190 | 0.87 | 108/119 (91%) | 18/19 (95%) | 25/25 (100%) | 52 (27%) | 0.10 / 0.20 | +1.0 (10) |
| **all** | 397 | 0.84 | 190/210 (90%) | 34/35 (97%) | 35/35 (100%) | 99 (25%) | 0.18 / 0.27 | +1.2 (23) |

## Rookies (no last season), before and after the last-3 average

| | n | ETR minus ours | big misses |
|---|---|---|---|
| before 2026-11-07 | 25 | +2.54 | 10 |
| from 2026-11-07 | 16 | +0.40 | 4 |

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

## Biggest misses, 2026-11-10

| player | ADP | ours vs ADP | ETR vs ADP | usual min | min | tag |
|---|---|---|---|---|---|---|
| Josh Hart NYK | 35.3 | +7.0 | +1.2 | 28.2 | 0.0 | Questionable / Questionable |
| Deni Avdija POR | 12.2 | +1.8 | +6.6 | 32.1 | 34.0 |  |
| Jaylen Brown PHI | 9.3 | -5.1 | -0.4 | 35.9 | 26.0 |  |
| Domantas Sabonis SAC | 13.6 | +4.8 | +0.2 | 35.6 | 24.0 | Questionable |
| Jose Alvarado NYK | 36.0 | -10.2 | -14.1 | 9.0 | 6.0 |  |
| Isaiah Collier UTA | 35.9 | -3.4 | +0.4 | 15.6 | 24.0 |  |
| Brayden Burries MIL (rookie) | 34.3 | -6.8 | -3.1 | 21.0 | 26.0 |  |
| Brook Lopez LAC | 35.4 | -2.3 | +1.3 | 23.9 | 19.0 |  |
| Lauri Markkanen UTA | 26.5 | +9.2 | +6.0 | 30.9 | 0.0 | Questionable / Questionable |
| Bam Adebayo MIA | 7.7 | +0.8 | -2.2 | 32.8 | 37.0 |  |

## Missed the same way on 3+ of the last 10 slates

- Nolan Traore: ETR above ours by 6.8, 4.4, 7.5
- Domantas Sabonis: ETR below ours by 3.2, 4.7, 6.2, 6.2, 4.6
- Lauri Markkanen: ETR below ours by 3.5, 5.8, 3.2
- LaMelo Ball: ETR below ours by 3.8, 3.7, 3.1
