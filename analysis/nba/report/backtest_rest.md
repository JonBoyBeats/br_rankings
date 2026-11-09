# NBA tiers backtest: the rest (step 8)

Written by scripts/nba_backtest_rest.py. 6-drafter slates unless marked; a scratch is scored through his swap.

## Players who changed tier between the AM and PM locks

| Move | From the higher of his two tiers | Players | ADP moved (AM to PM, picks earlier) | Projection moved (ETR at PM minus ours at AM) | Score over his PM ADP band | Breakers | Scratched |
|---|---|---|---|---|---|---|---|
| Moved up a tier | T1 | 4 | +0.1 | +4.0 | -7.0 | 0 | 0 |
| Moved up a tier | T2 | 15 | +0.1 | +3.4 | +2.2 | 4 | 0 |
| Moved up a tier | T3 | 23 | +0.6 | +8.0 | -2.0 | 5 | 1 |
| Moved up a tier | T4 | 14 | +1.3 | +5.9 | +3.9 | 4 | 0 |
| Moved down a tier | T1 | 3 | -0.1 | +1.8 | -4.8 | 1 | 0 |
| Moved down a tier | T2 | 8 | -0.6 | +2.3 | -2.1 | 1 | 1 |
| Moved down a tier | T3 | 20 | -0.4 | +2.4 | +0.7 | 3 | 1 |
| Moved down a tier | T4 | 19 | -0.1 | +0.8 | +3.7 | 3 | 0 |
| Same tier | T1 | 48 | +0.0 | +3.5 | +4.7 | 12 | 0 |
| Same tier | T2 | 131 | +0.0 | +3.1 | -1.0 | 21 | 4 |
| Same tier | T3 | 72 | +0.3 | +2.5 | -0.8 | 6 | 6 |
| Same tier | T4 | 82 | +0.0 | +1.9 | -0.2 | 16 | 1 |

## The ceiling blend

Rank correlation of ETR's blended number against its own median, priced players, per slate: 10-21 0.997, 10-22 1.000, 10-23 0.996, 10-24 0.997, 10-25 0.999, 10-26 0.998, 10-27 0.999, 10-28 0.998, 10-29 0.998, 10-30 0.998, 10-31 0.999, 11-01 0.999, 11-02 0.997, 11-04 0.997, 11-05 0.999, 11-06 0.997, 11-07 0.998, 11-08 0.999. Lowest 0.996 (2026-10-23). Every slate is at 0.97 or above: the blend is cosmetic for ordering (it moves the scale, not the order), and our Proj is one number converted both ways (1.0 by construction). No weight test needed.

## Residual correlations (for the contest side)

Residual = actual - ETR's median, every rotation player in every game, 18 nights (2026-10-21 to 2026-11-08). Correlation of two players' residuals in the same game (pairs, each counted once); 80% range from resampling nights. Close to 0: one player's big night says nothing about the other's. Written by scripts/nba_residuals.py.

| Relationship | All games | Spread: close (4.5 or less) | Spread: mid (5-9.5) | Spread: big (10+) |
|---|---|---|---|---|
| teammates: star + star | +0.04 (-0.00 to +0.08), 266 pairs | +0.02 (-0.08 to +0.12), 112 pairs | +0.09 (-0.09 to +0.25), 80 pairs | -0.01 (-0.17 to +0.10), 48 pairs |
| teammates: star + role | -0.01 (-0.03 to +0.01), 3692 pairs | -0.02 (-0.06 to +0.00), 1516 pairs | +0.00 (-0.04 to +0.04), 1108 pairs | -0.04 (-0.08 to -0.01), 692 pairs |
| teammates: role + role | -0.03 (-0.05 to -0.02), 5645 pairs | -0.02 (-0.05 to +0.00), 2245 pairs | -0.03 (-0.06 to -0.01), 1698 pairs | -0.06 (-0.08 to -0.04), 1100 pairs |
| teammates: same position group | -0.06 (-0.08 to -0.04), 3529 pairs | -0.04 (-0.09 to -0.01), 1400 pairs | -0.08 (-0.10 to -0.06), 1112 pairs | -0.10 (-0.14 to -0.08), 682 pairs |
| teammates: all | -0.02 (-0.03 to -0.01), 9603 pairs | -0.02 (-0.04 to -0.00), 3873 pairs | -0.01 (-0.03 to +0.00), 2886 pairs | -0.04 (-0.06 to -0.03), 1840 pairs |
| opponents: star + star | +0.10 (+0.06 to +0.15), 532 pairs | +0.01 (-0.05 to +0.07), 224 pairs | +0.19 (+0.12 to +0.26), 160 pairs | +0.19 (+0.13 to +0.25), 96 pairs |
| opponents: all | +0.00 (-0.01 to +0.01), 10659 pairs | -0.02 (-0.04 to +0.00), 4330 pairs | +0.02 (+0.00 to +0.03), 3180 pairs | +0.02 (-0.01 to +0.04), 2038 pairs |

No split by game total: totals aren't on file yet (the mirror keeps spreads only).

## Small slates (4-drafter pods)

Graded apart in tier_grade.md and tier_rules.md (5 slates so far: 10-20 has no projections, so 4 graded). Almost every cell is "not enough yet"; the only leans are AM middle PRICEY lagging (+6.8, 43 pairs) and AM T5 VALUE (+2.3, 55), both candidates. Nothing adopted on small slates; the 6-drafter switches are not applied to them by the report.
