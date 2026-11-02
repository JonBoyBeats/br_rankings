# NBA residual correlations

Residual = actual - ETR's median, every rotation player in every game, 12 nights (2026-10-21 to 2026-11-01). Correlation of two players' residuals in the same game (pairs, each counted once); 80% range from resampling nights. Close to 0: one player's big night says nothing about the other's. Written by scripts/nba_residuals.py.

| Relationship | All games | Spread: close (4.5 or less) | Spread: mid (5-9.5) | Spread: big (10+) |
|---|---|---|---|---|
| teammates: star + star | -0.00 (-0.05 to +0.03), 164 pairs | +0.03 (-0.09 to +0.16), 68 pairs | -0.11 (-0.37 to +0.09), 48 pairs | -0.08 (-0.39 to +0.17), 22 pairs |
| teammates: star + role | -0.02 (-0.04 to -0.00), 2280 pairs | -0.06 (-0.09 to -0.03), 936 pairs | -0.03 (-0.06 to +0.01), 658 pairs | -0.01 (-0.07 to +0.01), 310 pairs |
| teammates: role + role | -0.02 (-0.04 to -0.00), 3489 pairs | -0.01 (-0.04 to +0.01), 1414 pairs | -0.02 (-0.05 to +0.02), 994 pairs | -0.07 (-0.10 to -0.04), 479 pairs |
| teammates: same position group | -0.06 (-0.09 to -0.03), 2145 pairs | -0.05 (-0.12 to -0.00), 862 pairs | -0.10 (-0.12 to -0.08), 641 pairs | -0.11 (-0.16 to -0.06), 307 pairs |
| teammates: all | -0.02 (-0.03 to -0.00), 5933 pairs | -0.03 (-0.05 to -0.01), 2418 pairs | -0.02 (-0.05 to -0.01), 1700 pairs | -0.04 (-0.07 to -0.03), 811 pairs |
| opponents: star + star | +0.09 (+0.04 to +0.14), 328 pairs | +0.03 (-0.03 to +0.10), 136 pairs | +0.09 (+0.04 to +0.14), 96 pairs | +0.25 (+0.13 to +0.33), 44 pairs |
| opponents: all | +0.00 (-0.02 to +0.02), 6592 pairs | -0.01 (-0.04 to +0.02), 2702 pairs | +0.00 (-0.01 to +0.01), 1877 pairs | +0.03 (-0.00 to +0.05), 902 pairs |

No split by game total: totals aren't on file yet (the mirror keeps spreads only).
