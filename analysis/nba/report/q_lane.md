# NBA Q lane

Written by scripts/nba_q_lane.py. Projections are medians (expected actual points); a scratch is scored through his swap. Slates since 2026-10-27 (when our miss chances start).

## a. Our chance he plays, against what happened

| Window | Tag | Tier | Players | Predicted | Played | 80% range |
|---|---|---|---|---|---|---|
| AM | Questionable | T1-T2 | 5 | 58% | 40% | 14% to 100% |
| AM | Questionable | T3-T4 | 10 | 62% | 20% | 9% to 30% |
| AM | Questionable | T5 | 23 | 53% | 52% | 38% to 65% |
| AM | Questionable | all | 38 | 56% | 42% | 34% to 49% |
| AM | Probable | T5 | 7 | 92% | 86% | 71% to 100% |
| AM | Probable | all | 8 | 92% | 88% | 78% to 100% |
| AM | none | T1-T2 | 130 | 97% | 98% | 96% to 99% |
| AM | none | T3-T4 | 164 | 97% | 98% | 97% to 99% |
| AM | none | T5 | 493 | 96% | 97% | 95% to 98% |
| AM | none | all | 787 | 96% | 97% | 96% to 98% |
| PM | Questionable | T1-T2 | 4 | 62% | 50% | 20% to 100% |
| PM | Questionable | T3-T4 | 10 | 61% | 40% | 22% to 55% |
| PM | Questionable | T5 | 27 | 49% | 59% | 43% to 73% |
| PM | Questionable | all | 41 | 53% | 54% | 42% to 65% |
| PM | Doubtful | T5 | 5 | 2% | 0% | 0% to 0% |
| PM | Doubtful | all | 5 | 2% | 0% | 0% to 0% |
| PM | Probable | T1-T2 | 3 | 95% | 100% | 100% to 100% |
| PM | Probable | T5 | 10 | 88% | 90% | 82% to 100% |
| PM | Probable | all | 15 | 90% | 93% | 88% to 100% |
| PM | none | T1-T2 | 153 | 99% | 99% | 99% to 100% |
| PM | none | T3-T4 | 159 | 99% | 99% | 99% to 100% |
| PM | none | T5 | 502 | 99% | 99% | 98% to 100% |
| PM | none | all | 814 | 99% | 99% | 99% to 100% |

Refit on 1713 player-locks (both windows): played ~ 0.89 + 0.81 x logit(our chance) -1.09 if tagged Q/D/GTD. So our 70% for a tagged player reads 62%, our 50% reads 45%, an untagged 95% reads 96%.

| Predicted (calibrated) | Players | Played |
|---|---|---|
| tagged, 0-30% | 10 | 20% (predicted 5%) |
| tagged, 30-50% | 35 | 51% (predicted 42%) |
| tagged, 50-70% | 40 | 45% (predicted 58%) |
| tagged, 70-90% | 1 | 100% (predicted 78%) |

## b. The swap value S at each lock (best expected score among players under 50% drafted)

Excluded from swap tests (no credited swaps, so no actual average): 2026-11-01 (Obi Toppin (ADP 23.1) and Jakob Poeltl (23.4) both sat, 0.3 picks apart: ADP can't tell which one a swap replaced).

| Slate | S at AM | S at PM | The PM player | Swaps' actual average (credited) |
|---|---|---|---|---|
| 2026-10-21 | 30.7 | 32.8 | Ty Jerome | 43.4 (20) |
| 2026-10-22 | 15.9 | 18.6 | Cason Wallace | - |
| 2026-10-23 | 29.9 | 36.9 | Franz Wagner | - |
| 2026-10-24 | 26.0 | 31.7 | Jalen Green | 27.1 (432) |
| 2026-10-25 | 21.2 | 26.5 | Collin Murray-Boyles | 21.8 (2771) |
| 2026-10-26 | 26.9 | 30.9 | Josh Giddey | 24.9 (632) |
| 2026-10-27 | 20.5 | 24.2 | Mikal Bridges | - |
| 2026-10-28 | 35.5 | 35.0 | RJ Barrett | 38.5 (1782) |
| 2026-10-29 | 27.7 | 30.9 | Jeremiah Fears | 46.0 (2419) |
| 2026-10-30 | 35.7 | 34.9 | Immanuel Quickley | 34.1 (3621) |
| 2026-10-31 | 28.9 | 29.8 | Ryan Rollins | 32.6 (2619) |
| 2026-11-01 | 27.5 | 24.0 | Brandon Williams | - |
| 2026-11-02 | 38.5 | 39.4 | Austin Reaves | 38.1 (1550) |
| 2026-11-04 | 39.8 | 36.8 | LeBron James | 36.1 (3786) |
| 2026-11-05 | 20.9 | 19.5 | Khaman Maluach | - |
| 2026-11-06 | 36.2 | 37.1 | Dyson Daniels | 37.3 (4308) |
| 2026-11-07 | 31.8 | 30.6 | Isaiah Hartenstein | 34.0 (2906) |
| 2026-11-08 | 29.5 | 25.6 | Kris Dunn | 22.5 (2558) |

Swaps scored +1.1 against S at the PM lock on average (13 slates): S is about right.

## c-d. Q classes on X (swap-adjusted), by window and tier

| Window | Tier | Class | Players | Played | Slot score (him or his swap) | Breakers | Healthy tier higher / same / lower than ADP |
|---|---|---|---|---|---|---|---|
| AM | T1-T2 | FAIR | 3 | 0% | 37.2 | 0 | 0 / 3 / 0 |
| AM | T1-T2 | TRAP | 2 | 100% | 41.1 | 0 | 0 / 1 / 1 |
| AM | T3-T4 | SMASH | 6 | 33% | 35.9 | 1 | 6 / 0 / 0 |
| AM | T3-T4 | FAIR | 2 | 0% | 35.1 | 0 | 2 / 0 / 0 |
| AM | T3-T4 | TRAP | 1 | 0% | 22.9 | 0 | 1 / 0 / 0 |
| AM | T5 | SMASH | 1 | 0% | 33.7 | 0 | 1 / 0 / 0 |
| AM | T5 | FAIR | 23 | 52% | 30.0 | 3 | 0 / 23 / 0 |
| PM | T1-T2 | FAIR | 3 | 33% | 43.4 | 0 | 0 / 3 / 0 |
| PM | T1-T2 | TRAP | 1 | 100% | 41.0 | 0 | 0 / 1 / 0 |
| PM | T3-T4 | SMASH | 3 | 33% | 33.0 | 0 | 3 / 0 / 0 |
| PM | T3-T4 | FAIR | 4 | 25% | 36.0 | 1 | 3 / 1 / 0 |
| PM | T3-T4 | TRAP | 3 | 67% | 20.4 | 0 | 0 / 3 / 0 |
| PM | T5 | SMASH | 1 | 0% | 37.3 | 0 | 0 / 1 / 0 |
| PM | T5 | FAIR | 24 | 62% | 28.5 | 4 | 0 / 24 / 0 |

## d. Pushing a tagged player back: the button's order against each variant

Decision pairs (ADP within 4) that include a tagged player and that the variant orders differently from the button. Positive: the variant's order was right more, in points per pair.

| Window | Tag | Back one tier | Back two tiers | Rank on X |
|---|---|---|---|---|
| AM | Questionable | -2.6 (-3.9 to -0.7), 91 pairs, LEAN - (RULE numbers, check pending) | -0.7 (-2.9 to +2.2), 121 pairs, no lean | -3.6 (-8.7 to +2.3), 237 pairs, no lean |
| AM | Doubtful | - | - | +10.4, not enough yet (27) |
| AM | all tagged | -2.6 (-3.9 to -0.7), 91 pairs, LEAN - (RULE numbers, check pending) | -0.7 (-2.9 to +2.2), 121 pairs, no lean | -2.1 (-7.5 to +3.6), 264 pairs, no lean |
| PM | Questionable | -2.0 (-5.3 to +1.9), 44 pairs, no lean | +2.3, not enough yet (21) | -1.1 (-5.6 to +3.8), 284 pairs, no lean |
| PM | Doubtful | - | - | - |
| PM | all tagged | -2.0 (-5.3 to +1.9), 44 pairs, no lean | +2.3, not enough yet (21) | -1.1 (-5.6 to +3.8), 284 pairs, no lean |

## e. Beneficiaries: undrafted or T5 players with a teammate tagged at the AM lock

| Group | Players | Teammate sat | Score over his ADP band | Swap target (any credited swaps) |
|---|---|---|---|---|
| Round 6 at the AM lock, teammate sat | 8 | 8 | +3.7 (8 with a band) | 7 (1709 swaps) |
| Round 6 at the AM lock, teammate played | 8 | 0 | +2.6 (8 with a band) | 2 (258 swaps) |
| All (T5 or undrafted), teammate sat | 105 | 105 | +2.7 (68 with a band) | 52 (5375 swaps) |
| All (T5 or undrafted), teammate played | 68 | 0 | +1.3 (53 with a band) | 18 (1149 swaps) |

## Implied cost of a scratch, by tier

Each tier's average score (players who played, at the PM lock; T5 drafted only) against the average swap for players ruled out from that tier (credited swaps, weighted by teams). Priced up: at the PM lock every teammate projected for 20+ was already drafted inside ADP 30, so no cheap beneficiary was left for a swap; cheap: one was. Excluded from swap tests: 2026-11-01 (Obi Toppin (ADP 23.1) and Jakob Poeltl (23.4) both sat, 0.3 picks apart: ADP can't tell which one a swap replaced).

Swaps in money (contest side, money_report.md "Swaps by the ruled-out player's tier", 2026-11-09, on the swap credits before the 11-09 re-credit): teams with a T1-T2 scratch reached the top 10% at 0.42 times the rate of same-price teams with no swap (finish 13.4 percentile points worse; 6,262 teams, 5 slates); T3-T5 scratches 0.79 (finish +4.2; 12,522 teams, 10 slates). The swap doesn't make the slot whole in money, least of all at the top. No rule change yet.

| Tier (PM lock; AM if off the PM board) | Tier average | Out players (the real sample) | Swaps | Swap average (range by player) | Cost | Priced-up teammates: swaps, average | Cheap teammates: swaps, average |
|---|---|---|---|---|---|---|---|
| T1 | 52.2 | 1 (anecdote: under 5 players) | 1239 | 38.7 (38.7 to 38.7) | -13.6 | - | 1239, 38.7 |
| T2 | 41.3 | 4 (anecdote: under 5 players) | 6149 | 30.2 (21.2 to 37.9) | -11.1 | - | 6149, 30.2 |
| T3 | 34.0 | 11 | 17599 | 35.7 (22.9 to 46.0) | +1.7 | - | 17599, 35.7 |
| T4 | 33.8 | 7 | 2628 | 27.5 (22.7 to 38.1) | -6.4 | 968, 22.7 | 1660, 30.2 |
| T5 | 26.0 | 6 | 1789 | 30.9 (21.6 to 43.4) | +4.9 | - | 1789, 30.9 |
