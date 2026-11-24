# Max contests per lineup backtest (2026-11-24)

The operator's question, through the coordinator: with the current settings, does letting a lineup go in more contests earn more, and at what swing? This is analysis only. Nothing on the page changes, and the 60% night cap stays either way.

**Method.** `scripts/dk_maxuses_backtest.js` takes each graded night with a saved build and refills that night's real contests from the build's final pool the way main's Fill all contests does:

1. The largest stake first. `DKSim.pick` runs on each contest's seeded nights (1,000 per contest), using the lineups not yet at the max. The night cap is each player's Max%, from what earlier contests used.
2. A short contest relaxes one cap a step, keeping what it picked: max core 20%, then 25%, then max exposure 70%. This is the C4 step in `pickPortfolios`.
3. The stranded seats are counted at this point, before the top-up.
4. Auto top-up, in slate order. Each open seat takes the final-pool lineup that breaks the caps least, one seat at a time, as `strandFor` and `autoTopUp` do. The lineup must not already be in that contest and must be under the max.

The top-up ranks lineups by fewest caps broken, then fewest entries over. The page breaks the last tie by the cut board's value, which builds don't save, so here it uses the lineup's expected payout alone in that contest on the same sim nights.

Every set is scored on real points against each contest's real entries, with the owner's own entries left out and ties split.

**Fixed settings:** 60% contest exposure, 60% night cap, min unique 3, max core 15%, auto top-up on.

**Varied setting:** max contests per lineup at 3 (now), 5, and unlimited. The contest-profiles branch is not used.

There are **7 nights**: 11-16, 11-17, 11-18, 11-19 early and main, 11-20 early and main. That is 32 contests and 381 seats, all with standings. 11-23 has a build but no standings yet. Per-night output is in `maxuses_backtest_2026-11-24/`.

## The short answer

The max almost never binds. At 3, only **12 of 315 distinct lineups** across the 7 nights reach 3 contests. At 5, **2 lineups** go into a 4th contest (one on 11-17, one on 11-20 main), and no lineup reaches 5. Unlimited is therefore identical to 5.

The whole difference is one extra seat's worth of change on 11-20 main: **+$0.25** and one more top-10% finish. The swing is unchanged.

The 60% caps decide which lineups get reused, not the max. The night cap and per-contest exposure spread the picks, and each contest's own sim ranks the pool differently. A night has 4 or 5 contests, so the max has little room to bind.

## Per night

Max 3. Max 5 and unlimited are identical to max 3 except where noted.

| Night | Contests | Seats | Fees | Payout | Net | ROI | Top 1% | Top 10% | Distinct lineups | Lineups in 3 contests | Stranded before top-up |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 11-16 | 4 | 46 | 27.00 | 0.80 | −26.20 | −97.0% | 0 | 0 | 41 | 1 | 11 |
| 11-17 | 4 | 67 | 18.70 | 3.80 | −14.90 | −79.7% | 0 | 2 | 48 | 5 | 0 |
| 11-18 | 5 | 54 | 35.00 | 162.10 | +127.10 | +363.1% | 3 | 4 | 37 | 3 | 0 |
| 11-19 early | 4 | 26 | 31.00 | 28.33 | −2.67 | −8.6% | 0 | 5 | 25 | 0 | 2 |
| 11-19 main | 5 | 68 | 77.00 | 13.15 | −63.85 | −82.9% | 0 | 6 | 61 | 0 | 11 |
| 11-20 early | 5 | 56 | 58.20 | 158.90 | +100.70 | +173.0% | 5 | 18 | 50 | 1 | 1 |
| 11-20 main | 5 | 64 | 77.00 | 162.95 | +85.95 | +111.6% | 5 | 16 | 53 | 2 | 13 |

Where max 5 and unlimited differ:

- **11-17:** one lineup goes into 4 contests (4 seats). Net is unchanged at −14.90.
- **11-20 main:** one lineup goes into 4 contests. Payout is 163.20, net +86.20 (ROI +111.9%), and top-10% finishes rise to 17.

Every stranded seat was topped up: 38 across the 7 nights, the same under all three settings. Each of those 38 broke a cap, as a stranded seat must. The max does not change the stranded count, because the night and contest caps are what strand seats.

## Pooled

| | Max 3 | Max 5 | Unlimited |
|---|---|---|---|
| Fees | 323.90 | 323.90 | 323.90 |
| Payout | 530.03 | 530.28 | 530.28 |
| Net | +206.13 | +206.38 | +206.38 |
| ROI | +63.6% | +63.7% | +63.7% |
| SD of nightly net | 73.72 | 73.75 | 73.75 |
| Worst night | −63.85 (11-19 main) | −63.85 | −63.85 |
| Nights in profit | 3 of 7 | 3 of 7 | 3 of 7 |
| Top-1% finishes | 13 | 13 | 13 |
| Top-10% finishes | 51 | 52 | 52 |
| Distinct lineups (sum over nights) | 315 | 315 | 315 |
| Lineups in 4+ contests | 0 | 2 (8 seats) | 2 (8 seats) |
| Most contests for one lineup | 3 | 4 | 4 |
| Stranded before top-up | 38 | 38 | 38 |

**Where the gain comes from.** All of the +$0.25 is on 11-20 main. No other night moves by a cent. One night's single seat is no evidence either way.

**Thin sample.** These are seven nights, one bank each, about 380 seats. The P&L comes from a few big cashes: 11-18, 11-20 early and 11-20 main make all of the profit, while 4 of 7 nights lose. With a nightly SD of about $74, one cash can move a setting's total by tens of dollars, as 11-20 main did in the caps backtest. What is measured here is mechanical, not noisy: the max barely changes which lineups are entered. That should hold on other nights with 4 or 5 contests and these caps. It could change on a night with many more contests, or if the caps were loosened. Looser caps concentrate the fill on fewer lineups, and then reuse would bind.

## Recommendation

**Keep max contests per lineup at 3.** Moving to 5 is harmless, but it buys nothing measurable.

The operator's condition for 5 was that it earn more without much more swing. The swing is the same, but it does not earn more: +$0.25 over 7 nights, from one seat. At the current 60% caps the setting is close to inert, so it isn't worth a change, a version note or a tester's attention. If the operator prefers 5 for headroom on a bigger night, it costs nothing measurable here either.

The 60% night cap stays, and nothing on the page changes.

## Side note: main's fill scores better than the caps backtest's (e) on 11-20 main

This run reproduces main's fill, with the C4 relax steps and the least-breaking top-up. The caps backtest's setting e did neither: it topped up stranded seats by added value with the caps off and skipped the relax steps. On 6 of the 7 nights the two agree within a few dollars.

On **11-20 main**, main's fill makes **+85.95**, against +12.53 for e. That brings the pooled 60/60 figure to **+206.13**, against +133.18 for e and +219.15 for the 80/80 setting b. The 11-20 night that drove b's lead is mostly recovered by the fill as it actually runs. This run does not separate the relax steps from the top-up, and it is still one night.

The caps backtest doc also says 33 contests; the count is 32.
