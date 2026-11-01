# NBA blowout adjustment: re-run of the study (2023-26 plus 2026-27 to 10-31)

The board's `NBA_BLOWOUT = { minutes: 30, spread: -10, points: -1 }` (index.html) came from a study on
2021-26 closing spreads whose write-up didn't survive; only its conclusion is in the comment above
the constant. Another session re-ran it on 2023-26 (box scores on disk start in 2023-24): fit on
2023-25, tested on 2025-26. This is its summary, pasted into the morning-report session on
2026-11-01. The re-run scripts lived outside the repo and are gone.

Short version: big favorites' stars lose minutes, but win most of it back per minute against weak
opponents. The -1 is about right only because the board's morning Proj already credits the matchup.

## 1. Data and method

- Every player-game played, 2023-24 to 2026-27, with a pre-game projection and a spread: 69,890
  (21.1k, 23.7k, 24.1k, 1.1k this season).
- Spread: ESPN closing line for 2023-26 (`nba/odds/closing_2021-26.csv`); for 2026-27 the board's
  day-of snapshot (about 11am PT), not the close.
- Projection: the board's morning recipe from what was known before the game: expected minutes =
  average of his last 10 (last season's average until 3 games), times this season's FP/min with up
  to 300 minutes of last season mixed in. No matchup term, no ETR.
- Roles by expected minutes: 30+, 20-30, bench (under 20). Every effect is against the same role in
  games within 9.5 points.
- 30+ players, fit / test: fav 13+ 756/373, fav 10-12.5 954/421, fav 6.5-9.5 1797/821, fav 3-6
  2198/782, pick-2.5 2345/1194, dog 3-6 2063/733, dog 6.5-9.5 1506/647, dog 10-12.5 714/248,
  dog 13+ 452/237. Bench buckets about 500 to 2,800 each.

## 2. Effect by spread bucket (minutes vs expected, FP vs projection, against the within-9.5 baseline)

30+ minute players:

| Bucket | Fit 2023-25 | Test 2025-26 |
|---|---|---|
| Fav 13+ | -2.4 min, +0.1 FP | -2.7 min, -0.4 FP |
| Fav 10-12.5 | -1.0 min, +0.4 FP | -1.1 min, -0.1 FP |
| Fav 6.5-9.5 | -0.2 min, +0.5 FP | -0.3 min, +0.7 FP |
| Fav 3-6 | +0.2 min, +0.3 FP | -0.1 min, +0.3 FP |
| Pick-2.5 | -0.1 min, -0.4 FP | +0.2 min, -0.4 FP |
| Dog 3-6 | +0.2 min, +0.2 FP | +0.1 min, +0.1 FP |
| Dog 6.5-9.5 | -0.1 min, -0.6 FP | -0.1 min, -0.7 FP |
| Dog 10-12.5 | -1.0 min, -1.3 FP | -0.3 min, +1.2 FP |
| Dog 13+ | -0.6 min, -0.1 FP | -1.7 min, -1.1 FP |

Bench (under 20 expected minutes):

| Bucket | Fit 2023-25 | Test 2025-26 |
|---|---|---|
| Fav 13+ | -0.6 min, +0.1 FP | +0.1 min, +1.0 FP |
| Fav 10-12.5 | +0.1 min, +0.6 FP | -0.5 min, -0.3 FP |
| Dog 6.5-9.5 | +0.8 min, +0.7 FP | +1.0 min, +0.7 FP |
| Dog 10-12.5 | +2.3 min, +2.0 FP | +1.9 min, +1.4 FP |
| Dog 13+ | +3.4 min, +2.6 FP | +3.5 min, +3.3 FP |

Every other bench bucket is within ±0.5.

- Favorite stars lose minutes on a clean slide: none below 10, about 1 at 10-12.5, 2.5-3 at 13+
  (about -1.2 FP and -2.7 to -3.1 FP). They make it back per minute (+1.1 to +2.9 FP), so the total
  against this projection is about zero.
- About 60-85% of that per-minute gain is the weak opponent (each defense's FP/min allowed in its
  earlier games). Net of the opponent: about -0.5 (fit) / -1.0 (test) at 10-12.5 and -0.9 / -2.2 at
  13+. So -1 is about right on top of a matchup term, which the board's morning Proj has.
- Bench gains go to the losing side: +2 to +3.5 min and +1.4 to +3.3 FP as 10+ underdogs. 20-30
  minute players are small either way.

## 3. Underdog stars

They lose about 0.9 (fit) / 1.0 (test) minutes at 10+ (about 0.9 FP) but score more per minute than
the tougher opponent suggests: net -0.8 (fit), +0.1 (test). No adjustment held out of sample; the
buckets swing ±1.2 season to season (standard errors 0.4-0.7). Zero ± 1, not a proven offset.

## 4. Bigger or sliding adjustments, and the game total

Test season, 30+ favorites by 10+ (n 794), mean squared error: no adjustment 118.99; flat +0.28
(fit) 119.19; sliding past 9.5 (+0.03 a point) 119.18; board -1 119.55; minutes-only slide (-0.49 a
point) 122.27. Against an opponent-blind projection nothing beats doing nothing, and every
difference is tiny next to game-to-game noise (about 11 FP). The deciding test, -1 vs a slide on top
of the matchup term, needs the board's matchup term per night: the morning-report record keeps it
(`mtch`) from 2026-10-23 on, so it runs forward as H2 vs H4 in hypotheses.json.

Game total among favorites by 10+: high totals net +0.6 (fit, 227.5+) / +0.3 (test, 231.5+), low
totals -0.05 / -0.8. Same direction both seasons, about a point, not tested as a rule.

## 5. ETR

The -1 applies only to the morning Proj; once the day's ETR file is in, the board uses ETR with no
blowout adjustment, so no double count. Whether ETR prices blowout minutes can't be tested
historically. This season (ledger, games with a saved line Oct 23-30, actual minus ETR's median),
30+ players: fav 10+ +3.2 (median +6.6, n 35), fav 3-9.5 +0.1 (100), pick-2.5 -2.4 (84), dog 3-9.5
+0.8 (84), dog 10+ -0.7 (21). Under-30 players as 10+ underdogs: +2.5 (n 74) on +2.2 minutes.

## 6. Out of sample

2025-26, 30+ favorites by 10+: minutes cost -2.1 FP, per-minute gain +1.9, total -0.2 against the
opponent-blind projection; net of the opponent -1.0 at 10-12.5 and -2.2 at 13+. Underdogs by 10+:
+0.1. 2026-27 so far (day-of lines): favorites by 13+ +5.7 (n 14), 10-12.5 +8.3 (13); underdogs
10-12.5 +1.6 (7), 13+ -5.4 (7). Too small to read.

Caveat: the morning report's "blowout" tag is a final margin of 15+, known only afterward. Only the
pre-game spread is actionable, and most eventual blowouts weren't 10+ spreads.
