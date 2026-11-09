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

| Slate | S at AM | S at PM | The PM player | Swaps' actual average (credited) |
|---|---|---|---|---|
| 2026-10-21 | 30.7 | 32.8 | Ty Jerome | 42.4 (21) |
| 2026-10-22 | 15.9 | 18.6 | Cason Wallace | - |
| 2026-10-23 | 29.9 | 36.9 | Franz Wagner | - |
| 2026-10-24 | 26.0 | 31.7 | Jalen Green | 27.4 (1372) |
| 2026-10-25 | 21.2 | 26.5 | Collin Murray-Boyles | 21.9 (2303) |
| 2026-10-26 | 26.9 | 30.9 | Josh Giddey | 25.5 (515) |
| 2026-10-27 | 20.5 | 24.2 | Mikal Bridges | - |
| 2026-10-28 | 35.5 | 35.0 | RJ Barrett | 38.2 (1662) |
| 2026-10-29 | 27.7 | 30.9 | Jeremiah Fears | 44.6 (732) |
| 2026-10-30 | 35.7 | 34.9 | Immanuel Quickley | 34.4 (2562) |
| 2026-10-31 | 28.9 | 29.8 | Ryan Rollins | - |
| 2026-11-01 | 27.5 | 24.0 | Brandon Williams | - |
| 2026-11-02 | 38.5 | 39.4 | Austin Reaves | 38.5 (1545) |
| 2026-11-04 | 39.8 | 36.8 | LeBron James | 36.2 (3707) |
| 2026-11-05 | 20.9 | 19.5 | Khaman Maluach | - |
| 2026-11-06 | 36.2 | 37.1 | Dyson Daniels | 37.4 (2595) |
| 2026-11-07 | 31.8 | 30.6 | Isaiah Hartenstein | 35.2 (2222) |
| 2026-11-08 | 29.5 | 25.6 | Kris Dunn | 22.5 (2328) |

Swaps scored +1.0 against S at the PM lock on average (12 slates): S is about right.

## c-d. Q classes on X (swap-adjusted), by window and tier

| Window | Tier | Class | Players | Played | Slot score (him or his swap) | Breakers | Healthy tier higher / same / lower than ADP |
|---|---|---|---|---|---|---|---|
| AM | T1-T2 | FAIR | 3 | 0% | 24.9 | 0 | 0 / 3 / 0 |
| AM | T1-T2 | TRAP | 2 | 100% | 41.1 | 0 | 0 / 1 / 1 |
| AM | T3-T4 | SMASH | 6 | 33% | 36.2 | 1 | 6 / 0 / 0 |
| AM | T3-T4 | FAIR | 2 | 0% | 35.2 | 0 | 2 / 0 / 0 |
| AM | T3-T4 | TRAP | 1 | 0% | 22.5 | 0 | 1 / 0 / 0 |
| AM | T5 | SMASH | 1 | 0% | 32.8 | 0 | 1 / 0 / 0 |
| AM | T5 | FAIR | 23 | 52% | 30.1 | 3 | 0 / 23 / 0 |
| PM | T1-T2 | FAIR | 3 | 33% | 30.8 | 0 | 0 / 3 / 0 |
| PM | T1-T2 | TRAP | 1 | 100% | 41.0 | 0 | 0 / 1 / 0 |
| PM | T3-T4 | SMASH | 3 | 33% | 33.2 | 0 | 3 / 0 / 0 |
| PM | T3-T4 | FAIR | 4 | 25% | 36.6 | 1 | 3 / 1 / 0 |
| PM | T3-T4 | TRAP | 3 | 67% | 20.2 | 0 | 0 / 3 / 0 |
| PM | T5 | SMASH | 1 | 0% | 37.4 | 0 | 0 / 1 / 0 |
| PM | T5 | FAIR | 24 | 62% | 28.5 | 4 | 0 / 24 / 0 |

## d. Pushing a tagged player back: the button's order against each variant

Decision pairs (ADP within 4) that include a tagged player and that the variant orders differently from the button. Positive: the variant's order was right more, in points per pair.

| Window | Tag | Back one tier | Back two tiers | Rank on X |
|---|---|---|---|---|
| AM | Questionable | -1.1 (-3.6 to +2.0), 89 pairs, no lean | +0.8 (-1.9 to +4.1), 119 pairs, no lean | -3.2 (-8.5 to +2.6), 235 pairs, no lean |
| AM | Doubtful | - | - | +10.7, not enough yet (27) |
| AM | all tagged | -1.1 (-3.6 to +2.0), 89 pairs, no lean | +0.8 (-1.9 to +4.1), 119 pairs, no lean | -1.8 (-7.4 to +3.9), 262 pairs, no lean |
| PM | Questionable | -8.0, not enough yet (27) | +21.0, not enough yet (2) | -1.6 (-5.4 to +2.7), 364 pairs, no lean |
| PM | Doubtful | - | - | - |
| PM | all tagged | -8.0, not enough yet (27) | +21.0, not enough yet (2) | -1.6 (-5.4 to +2.7), 364 pairs, no lean |

## e. Beneficiaries: undrafted or T5 players with a teammate tagged at the AM lock

| Group | Players | Teammate sat | Score over his ADP band | Swap target (any credited swaps) |
|---|---|---|---|---|
| Round 6 at the AM lock, teammate sat | 8 | 8 | +3.7 (8 with a band) | 7 (1647 swaps) |
| Round 6 at the AM lock, teammate played | 8 | 0 | +2.6 (8 with a band) | 2 (219 swaps) |
| All (T5 or undrafted), teammate sat | 105 | 105 | +2.7 (68 with a band) | 53 (3862 swaps) |
| All (T5 or undrafted), teammate played | 68 | 0 | +1.3 (53 with a band) | 20 (945 swaps) |

## Implied cost of a scratch, by tier

Each tier's average score (players who played, at the PM lock; T5 drafted only) against the average swap for players ruled out from that tier (credited swaps, weighted by teams). Priced up: at the PM lock every teammate projected for 20+ was already drafted inside ADP 30, so no cheap beneficiary was left for a swap; cheap: one was.

| Tier (PM lock; AM if off the PM board) | Tier average | Out players (the real sample) | Swaps | Swap average (range by player) | Cost | Priced-up teammates: swaps, average | Cheap teammates: swaps, average |
|---|---|---|---|---|---|---|---|
| T1 | 52.2 | 1 (anecdote: under 5 players) | 1214 | 38.5 (38.5 to 38.5) | -13.8 | - | 1214, 38.5 |
| T2 | 41.3 | 4 (anecdote: under 5 players) | 5233 | 29.7 (0.0 to 37.4) | -11.6 | - | 5233, 29.7 |
| T3 | 34.0 | 8 | 11913 | 35.1 (22.5 to 44.6) | +1.1 | - | 11913, 35.1 |
| T4 | 33.8 | 4 (anecdote: under 5 players) | 3183 | 27.1 (22.1 to 37.6) | -6.7 | 848, 22.1 | 2335, 28.9 |
| T5 | 26.0 | 1 (anecdote: under 5 players) | 21 | 42.4 (42.4 to 42.4) | +16.4 | - | 21, 42.4 |
