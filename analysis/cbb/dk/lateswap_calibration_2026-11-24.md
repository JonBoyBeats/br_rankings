# Late swap: are the stated numbers calibrated?

2026-11-24, the coordinator's request (analysis only; nothing on the page changes). `python3 scripts/dk_lateswap_calib.py`.

At each tip break of 9 saved nights (the 2026-11-21 backtest's five and the later graded nights), every one of our entries' **stated** cash %, top-1 % and expected payout is rebuilt with the page's own code (dk_sim.js nights at the page's 1,000, dk_swap.js board and field draws, the chalk fitted per contest as the page does, the started games' points so far from ESPN's play-by-play at the next tip) and scored against the real final standings. A random 40 field entries per contest are scored the same way (their lineups known, as ours are). An entry counts once per break, so a night's entries repeat across its breaks: the night is the unit, and the per-night rows carry the weight.

## Verdict

**Overconfident for our entries; close to calibrated for the field.** The spread of the simulation is about right, so the cause is not mainly a too-narrow rest-of-game draw: it is that our lineups are picked on the same projections the simulation draws from, so it rates them too well.

- **Expected payout:** at each night's first break our entries' stated expected payout sums to **$648 against $376 paid** (1.7x; fees $330). The field sample, scored the same way, states $5,429 against $6,018 paid (0.90x), so the board itself is not inflating payouts.
- **Top 1%:** our entries stated at 5–50% (148 entry-breaks, mean 11.5%) finished top 1% 4.7% of the time; the field sample's (241, mean 12.2%) 11.2%.
- **Cash:** stated 95%+ holds (ours 61 entry-breaks at a mean 98.8% cashed 98.4%). Between 20% and 95% it runs high: ours stated 47.5%, cashed 37.3% (719 entry-breaks); the field sample stated 42.2%, cashed 37.7%.
- **Why:** each entry's final total against its simulated distribution: the realized miss is 0.89x the simulated spread for ours and 1.03x for the field (1.0 = right), and the cash line's standardized miss has an sd of 1.02. But our entries finish 5.0 points under their simulated mean on average (mean percentile 0.427; the field's -0.9 and 0.493): the sim's projections favour the players our lineups were built from, and those players come in under them. That bias, not the width, is what inflates our stated payout and top 1%.
- **The variance fix:** widening every draw x1.25 brings the share of final totals outside the 5–95% band from 14.2% to about 10% and lowers the Brier score slightly, but held out by night it beats the page on only 5 of 9 nights, and it leaves our first-break stated payout at $583 against $376. Turning on the team and game draws changes nothing that matters. Where the widening does help is the field's middle: the field sample's 20–95% cash runs about 6 points high on the page's draw and close to right at x1.25 (the per-variant table below).
- **Recommendation:** read our stated expected payout and top 1% as roughly 1.7x too high, and the 20–95% cash figures as about 10 points high; the 95%+ cash figures are fine. A variance multiplier is not worth putting on the page on this evidence. The fix that would address the cause is a haircut on our own entries (their lineups' simulated points shrunk toward the field's view, e.g. by the ~5.0-point mean miss), to be tested held out before any page change.
- **A data gap, now fixed:** the widest misses in the first run were late breaks where a started player had no ESPN id on his card (2026-11-19 main: Malique Ewin, 44.5 DraftKings points, counted 0 so far with almost no game left). The page's live points and this study now find such a player by name in the game's box score (dk_swap.js liveState, 8886226), and the Swap tab names any started player still unmatched. These tables are after the fix; it changed only 2026-11-19 main, and took the share of final totals outside the 5–95% band from 16.9% to 14.2%.
- **2026-11-24 is not in yet:** the sync repo holds its late-swap standings from mid-slate only (time remaining and hidden slots). Once the final standings are saved to analysis/cbb/dk/standings/, add it with `python3 scripts/dk_lateswap_calib.py --add 2026-11-24:157024`.
- **Thin sample:** 9 nights; three of them (11-16, 11-21, 11-22) hold 1–4 of our entries, and a few big cashes decide the payout totals.


## Calibration: stated cash % (our entries, every break)

| Stated cash | Entry-breaks | Nights | Mean stated | Real cash rate |
|---|---|---|---|---|
| 0–20% | 365 | 7 | 6.5% | 1.6% |
| 20–50% | 454 | 9 | 36.1% | 26.4% |
| 50–80% | 209 | 8 | 61.5% | 47.8% |
| 80–95% | 56 | 6 | 87.7% | 85.7% |
| 95–100% | 61 | 7 | 98.8% | 98.4% |

Field sample (40 a contest, lineups known):

| Stated cash | Entry-breaks | Mean stated | Real cash rate |
|---|---|---|---|
| 0–20% | 2288 | 6.8% | 5.7% |
| 20–50% | 1483 | 32.4% | 28.9% |
| 50–80% | 479 | 63.5% | 56.4% |
| 80–95% | 93 | 88.0% | 81.7% |
| 95–100% | 137 | 98.6% | 98.5% |

## Calibration: stated top 1%

| Stated top 1% | Ours: entry-breaks | stated | real | Field sample: entry-breaks | stated | real |
|---|---|---|---|---|---|---|
| 0–5% | 991 | 1.1% | 0.7% | 4225 | 0.7% | 0.9% |
| 5–20% | 125 | 8.3% | 2.4% | 209 | 9.1% | 8.1% |
| 20–50% | 23 | 28.8% | 17.4% | 32 | 32.7% | 31.2% |
| 50–100% | 6 | 80.4% | 83.3% | 14 | 71.4% | 85.7% |

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
| **Pooled** | | | | | | | | | **648.43** | **375.90** | **329.60** | | |

## Why: the simulated spread against the realized

Each entry's final total placed in its own simulated distribution at the break (z = (final − simulated mean) / simulated sd; the share outside the 5–95% band is 10% when the spread is right).

| | Entry-breaks | sd of z (1 = right) | mean z | outside 5–95% |
|---|---|---|---|---|
| Our entries | 1129 | 1.03 | -0.31 | 14.2% |
| Field sample | 4346 | 1.13 | -0.07 | 15.5% |
| The cash line (each contest, each break) | 112 | 1.02 | +0.08 | 13.4% |

## Variants

Every player's simulated deviation from his projection scaled (x1.25 / x1.5 / x2), or the team and game draws turned on (team 0.2, game 0.1). Brier score of stated cash plus stated top 1% against what happened, ours and the field sample (lower is better).

| Variant | Brier | 95%+ stated cash: n | real | Our final total outside 5–95% | sd of z |
|---|---|---|---|---|---|
| page | 0.1391 | 61 | 98.4% | 14.2% | 1.03 |
| x1.25 | 0.1383 | 42 | 100.0% | 7.4% | 0.83 |
| x1.5 | 0.1394 | 24 | 100.0% | 4.9% | 0.70 |
| x2 | 0.1435 | 11 | 100.0% | 2.4% | 0.54 |
| corr | 0.1391 | 63 | 98.4% | 13.3% | 1.02 |

Stated cash against real, per variant (entry-breaks: stated / real):

| Variant | Kind | 0–20% | 20–50% | 50–80% | 80–95% | 95–100% |
|---|---|---|---|---|---|---|
| page | ours | 365: 6.5 / 1.6 | 454: 36.1 / 26.4 | 209: 61.5 / 47.8 | 56: 87.7 / 85.7 | 61: 98.8 / 98.4 |
| page | field | 2288: 6.8 / 5.7 | 1483: 32.4 / 28.9 | 479: 63.5 / 56.4 | 93: 88.0 / 81.7 | 137: 98.6 / 98.5 |
| x1.25 | ours | 333: 7.2 / 1.8 | 551: 35.2 / 26.7 | 173: 61.7 / 57.2 | 46: 88.2 / 87.0 | 42: 98.2 / 100.0 |
| x1.25 | field | 2157: 7.9 / 4.9 | 1717: 31.8 / 29.0 | 424: 61.7 / 61.6 | 96: 88.5 / 92.7 | 86: 98.7 / 100.0 |
| x1.5 | ours | 308: 7.9 / 1.9 | 613: 34.1 / 26.6 | 154: 61.5 / 63.6 | 46: 88.6 / 93.5 | 24: 98.0 / 100.0 |
| x1.5 | field | 2036: 8.8 / 4.2 | 1929: 31.2 / 29.1 | 364: 60.4 / 67.0 | 87: 87.5 / 96.6 | 64: 98.6 / 100.0 |
| x2 | ours | 277: 9.3 / 1.8 | 704: 33.1 / 28.0 | 118: 62.6 / 73.7 | 35: 86.7 / 97.1 | 11: 97.7 / 100.0 |
| x2 | field | 1841: 10.0 / 3.0 | 2280: 30.5 / 29.7 | 265: 61.4 / 79.6 | 58: 88.1 / 100.0 | 36: 98.9 / 100.0 |
| corr | ours | 365: 6.6 / 2.2 | 455: 36.2 / 26.2 | 211: 61.9 / 48.3 | 51: 88.0 / 84.3 | 63: 98.5 / 98.4 |
| corr | field | 2269: 6.8 / 5.3 | 1498: 32.5 / 29.1 | 468: 63.0 / 55.3 | 110: 86.9 / 81.8 | 135: 98.6 / 98.5 |

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

The picked multiplier beats the page on 5 of 9 nights held out.

