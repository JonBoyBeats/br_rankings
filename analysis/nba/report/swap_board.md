# NBA swap board backtest (step 7)

Written by scripts/nba_swap_board.py. Credited swaps only (swaps.csv).

## a. Swap efficiency: points left on the table against the best undrafted option by ETR's final projection

| Swaps | Group | Swaps | Points left per swap | Share where the swap was already the best option or better |
|---|---|---|---|---|
| Field and you | T1 | 1214 | +1.7 | 72% |
| Field and you | T2 | 5233 | +3.0 | 50% |
| Field and you | T3 | 11913 | +0.6 | 70% |
| Field and you | T4 | 3183 | -2.3 | 73% |
| Field and you | T5 | 21 | +0.6 | 62% |
| Field and you | all | 21564 | +0.8 | 66% |
| Your teams | AM | 46 | -0.4 | 74% |
| Your teams | PM | 54 | -1.2 | 83% |
| Your teams | all | 100 | -0.8 | 79% |

## b. Your swapped teams under three orders of near-ties (within 2 points on ETR's final)

| Order | Your swaps | Their points | Nights | Share on the night's most-hit target (avg) | That target's exposure (drafted + swapped, avg) | His field drafted% (avg) |
|---|---|---|---|---|---|---|
| Projection only | 100 | 30.2 | 9 | 65% | 17% | 63% |
| Ownership lowest first (your habit) | 100 | 30.7 | 9 | 69% | 16% | 32% |
| Ownership highest first | 100 | 30.7 | 9 | 53% | 14% | 76% |

## Your own swaps

Graded from your real swaps in the contest rosters (your Underdog app order, which the board never sees): analysis/nba/report/my_swaps.md. The replay of your saved order that used to stand here is superseded.

Reading section a: points left on the table are the best option's score minus the swap's, so positive means the swap fell short. The field left +0.8 a swap; your swaps came out ahead of ETR's final best by 0.8 (AM 0.4, PM 1.2).

## Your live moves: board saves after the slate locked

| Slate | Saves that day | After lock | Top-80 ranks moved by them |
|---|---|---|---|
| 2026-10-21 | 123 | 0 | 0 |
| 2026-10-22 | 30 | 0 | 0 |
| 2026-10-23 | 110 | 0 | 0 |
| 2026-10-24 | 37 | 0 | 0 |
| 2026-10-25 | 174 | 0 | 0 |
| 2026-10-26 | 198 | 0 | 0 |
| 2026-10-27 | 200 | 0 | 0 |
| 2026-10-28 | 162 | 0 | 0 |
| 2026-10-29 | 85 | 0 | 0 |
| 2026-10-30 | 133 | 3 | 62 |
| 2026-10-31 | 137 | 0 | 0 |
| 2026-11-01 | 33 | 0 | 0 |
| 2026-11-02 | 245 | 4 | 12 |
| 2026-11-04 | 149 | 6 | 28 |
| 2026-11-05 | 33 | 0 | 0 |
| 2026-11-06 | 154 | 0 | 0 |
| 2026-11-07 | 50 | 0 | 0 |
| 2026-11-08 | 28 | 0 | 0 |
