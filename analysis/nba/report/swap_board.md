# NBA swap board backtest (step 7)

Written by scripts/nba_swap_board.py. Credited swaps only (swaps.csv). Excluded from swap tests: 2026-11-01 (Obi Toppin (ADP 23.1) and Jakob Poeltl (23.4) both sat, 0.3 picks apart: ADP can't tell which one a swap replaced).

## a. Swap efficiency: points left on the table against the best undrafted option by ETR's final projection

| Swaps | Group | Swaps | Points left per swap | Share where the swap was already the best option or better |
|---|---|---|---|---|
| Field and you | T1 | 1239 | +1.5 | 76% |
| Field and you | T2 | 12537 | +0.2 | 68% |
| Field and you | T3 | 13123 | +3.0 | 66% |
| Field and you | T4 | 5470 | +0.2 | 65% |
| Field and you | T5 | 1683 | -5.4 | 85% |
| Field and you | T6 | 12391 | +1.1 | 64% |
| Field and you | all | 46443 | +1.1 | 67% |
| Your teams | AM | 106 | +1.7 | 69% |
| Your teams | OVERNIGHT | 36 | -3.0 | 92% |
| Your teams | PM | 100 | +1.0 | 75% |
| Your teams | all | 242 | +0.7 | 75% |

## b. Your swapped teams under three orders of near-ties (within 2 points on ETR's final)

| Order | Your swaps | Their points | Nights | Share on the night's most-hit target (avg) | That target's exposure (drafted + swapped, avg) | His field drafted% (avg) |
|---|---|---|---|---|---|---|
| Projection only | 242 | 33.8 | 16 | 58% | 18% | 52% |
| Ownership lowest first (your habit) | 242 | 32.5 | 16 | 68% | 21% | 34% |
| Ownership highest first | 242 | 33.1 | 16 | 53% | 17% | 66% |

## Your own swaps

Graded from your real swaps in the contest rosters (your Underdog app order, which the board never sees): analysis/nba/report/my_swaps.md. The replay of your saved order that used to stand here is superseded.

Reading section a: points left on the table are the best option's score minus the swap's, so positive means the swap fell short. The field left +1.1 a swap; yours left +0.7 (AM +1.7, PM +1.0).

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
