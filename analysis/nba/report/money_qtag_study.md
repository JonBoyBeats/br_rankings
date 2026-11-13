# Q-tag study: drafting Q-tagged players, their swaps and their teammates, in contest results

Written by scripts/nba_money_qtags.py (definitions in its docstring), 2026-10-21 to 2026-11-12: 22 nights, 348989 teams with a draft window and price, 348989 of them matched to the snapshot they drafted at. Multiples are against the same contest and price quintile (the field averages 1.0). Results only: no rule changes.

Tag history: Underdog's tag on each priced player in the ADP mirror's snapshots, 747 snapshots over these slates, median 1.0 hours apart (90% within 1.0 hours); a team's draft hour is matched to one of them.

## Summary

(written by hand from the tables below when the file is published)

## 1. The whole bet

### By the tier the Q pick was taken in

| Group | top 1% (finishes of expected) | cash (of expected) | top 10% (80% range) (of expected) | teams |
|---|---|---|---|---|
| no Q pick | 0.98 (2981 of 3043.9) | 0.99 (53729 of 54066.3) | 0.99 (0.97-1.01) (29579 of 29807.1) | 298166 |
| any Q pick | 1.11 (611 of 548.1) | 1.03 (10151 of 9813.7) | 1.04 (0.92-1.18) (5509 of 5280.9) | 50823 |
| T1 | 0.33 (8 of 24.3) | 0.97 (446 of 458.1) | 0.86 (196 of 227.6) | 1969 |
| T2 | 1.48 (303 of 204.4) | 1.22 (4375 of 3594.3) | 1.29 (0.92-1.62) (2479 of 1924.2) | 17006 |
| T3 | 0.98 (171 of 173.9) | 0.95 (3063 of 3209.7) | 0.95 (0.77-1.19) (1593 of 1684.4) | 16595 |
| T4 | 0.98 (82 of 83.3) | 0.95 (1499 of 1583.8) | 0.94 (0.69-1.35) (772 of 824.4) | 8568 |
| T5 | 0.96 (84 of 87.9) | 1.09 (1546 of 1423.8) | 1.04 (0.89-1.27) (899 of 861.0) | 8709 |
| T? | 0.76 (15 of 19.8) | 0.69 (266 of 383.2) | 0.61 (0.59-0.82) (117 of 190.8) | 1851 |

### By his final status

| Group | top 1% (finishes of expected) | cash (of expected) | top 10% (80% range) (of expected) | teams |
|---|---|---|---|---|
| Q pick played | 1.30 (449 of 345.3) | 1.14 (7109 of 6241.4) | 1.18 (0.94-1.43) (3901 of 3292.8) | 31093 |
| Q pick sat | 0.77 (176 of 227.2) | 0.85 (3448 of 4045.3) | 0.81 (0.73-0.88) (1795 of 2229.6) | 22009 |

### By how far he fell past his pre-tag ADP (ADP at the team's draft hour minus the last ADP before the tag)

| Group | top 1% (finishes of expected) | cash (of expected) | top 10% (80% range) (of expected) | teams |
|---|---|---|---|---|
| fell rose | 1.37 (9 of 6.6) | 1.18 (136 of 115.5) | 1.12 (0.66-1.37) (66 of 59.1) | 569 |
| fell 0-3 picks | 1.61 (266 of 165.7) | 1.26 (3648 of 2904.2) | 1.34 (0.98-1.58) (2043 of 1522.0) | 12549 |
| fell 3-6 picks | 1.80 (48 of 26.7) | 1.29 (650 of 503.4) | 1.44 (1.16-1.57) (369 of 256.3) | 2313 |
| fell 6+ picks | 0.21 (10 of 47.2) | 0.67 (660 of 992.5) | 0.48 (0.36-0.89) (227 of 471.2) | 4949 |
| fell tagged from the first snapshot | 0.94 (316 of 336.4) | 0.96 (5719 of 5943.7) | 0.95 (0.86-1.07) (3136 of 3296.6) | 33350 |

### By turn (the Q pick among the team's two turn picks)

| Group | top 1% (finishes of expected) | cash (of expected) | top 10% (80% range) (of expected) | teams |
|---|---|---|---|---|
| 1/2 turn, a turn pick Q-tagged | 0.54 (12 of 22.3) | 0.96 (375 of 392.2) | 0.88 (0.60-1.01) (184 of 208.7) | 1841 |
| 1/2 turn, no Q at the turn | 0.91 (1393 of 1532.8) | 0.94 (26508 of 28090.0) | 0.92 (0.81-1.02) (13965 of 15184.8) | 158026 |
| 2/3 turn, a turn pick Q-tagged | 2.29 (253 of 110.7) | 1.49 (2878 of 1933.2) | 1.71 (1.07-2.34) (1776 of 1040.1) | 8661 |
| 2/3 turn, no Q at the turn | 1.11 (1272 of 1143.4) | 1.06 (20898 of 19667.0) | 1.06 (0.89-1.26) (11755 of 11044.6) | 104986 |

## 2. Cost of an out

### Teams whose Q pick sat, and played, by tier

| Group | top 1% (finishes of expected) | cash (of expected) | top 10% (80% range) (of expected) | teams |
|---|---|---|---|---|
| T1, played | 0.33 (8 of 24.3) | 0.97 (446 of 458.1) | 0.86 (196 of 227.6) | 1969 |
| T2, sat | 0.58 (28 of 48.4) | 0.76 (619 of 811.9) | 0.75 (0.35-0.82) (352 of 467.9) | 4525 |
| T2, played | 1.76 (276 of 156.5) | 1.35 (3771 of 2790.3) | 1.46 (0.94-1.92) (2139 of 1460.5) | 12507 |
| T3, sat | 0.70 (78 of 112.0) | 0.84 (1764 of 2110.5) | 0.77 (0.69-0.86) (861 of 1120.5) | 11422 |
| T3, played | 1.48 (93 of 63.0) | 1.17 (1317 of 1130.4) | 1.28 (0.77-1.86) (737 of 577.2) | 5324 |
| T4, sat | 0.75 (12 of 16.0) | 0.75 (205 of 273.4) | 0.69 (0.48-0.86) (111 of 161.9) | 1647 |
| T4, played | 1.04 (70 of 67.3) | 0.99 (1294 of 1310.4) | 1.00 (0.72-1.72) (661 of 662.4) | 6921 |
| T5, sat | 1.39 (44 of 31.6) | 1.27 (605 of 476.6) | 1.23 (0.95-1.29) (362 of 294.5) | 2625 |
| T5, played | 0.71 (40 of 56.3) | 0.99 (941 of 947.4) | 0.95 (0.81-1.30) (537 of 566.7) | 6086 |
| T?, sat | 0.76 (15 of 19.8) | 0.69 (266 of 382.9) | 0.61 (0.59-0.83) (117 of 190.6) | 1849 |
| T?, played | 0.00 (0 of 0.0) | 0.00 (0 of 0.3) | 0.00 (0 of 0.2) | 2 |

## 3. Swap crowding

22 nights with swaps, 1983 swap targets across contests, 221 crowd swaps (after-swap share of pods 15+ points above the draft's).

### Swap targets against the field

| Group | top 1% (finishes of expected) | cash (of expected) | top 10% (80% range) (of expected) | teams |
|---|---|---|---|---|
| crowd swap | 0.99 (399 of 403.9) | 0.92 (6477 of 7038.8) | 0.91 (0.77-1.05) (3567 of 3900.4) | 37021 |
| other swap | 0.73 (226 of 310.8) | 0.77 (4217 of 5503.4) | 0.74 (0.66-0.82) (2228 of 3000.8) | 28098 |
| crowd swap, with an other target within 6 projected points | 1.02 (399 of 392.9) | 0.94 (6468 of 6855.4) | 0.94 (0.81-1.07) (3563 of 3788.6) | 35499 |
| other swap, with a crowd target within 6 projected points | 0.76 (206 of 269.8) | 0.79 (3816 of 4807.8) | 0.77 (0.68-0.86) (2008 of 2616.9) | 24855 |

Crowd swap against other swap targets within 6 projected points, same contest and price quintile: top 1% 1.34, cash 1.19, top 10% 1.22 (80% range 1.02-1.48; 93% of resamples above 1); 35464 / 24852 teams, 15 slates.

## 4. Beneficiaries before the news

### Teams holding a T1-T4 teammate of a Q-tagged player, against the field

| Group | top 1% (finishes of expected) | cash (of expected) | top 10% (80% range) (of expected) | teams |
|---|---|---|---|---|
| no beneficiary | 0.94 (1314 of 1403.2) | 0.95 (24081 of 25312.3) | 0.94 (0.89-0.98) (12886 of 13761.1) | 139763 |
| T1 beneficiary, Q teammate sat | 1.46 (272 of 186.5) | 1.38 (4484 of 3250.4) | 1.43 (1.06-1.68) (2609 of 1822.4) | 18794 |
| T1 beneficiary, Q teammate played | 1.16 (134 of 115.7) | 1.05 (2234 of 2135.0) | 1.09 (0.68-1.50) (1252 of 1149.4) | 10774 |
| T2 beneficiary, Q teammate sat | 0.91 (743 of 819.4) | 0.93 (13492 of 14561.6) | 0.92 (0.82-1.02) (7338 of 7961.4) | 78288 |
| T2 beneficiary, Q teammate played | 0.93 (500 of 539.9) | 1.04 (10025 of 9618.7) | 1.04 (0.90-1.20) (5461 of 5233.6) | 50144 |
| T3 beneficiary, Q teammate sat | 1.19 (657 of 551.9) | 1.08 (10238 of 9499.6) | 1.07 (0.93-1.21) (5671 of 5298.8) | 52303 |
| T3 beneficiary, Q teammate played | 0.92 (273 of 296.4) | 0.96 (5515 of 5732.7) | 0.94 (0.77-1.11) (2811 of 2999.0) | 31393 |
| T4 beneficiary, Q teammate sat | 1.08 (612 of 564.4) | 1.07 (10017 of 9404.5) | 1.08 (0.97-1.19) (5780 of 5338.0) | 50874 |
| T4 beneficiary, Q teammate played | 1.11 (389 of 351.0) | 1.10 (6990 of 6351.1) | 1.13 (1.00-1.31) (3931 of 3481.8) | 33725 |

