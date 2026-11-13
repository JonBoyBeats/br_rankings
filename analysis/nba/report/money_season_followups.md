# Season follow-ups: real ownership in T5, the tiebreak's width, the edge by tier, duds at the cash line

Written by scripts/nba_money_season2.py (definitions in its docstring), 2026-10-21 to 2026-11-12: 22 nights, 348989 teams with a draft window and price. Multiples are against the same contest and price quintile (the field averages 1.0). Results only: no rule changes.

## Summary

1. **Real ownership.** A player can go to one team per pod, so real ownership tops out at 1 in 6 (16.7%) on 6-drafter nights
   and 1 in 4 (25%) on 4-drafter nights: nothing reaches 30%, and 20-30% is 4-drafter nights only. Swaps move picks into the
   middle (10-20% holds 49% of T5 picks at the draft, 61% after swaps). *For T5: read ownership as a share of pods (ownership
   x pod size); the board's drafted% is that share.*
2. **T5 leverage curve.** At the draft: 0-5% 1.30x at the top 1% (1.10x at the top 10%), 5-10% 1.20x (1.12x), 10-20% 0.80x
   (0.90x, range 0.85-0.94), 20-30% 0.70x (0.80x). It crosses 1.0 at about 10% owned, which is about 60% of pods on a
   6-drafter night. After swaps the curve is flatter (1.01x, 0.99x, 0.96x, 0.80x at the top 10%). *For T5: a player taken in
   most pods trails the field; under about 10% owned is where the edge is.*
3. **How wide the less-owned tiebreak can go.** For two T5 players within X projected points, the less-owned one's holders
   beat the more-owned one's at every width tested: top 10% 1.23 at 2 points, 1.20 at 3, 1.17 at 4 and 5, 1.15 at 6 (range
   1.08-1.23, every resample above 1); top 1% 1.49 down to 1.34. The edge thins slowly and is still there at 6, the widest
   tested. *For T5: the less-owned tiebreak holds out to at least 6 projected points, three times today's 2.*
4. **Share of the edge.** T1 carries 30% of the top-1% teams' 62-point edge on 15% of the field's points (2.0x its weight); T2
   20% on 32% (0.6x); T3 and T4 about their weight (0.9x); T5 14% on 12% (1.1x). *For T5: it pulls a little more than its
   points' share, so its order matters somewhat more than its size suggests; T1 is still the big lever.*
5. **Duds and smashes at the cash line.** A dud cuts a team's cash rate to 0.10-0.37x of the field's (T5: 0.29x cash, 0.18x top
   10%, no top-1% team). A smash lifts cash 1.5-2.6x; T5's smash is the smallest lift (1.49x cash, 1.63x top 10%) because T5
   smashes are common (28% of the field's teams have one). *For T5: a bust costs about as much as anywhere else and a smash buys
   the least, so a T5 player's floor (his minutes) comes before his ceiling.*

Caveats. Ownership is counted from the contest's own rosters (draft: a swapped-in pick credited to the ruled-out player
where the swap is credited). Test 3 counts a team once for each pair it falls in, and pairs aren't held to an ADP window, so
the less-owned player is often the later pick; teams are matched on whole-team price, not the pick's.

## 1-2. T5 by real ownership

**Draft ownership**

| T5 ownership | share of the field's T5 picks | top 1% (finishes of expected) | cash (of expected) | top 10% (80% range) (of expected) | teams |
|---|---|---|---|---|---|
| 0-5% | 20.6% (67228) | 1.30 (782 of 599.4) | 1.07 (11510 of 10771.4) | 1.10 (0.97-1.25) (6521 of 5904.0) | 63641 |
| 5-10% | 22.6% (73615) | 1.20 (811 of 678.4) | 1.09 (13441 of 12344.9) | 1.12 (1.00-1.25) (7564 of 6752.7) | 71830 |
| 10-20% | 48.6% (158202) | 0.80 (1124 of 1408.2) | 0.92 (22416 of 24296.9) | 0.90 (0.85-0.94) (12328 of 13741.4) | 138414 |
| 20-30% | 8.2% (26767) | 0.70 (162 of 230.1) | 0.85 (3834 of 4487.8) | 0.80 (0.75-0.87) (1820 of 2264.0) | 23669 |
| 30-50% | 0.0% (0) | - | - | - | 0 |
| 50%+ | 0.0% (0) | - | - | - | 0 |

**After swaps ownership**

| T5 ownership | share of the field's T5 picks | top 1% (finishes of expected) | cash (of expected) | top 10% (80% range) (of expected) | teams |
|---|---|---|---|---|---|
| 0-5% | 17.8% (67801) | 1.18 (721 of 609.2) | 0.98 (10678 of 10898.1) | 1.01 (0.88-1.15) (6053 of 5983.5) | 62900 |
| 5-10% | 14.0% (53345) | 0.93 (471 of 504.8) | 0.99 (9024 of 9106.9) | 0.99 (0.89-1.09) (4911 of 4983.4) | 52204 |
| 10-20% | 60.9% (231466) | 0.95 (1802 of 1902.5) | 0.97 (32187 of 33208.5) | 0.96 (0.91-1.01) (17885 of 18575.3) | 186340 |
| 20-30% | 7.3% (27653) | 0.70 (164 of 235.7) | 0.85 (3897 of 4585.2) | 0.80 (0.75-0.86) (1856 of 2317.5) | 24236 |
| 30-50% | 0.0% (0) | - | - | - | 0 |
| 50%+ | 0.0% (0) | - | - | - | 0 |

## 3. T5: how wide the less-owned tiebreak can go

| Within (projected points) | ownership | less-owned's holders against the more-owned's: top 1% | cash | top 10% (80% range; share of resamples above 1) | team-pairs A / B | slates |
|---|---|---|---|---|---|---|
| 2 | draft | 1.49 | 1.18 | 1.23 (1.15-1.31; 100%) | 541293 / 2170578 | 21 |
| 3 | draft | 1.42 | 1.15 | 1.20 (1.12-1.28; 100%) | 762531 / 3266426 | 21 |
| 4 | draft | 1.38 | 1.13 | 1.17 (1.09-1.26; 100%) | 918529 / 4386031 | 21 |
| 5 | draft | 1.37 | 1.13 | 1.17 (1.10-1.25; 100%) | 1039829 / 5441910 | 21 |
| 6 | draft | 1.34 | 1.11 | 1.15 (1.08-1.23; 100%) | 1131965 / 6533590 | 21 |
| 2 | after swaps | 1.40 | 1.14 | 1.18 (1.10-1.27; 100%) | 634472 / 2559918 | 21 |
| 3 | after swaps | 1.34 | 1.12 | 1.16 (1.09-1.23; 100%) | 898918 / 3859891 | 21 |
| 4 | after swaps | 1.31 | 1.11 | 1.14 (1.06-1.22; 100%) | 1085073 / 5171701 | 21 |
| 5 | after swaps | 1.29 | 1.10 | 1.13 (1.06-1.21; 100%) | 1232628 / 6409339 | 21 |
| 6 | after swaps | 1.24 | 1.08 | 1.11 (1.04-1.17; 99%) | 1340439 / 7687989 | 21 |

## 4. Share of the edge by tier

| Tier | top-1% edge over same-price teams | share of the edge | field's average points | share of the field's points | edge share over points share |
|---|---|---|---|---|---|
| T1 | +18.7 | 30% | 32.1 | 15% | 2.01 |
| T2 | +12.3 | 20% | 69.6 | 32% | 0.61 |
| T3 | +11.1 | 18% | 42.1 | 20% | 0.91 |
| T4 | +10.8 | 17% | 41.9 | 19% | 0.89 |
| T5 | +8.7 | 14% | 26.3 | 12% | 1.14 |
| no tier row | +0.8 | 1% | 3.3 | 2% | 0.85 |
| **all** | +62.3 | 100% | 215.3 | 100% | |

## 5. Duds and smashes at the cash line

| | Tier | top 1% (finishes of expected) | cash (of expected) | top 10% (80% range) (of expected) | teams |
|---|---|---|---|---|---|
| dud (under 60%) | T1 | 0.00 (0 of 105.2) | 0.10 (185 of 1844.1) | 0.03 (0.01-0.06) (28 of 943.6) | 10358 |
| dud (under 60%) | T2 | 0.03 (17 of 495.6) | 0.23 (2079 of 9113.1) | 0.14 (0.08-0.21) (693 of 4893.0) | 50037 |
| dud (under 60%) | T3 | 0.05 (15 of 332.6) | 0.26 (1661 of 6505.3) | 0.16 (0.13-0.19) (524 of 3261.9) | 34583 |
| dud (under 60%) | T4 | 0.05 (22 of 403.5) | 0.37 (2577 of 6977.4) | 0.25 (0.19-0.30) (966 of 3928.0) | 39392 |
| dud (under 60%) | T5 | 0.00 (0 of 226.0) | 0.29 (1113 of 3836.9) | 0.18 (0.13-0.21) (383 of 2158.9) | 21695 |
| smash (over 150%) | T1 | 3.35 (464 of 138.6) | 2.57 (5835 of 2271.4) | 2.91 (2.71-3.13) (3604 of 1240.0) | 9825 |
| smash (over 150%) | T2 | 1.94 (336 of 173.6) | 1.56 (5283 of 3384.0) | 1.66 (1.52-1.81) (2914 of 1751.0) | 16437 |
| smash (over 150%) | T3 | 2.97 (632 of 212.7) | 1.91 (8636 of 4513.4) | 2.19 (2.02-2.38) (4767 of 2181.0) | 22089 |
| smash (over 150%) | T4 | 3.42 (846 of 247.1) | 1.99 (8168 of 4114.4) | 2.23 (2.04-2.45) (5118 of 2296.7) | 21705 |
| smash (over 150%) | T5 | 2.10 (2065 of 984.4) | 1.49 (25649 of 17165.7) | 1.63 (1.49-1.81) (15623 of 9578.8) | 98336 |
