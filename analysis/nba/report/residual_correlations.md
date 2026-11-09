# NBA residual correlations

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
