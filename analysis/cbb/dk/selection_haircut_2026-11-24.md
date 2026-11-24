# The selection haircut: does lowering our own lineups' simulated scores fix the overconfidence?

2026-11-24, the coordinator's follow-up to analysis/cbb/dk/lateswap_calibration_2026-11-24.md (analysis only; nothing on the page changes). `python3 scripts/dk_selection_haircut.py` (part a reads the calibration's results: `python3 scripts/dk_lateswap_calib.py` first).

## Verdict

- **Late swap (a): does not pass the bar.** Held out by night, the flat haircut beats no haircut on 6 of 9 nights (worse on 3), mean Brier gain 0.00301 against 2 x SE 0.01158; the scaled one on 4 of 9 (worse on 4), 0.00008 against 0.00605. Directionally it is right: pooled, a flat 4-6 point haircut brings our stated first-break payout from $649 to $376-449 against $376 paid and the 20-95% cash band to within 2-3 points, and lowers the pooled Brier score from 0.1538 to 0.1447; but night by night it is not consistent enough to clear the bar.
- **Pre-lock (b): the inflation is roughly uniform, not concentrated.** Across 7 builds, the projection-rank top tenth of kept lineups (or the board's own top tenth where saved) came in -6.7 points under its projection against -5.1 for the rest; the gap (top tenth minus the rest) was negative on 3 of 7 nights.
- **Pre-lock payouts are not inflated:** on the 4 builds that saved the board's values, the simulated payout per entry matched the real one tier by tier: the top tenth $1.48 simulated against $1.46 real, the rest $1.09 against $1.06; the variants $1.49 against $3.79 (mostly one night). Pooled by lineup the top tenth did come in further under its projection (-12.0 points against -6.4 for the rest), but that comes from which nights each tier is drawn from (the board's top tenth exists only on the 4 newer builds, two of them nights everything ran 20+ points under); night by night the gap is not consistent.
- **What a haircut would change:** a haircut that lowers every one of our lineups by the same amount leaves their order unchanged, so the cut and the fill (which rank our lineups against each other on the same field) would keep and enter the same lineups; only the stated numbers move. Only a haircut that hits the most-selected lineups harder would reshuffle them, and the evidence above says whether that is warranted.
- **Recommendation:** no page change: the haircut does not pass held out. Keep reading our stated late-swap payout and top 1% as inflated (the calibration's ~1.7x on payout); revisit with more nights.
- **2026-11-24 is not in:** its final standings were not saved by this run (the sync repo holds mid-slate standings only).
- **The live-points fix (no ESPN id) and the calibration:** the calibration re-run after the fix (8886226) changes only 2026-11-19 main (130 of its 272 entry-breaks; its stated cash 33.9% -> 43.1%, with Malique Ewin's points now counted). Pooled, our final totals outside the simulated 5-95% band fall from 16.9% to 14.2% and the sd of the standardized miss from 3.05 to 1.03 (the spread is right once the gap is closed); the first-break payout totals ($648 stated vs $376 paid) do not move, and our entries now finish further under their simulated mean (mean percentile 0.427).

## (a) Late swap: our entries with a haircut

Our entries' stated numbers with the haircut, every break of 9 nights; payout at each night's first break (each entry once).

| Haircut | Brier (cash + top 1%) | Stated $ | Paid $ | Mid cash (20–95% stated): n / stated / real | Top 1% (5–50% stated): n / stated / real |
|---|---|---|---|---|---|
| flat 0 | 0.1538 | 649 | 376 | 719 / 47.5% / 37.3% | 148 / 11.5% / 4.7% |
| flat 1 | 0.1503 | 593 | 376 | 709 / 46.2% / 37.9% | 129 / 11.1% / 5.4% |
| flat 2 | 0.1478 | 540 | 376 | 695 / 44.9% / 38.8% | 108 / 11.0% / 6.5% |
| flat 3 | 0.1458 | 494 | 376 | 686 / 43.7% / 39.7% | 93 / 11.1% / 6.5% |
| flat 4 | 0.1447 | 449 | 376 | 668 / 42.5% / 40.3% | 72 / 11.4% / 8.3% |
| flat 6 | 0.1447 | 376 | 376 | 632 / 40.9% / 42.9% | 52 / 11.1% / 9.6% |
| flat 8 | 0.1477 | 315 | 376 | 569 / 39.7% / 45.5% | 36 / 13.0% / 16.7% |
| scaled 0.25 | 0.1494 | 453 | 376 | 734 / 41.8% / 41.6% | 35 / 9.6% / 20.0% |
| scaled 0.5 | 0.1727 | 328 | 376 | 707 / 33.6% / 43.0% | 1 / 6.7% / 0.0% |
| scaled 0.75 | 0.2155 | 246 | 376 | 542 / 25.7% / 43.4% | 0 / –% / –% |
| scaled 1 | 0.2505 | 181 | 376 | 223 / 23.0% / 31.4% | 0 / –% / –% |

Held out by night, flat points (the size picked on the other nights):

| Night | Slate | Picked | Brier, none | Brier, picked | Stated $, none | Stated $, picked | Paid $ |
|---|---|---|---|---|---|---|---|
| 2026-11-16 | 156660 | flat 4 | 0.0624 | 0.0381 | 19.38 | 9.62 | 0.00 |
| 2026-11-17 | 156663 | flat 4 | 0.1045 | 0.0927 | 38.10 | 27.49 | 8.00 |
| 2026-11-20 | 157013 | flat 6 | 0.1868 | 0.1904 | 121.75 | 64.98 | 46.25 |
| 2026-11-20 | 157015 | flat 6 | 0.2013 | 0.1997 | 151.98 | 96.09 | 139.75 |
| 2026-11-21 | 157017 | flat 6 | 0.0831 | 0.0722 | 24.90 | 15.66 | 2.90 |
| 2026-11-22 | 157019 | flat 6 | 0.2763 | 0.2924 | 1.90 | 1.21 | 2.50 |
| 2026-11-18 | 157033 | flat 4 | 0.1023 | 0.0960 | 59.36 | 38.01 | 131.40 |
| 2026-11-19 | 157138 | flat 6 | 0.2249 | 0.2545 | 43.50 | 19.80 | 27.50 |
| 2026-11-19 | 157139 | flat 4 | 0.1608 | 0.1395 | 187.70 | 136.79 | 17.60 |

Held out by night, scaled by the lineup's simulated mean over the contest's (the size picked on the other nights):

| Night | Slate | Picked | Brier, none | Brier, picked | Stated $, none | Stated $, picked | Paid $ |
|---|---|---|---|---|---|---|---|
| 2026-11-16 | 156660 | scaled 0.25 | 0.0624 | 0.0465 | 19.38 | 10.79 | 0.00 |
| 2026-11-17 | 156663 | scaled 0.25 | 0.1045 | 0.1002 | 38.10 | 30.00 | 8.00 |
| 2026-11-20 | 157013 | scaled 0.25 | 0.1868 | 0.1958 | 121.75 | 77.10 | 46.25 |
| 2026-11-20 | 157015 | scaled 0.25 | 0.2013 | 0.1999 | 151.98 | 106.13 | 139.75 |
| 2026-11-21 | 157017 | scaled 0.25 | 0.0831 | 0.0897 | 24.90 | 19.25 | 2.90 |
| 2026-11-22 | 157019 | scaled 0.25 | 0.2763 | 0.2667 | 1.90 | 1.60 | 2.50 |
| 2026-11-18 | 157033 | scaled 0.25 | 0.1023 | 0.1043 | 59.36 | 43.17 | 131.40 |
| 2026-11-19 | 157138 | scaled 0.25 | 0.2249 | 0.2378 | 43.50 | 29.31 | 27.50 |
| 2026-11-19 | 157139 | flat 0 | 0.1608 | 0.1608 | 187.70 | 187.70 | 17.60 |

## (b) Pre-lock: kept lineups' real results by how selected they are

Real points minus projected points (the projection the sim drew from), and where the build saved the board's values, the simulated payout per entry against the real payout over the board's contests (weighted as the board weights them). Top tenth: the board's top tenth by simulated value; on the builds saved before the board's values, the top tenth by projected points stands in.

| Tier | Kept lineups | Real − projected points | Sim payout / entry | Real payout / entry | Lineups with both |
|---|---|---|---|---|---|
| top tenth | 710 | -11.96 | $1.48 | $1.46 | 710 |
| top tenth (proj) | 450 | -1.79 | – | – | 0 |
| variants | 400 | +0.52 | $1.49 | $3.79 | 400 |
| rest | 10839 | -6.43 | $1.09 | $1.06 | 6789 |

Per night (real − projected points):

| Night | Slate | Kept | Top tenth | Variants | Rest | Entered | Top tenth − rest | Board values saved |
|---|---|---|---|---|---|---|---|---|
| 2026-11-16 | 156660 | 1000 | +5.75 | – | +13.78 | +1.68 | -8.03 | no |
| 2026-11-17 | 156663 | 2000 | -15.14 | – | -3.82 | -11.26 | -11.32 | no |
| 2026-11-18 | 157033 | 1500 | +10.99 | – | +9.87 | +5.16 | +1.12 | no |
| 2026-11-19 | 157138 | 1521 | -23.23 | -11.72 | -25.50 | -17.54 | +2.27 | yes |
| 2026-11-19 | 157139 | 2098 | -0.61 | +5.88 | -2.92 | +0.52 | +2.31 | yes |
| 2026-11-20 | 157013 | 2002 | -22.89 | -24.48 | -22.86 | -18.25 | -0.03 | yes |
| 2026-11-20 | 157015 | 2278 | -1.57 | -0.07 | -4.24 | -1.80 | +2.67 | yes |
