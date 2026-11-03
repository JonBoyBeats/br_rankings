# NBA residual correlations

Residual = actual - ETR's median, every rotation player in every game, 13 nights (2026-10-21 to 2026-11-02). Correlation of two players' residuals in the same game (pairs, each counted once); 80% range from resampling nights. Close to 0: one player's big night says nothing about the other's. Written by scripts/nba_residuals.py.

| Relationship | All games | Spread: close (4.5 or less) | Spread: mid (5-9.5) | Spread: big (10+) |
|---|---|---|---|---|
| teammates: star + star | -0.00 (-0.04 to +0.03), 194 pairs | +0.04 (-0.10 to +0.14), 82 pairs | -0.06 (-0.26 to +0.12), 58 pairs | -0.12 (-0.43 to +0.07), 28 pairs |
| teammates: star + role | -0.02 (-0.04 to -0.00), 2666 pairs | -0.06 (-0.08 to -0.03), 1110 pairs | -0.02 (-0.05 to +0.01), 786 pairs | -0.02 (-0.07 to +0.00), 394 pairs |
| teammates: role + role | -0.02 (-0.04 to -0.00), 4036 pairs | -0.01 (-0.03 to +0.01), 1646 pairs | -0.02 (-0.06 to +0.01), 1178 pairs | -0.07 (-0.10 to -0.05), 610 pairs |
| teammates: same position group | -0.06 (-0.09 to -0.03), 2505 pairs | -0.05 (-0.11 to -0.00), 1013 pairs | -0.08 (-0.11 to -0.06), 772 pairs | -0.10 (-0.15 to -0.07), 385 pairs |
| teammates: all | -0.02 (-0.03 to -0.01), 6896 pairs | -0.03 (-0.04 to -0.01), 2838 pairs | -0.02 (-0.04 to -0.01), 2022 pairs | -0.05 (-0.08 to -0.03), 1032 pairs |
| opponents: star + star | +0.08 (+0.04 to +0.13), 388 pairs | +0.02 (-0.04 to +0.09), 164 pairs | +0.09 (+0.06 to +0.14), 116 pairs | +0.23 (+0.09 to +0.32), 56 pairs |
| opponents: all | +0.00 (-0.01 to +0.02), 7656 pairs | -0.01 (-0.03 to +0.02), 3175 pairs | +0.01 (-0.01 to +0.02), 2226 pairs | +0.04 (+0.01 to +0.05), 1144 pairs |

No split by game total: totals aren't on file yet (the mirror keeps spreads only).
