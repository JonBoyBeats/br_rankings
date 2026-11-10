# NBA swap board backtest (step 7)

Written by scripts/nba_swap_board.py. Credited swaps only (swaps.csv). Excluded from swap tests: 2026-11-01 (Obi Toppin (ADP 23.1) and Jakob Poeltl (23.4) both sat, 0.3 picks apart: ADP can't tell which one a swap replaced).

## a. Swap efficiency: points left on the table against the best undrafted option by ETR's final projection

| Swaps | Group | Swaps | Points left per swap | Share where the swap was already the best option or better |
|---|---|---|---|---|
| Field and you | T1 | 1239 | +1.5 | 76% |
| Field and you | T2 | 9214 | +1.7 | 59% |
| Field and you | T3 | 17611 | +1.8 | 68% |
| Field and you | T4 | 3711 | -1.1 | 68% |
| Field and you | T5 | 1463 | -1.4 | 81% |
| Field and you | all | 33238 | +1.3 | 66% |
| Your teams | AM | 73 | +0.0 | 75% |
| Your teams | OVERNIGHT | 29 | -2.6 | 93% |
| Your teams | PM | 72 | +0.9 | 76% |
| Your teams | all | 174 | -0.0 | 79% |

## b. Your swapped teams under three orders of near-ties (within 2 points on ETR's final)

| Order | Your swaps | Their points | Nights | Share on the night's most-hit target (avg) | That target's exposure (drafted + swapped, avg) | His field drafted% (avg) |
|---|---|---|---|---|---|---|
| Projection only | 174 | 33.8 | 11 | 61% | 17% | 59% |
| Ownership lowest first (your habit) | 174 | 33.9 | 11 | 66% | 20% | 34% |
| Ownership highest first | 174 | 34.0 | 11 | 55% | 16% | 69% |

## Your own swaps

Graded from your real swaps in the contest rosters (your Underdog app order, which the board never sees): analysis/nba/report/my_swaps.md. The replay of your saved order that used to stand here is superseded.

Reading section a: points left on the table are the best option's score minus the swap's, so positive means the swap fell short. The field left +1.3 a swap; yours left -0.0 (AM +0.0, PM +0.9).

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
| 2026-11-09 | 149 | 0 | 0 |
