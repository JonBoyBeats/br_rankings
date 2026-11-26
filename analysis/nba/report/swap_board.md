# NBA swap board backtest (step 7)

Written by scripts/nba_swap_board.py. Credited swaps only (swaps.csv). Excluded from swap tests: 2026-11-01 (Obi Toppin (ADP 23.1) and Jakob Poeltl (23.4) both sat, 0.3 picks apart: ADP can't tell which one a swap replaced).

## a. Swap efficiency: points left on the table against the best undrafted option by ETR's final projection

| Swaps | Group | Swaps | Points left per swap | Share where the swap was already the best option or better |
|---|---|---|---|---|
| Field and you | T1 | 5337 | +0.4 | 73% |
| Field and you | T2 | 24975 | +2.4 | 55% |
| Field and you | T3 | 13123 | +3.0 | 66% |
| Field and you | T4 | 6692 | -0.6 | 67% |
| Field and you | T5 | 2486 | -4.6 | 82% |
| Field and you | T6 | 13884 | +1.4 | 62% |
| Field and you | all | 66497 | +1.6 | 62% |
| Your teams | AM | 110 | +1.7 | 69% |
| Your teams | OVERNIGHT | 36 | -3.0 | 92% |
| Your teams | PM | 122 | +2.8 | 70% |
| Your teams | all | 268 | +1.6 | 73% |

## b. Your swapped teams under three orders of near-ties (within 2 points on ETR's final)

| Order | Your swaps | Their points | Nights | Share on the night's most-hit target (avg) | That target's exposure (drafted + swapped, avg) | His field drafted% (avg) |
|---|---|---|---|---|---|---|
| Projection only | 268 | 34.1 | 20 | 60% | 19% | 49% |
| Ownership lowest first (your habit) | 268 | 31.4 | 20 | 69% | 19% | 29% |
| Ownership highest first | 268 | 33.1 | 20 | 56% | 17% | 61% |

## Your own swaps

Graded from your real swaps in the contest rosters (your Underdog app order, which the board never sees): analysis/nba/report/my_swaps.md. The replay of your saved order that used to stand here is superseded.

Reading section a: points left on the table are the best option's score minus the swap's, so positive means the swap fell short. The field left +1.6 a swap; yours left +1.6 (AM +1.7, PM +2.8).

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
| 2026-11-10 | 50 | 0 | 0 |
| 2026-11-11 | 145 | 1 | 14 |
| 2026-11-12 | 90 | 0 | 0 |
| 2026-11-13 | 96 | 1 | 42 |
| 2026-11-14 | 13 | 0 | 0 |
| 2026-11-15 | 3 | 3 | 0 |
| 2026-11-16 | 42 | 0 | 0 |
| 2026-11-17 | 60 | 0 | 0 |
| 2026-11-18 | 76 | 1 | 41 |
| 2026-11-19 | 42 | 0 | 0 |
| 2026-11-20 | 29 | 0 | 0 |
| 2026-11-21 | 20 | 0 | 0 |
| 2026-11-22 | 7 | 0 | 0 |
| 2026-11-23 | 47 | 0 | 0 |
| 2026-11-24 | 14 | 0 | 0 |
| 2026-11-25 | 5 | 0 | 0 |
