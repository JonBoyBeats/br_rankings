# NBA swap board backtest (step 7)

Written by scripts/nba_swap_board.py. Credited swaps only (swaps.csv). Excluded from swap tests: 2026-11-01 (Obi Toppin (ADP 23.1) and Jakob Poeltl (23.4) both sat, 0.3 picks apart: ADP can't tell which one a swap replaced).

## a. Swap efficiency: points left on the table against the best undrafted option by ETR's final projection

| Swaps | Group | Swaps | Points left per swap | Share where the swap was already the best option or better |
|---|---|---|---|---|
| Field and you | T1 | 1239 | +1.5 | 76% |
| Field and you | T2 | 19968 | +2.5 | 56% |
| Field and you | T3 | 13123 | +3.0 | 66% |
| Field and you | T4 | 6319 | -0.6 | 67% |
| Field and you | T5 | 1990 | -4.9 | 84% |
| Field and you | T6 | 12885 | +0.8 | 64% |
| Field and you | all | 55524 | +1.6 | 63% |
| Your teams | AM | 109 | +1.7 | 69% |
| Your teams | OVERNIGHT | 36 | -3.0 | 92% |
| Your teams | PM | 119 | +3.2 | 70% |
| Your teams | all | 264 | +1.7 | 72% |

## b. Your swapped teams under three orders of near-ties (within 2 points on ETR's final)

| Order | Your swaps | Their points | Nights | Share on the night's most-hit target (avg) | That target's exposure (drafted + swapped, avg) | His field drafted% (avg) |
|---|---|---|---|---|---|---|
| Projection only | 264 | 34.2 | 18 | 58% | 18% | 49% |
| Ownership lowest first (your habit) | 264 | 31.5 | 18 | 69% | 20% | 31% |
| Ownership highest first | 264 | 33.1 | 18 | 53% | 16% | 63% |

## Your own swaps

Graded from your real swaps in the contest rosters (your Underdog app order, which the board never sees): analysis/nba/report/my_swaps.md. The replay of your saved order that used to stand here is superseded.

Reading section a: points left on the table are the best option's score minus the swap's, so positive means the swap fell short. The field left +1.6 a swap; yours left +1.7 (AM +1.7, PM +3.2).

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
