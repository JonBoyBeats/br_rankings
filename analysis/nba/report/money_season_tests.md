# Season tests: T5 and the tier boundaries in contest results

Written by scripts/nba_money_season.py (definitions in its docstring), 2026-10-21 to 2026-11-12: 22 nights, 348989 teams with a draft window and price. Multiples are against the same contest and price quintile (the field averages 1.0). Results only: no rule changes.

## Summary

1. **T5 by drafted%.** The guess doesn't hold: there is no middle sweet spot. Under 20% drafted beats the field (top 1% 1.48x,
   top 10% 1.16x, range 1.02-1.30), 20-70% is the field (1.01x / 1.03x), and 70%+ trails it (0.82x / 0.89x, range 0.84-0.94).
   The line falls somewhere between 20% and 70%; inside 20-70% the bands swing (50-60% 0.66x, 60-70% 1.27x at the top 1%) on
   few players. *Suggests: in T5, the less-drafted player first; the same direction as the T5 ownership tiebreak.*
2. **Upside in T5.** Within a drafted% group, a Boom% above the usual for the projection does about the same as one below it
   (under 20%: 1.54x vs 1.43x at the top 1%, 1.19x vs 1.13x at the top 10%; 20-70%: 0.99x vs 1.02x; 70%+: 0.84x vs 0.80x), with
   ranges that overlap everywhere. *Suggests: Boom adds nothing once drafted% is known; don't use it to order T5.*
3. **Where winners are made.** Top-1% teams beat same-price teams by 62 points: T1 +18.7, T2 +12.3, T3 +11.1, T4 +10.8, T5 +8.7
   (median night: +15.8, +13.5, +5.6, +10.9, +6.5). T1 is the biggest single source; T5 the smallest. *Suggests: the T5 order
   is the smallest of the five levers; it matters, but less than any tier above it.*
4. **Duds and smashes.** A dud is close to fatal in every tier: 0-0.6% of top-1% teams carry one against 3-14% of the field
   (ratios 0.00-0.05); no top-1% team all season had a T5 pick under 60% of that night's T5 average (the field: 6.3%). Smashes
   run 2-3.4x the field's rate; 57.5% of top-1% teams have a T5 smash against 27.4% of the field. *Suggests: in T5, a player's
   floor (will he play his minutes) comes before his ceiling: a T5 bust ends a team, and Boom doesn't sort the smashes (test 2).*
5. **Boundaries.** A T4 VALUE player against a T3 PRICEY one in the same round: 2.58x vs 0.71x at the top 1%, A against B 2.83
   (1.55-4.85) at the top 10%, but on 5 slates only. A T4 PRICEY player against one of the button's top three in T5 in the same
   round: 0.90x vs 1.10x at the top 1%, A against B 0.83 (0.71-0.97) on 10 slates. *Suggests: the top of T5 holds its own
   against T4 PRICEY, so T5's first three needn't wait behind them; T4 VALUE over T3 PRICEY is strong but thin.*

Caveats. Drafted% at lock is the board's modelled share (the field model's curve by ADP rank): T5 has 30 distinct values, and
none falls in 40-50%, so the bands are lumpy, and low drafted% also means the latest picks. Multiples match on the team's
whole price, not on the T5 pick's own price. The T5 average behind a dud counts every T5 player who played (23.4 points on the
season, against 28.2 for the field's T5 picks), so a T5 dud is close to a non-start.

## 1. T5 by how often drafted

| Drafted% at lock | share of the field's T5 picks | top-1% multiple (finishes of expected) | top-10% multiple (80% range) (finishes of expected) | teams |
|---|---|---|---|---|
| 0-10% | 9.8% (32002) | 1.58 (447 of 283.1) | 1.20 (1.00-1.41) (3341 of 2794.3) | 30545 |
| 10-20% | 6.3% (20596) | 1.32 (252 of 191.5) | 1.10 (0.97-1.22) (2089 of 1900.7) | 20438 |
| 20-30% | 2.8% (8974) | 1.02 (88 of 86.0) | 0.96 (0.75-1.21) (818 of 851.8) | 8974 |
| 30-40% | 13.4% (43516) | 1.03 (427 of 415.6) | 1.04 (0.93-1.19) (4159 of 4001.8) | 43227 |
| 40-50% | 0.0% (0) | - | - | 0 |
| 50-60% | 6.5% (21166) | 0.66 (132 of 198.9) | 0.88 (0.70-1.06) (1757 of 1986.4) | 21166 |
| 60-70% | 6.6% (21664) | 1.27 (259 of 204.4) | 1.19 (1.03-1.35) (2424 of 2038.8) | 21664 |
| 70-80% | 12.4% (40360) | 0.63 (247 of 394.7) | 0.77 (0.65-0.89) (2904 of 3793.1) | 40360 |
| 80-90% | 20.9% (68058) | 0.91 (607 of 666.1) | 0.95 (0.81-1.08) (6236 of 6598.6) | 66820 |
| 90-100% | 21.3% (69301) | 0.79 (496 of 629.9) | 0.91 (0.79-1.01) (5642 of 6219.1) | 62278 |
| no drafted% | 0.1% (175) | 0.00 (0 of 1.4) | 0.67 (0.29-1.11) (10 of 14.9) | 175 |
| | | | | |
| **under 20%** | 16.1% (52598) | 1.48 (689 of 466.1) | 1.16 (1.02-1.30) (5341 of 4609.1) | 49816 |
| **20-70%** | 29.3% (95320) | 1.01 (899 of 890.2) | 1.03 (0.96-1.12) (9018 of 8722.8) | 92951 |
| **70%+** | 54.5% (177719) | 0.82 (1269 of 1556.1) | 0.89 (0.84-0.94) (13670 of 15287.1) | 154702 |

## 2. Upside in T5 (Boom% against the usual for his projection)

Usual Boom% for a projection: 0.167 + 0.0022 x (projection - 29.9), from 2002 T5 player-windows.

| Drafted% band | Boom vs usual | top-1% multiple (finishes of expected) | top-10% multiple (80% range) (finishes of expected) | teams |
|---|---|---|---|---|
| **under 20%** | higher | 1.54 (318 of 207.0) | 1.19 (1.04-1.36) (2420 of 2025.7) | 22021 |
| **under 20%** | lower | 1.43 (374 of 261.9) | 1.13 (0.93-1.32) (2952 of 2615.4) | 28505 |
| **20-70%** | higher | 0.99 (396 of 399.6) | 1.01 (0.89-1.13) (3930 of 3902.4) | 41886 |
| **20-70%** | lower | 1.02 (506 of 497.6) | 1.05 (0.94-1.17) (5128 of 4885.6) | 51908 |
| **70%+** | higher | 0.84 (489 of 583.8) | 0.92 (0.78-1.04) (5194 of 5672.6) | 56674 |
| **70%+** | lower | 0.80 (863 of 1077.3) | 0.88 (0.80-0.95) (9349 of 10642.3) | 108906 |
| 0-10% | higher | 1.45 (203 of 139.8) | 1.22 (0.98-1.48) (1655 of 1358.5) | 14758 |
| 0-10% | lower | 1.73 (245 of 141.7) | 1.18 (0.90-1.47) (1685 of 1425.1) | 15960 |
| 10-20% | higher | 1.69 (116 of 68.5) | 1.14 (0.93-1.35) (777 of 680.3) | 7446 |
| 10-20% | lower | 1.10 (136 of 123.4) | 1.07 (0.89-1.23) (1314 of 1224.5) | 13039 |
| 20-30% | higher | 1.39 (79 of 56.7) | 1.10 (0.80-1.50) (618 of 563.3) | 5827 |
| 20-30% | lower | 0.31 (9 of 29.3) | 0.69 (0.46-0.95) (200 of 288.5) | 3147 |
| 30-40% | higher | 1.10 (194 of 175.9) | 1.10 (0.91-1.31) (1841 of 1671.5) | 18403 |
| 30-40% | lower | 0.97 (236 of 242.2) | 0.99 (0.84-1.18) (2334 of 2347.1) | 24939 |
| 50-60% | higher | 0.52 (45 of 86.0) | 0.72 (0.53-0.96) (624 of 864.2) | 9355 |
| 50-60% | lower | 0.77 (87 of 112.9) | 1.01 (0.82-1.17) (1133 of 1122.2) | 11811 |
| 60-70% | higher | 0.95 (79 of 83.6) | 1.03 (0.74-1.33) (859 of 833.2) | 8710 |
| 60-70% | lower | 1.50 (177 of 117.8) | 1.29 (1.04-1.57) (1521 of 1177.4) | 12670 |
| 70-80% | higher | 0.47 (66 of 139.0) | 0.60 (0.43-0.78) (753 of 1263.9) | 12614 |
| 70-80% | lower | 0.71 (181 of 255.7) | 0.85 (0.72-1.01) (2151 of 2529.3) | 27746 |
| 80-90% | higher | 1.07 (296 of 275.9) | 1.13 (0.88-1.35) (3087 of 2732.5) | 27723 |
| 80-90% | lower | 0.79 (312 of 394.0) | 0.81 (0.64-1.02) (3183 of 3909.6) | 39749 |
| 90-100% | higher | 0.72 (137 of 190.7) | 0.81 (0.60-1.02) (1533 of 1887.2) | 18703 |
| 90-100% | lower | 0.83 (398 of 482.0) | 0.94 (0.81-1.06) (4466 of 4747.8) | 47436 |

## 3. Where winners are made: points by tier

| Tier | top-1% minus same-price field, season | median night | top-1% minus whole contest, season | median night |
|---|---|---|---|---|
| T1 | +18.7 | +15.8 | +22.1 | +22.0 |
| T2 | +12.3 | +13.5 | +13.8 | +11.3 |
| T3 | +11.1 | +5.6 | +10.4 | +4.4 |
| T4 | +10.8 | +10.9 | +11.1 | +11.3 |
| T5 | +8.7 | +6.5 | +7.2 | +4.5 |
| no tier row | +0.8 | -0.0 | +1.3 | +0.1 |
| **all six picks** | +62.3 | (+52.2) | +65.8 | (+53.6) |

3592 top-1% teams. Medians don't add up across tiers; the season columns do (every pick has a tier row or falls in "no tier row").

## 4. Dud and smash tolerance

| | Tier | top-1% teams carrying one | field's share (same contest and price) | ratio |
|---|---|---|---|---|
| dud (under 60%) | T1 | 0.0% (0 of 3592) | 2.9% | 0.00 |
| dud (under 60%) | T2 | 0.5% (17 of 3592) | 13.8% | 0.03 |
| dud (under 60%) | T3 | 0.4% (15 of 3592) | 9.3% | 0.05 |
| dud (under 60%) | T4 | 0.6% (22 of 3592) | 11.2% | 0.05 |
| dud (under 60%) | T5 | 0.0% (0 of 3592) | 6.3% | 0.00 |
| smash (over 150%) | T1 | 12.9% (464 of 3592) | 3.9% | 3.35 |
| smash (over 150%) | T2 | 9.4% (336 of 3592) | 4.8% | 1.94 |
| smash (over 150%) | T3 | 17.6% (632 of 3592) | 5.9% | 2.97 |
| smash (over 150%) | T4 | 23.6% (846 of 3592) | 6.9% | 3.42 |
| smash (over 150%) | T5 | 57.5% (2065 of 3592) | 27.4% | 2.10 |

## 5. Boundaries

| Test | pairs | side | top-1% multiple (finishes of expected) | top-10% multiple (80% range) (finishes of expected) | teams |
|---|---|---|---|---|---|
| T4 VALUE (A) vs T3 PRICEY (B) | same round | A | 2.58 (190 of 73.5) | 1.81 (1.28-2.29) (1329 of 732.6) | 8481 |
| | | B | 0.71 (55 of 77.2) | 0.66 (0.41-0.98) (497 of 753.2) | 8696 |
| | | A against B | 2.83 (1.55-4.85) at 10%, 6.05 at 1%; finish -14.8; 8994 teams, 5 slates |
| T4 PRICEY (A) vs a top-3 T5 (B) | same round | A | 0.90 (221 of 246.8) | 0.95 (0.76-1.14) (2325 of 2443.5) | 25365 |
| | | B | 1.10 (339 of 308.2) | 1.00 (0.90-1.11) (2933 of 2931.5) | 29436 |
| | | A against B | 0.83 (0.71-0.97) at 10%, 0.65 at 1%; finish +0.3; 56754 teams, 10 slates |
