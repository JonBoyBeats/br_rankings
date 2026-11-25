# Late swap: are the stated numbers calibrated?

2026-11-24, the coordinator's request (analysis only; nothing on the page changes). `python3 scripts/dk_lateswap_calib.py`.

At each tip break of 11 saved nights (the 2026-11-21 backtest's five plus 2026-11-24:157024, 2026-11-24:157026 and the later graded nights), every one of our entries' **stated** cash %, top-1 % and expected payout is rebuilt with the page's own code (dk_sim.js nights at the page's 1,000, dk_swap.js board and field draws, the chalk fitted per contest as the page does, the started games' points so far from ESPN's play-by-play at the next tip) and scored against the real final standings. A random 40 field entries per contest are scored the same way (their lineups known, as ours are). An entry counts once per break, so a night's entries repeat across its breaks: the night is the unit, and the per-night rows carry the weight.

## Verdict

**Overconfident for our entries; close to calibrated for the field.** The spread of the simulation is about right, so the cause is not mainly a too-narrow rest-of-game draw: it is that our lineups are picked on the same projections the simulation draws from, so it rates them too well.

- **Expected payout:** at each night's first break our entries' stated expected payout sums to **$1,196 against $778 paid** (1.5x; fees $520). The field sample, scored the same way, states $7,550 against $7,386 paid (1.02x), so the board itself is not inflating payouts.
- **Top 1%:** our entries stated at 5–50% (329 entry-breaks, mean 11.8%) finished top 1% 6.4% of the time; the field sample's (366, mean 12.0%) 8.7%.
- **Cash:** stated 95%+ holds (ours 132 entry-breaks at a mean 98.7% cashed 91.7%). Between 20% and 95% it runs high: ours stated 51.0%, cashed 41.3% (1178 entry-breaks); the field sample stated 41.3%, cashed 38.1%.
- **Why:** each entry's final total against its simulated distribution: the realized miss is 0.87x the simulated spread for ours and 0.98x for the field (1.0 = right), and the cash line's standardized miss has an sd of 0.95. But our entries finish 5.7 points under their simulated mean on average (mean percentile 0.418; the field's -2.8 and 0.470): the sim's projections favour the players our lineups were built from, and those players come in under them. That bias, not the width, is what inflates our stated payout and top 1%.
- **The variance fix:** widening every draw x1.25 brings the share of final totals outside the 5–95% band from 14.8% to about 10% and lowers the Brier score slightly, but held out by night it beats the page on only 7 of 11 nights, and it leaves our first-break stated payout at $1,020 against $778. Turning on the team and game draws changes nothing that matters. Where the widening does help is the field's middle: the field sample's 20–95% cash runs about 6 points high on the page's draw and close to right at x1.25 (the per-variant table below).
- **Recommendation:** read our stated expected payout and top 1% as roughly 1.5x too high, and the 20–95% cash figures as about 10 points high; the 95%+ cash figures are fine. A variance multiplier is not worth putting on the page on this evidence. The fix that would address the cause is a haircut on our own entries (their lineups' simulated points shrunk toward the field's view, e.g. by the ~5.7-point mean miss), to be tested held out before any page change.
- **A data gap, now fixed:** the widest misses in the first run were late breaks where a started player had no ESPN id on his card (2026-11-19 main: Malique Ewin, 44.5 DraftKings points, counted 0 so far with almost no game left). The page's live points and this study now find such a player by name in the game's box score (dk_swap.js liveState, 8886226), and the Swap tab names any started player still unmatched. These tables are after the fix; it changed only 2026-11-19 main, and took the share of final totals outside the 5–95% band from 16.9% to 14.2%.
- **2026-11-24 is not in yet:** the sync repo holds its late-swap standings from mid-slate only (time remaining and hidden slots). Once the final standings are saved to analysis/cbb/dk/standings/, add it with `python3 scripts/dk_lateswap_calib.py --add 2026-11-24:157024`.
- **Thin sample:** 11 nights; three of them (11-16, 11-21, 11-22) hold 1–4 of our entries, and a few big cashes decide the payout totals.


## Calibration: stated cash % (our entries, every break)

| Stated cash | Entry-breaks | Nights | Mean stated | Real cash rate |
|---|---|---|---|---|
| 0–20% | 433 | 9 | 6.7% | 2.5% |
| 20–50% | 634 | 11 | 36.2% | 28.9% |
| 50–80% | 427 | 10 | 62.8% | 53.6% |
| 80–95% | 117 | 8 | 88.2% | 64.1% |
| 95–100% | 132 | 9 | 98.7% | 91.7% |

Field sample (40 a contest, lineups known):

| Stated cash | Entry-breaks | Mean stated | Real cash rate |
|---|---|---|---|
| 0–20% | 3380 | 7.1% | 5.5% |
| 20–50% | 2348 | 32.4% | 30.7% |
| 50–80% | 673 | 62.8% | 55.1% |
| 80–95% | 135 | 87.9% | 82.2% |
| 95–100% | 164 | 98.5% | 98.8% |

## Calibration: stated top 1%

| Stated top 1% | Ours: entry-breaks | stated | real | Field sample: entry-breaks | stated | real |
|---|---|---|---|---|---|---|
| 0–5% | 1396 | 1.3% | 1.3% | 6317 | 0.7% | 0.7% |
| 5–20% | 281 | 8.3% | 5.7% | 319 | 9.0% | 6.0% |
| 20–50% | 48 | 32.1% | 10.4% | 47 | 32.1% | 27.7% |
| 50–100% | 18 | 72.1% | 55.6% | 17 | 71.2% | 82.4% |

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
| **Pooled** | | | | | | | | | **1,196.36** | **778.15** | **519.60** | | |

## Why: the simulated spread against the realized

Each entry's final total placed in its own simulated distribution at the break (z = (final − simulated mean) / simulated sd; the share outside the 5–95% band is 10% when the spread is right).

| | Entry-breaks | sd of z (1 = right) | mean z | outside 5–95% |
|---|---|---|---|---|
| Our entries | 1725 | 1.02 | -0.35 | 14.8% |
| Field sample | 6552 | 1.06 | -0.15 | 13.2% |
| The cash line (each contest, each break) | 171 | 0.95 | -0.08 | 9.4% |

## Variants

Every player's simulated deviation from his projection scaled (x1.25 / x1.5 / x2), or the team and game draws turned on (team 0.2, game 0.1). Brier score of stated cash plus stated top 1% against what happened, ours and the field sample (lower is better).

| Variant | Brier | 95%+ stated cash: n | real | Our final total outside 5–95% | sd of z |
|---|---|---|---|---|---|
| page | 0.1494 | 132 | 91.7% | 14.8% | 1.02 |
| x1.25 | 0.1476 | 86 | 100.0% | 8.7% | 0.82 |
| x1.5 | 0.1481 | 53 | 100.0% | 5.9% | 0.69 |
| x2 | 0.1513 | 17 | 100.0% | 1.6% | 0.53 |
| corr | 0.1497 | 132 | 92.4% | 14.3% | 1.01 |

Stated cash against real, per variant (entry-breaks: stated / real):

| Variant | Kind | 0–20% | 20–50% | 50–80% | 80–95% | 95–100% |
|---|---|---|---|---|---|---|
| page | ours | 433: 6.7 / 2.5 | 634: 36.2 / 28.9 | 427: 62.8 / 53.6 | 117: 88.2 / 64.1 | 132: 98.7 / 91.7 |
| page | field | 3380: 7.1 / 5.5 | 2348: 32.4 / 30.7 | 673: 62.8 / 55.1 | 135: 87.9 / 82.2 | 164: 98.5 / 98.8 |
| x1.25 | ours | 399: 7.6 / 2.8 | 782: 35.8 / 30.4 | 369: 61.7 / 57.5 | 107: 88.1 / 67.3 | 86: 98.3 / 100.0 |
| x1.25 | field | 3192: 8.1 / 4.9 | 2704: 31.7 / 30.5 | 573: 61.5 / 61.3 | 131: 88.0 / 91.6 | 100: 98.6 / 100.0 |
| x1.5 | ours | 369: 8.3 / 3.0 | 899: 35.1 / 31.7 | 331: 61.8 / 58.6 | 91: 88.2 / 83.5 | 53: 97.8 / 100.0 |
| x1.5 | field | 3034: 9.0 / 4.3 | 2994: 31.1 / 30.6 | 494: 60.7 / 67.0 | 109: 87.7 / 97.2 | 69: 98.7 / 100.0 |
| x2 | ours | 334: 9.7 / 3.0 | 1070: 34.3 / 33.6 | 254: 62.1 / 65.4 | 68: 87.1 / 98.5 | 17: 97.6 / 100.0 |
| x2 | field | 2788: 10.3 / 3.5 | 3443: 30.3 / 30.8 | 359: 60.9 / 78.6 | 70: 87.6 / 100.0 | 40: 98.7 / 100.0 |
| corr | ours | 434: 6.8 / 3.0 | 635: 36.3 / 29.1 | 425: 63.0 / 52.9 | 117: 88.4 / 63.2 | 132: 98.6 / 92.4 |
| corr | field | 3350: 7.0 / 5.5 | 2365: 32.5 / 30.4 | 669: 62.4 / 54.1 | 153: 87.2 / 81.7 | 163: 98.5 / 98.8 |

Held out by night (the multiplier picked on the other nights, scored on this one):

| Night | Slate | Picked | Brier, page | Brier, picked |
|---|---|---|---|---|
| 2026-11-16 | 156660 | x1.25 | 0.1630 | 0.1624 |
| 2026-11-17 | 156663 | x1.25 | 0.1007 | 0.1016 |
| 2026-11-18 | 157033 | x1.25 | 0.1118 | 0.1130 |
| 2026-11-19 | 157138 | x1.25 | 0.1616 | 0.1617 |
| 2026-11-19 | 157139 | x1.25 | 0.1550 | 0.1512 |
| 2026-11-20 | 157013 | x1.25 | 0.1441 | 0.1423 |
| 2026-11-20 | 157015 | x1.25 | 0.1570 | 0.1580 |
| 2026-11-21 | 157017 | x1.25 | 0.1359 | 0.1340 |
| 2026-11-22 | 157019 | x1.25 | 0.1620 | 0.1579 |
| 2026-11-24 | 157024 | x1.25 | 0.1912 | 0.1852 |
| 2026-11-24 | 157026 | x1.25 | 0.1423 | 0.1419 |

The picked multiplier beats the page on 7 of 11 nights held out.

