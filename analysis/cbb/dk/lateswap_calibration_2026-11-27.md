# Late swap: are the stated numbers calibrated?

2026-11-24, the coordinator's request (analysis only; nothing on the page changes). `python3 scripts/dk_lateswap_calib.py`.

At each tip break of 15 saved nights (the 2026-11-21 backtest's five plus 2026-11-24:157024, 2026-11-24:157026, 2026-11-25:157293, 2026-11-25:157295, 2026-11-26:157380, 2026-11-26:157382 and the later graded nights), every one of our entries' **stated** cash %, top-1 % and expected payout is rebuilt with the page's own code (dk_sim.js nights at the page's 1,000, dk_swap.js board and field draws, the chalk fitted per contest as the page does, the started games' points so far from ESPN's play-by-play at the next tip) and scored against the real final standings. A random 40 field entries per contest are scored the same way (their lineups known, as ours are). An entry counts once per break, so a night's entries repeat across its breaks: the night is the unit, and the per-night rows carry the weight.

## Verdict

**Overconfident for our entries; close to calibrated for the field.** The spread of the simulation is about right, so the cause is not mainly a too-narrow rest-of-game draw: it is that our lineups are picked on the same projections the simulation draws from, so it rates them too well.

- **Expected payout:** at each night's first break our entries' stated expected payout sums to **$2,228 against $1,064 paid** (2.1x; fees $874). The field sample, scored the same way, states $11,511 against $10,435 paid (1.10x), so the board itself is not inflating payouts.
- **Top 1%:** our entries stated at 5–50% (458 entry-breaks, mean 10.7%) finished top 1% 4.8% of the time; the field sample's (537, mean 12.3%) 9.5%.
- **Cash:** stated 95%+ holds (ours 132 entry-breaks at a mean 98.7% cashed 91.7%). Between 20% and 95% it runs high: ours stated 49.7%, cashed 34.5% (1599 entry-breaks); the field sample stated 40.7%, cashed 36.9%.
- **Why:** each entry's final total against its simulated distribution: the realized miss is 0.93x the simulated spread for ours and 1.02x for the field (1.0 = right), and the cash line's standardized miss has an sd of 1.02. But our entries finish 7.5 points under their simulated mean on average (mean percentile 0.409; the field's -1.4 and 0.488): the sim's projections favour the players our lineups were built from, and those players come in under them. That bias, not the width, is what inflates our stated payout and top 1%.
- **The variance fix:** widening every draw x1.25 brings the share of final totals outside the 5–95% band from 15.9% to about 10% and lowers the Brier score slightly, but held out by night it beats the page on only 9 of 15 nights, and it leaves our first-break stated payout at $1,913 against $1,064. Turning on the team and game draws changes nothing that matters. Where the widening does help is the field's middle: the field sample's 20–95% cash runs about 6 points high on the page's draw and close to right at x1.25 (the per-variant table below).
- **Recommendation:** read our stated expected payout and top 1% as roughly 2.1x too high, and the 20–95% cash figures as about 15 points high; the 95%+ cash figures are fine. A variance multiplier is not worth putting on the page on this evidence. The fix that would address the cause is a haircut on our own entries (their lineups' simulated points shrunk toward the field's view, e.g. by the ~7.5-point mean miss), to be tested held out before any page change.
- **A data gap, now fixed:** the widest misses in the first run were late breaks where a started player had no ESPN id on his card (2026-11-19 main: Malique Ewin, 44.5 DraftKings points, counted 0 so far with almost no game left). The page's live points and this study now find such a player by name in the game's box score (dk_swap.js liveState, 8886226), and the Swap tab names any started player still unmatched. These tables are after the fix; it changed only 2026-11-19 main, and took the share of final totals outside the 5–95% band from 16.9% to 14.2%.
- **2026-11-24 is not in yet:** the sync repo holds its late-swap standings from mid-slate only (time remaining and hidden slots). Once the final standings are saved to analysis/cbb/dk/standings/, add it with `python3 scripts/dk_lateswap_calib.py --add 2026-11-24:157024`.
- **Thin sample:** 15 nights; three of them (11-16, 11-21, 11-22) hold 1–4 of our entries, and a few big cashes decide the payout totals.


## Calibration: stated cash % (our entries, every break)

| Stated cash | Entry-breaks | Nights | Mean stated | Real cash rate |
|---|---|---|---|---|
| 0–20% | 599 | 13 | 6.9% | 3.2% |
| 20–50% | 884 | 15 | 36.2% | 24.1% |
| 50–80% | 588 | 14 | 61.7% | 43.7% |
| 80–95% | 127 | 10 | 88.0% | 64.6% |
| 95–100% | 132 | 9 | 98.7% | 91.7% |

Field sample (40 a contest, lineups known):

| Stated cash | Entry-breaks | Mean stated | Real cash rate |
|---|---|---|---|
| 0–20% | 4486 | 7.3% | 5.5% |
| 20–50% | 3251 | 32.4% | 29.8% |
| 50–80% | 872 | 62.3% | 54.9% |
| 80–95% | 170 | 87.9% | 81.8% |
| 95–100% | 188 | 98.5% | 98.9% |

## Calibration: stated top 1%

| Stated top 1% | Ours: entry-breaks | stated | real | Field sample: entry-breaks | stated | real |
|---|---|---|---|---|---|---|
| 0–5% | 1851 | 1.3% | 1.0% | 8401 | 0.8% | 0.8% |
| 5–20% | 405 | 8.0% | 4.0% | 463 | 9.3% | 6.7% |
| 20–50% | 53 | 31.3% | 11.3% | 74 | 30.8% | 27.0% |
| 50–100% | 21 | 70.6% | 57.1% | 29 | 69.0% | 86.2% |

## Per night (our entries; the payout columns at the first break only, so each entry counts once)

| Night | Slate | Entries | Breaks | Entry-breaks | Stated cash | Real cash | Stated top 1% | Real top 1% | Stated $ (1st break) | Real $ | Fees | Field sample: stated cash | real cash |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-16 | 156660 | 1 | 2 | 2 | 21.6% | 0.0% | 0.7% | 0.0% | 19.38 | 0.00 | 15.00 | 29.1% | 22.5% |
| 2026-11-17 | 156663 | 66 | 4 | 268 | 25.3% | 16.4% | 2.0% | 1.5% | 38.10 | 8.00 | 18.70 | 30.1% | 25.6% |
| 2026-11-18 | 157033 | 54 | 3 | 162 | 24.0% | 14.8% | 2.2% | 1.9% | 59.36 | 131.40 | 35.00 | 22.5% | 17.0% |
| 2026-11-19 | 157138 | 26 | 2 | 52 | 31.4% | 38.5% | 0.8% | 0.0% | 43.51 | 27.50 | 31.00 | 28.0% | 25.6% |
| 2026-11-19 | 157139 | 68 | 4 | 272 | 43.1% | 26.5% | 2.3% | 0.0% | 187.70 | 17.60 | 77.00 | 24.4% | 24.0% |
| 2026-11-20 | 157013 | 54 | 2 | 112 | 42.8% | 37.5% | 4.4% | 3.6% | 121.60 | 46.25 | 58.20 | 27.7% | 21.5% |
| 2026-11-20 | 157015 | 62 | 4 | 256 | 49.2% | 46.9% | 4.7% | 3.1% | 151.98 | 139.75 | 77.00 | 24.7% | 23.5% |
| 2026-11-21 | 157017 | 4 | 3 | 12 | 56.6% | 50.0% | 4.2% | 0.0% | 24.90 | 2.90 | 16.35 | 25.6% | 21.2% |
| 2026-11-22 | 157019 | 3 | 3 | 9 | 51.0% | 66.7% | 0.9% | 0.0% | 1.90 | 2.50 | 1.35 | 25.6% | 29.2% |
| 2026-11-24 | 157024 | 62 | 5 | 330 | 66.1% | 62.1% | 8.9% | 9.1% | 369.64 | 379.20 | 98.00 | 25.2% | 23.4% |
| 2026-11-24 | 157026 | 66 | 4 | 268 | 43.3% | 29.9% | 2.6% | 0.0% | 178.29 | 23.05 | 92.00 | 23.6% | 22.5% |
| 2026-11-25 | 157293 | 62 | 5 | 330 | 35.3% | 4.5% | 2.9% | 0.0% | 335.15 | 2.70 | 112.00 | 26.7% | 21.7% |
| 2026-11-25 | 157295 | 64 | 3 | 192 | 36.5% | 28.1% | 2.8% | 1.6% | 316.24 | 263.15 | 82.00 | 26.3% | 21.7% |
| 2026-11-26 | 157380 | 5 | 9 | 45 | 28.4% | 0.0% | 5.0% | 0.0% | 233.14 | 0.00 | 80.00 | 19.3% | 19.1% |
| 2026-11-26 | 157382 | 5 | 4 | 20 | 34.0% | 20.0% | 7.0% | 0.0% | 146.69 | 20.00 | 80.00 | 19.6% | 14.9% |
| **Pooled** | | | | | | | | | **2,227.57** | **1,064.00** | **873.60** | | |

## Why: the simulated spread against the realized

Each entry's final total placed in its own simulated distribution at the break (z = (final − simulated mean) / simulated sd; the share outside the 5–95% band is 10% when the spread is right).

| | Entry-breaks | sd of z (1 = right) | mean z | outside 5–95% |
|---|---|---|---|---|
| Our entries | 2307 | 1.05 | -0.37 | 15.9% |
| Field sample | 8803 | 1.10 | -0.08 | 13.4% |
| The cash line (each contest, each break) | 245 | 1.02 | +0.10 | 9.0% |

## Variants

Every player's simulated deviation from his projection scaled (x1.25 / x1.5 / x2), or the team and game draws turned on (team 0.2, game 0.1). Brier score of stated cash plus stated top 1% against what happened, ours and the field sample (lower is better).

| Variant | Brier | 95%+ stated cash: n | real | Our final total outside 5–95% | sd of z |
|---|---|---|---|---|---|
| page | 0.1506 | 132 | 91.7% | 15.9% | 1.05 |
| x1.25 | 0.1483 | 86 | 100.0% | 8.4% | 0.84 |
| x1.5 | 0.1483 | 53 | 100.0% | 5.2% | 0.71 |
| x2 | 0.1510 | 17 | 100.0% | 1.5% | 0.55 |
| corr | 0.1508 | 132 | 92.4% | 15.5% | 1.04 |

Stated cash against real, per variant (entry-breaks: stated / real):

| Variant | Kind | 0–20% | 20–50% | 50–80% | 80–95% | 95–100% |
|---|---|---|---|---|---|---|
| page | ours | 599: 6.9 / 3.2 | 884: 36.2 / 24.1 | 588: 61.7 / 43.7 | 127: 88.0 / 64.6 | 132: 98.7 / 91.7 |
| page | field | 4486: 7.3 / 5.5 | 3251: 32.4 / 29.8 | 872: 62.3 / 54.9 | 170: 87.9 / 81.8 | 188: 98.5 / 98.9 |
| x1.25 | ours | 554: 7.9 / 3.4 | 1120: 36.1 / 24.8 | 461: 61.2 / 51.0 | 109: 88.0 / 67.9 | 86: 98.3 / 100.0 |
| x1.25 | field | 4247: 8.4 / 4.9 | 3723: 31.6 / 29.9 | 723: 61.0 / 60.7 | 161: 87.9 / 92.5 | 113: 98.5 / 100.0 |
| x1.5 | ours | 516: 8.7 / 3.5 | 1285: 35.4 / 25.9 | 383: 61.3 / 54.8 | 93: 88.0 / 83.9 | 53: 97.8 / 100.0 |
| x1.5 | field | 4036: 9.3 / 4.3 | 4127: 31.0 / 30.2 | 596: 60.8 / 66.1 | 133: 87.7 / 97.0 | 75: 98.6 / 100.0 |
| x2 | ours | 465: 10.1 / 3.7 | 1503: 34.3 / 27.3 | 277: 61.8 / 65.0 | 68: 87.1 / 98.5 | 17: 97.6 / 100.0 |
| x2 | field | 3716: 10.5 / 3.7 | 4690: 30.0 / 30.2 | 436: 61.0 / 78.0 | 82: 87.3 / 100.0 | 43: 98.6 / 100.0 |
| corr | ours | 596: 6.9 / 3.5 | 910: 36.4 / 24.3 | 566: 62.1 / 43.6 | 126: 88.1 / 64.3 | 132: 98.6 / 92.4 |
| corr | field | 4470: 7.3 / 5.5 | 3257: 32.5 / 29.6 | 863: 62.0 / 54.0 | 188: 87.2 / 82.4 | 189: 98.4 / 98.4 |

Held out by night (the multiplier picked on the other nights, scored on this one):

| Night | Slate | Picked | Brier, page | Brier, picked |
|---|---|---|---|---|
| 2026-11-16 | 156660 | x1.25 | 0.1630 | 0.1624 |
| 2026-11-17 | 156663 | x1.5 | 0.1007 | 0.1039 |
| 2026-11-18 | 157033 | x1.5 | 0.1118 | 0.1149 |
| 2026-11-19 | 157138 | x1.5 | 0.1616 | 0.1639 |
| 2026-11-19 | 157139 | x1.25 | 0.1550 | 0.1512 |
| 2026-11-20 | 157013 | x1.5 | 0.1441 | 0.1434 |
| 2026-11-20 | 157015 | x1.5 | 0.1570 | 0.1599 |
| 2026-11-21 | 157017 | x1.25 | 0.1359 | 0.1340 |
| 2026-11-22 | 157019 | x1.25 | 0.1620 | 0.1579 |
| 2026-11-24 | 157024 | x1.25 | 0.1912 | 0.1852 |
| 2026-11-24 | 157026 | x1.5 | 0.1423 | 0.1429 |
| 2026-11-25 | 157293 | x1.25 | 0.1605 | 0.1559 |
| 2026-11-25 | 157295 | x1.25 | 0.1681 | 0.1602 |
| 2026-11-26 | 157380 | x1.5 | 0.1253 | 0.1359 |
| 2026-11-26 | 157382 | x1.25 | 0.1216 | 0.1187 |

The picked multiplier beats the page on 9 of 15 nights held out.

