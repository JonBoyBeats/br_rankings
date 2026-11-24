# Late swap: are the stated numbers calibrated?

2026-11-24, the coordinator's request (analysis only; nothing on the page changes). `python3 scripts/dk_lateswap_calib.py`.

At each tip break of 9 saved nights (the 2026-11-21 backtest's five and the later graded nights), every one of our entries' **stated** cash %, top-1 % and expected payout is rebuilt with the page's own code (dk_sim.js nights at the page's 1,000, dk_swap.js board and field draws, the chalk fitted per contest as the page does, the started games' points so far from ESPN's play-by-play at the next tip) and scored against the real final standings. A random 40 field entries per contest are scored the same way (their lineups known, as ours are). An entry counts once per break, so a night's entries repeat across its breaks: the night is the unit, and the per-night rows carry the weight.

## Verdict

**Overconfident for our entries; close to calibrated for the field.** The spread of the simulation is about right, so the cause is not mainly a too-narrow rest-of-game draw: it is that our lineups are picked on the same projections the simulation draws from, so it rates them too well.

- **Expected payout:** at each night's first break our entries' stated expected payout sums to **$648 against $376 paid** (1.7x; fees $330). The field sample, scored the same way, states $5,429 against $6,018 paid (0.90x), so the board itself is not inflating payouts.
- **Top 1%:** our entries stated at 5–50% (149 entry-breaks, mean 11.8%) finished top 1% 4.7% of the time; the field sample's (249, mean 11.9%) 10.4%.
- **Cash:** stated 95%+ holds (ours 53 entry-breaks at a mean 98.8% cashed 98.1%). Between 20% and 95% it runs high: ours stated 46.9%, cashed 36.7% (692 entry-breaks); the field sample stated 42.5%, cashed 36.4%.
- **Why:** each entry's final total against its simulated distribution: the realized miss is 0.95x the simulated spread for ours and 1.05x for the field (1.0 = right), and the cash line's standardized miss has an sd of 1.01. But our entries finish 2.5 points under their simulated mean on average (mean percentile 0.470; the field's -0.2 and 0.501): the sim's projections favour the players our lineups were built from, and those players come in under them. That bias, not the width, is what inflates our stated payout and top 1%.
- **The variance fix:** widening every draw x1.25 brings the share of final totals outside the 5–95% band from 16.9% to about 10% and lowers the Brier score slightly, but held out by night it beats the page on only 5 of 9 nights, and it leaves our first-break stated payout at $583 against $376. Turning on the team and game draws changes nothing that matters. Where the widening does help is the field's middle: the field sample's 20–95% cash runs about 6 points high on the page's draw and close to right at x1.25 (the per-variant table below).
- **Recommendation:** read our stated expected payout and top 1% as roughly 1.7x too high, and the 20–95% cash figures as about 10 points high; the 95%+ cash figures are fine. A variance multiplier is not worth putting on the page on this evidence. The fix that would address the cause is a haircut on our own entries (their lineups' simulated points shrunk toward the field's view, e.g. by the ~2.5-point mean miss), to be tested held out before any page change.
- **A data gap the page shares:** the widest misses are late breaks where a started player has no ESPN id on his card (2026-11-19 main: Malique Ewin, 44.5 DraftKings points, counted 0 so far with almost no game left). The page's live points (dk_swap.js liveState) map players the same way, so such a player reads 0 there too.
- **2026-11-24 is not in yet:** the sync repo holds its late-swap standings from mid-slate only (time remaining and hidden slots). Once the final standings are saved to analysis/cbb/dk/standings/, add it with `python3 scripts/dk_lateswap_calib.py --add 2026-11-24:157024`.
- **Thin sample:** 9 nights; three of them (11-16, 11-21, 11-22) hold 1–4 of our entries, and a few big cashes decide the payout totals.


## Calibration: stated cash % (our entries, every break)

| Stated cash | Entry-breaks | Nights | Mean stated | Real cash rate |
|---|---|---|---|---|
| 0–20% | 400 | 7 | 6.1% | 7.0% |
| 20–50% | 448 | 9 | 35.9% | 27.2% |
| 50–80% | 191 | 8 | 60.9% | 47.1% |
| 80–95% | 53 | 6 | 88.4% | 79.2% |
| 95–100% | 53 | 7 | 98.8% | 98.1% |

Field sample (40 a contest, lineups known):

| Stated cash | Entry-breaks | Mean stated | Real cash rate |
|---|---|---|---|
| 0–20% | 2261 | 6.8% | 6.5% |
| 20–50% | 1494 | 32.6% | 28.0% |
| 50–80% | 480 | 63.6% | 52.3% |
| 80–95% | 104 | 88.1% | 83.7% |
| 95–100% | 141 | 98.6% | 95.0% |

## Calibration: stated top 1%

| Stated top 1% | Ours: entry-breaks | stated | real | Field sample: entry-breaks | stated | real |
|---|---|---|---|---|---|---|
| 0–5% | 990 | 1.1% | 0.7% | 4217 | 0.7% | 0.9% |
| 5–20% | 124 | 8.3% | 2.4% | 219 | 9.0% | 8.7% |
| 20–50% | 25 | 29.3% | 16.0% | 30 | 32.8% | 23.3% |
| 50–100% | 6 | 80.4% | 83.3% | 14 | 74.4% | 85.7% |

## Per night (our entries; the payout columns at the first break only, so each entry counts once)

| Night | Slate | Entries | Breaks | Entry-breaks | Stated cash | Real cash | Stated top 1% | Real top 1% | Stated $ (1st break) | Real $ | Fees | Field sample: stated cash | real cash |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-16 | 156660 | 1 | 2 | 2 | 21.6% | 0.0% | 0.7% | 0.0% | 19.38 | 0.00 | 15.00 | 29.1% | 22.5% |
| 2026-11-17 | 156663 | 66 | 4 | 268 | 25.3% | 16.4% | 2.0% | 1.5% | 38.10 | 8.00 | 18.70 | 30.1% | 25.6% |
| 2026-11-18 | 157033 | 54 | 3 | 162 | 24.0% | 14.8% | 2.2% | 1.9% | 59.36 | 131.40 | 35.00 | 22.5% | 17.0% |
| 2026-11-19 | 157138 | 26 | 2 | 52 | 31.4% | 38.5% | 0.8% | 0.0% | 43.51 | 27.50 | 31.00 | 28.0% | 25.6% |
| 2026-11-19 | 157139 | 68 | 4 | 272 | 33.9% | 26.5% | 2.3% | 0.0% | 187.70 | 17.60 | 77.00 | 26.7% | 24.0% |
| 2026-11-20 | 157013 | 54 | 2 | 112 | 42.8% | 37.5% | 4.4% | 3.6% | 121.60 | 46.25 | 58.20 | 27.7% | 21.5% |
| 2026-11-20 | 157015 | 62 | 4 | 256 | 49.2% | 46.9% | 4.7% | 3.1% | 151.98 | 139.75 | 77.00 | 24.7% | 23.5% |
| 2026-11-21 | 157017 | 4 | 3 | 12 | 56.6% | 50.0% | 4.2% | 0.0% | 24.90 | 2.90 | 16.35 | 25.6% | 21.2% |
| 2026-11-22 | 157019 | 3 | 3 | 9 | 51.0% | 66.7% | 0.9% | 0.0% | 1.90 | 2.50 | 1.35 | 25.6% | 29.2% |
| **Pooled** | | | | | | | | | **648.43** | **375.90** | **329.60** | | |

## Why: the simulated spread against the realized

Each entry's final total placed in its own simulated distribution at the break (z = (final − simulated mean) / simulated sd; the share outside the 5–95% band is 10% when the spread is right).

| | Entry-breaks | sd of z (1 = right) | mean z | outside 5–95% |
|---|---|---|---|---|
| Our entries | 1129 | 3.05 | +0.11 | 16.9% |
| Field sample | 4346 | 1.33 | -0.01 | 16.6% |
| The cash line (each contest, each break) | 112 | 1.01 | +0.19 | 13.4% |

## Variants

Every player's simulated deviation from his projection scaled (x1.25 / x1.5 / x2), or the team and game draws turned on (team 0.2, game 0.1). Brier score of stated cash plus stated top 1% against what happened, ours and the field sample (lower is better).

| Variant | Brier | 95%+ stated cash: n | real | Our final total outside 5–95% | sd of z |
|---|---|---|---|---|---|
| page | 0.1469 | 53 | 98.1% | 16.9% | 3.05 |
| x1.25 | 0.1453 | 36 | 100.0% | 10.5% | 2.46 |
| x1.5 | 0.1456 | 23 | 100.0% | 7.5% | 2.09 |
| x2 | 0.1486 | 12 | 100.0% | 4.5% | 1.63 |
| corr | 0.1468 | 52 | 98.1% | 16.1% | 3.16 |

Stated cash against real, per variant (entry-breaks: stated / real):

| Variant | Kind | 0–20% | 20–50% | 50–80% | 80–95% | 95–100% |
|---|---|---|---|---|---|---|
| page | ours | 400: 6.1 / 7.0 | 448: 35.9 / 27.2 | 191: 60.9 / 47.1 | 53: 88.4 / 79.2 | 53: 98.8 / 98.1 |
| page | field | 2261: 6.8 / 6.5 | 1494: 32.6 / 28.0 | 480: 63.6 / 52.3 | 104: 88.1 / 83.7 | 141: 98.6 / 95.0 |
| x1.25 | ours | 367: 6.7 / 7.4 | 544: 35.0 / 27.6 | 150: 60.9 / 55.3 | 48: 87.4 / 79.2 | 36: 98.4 / 100.0 |
| x1.25 | field | 2125: 7.9 / 5.7 | 1736: 31.9 / 28.1 | 424: 62.0 / 58.0 | 105: 88.0 / 89.5 | 90: 98.5 / 98.9 |
| x1.5 | ours | 346: 7.5 / 7.2 | 601: 34.0 / 28.0 | 136: 61.8 / 61.0 | 39: 88.0 / 89.7 | 23: 98.1 / 100.0 |
| x1.5 | field | 2009: 8.7 / 5.1 | 1945: 31.3 / 28.3 | 372: 61.2 / 64.5 | 92: 88.0 / 91.3 | 62: 98.6 / 100.0 |
| x2 | ours | 314: 9.0 / 7.6 | 689: 32.9 / 28.7 | 100: 63.0 / 71.0 | 30: 86.6 / 96.7 | 12: 97.8 / 100.0 |
| x2 | field | 1812: 9.9 / 3.8 | 2290: 30.6 / 28.9 | 277: 61.2 / 75.5 | 65: 87.3 / 98.5 | 36: 98.8 / 100.0 |
| corr | ours | 405: 6.3 / 7.7 | 446: 36.3 / 26.9 | 189: 61.4 / 48.1 | 53: 88.8 / 77.4 | 52: 98.7 / 98.1 |
| corr | field | 2243: 6.8 / 6.2 | 1504: 32.6 / 28.2 | 474: 63.1 / 51.3 | 120: 87.0 / 82.5 | 139: 98.6 / 96.4 |

Held out by night (the multiplier picked on the other nights, scored on this one):

| Night | Slate | Picked | Brier, page | Brier, picked |
|---|---|---|---|---|
| 2026-11-16 | 156660 | x1.25 | 0.1630 | 0.1624 |
| 2026-11-17 | 156663 | x1.5 | 0.1007 | 0.1039 |
| 2026-11-18 | 157033 | x1.25 | 0.1118 | 0.1130 |
| 2026-11-19 | 157138 | x1.25 | 0.1616 | 0.1617 |
| 2026-11-19 | 157139 | x1.25 | 0.1959 | 0.1880 |
| 2026-11-20 | 157013 | x1.25 | 0.1441 | 0.1423 |
| 2026-11-20 | 157015 | x1.5 | 0.1570 | 0.1599 |
| 2026-11-21 | 157017 | x1.25 | 0.1359 | 0.1340 |
| 2026-11-22 | 157019 | x1.25 | 0.1620 | 0.1579 |

The picked multiplier beats the page on 5 of 9 nights held out.

