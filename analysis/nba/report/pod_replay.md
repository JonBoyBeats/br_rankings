# Pod replay: my NBA rankings graded by team outcomes

Results only. Generated 2026-11-17 17:59 from 25 nights (2026-10-21 to 2026-11-16).

## Plain English

- **Which ETR version for the PM** (since 2026-11-17): no nights yet.
- **My locked list, replayed through every real seat** (25 nights, 420872 seats): top 1% 1.29%, top 10% 12.7%, mean finish percentile 45.2 (an average team: 1%, 10%, 50).
- **Against the button's list** (7 nights): my list +0.27 pts top-10% (80% range -3.03 to +3.44), -0.88 pts top-1%, mean finish -3.8.
- **Against ADP** (25 nights): my list +1.76 pts top-10% (80% range +0.51 to +2.92), +0.19 pts top-1%, mean finish -3.0.
- **Against ETR's order (PM)** (25 nights, PM): my list -4.08 pts top-10% (80% range -7.38 to -0.76), -0.99 pts top-1%, mean finish +1.3.
- **My manual moves, tier by tier** (top-10% points my moves added, 80% range): T1 +0.24 (-0.07 to +0.53); T2 +2.05 (+0.64 to +3.64); T3 -1.49 (-3.89 to +0.96); T4 +0.34 (-0.81 to +1.53); T5 -0.24 (-1.67 to +0.98).
- **ETR by tier (PM):** my list minus my list with one tier in ETR's order, top-10% points (80% range; below zero, ETR's order beat mine in that tier): T1 -0.10 (-0.53 to +0.32); T2 -0.06 (-0.97 to +0.79); T3 -0.32 (-1.52 to +0.95); T4 -0.55 (-1.13 to -0.03); T5 -0.73 (-1.70 to +0.24).
- **ETR-based button variants (PM)**, top-10% points (80% range), top-1% points: (a) minus (f) the button on ETR tiers -3.41 (-6.94 to +0.14), -1.24; (a) minus (g) ETR with the button's T5 rule -3.85 (-7.31 to -0.54), -0.94; (g) minus (e) pure ETR: what the T5 rule adds -0.23 (-0.64 to +0.15), -0.04; (b') minus (f): ADP tiers against ETR tiers in the button -0.95 (-3.29 to +1.58), -0.29.
- **Top 1% at my seats:** my real teams 17, my locked list at the same seats 25 (round-6 redraws 22-31, a count this size swings 20-33 by luck); real minus list -8, nights resampled -18 to +3.
- **Round 6 fidelity:** 30% of my real round-6 picks were (a)'s #1 still available, 80% were in its top 6 (the replay's weighted draw: 38% and 100%).
- **My real teams** (1926): top 10% 13.0% against 13.9% for (a) replayed at the same seats; they beat 49% of (a)'s replayed teams on average (50% = in line with the list).

## How it was run

- Every real pod in every main-slate contest, every seat, each window's pods (the lock nearest the draft time, as the money engine sorts them). That seat's drafter becomes me, drafting off a list: the highest available at each of my picks.
- The other drafters keep their real picks; when I've taken one of theirs, they take the next available by the window's ADP (their later picks stay as they were unless taken too).
- **Pick order is estimated.** Underdog doesn't publish draft slots. Each team's picks, sorted by the ADP each was taken at, are its rounds 1-6; the pod's seats are the snake slots that fit those ADPs best (the swap crediting's fit).
- Rounds 1-5 follow the list strictly. Round 6: drawn from the top 6 still available on the list, weighted 38/25/14/11/6/6 to match my real round-6 habit, one seeded draw per pod and seat, the same for every list.
- Scored on the night's box scores as Underdog scored them: a player's box score is corrected where the leaderboards' team totals disagree (stat corrections, 1-4.5 points, one or two players most nights; every night's teams then reconcile to within 3). A scratched player (0 minutes for a team that played, swapped at least as often as he was left on a real roster: a DNP kept on rosters scores 0) is swapped to the highest player on the same list left undrafted in the replayed pod whose game hadn't started at the swap (the earliest real swap target's tip, else his own team's tip).
- Placed in the contest's real standings: my seat's real score is replaced, everyone else's stays as it was (the pod-mates who lost a player to me aren't re-scored). Ties ignored. Top X%: place <= ceil(X% of entries). Cash: any payout. ROI: payout over fees.
- (c) undoes one tier's manual moves: that tier's players (by the button's tier) go back to their button positions and everyone else keeps my order around them. A list identical to (a) reuses (a)'s results.
- (b) and (c) need the button's list at the lock: on file from 2026-11-09 (PM) and 2026-11-10 (AM). (e) is ETR's PM projections, highest first (ETR's own rank isn't kept). 11/15 had no locks on file and is out.
- (f) is my PM list with one of my tiers (my tier lines at the PM lock, on file from 10/23) in ETR's order: that tier's places in my list, filled by its players highest ETR projection first. (a) minus (f) below zero: ETR's order beat mine there.
- (b'), (f) and (g), PM: the Tiers button rebuilt here from the PM lock's inputs (scripts/nba_tier_history.py, the 11/13 rules on every night; it matches the board's own PM order at 26-36 of the top 36 places since 11/13). (b') on ADP tiers as the board; (f) the same rules with the tiers starting from ETR's ladder and moving one tier toward ADP's at two or more apart; (g) ETR's order for ETR's T1-T4, then T5 by the button's rule (under the 60% drafted line first, by projection; ETR's T4 PRICEY players behind T5's top 3; the minutes floor), 60%+ below the cut. (b') minus (f) isolates the tiers' source.

## Season: Both windows

| List | Nights | Seats | Top 1% | Top 10% | Mean finish pct | Cash | ROI |
|---|---|---|---|---|---|---|---|
| (a) my locked list | 25 | 420872 | 1.29% | 12.7% | 45.2 | 23% | +30% |
| (b) the button's list | 7 | 127584 | 2.08% | 12.9% | 46.7 | 23% | +59% |
| (c1) mine, T1's moves undone | 7 | 127584 | 1.19% | 13.0% | 42.3 | 25% | +15% |
| (c2) mine, T2's moves undone | 7 | 127584 | 0.93% | 11.2% | 46.0 | 21% | -9% |
| (c3) mine, T3's moves undone | 7 | 127584 | 2.18% | 14.7% | 42.4 | 27% | +69% |
| (c4) mine, T4's moves undone | 7 | 127584 | 1.27% | 12.9% | 45.1 | 24% | +19% |
| (c5) mine, T5's moves undone | 7 | 127584 | 1.32% | 13.5% | 43.6 | 25% | +26% |
| (d) ADP | 25 | 420872 | 1.11% | 10.9% | 48.2 | 20% | -1% |
| (e) ETR (PM) | 25 | 296794 | 2.23% | 16.5% | 44.1 | 27% | +71% |
| (f1) mine (PM), T1 in ETR's order | 22 | 251084 | 1.27% | 12.5% | 45.0 | 23% | +30% |
| (f2) mine (PM), T2 in ETR's order | 23 | 264800 | 1.20% | 12.3% | 45.8 | 23% | +26% |
| (f3) mine (PM), T3 in ETR's order | 23 | 264800 | 1.59% | 12.5% | 46.9 | 23% | +34% |
| (f4) mine (PM), T4 in ETR's order | 23 | 264800 | 1.34% | 12.8% | 45.5 | 23% | +31% |
| (f5) mine (PM), T5 in ETR's order | 23 | 264800 | 1.35% | 12.9% | 44.9 | 24% | +37% |
| (b') the button rebuilt here (PM) | 25 | 296794 | 2.19% | 14.9% | 44.5 | 25% | +111% |
| (f) the button on ETR tiers (PM) | 25 | 296794 | 2.48% | 15.8% | 43.4 | 27% | +101% |
| (g) ETR order, the button's T5 rule (PM) | 25 | 296794 | 2.19% | 16.2% | 45.0 | 26% | +66% |

Paired: (a) minus each list, same pods and seats, nights resampled for the 80% ranges.

| (a) minus, or the pair named | Nights | Top 1% (pts) | 80% range | Top 10% (pts) | 80% range | Mean finish pct (lower is better) | 80% range |
|---|---|---|---|---|---|---|---|
| (b) the button's list | 7 | -0.88 | -2.12 to +0.35 | +0.27 | -3.03 to +3.44 | -3.76 | -8.91 to +1.27 |
| (c1) mine, T1's moves undone | 7 | +0.01 | +0.00 to +0.02 | +0.24 | -0.07 to +0.53 | +0.62 | -0.29 to +1.60 |
| (c2) mine, T2's moves undone | 7 | +0.27 | +0.10 to +0.45 | +2.05 | +0.64 to +3.64 | -3.03 | -5.08 to -1.17 |
| (c3) mine, T3's moves undone | 7 | -0.98 | -2.25 to +0.27 | -1.49 | -3.89 to +0.96 | +0.58 | -0.97 to +2.08 |
| (c4) mine, T4's moves undone | 7 | -0.07 | -0.19 to +0.05 | +0.34 | -0.81 to +1.53 | -2.17 | -4.52 to +0.05 |
| (c5) mine, T5's moves undone | 7 | -0.12 | -0.35 to +0.09 | -0.24 | -1.67 to +0.98 | -0.63 | -2.16 to +0.91 |
| (d) ADP | 25 | +0.19 | -0.10 to +0.47 | +1.76 | +0.51 to +2.92 | -3.03 | -5.16 to -0.74 |
| (e) ETR (PM) | 25 | -0.99 | -1.79 to -0.21 | -4.08 | -7.38 to -0.76 | +1.32 | -2.80 to +5.24 |
| (f1) mine (PM), T1 in ETR's order | 22 | +0.04 | -0.03 to +0.13 | -0.10 | -0.53 to +0.32 | +0.71 | +0.15 to +1.36 |
| (f2) mine (PM), T2 in ETR's order | 23 | +0.06 | -0.14 to +0.24 | -0.06 | -0.97 to +0.79 | +0.05 | -1.22 to +1.27 |
| (f3) mine (PM), T3 in ETR's order | 23 | -0.33 | -0.67 to +0.02 | -0.32 | -1.52 to +0.95 | -1.10 | -2.19 to -0.01 |
| (f4) mine (PM), T4 in ETR's order | 23 | -0.08 | -0.17 to -0.01 | -0.55 | -1.13 to -0.03 | +0.31 | -0.43 to +1.00 |
| (f5) mine (PM), T5 in ETR's order | 23 | -0.09 | -0.20 to +0.02 | -0.73 | -1.70 to +0.24 | +0.96 | -0.42 to +2.39 |
| (b') the button rebuilt here (PM) | 25 | -0.95 | -1.86 to -0.14 | -2.47 | -5.26 to +0.20 | +0.93 | -1.86 to +3.66 |
| (f) the button on ETR tiers (PM) | 25 | -1.24 | -2.15 to -0.33 | -3.41 | -6.94 to +0.14 | +2.04 | -1.81 to +5.96 |
| (g) ETR order, the button's T5 rule (PM) | 25 | -0.94 | -1.82 to -0.13 | -3.85 | -7.31 to -0.54 | +0.43 | -3.74 to +4.57 |
| (g) ETR order, the button's T5 rule (PM) minus (e) ETR (PM) | 25 | -0.04 | -0.17 to +0.08 | -0.23 | -0.64 to +0.15 | +0.89 | +0.14 to +1.75 |
| (b') the button rebuilt here (PM) minus (f) the button on ETR tiers (PM) | 25 | -0.29 | -1.10 to +0.59 | -0.95 | -3.29 to +1.58 | +1.11 | -1.67 to +3.75 |
| (f) the button on ETR tiers (PM) minus (e) ETR (PM) | 25 | +0.25 | -0.25 to +0.75 | -0.67 | -2.92 to +1.55 | -0.72 | -2.87 to +1.41 |
| (g) ETR order, the button's T5 rule (PM) minus (f) the button on ETR tiers (PM) | 25 | -0.29 | -0.78 to +0.19 | +0.44 | -1.80 to +2.75 | +1.62 | -0.66 to +3.86 |

## Season: AM

| List | Nights | Seats | Top 1% | Top 10% | Mean finish pct | Cash | ROI |
|---|---|---|---|---|---|---|---|
| (a) my locked list | 20 | 124078 | 1.41% | 13.3% | 44.7 | 24% | +30% |
| (b) the button's list | 5 | 36606 | 1.29% | 12.3% | 47.1 | 22% | +21% |
| (c1) mine, T1's moves undone | 5 | 36606 | 2.15% | 16.6% | 38.9 | 30% | +88% |
| (c2) mine, T2's moves undone | 5 | 36606 | 1.62% | 14.0% | 43.6 | 25% | +34% |
| (c3) mine, T3's moves undone | 5 | 36606 | 1.82% | 17.1% | 39.6 | 30% | +69% |
| (c4) mine, T4's moves undone | 5 | 36606 | 2.29% | 17.2% | 40.3 | 30% | +107% |
| (c5) mine, T5's moves undone | 5 | 36606 | 2.18% | 16.8% | 39.9 | 30% | +95% |
| (d) ADP | 20 | 124078 | 1.18% | 11.1% | 48.1 | 20% | +4% |

Paired: (a) minus each list, same pods and seats, nights resampled for the 80% ranges.

| (a) minus, or the pair named | Nights | Top 1% (pts) | 80% range | Top 10% (pts) | 80% range | Mean finish pct (lower is better) | 80% range |
|---|---|---|---|---|---|---|---|
| (b) the button's list | 5 | +0.89 | +0.41 to +1.46 | +5.25 | +4.58 to +5.85 | -8.76 | -12.03 to -5.13 |
| (c1) mine, T1's moves undone | 5 | +0.04 | +0.00 to +0.06 | +0.95 | -0.01 to +1.73 | -0.56 | -1.03 to +0.01 |
| (c2) mine, T2's moves undone | 5 | +0.57 | +0.07 to +1.17 | +3.56 | +1.52 to +6.04 | -5.24 | -7.98 to -1.90 |
| (c3) mine, T3's moves undone | 5 | +0.37 | -0.01 to +0.81 | +0.48 | -0.43 to +1.34 | -1.31 | -2.03 to -0.52 |
| (c4) mine, T4's moves undone | 5 | -0.10 | -0.43 to +0.18 | +0.33 | -1.72 to +1.94 | -2.00 | -4.39 to +0.84 |
| (c5) mine, T5's moves undone | 5 | +0.01 | -0.51 to +0.53 | +0.72 | -1.29 to +2.46 | -1.55 | -2.80 to +0.04 |
| (d) ADP | 20 | +0.23 | -0.19 to +0.63 | +2.24 | +0.19 to +4.18 | -3.43 | -6.51 to -0.28 |

## Season: PM

| List | Nights | Seats | Top 1% | Top 10% | Mean finish pct | Cash | ROI |
|---|---|---|---|---|---|---|---|
| (a) my locked list | 25 | 296794 | 1.24% | 12.4% | 45.4 | 23% | +30% |
| (b) the button's list | 7 | 90978 | 2.39% | 13.2% | 46.5 | 23% | +74% |
| (c1) mine, T1's moves undone | 7 | 90978 | 0.80% | 11.5% | 43.7 | 23% | -14% |
| (c2) mine, T2's moves undone | 7 | 90978 | 0.66% | 10.0% | 46.9 | 20% | -25% |
| (c3) mine, T3's moves undone | 7 | 90978 | 2.32% | 13.8% | 43.5 | 25% | +69% |
| (c4) mine, T4's moves undone | 7 | 90978 | 0.86% | 11.1% | 47.0 | 22% | -15% |
| (c5) mine, T5's moves undone | 7 | 90978 | 0.97% | 12.1% | 45.1 | 23% | -0% |
| (d) ADP | 25 | 296794 | 1.07% | 10.8% | 48.3 | 20% | -3% |
| (e) ETR (PM) | 25 | 296794 | 2.23% | 16.5% | 44.1 | 27% | +71% |
| (f1) mine (PM), T1 in ETR's order | 22 | 251084 | 1.27% | 12.5% | 45.0 | 23% | +30% |
| (f2) mine (PM), T2 in ETR's order | 23 | 264800 | 1.20% | 12.3% | 45.8 | 23% | +26% |
| (f3) mine (PM), T3 in ETR's order | 23 | 264800 | 1.59% | 12.5% | 46.9 | 23% | +34% |
| (f4) mine (PM), T4 in ETR's order | 23 | 264800 | 1.34% | 12.8% | 45.5 | 23% | +31% |
| (f5) mine (PM), T5 in ETR's order | 23 | 264800 | 1.35% | 12.9% | 44.9 | 24% | +37% |
| (b') the button rebuilt here (PM) | 25 | 296794 | 2.19% | 14.9% | 44.5 | 25% | +111% |
| (f) the button on ETR tiers (PM) | 25 | 296794 | 2.48% | 15.8% | 43.4 | 27% | +101% |
| (g) ETR order, the button's T5 rule (PM) | 25 | 296794 | 2.19% | 16.2% | 45.0 | 26% | +66% |

Paired: (a) minus each list, same pods and seats, nights resampled for the 80% ranges.

| (a) minus, or the pair named | Nights | Top 1% (pts) | 80% range | Top 10% (pts) | 80% range | Mean finish pct (lower is better) | 80% range |
|---|---|---|---|---|---|---|---|
| (b) the button's list | 7 | -1.59 | -3.35 to +0.10 | -1.74 | -6.34 to +2.59 | -1.75 | -7.89 to +4.00 |
| (c1) mine, T1's moves undone | 7 | +0.00 | +0.00 to +0.00 | -0.05 | -0.10 to +0.00 | +1.09 | +0.00 to +2.36 |
| (c2) mine, T2's moves undone | 7 | +0.15 | -0.03 to +0.35 | +1.44 | -0.67 to +3.64 | -2.14 | -4.71 to +0.10 |
| (c3) mine, T3's moves undone | 7 | -1.52 | -3.26 to +0.16 | -2.29 | -5.64 to +1.00 | +1.33 | -0.68 to +3.37 |
| (c4) mine, T4's moves undone | 7 | -0.06 | -0.19 to +0.07 | +0.34 | -0.95 to +1.55 | -2.24 | -4.60 to -0.11 |
| (c5) mine, T5's moves undone | 7 | -0.17 | -0.38 to +0.02 | -0.62 | -1.93 to +0.56 | -0.26 | -2.00 to +1.43 |
| (d) ADP | 25 | +0.17 | -0.23 to +0.56 | +1.56 | -0.07 to +2.99 | -2.87 | -5.06 to -0.41 |
| (e) ETR (PM) | 25 | -0.99 | -1.79 to -0.21 | -4.08 | -7.38 to -0.76 | +1.32 | -2.80 to +5.24 |
| (f1) mine (PM), T1 in ETR's order | 22 | +0.04 | -0.03 to +0.13 | -0.10 | -0.53 to +0.32 | +0.71 | +0.15 to +1.36 |
| (f2) mine (PM), T2 in ETR's order | 23 | +0.06 | -0.14 to +0.24 | -0.06 | -0.97 to +0.79 | +0.05 | -1.22 to +1.27 |
| (f3) mine (PM), T3 in ETR's order | 23 | -0.33 | -0.67 to +0.02 | -0.32 | -1.52 to +0.95 | -1.10 | -2.19 to -0.01 |
| (f4) mine (PM), T4 in ETR's order | 23 | -0.08 | -0.17 to -0.01 | -0.55 | -1.13 to -0.03 | +0.31 | -0.43 to +1.00 |
| (f5) mine (PM), T5 in ETR's order | 23 | -0.09 | -0.20 to +0.02 | -0.73 | -1.70 to +0.24 | +0.96 | -0.42 to +2.39 |
| (b') the button rebuilt here (PM) | 25 | -0.95 | -1.86 to -0.14 | -2.47 | -5.26 to +0.20 | +0.93 | -1.86 to +3.66 |
| (f) the button on ETR tiers (PM) | 25 | -1.24 | -2.15 to -0.33 | -3.41 | -6.94 to +0.14 | +2.04 | -1.81 to +5.96 |
| (g) ETR order, the button's T5 rule (PM) | 25 | -0.94 | -1.82 to -0.13 | -3.85 | -7.31 to -0.54 | +0.43 | -3.74 to +4.57 |
| (g) ETR order, the button's T5 rule (PM) minus (e) ETR (PM) | 25 | -0.04 | -0.17 to +0.08 | -0.23 | -0.64 to +0.15 | +0.89 | +0.14 to +1.75 |
| (b') the button rebuilt here (PM) minus (f) the button on ETR tiers (PM) | 25 | -0.29 | -1.10 to +0.59 | -0.95 | -3.29 to +1.58 | +1.11 | -1.67 to +3.75 |
| (f) the button on ETR tiers (PM) minus (e) ETR (PM) | 25 | +0.25 | -0.25 to +0.75 | -0.67 | -2.92 to +1.55 | -0.72 | -2.87 to +1.41 |
| (g) ETR order, the button's T5 rule (PM) minus (f) the button on ETR tiers (PM) | 25 | -0.29 | -0.78 to +0.19 | +0.44 | -1.80 to +2.75 | +1.62 | -0.66 to +3.86 |

## Top 1% at my seats: luck or list

My locked list (a) replayed at my real seats and pods only (1926 teams, 25 nights), against my real teams.

| | Top-1% finishes |
|---|---|
| My real teams | 17 |
| (a) at the same seats, the replay's draw | 25 |
| (a), 200 round-6 redraws: median (10%-90%) | 26 (22-31) |
| (a), nights resampled: 80% range | 17-33 |
| (a), Poisson spread around its redraw mean (26.1): 80% range | 20-33 |
| Real minus (a), nights resampled: 80% range | -8 (-18 to +3) |

The redraws show how much the round-6 pick alone moves the count; the nights and Poisson ranges show how far a count this size swings by luck. Real and (a) share the same nights' box scores, so the real-minus-(a) range is the gap from drafting off something other than the locked list (earlier boards, round-6 choices).

## The PM button on ETR tiers (since 2026-11-17, PM)

Which ETR version the PM should use: (e) pure ETR, (f) the button on ETR tiers, (g) ETR with the button's T5 rule. Points of top-10% and top-1% rate (80% range, nights resampled); below zero, the second list did better.

| Pair | Nights | Top 10% (pts) | 80% range | Top 1% (pts) | 80% range |
|---|---|---|---|---|---|
| (f) the button on ETR tiers (PM) minus (e) ETR (PM) | 0 | - | - | - | - |
| (g) ETR order, the button's T5 rule (PM) minus (f) the button on ETR tiers (PM) | 0 | - | - | - | - |
| (g) ETR order, the button's T5 rule (PM) minus (e) ETR (PM) | 0 | - | - | - | - |

(f) rebuilt here against the board's own PM order (the ETR-tier button from 2026-11-17), places of the top 36 that agree: no nights yet.

## Since the rules went in

(a) minus each list, both windows, top-10% points (80% range), from each rule date's first night per window (AM and PM apart in pod_replay.json). Season is above.

### Since 2026-11-13 (AM) / 2026-11-13 (PM): gallagher-bad-arrow, swap-button

| (a) minus, or the pair named | Window | Nights | Top 10% (pts) | 80% range | Top 1% (pts) | Mean finish pct |
|---|---|---|---|---|---|---|
| (b) the button's list | BOTH | 3 | -3.48 | -8.08 to +1.42 | -2.45 | +1.47 |
| (c1) mine, T1's moves undone | BOTH | 3 | -0.00 | -0.00 to +0.00 | +0.00 | +0.00 |
| (c2) mine, T2's moves undone | BOTH | 3 | +1.14 | +0.14 to +2.06 | +0.18 | -1.48 |
| (c3) mine, T3's moves undone | BOTH | 3 | -4.74 | -9.48 to +0.31 | -2.64 | +2.85 |
| (c4) mine, T4's moves undone | BOTH | 3 | -0.17 | -1.23 to +0.82 | -0.12 | -0.12 |
| (c5) mine, T5's moves undone | BOTH | 3 | +0.20 | -0.48 to +0.83 | +0.00 | -0.02 |
| (d) ADP | BOTH | 3 | +4.94 | +2.88 to +6.73 | +0.14 | -11.76 |
| (e) ETR (PM) | BOTH | 3 | -14.03 | -26.83 to -3.38 | -3.91 | +11.51 |
| (f1) mine (PM), T1 in ETR's order | BOTH | 3 | +0.00 | +0.00 to +0.00 | +0.00 | +0.00 |
| (f2) mine (PM), T2 in ETR's order | BOTH | 3 | +0.36 | -0.34 to +1.00 | -0.02 | -2.48 |
| (f3) mine (PM), T3 in ETR's order | BOTH | 3 | -3.05 | -6.49 to +0.29 | -1.41 | +2.21 |
| (f4) mine (PM), T4 in ETR's order | BOTH | 3 | +0.02 | -0.01 to +0.05 | +0.01 | +0.01 |
| (f5) mine (PM), T5 in ETR's order | BOTH | 3 | -2.79 | -5.33 to -0.67 | -0.34 | +3.02 |
| (b') the button rebuilt here (PM) | BOTH | 3 | -3.29 | -8.50 to +2.48 | -2.17 | -1.01 |
| (f) the button on ETR tiers (PM) | BOTH | 3 | -6.02 | -10.44 to -2.34 | -2.10 | +6.60 |
| (g) ETR order, the button's T5 rule (PM) | BOTH | 3 | -12.70 | -26.66 to -1.09 | -3.75 | +7.20 |
| (g) ETR order, the button's T5 rule (PM) minus (e) ETR (PM) | BOTH | 3 | -1.33 | -2.37 to -0.17 | -0.17 | +4.31 |
| (b') the button rebuilt here (PM) minus (f) the button on ETR tiers (PM) | BOTH | 3 | -2.73 | -8.96 to +2.89 | +0.07 | +7.60 |
| (f) the button on ETR tiers (PM) minus (e) ETR (PM) | BOTH | 3 | -8.01 | -16.80 to -0.09 | -1.81 | +4.91 |
| (g) ETR order, the button's T5 rule (PM) minus (f) the button on ETR tiers (PM) | BOTH | 3 | +6.68 | -1.25 to +16.22 | +1.65 | -0.60 |

### Since 2026-11-14 (AM) / 2026-11-13 (PM): elite-cut, q-adp-fall, q-keeps-tier, q-t1-to-t2, q-t5-follows-t5, q-teammate-tiebreak, t2-am-adp, t2-pm-elite-break, t3-pricey-over-t4-value, t34-am-adp-groups, t34-pm-etr-groups, t4-borrow-t3, t4-ends-round6, t4-pricey-to-t5, t4-value-from-a5, t5-4drafter-no-line, t5-drafted-60, t5-ends-at-cut, t5-minutes-floor

| (a) minus, or the pair named | Window | Nights | Top 10% (pts) | 80% range | Top 1% (pts) | Mean finish pct |
|---|---|---|---|---|---|---|
| (b) the button's list | BOTH | 3 | -4.27 | -10.94 to +1.42 | -2.77 | +1.39 |
| (c1) mine, T1's moves undone | BOTH | 3 | -0.00 | -0.00 to +0.00 | +0.00 | +0.00 |
| (c2) mine, T2's moves undone | BOTH | 3 | +1.11 | +0.00 to +2.13 | +0.17 | -2.14 |
| (c3) mine, T3's moves undone | BOTH | 3 | -5.20 | -11.64 to +0.31 | -2.94 | +3.13 |
| (c4) mine, T4's moves undone | BOTH | 3 | -0.49 | -1.23 to +0.39 | -0.15 | +0.09 |
| (c5) mine, T5's moves undone | BOTH | 3 | -0.04 | -0.48 to +0.48 | -0.01 | +0.22 |
| (d) ADP | BOTH | 3 | +4.92 | +2.88 to +7.11 | +0.16 | -12.25 |
| (e) ETR (PM) | BOTH | 3 | -14.03 | -26.83 to -3.38 | -3.91 | +11.51 |
| (f1) mine (PM), T1 in ETR's order | BOTH | 3 | +0.00 | +0.00 to +0.00 | +0.00 | +0.00 |
| (f2) mine (PM), T2 in ETR's order | BOTH | 3 | +0.36 | -0.34 to +1.00 | -0.02 | -2.48 |
| (f3) mine (PM), T3 in ETR's order | BOTH | 3 | -3.05 | -6.49 to +0.29 | -1.41 | +2.21 |
| (f4) mine (PM), T4 in ETR's order | BOTH | 3 | +0.02 | -0.01 to +0.05 | +0.01 | +0.01 |
| (f5) mine (PM), T5 in ETR's order | BOTH | 3 | -2.79 | -5.33 to -0.67 | -0.34 | +3.02 |
| (b') the button rebuilt here (PM) | BOTH | 3 | -3.29 | -8.50 to +2.48 | -2.17 | -1.01 |
| (f) the button on ETR tiers (PM) | BOTH | 3 | -6.02 | -10.44 to -2.34 | -2.10 | +6.60 |
| (g) ETR order, the button's T5 rule (PM) | BOTH | 3 | -12.70 | -26.66 to -1.09 | -3.75 | +7.20 |
| (g) ETR order, the button's T5 rule (PM) minus (e) ETR (PM) | BOTH | 3 | -1.33 | -2.37 to -0.17 | -0.17 | +4.31 |
| (b') the button rebuilt here (PM) minus (f) the button on ETR tiers (PM) | BOTH | 3 | -2.73 | -8.96 to +2.89 | +0.07 | +7.60 |
| (f) the button on ETR tiers (PM) minus (e) ETR (PM) | BOTH | 3 | -8.01 | -16.80 to -0.09 | -1.81 | +4.91 |
| (g) ETR order, the button's T5 rule (PM) minus (f) the button on ETR tiers (PM) | BOTH | 3 | +6.68 | -1.25 to +16.22 | +1.65 | -0.60 |

### Since 2026-11-14 (AM) / 2026-11-14 (PM): proj-box-3-days, proj-fresh-absence

| (a) minus, or the pair named | Window | Nights | Top 10% (pts) | 80% range | Top 1% (pts) | Mean finish pct |
|---|---|---|---|---|---|---|
| (b) the button's list | BOTH | 2 | +1.08 | - | +0.13 | -1.97 |
| (c1) mine, T1's moves undone | BOTH | 2 | -0.00 | - | +0.00 | +0.00 |
| (c2) mine, T2's moves undone | BOTH | 2 | +1.58 | - | +0.25 | -3.04 |
| (c3) mine, T3's moves undone | BOTH | 2 | +0.24 | - | +0.04 | -0.07 |
| (c4) mine, T4's moves undone | BOTH | 2 | -0.94 | - | -0.24 | +0.58 |
| (c5) mine, T5's moves undone | BOTH | 2 | -0.37 | - | -0.03 | +0.47 |
| (d) ADP | BOTH | 2 | +3.64 | - | +0.41 | -8.57 |
| (e) ETR (PM) | BOTH | 2 | -17.00 | - | -3.51 | +13.55 |
| (f1) mine (PM), T1 in ETR's order | BOTH | 2 | +0.00 | - | +0.00 | +0.00 |
| (f2) mine (PM), T2 in ETR's order | BOTH | 2 | -0.02 | - | -0.04 | -3.59 |
| (f3) mine (PM), T3 in ETR's order | BOTH | 2 | +0.20 | - | +0.04 | +0.01 |
| (f4) mine (PM), T4 in ETR's order | BOTH | 2 | +0.04 | - | +0.01 | +0.01 |
| (f5) mine (PM), T5 in ETR's order | BOTH | 2 | -3.87 | - | -0.47 | +4.25 |
| (b') the button rebuilt here (PM) | BOTH | 2 | +1.78 | - | +0.11 | -4.81 |
| (f) the button on ETR tiers (PM) | BOTH | 2 | -4.44 | - | -0.94 | +6.64 |
| (g) ETR order, the button's T5 rule (PM) | BOTH | 2 | -15.11 | - | -3.29 | +7.22 |
| (g) ETR order, the button's T5 rule (PM) minus (e) ETR (PM) | BOTH | 2 | -1.89 | - | -0.22 | +6.33 |
| (b') the button rebuilt here (PM) minus (f) the button on ETR tiers (PM) | BOTH | 2 | -6.21 | - | -1.04 | +11.45 |
| (f) the button on ETR tiers (PM) minus (e) ETR (PM) | BOTH | 2 | -12.56 | - | -2.57 | +6.91 |
| (g) ETR order, the button's T5 rule (PM) minus (f) the button on ETR tiers (PM) | BOTH | 2 | +10.67 | - | +2.35 | -0.59 |

### Since 2026-11-17 (AM) / 2026-11-17 (PM): tiers-pm-etr

| (a) minus, or the pair named | Window | Nights | Top 10% (pts) | 80% range | Top 1% (pts) | Mean finish pct |
|---|---|---|---|---|---|---|

## Round 6 fidelity

My real round-6 pick (each of my real teams' sixth by ADP-at-draft), placed among (a)'s top still available at that seat's round-6 pick in the replay. The replay's draw puts 38%/25%/14%/11%/6%/6% at places 1-6 (from the first replay's even-draw check).

| Window | Teams | #1 | #2 | #3 | #4 | #5 | #6 | 7-15 | not in top 15 |
|---|---|---|---|---|---|---|---|---|---|
| BOTH | 1926 | 30% | 20% | 11% | 9% | 5% | 5% | 10% | 10% |
| AM | 563 | 32% | 18% | 14% | 8% | 4% | 5% | 4% | 15% |
| PM | 1363 | 29% | 21% | 10% | 9% | 5% | 5% | 12% | 8% |

By night (both windows): the share of my real round-6 picks that were (a)'s #1 available, #1-3, #1-6.

| Night | Teams | #1 | #1-3 | #1-6 |
|---|---|---|---|---|
| 2026-10-21 | 50 | 36% | 76% | 94% |
| 2026-10-22 | 20 | 50% | 90% | 95% |
| 2026-10-23 | 60 | 23% | 62% | 92% |
| 2026-10-24 | 40 | 2% | 60% | 88% |
| 2026-10-25 | 80 | 14% | 54% | 92% |
| 2026-10-26 | 100 | 34% | 66% | 75% |
| 2026-10-27 | 150 | 47% | 69% | 86% |
| 2026-10-28 | 110 | 26% | 45% | 64% |
| 2026-10-29 | 100 | 52% | 77% | 78% |
| 2026-10-30 | 182 | 29% | 71% | 91% |
| 2026-10-31 | 40 | 10% | 58% | 68% |
| 2026-11-01 | 40 | 78% | 100% | 100% |
| 2026-11-02 | 85 | 21% | 44% | 75% |
| 2026-11-04 | 90 | 23% | 52% | 86% |
| 2026-11-05 | 60 | 52% | 88% | 97% |
| 2026-11-06 | 92 | 5% | 21% | 36% |
| 2026-11-07 | 40 | 30% | 78% | 92% |
| 2026-11-08 | 40 | 62% | 100% | 100% |
| 2026-11-09 | 95 | 15% | 33% | 64% |
| 2026-11-10 | 80 | 25% | 54% | 81% |
| 2026-11-11 | 80 | 15% | 41% | 61% |
| 2026-11-12 | 80 | 41% | 81% | 98% |
| 2026-11-13 | 102 | 36% | 66% | 75% |
| 2026-11-14 | 10 | 10% | 80% | 90% |
| 2026-11-16 | 100 | 22% | 57% | 77% |

## My real teams against (a)

My real teams beside (a) replayed at the same seats, and where they land in (a)'s replayed distribution (all seats, same night and window).

| Window | Teams | Real top 1% | (a) top 1% | Real top 10% | (a) top 10% | Real mean finish | (a) mean finish | Real beat this share of (a)'s replays |
|---|---|---|---|---|---|---|---|---|
| BOTH | 1926 | 0.88% | 1.30% | 13.0% | 13.9% | 44.9 | 43.0 | 49% |
| AM | 563 | 0.71% | 1.24% | 14.0% | 14.6% | 46.2 | 42.8 | 48% |
| PM | 1363 | 0.95% | 1.32% | 12.5% | 13.6% | 44.4 | 43.0 | 49% |

## By night

Top 10% / mean finish percentile for each list; seats are every seat in that window's pods.

| Night | Window | Seats | (a) | (b) | (c1) | (c2) | (c3) | (c4) | (c5) | (d) | (e) | (f1) | (f2) | (f3) | (f4) | (f5) | (b') | (f) | (g) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-21 | PM | 16254 | 13.7% / 41 | - | - | - | - | - | - | 7.4% / 49 | 26.9% / 29 | - | - | - | - | - | 42.1% / 25 | 29.5% / 27 | 24.1% / 32 |
| 2026-10-22 | PM | 15740 | 14.2% / 43 | - | - | - | - | - | - | 10.5% / 49 | 14.5% / 45 | - | - | - | - | - | 3.4% / 51 | 2.3% / 56 | 14.8% / 44 |
| 2026-10-23 | PM | 15732 | 14.0% / 41 | - | - | - | - | - | - | 8.1% / 48 | 1.5% / 63 | 14.6% / 39 | 19.1% / 36 | 13.2% / 42 | 13.3% / 43 | 11.5% / 43 | 9.4% / 46 | 3.6% / 60 | 1.3% / 63 |
| 2026-10-24 | AM | 6714 | 2.5% / 51 | - | - | - | - | - | - | 12.7% / 42 | - | - | - | - | - | - | - | - | - |
| 2026-10-24 | PM | 7860 | 24.7% / 45 | - | - | - | - | - | - | 12.3% / 43 | 23.3% / 52 | 24.7% / 45 | 24.7% / 45 | 24.7% / 45 | 24.8% / 45 | 23.8% / 50 | 19.9% / 44 | 22.5% / 41 | 21.4% / 53 |
| 2026-10-25 | AM | 3366 | 8.1% / 40 | - | - | - | - | - | - | 4.2% / 52 | - | - | - | - | - | - | - | - | - |
| 2026-10-25 | PM | 7782 | 2.7% / 51 | - | - | - | - | - | - | 4.7% / 54 | 4.2% / 48 | 2.7% / 51 | 2.9% / 50 | 2.9% / 50 | 3.5% / 48 | 2.7% / 50 | 5.5% / 48 | 3.6% / 49 | 4.3% / 48 |
| 2026-10-26 | PM | 13530 | 27.3% / 30 | - | - | - | - | - | - | 14.3% / 41 | 21.6% / 32 | 22.4% / 33 | 24.5% / 30 | 36.1% / 23 | 26.5% / 31 | 24.7% / 32 | 21.8% / 29 | 13.3% / 34 | 21.8% / 32 |
| 2026-10-27 | AM | 5046 | 6.6% / 62 | - | - | - | - | - | - | 14.3% / 41 | - | - | - | - | - | - | - | - | - |
| 2026-10-27 | PM | 10704 | 14.9% / 42 | - | - | - | - | - | - | 13.7% / 43 | 10.2% / 49 | 14.9% / 42 | 11.4% / 47 | 6.4% / 48 | 22.7% / 34 | 8.8% / 44 | 11.7% / 47 | 7.4% / 54 | 12.1% / 49 |
| 2026-10-28 | AM | 4032 | 15.0% / 43 | - | - | - | - | - | - | 13.8% / 45 | - | - | - | - | - | - | - | - | - |
| 2026-10-28 | PM | 11718 | 3.5% / 60 | - | - | - | - | - | - | 16.4% / 43 | 2.9% / 70 | 3.5% / 60 | 5.9% / 51 | 2.8% / 68 | 3.4% / 61 | 5.8% / 57 | 2.8% / 59 | 6.2% / 58 | 3.0% / 70 |
| 2026-10-29 | AM | 4708 | 13.7% / 35 | - | - | - | - | - | - | 6.7% / 62 | - | - | - | - | - | - | - | - | - |
| 2026-10-29 | PM | 8848 | 15.2% / 40 | - | - | - | - | - | - | 4.3% / 59 | 34.5% / 25 | 15.2% / 40 | 17.7% / 37 | 13.8% / 41 | 19.2% / 39 | 15.2% / 40 | 22.2% / 37 | 42.3% / 21 | 34.5% / 25 |
| 2026-10-30 | AM | 7104 | 10.6% / 43 | - | - | - | - | - | - | 8.3% / 55 | - | - | - | - | - | - | - | - | - |
| 2026-10-30 | PM | 13764 | 15.0% / 36 | - | - | - | - | - | - | 8.4% / 53 | 16.6% / 30 | 16.8% / 33 | 11.1% / 40 | 17.6% / 33 | 18.9% / 32 | 15.2% / 35 | 17.6% / 31 | 13.7% / 39 | 16.1% / 31 |
| 2026-10-31 | AM | 5322 | 17.2% / 46 | - | - | - | - | - | - | 12.6% / 48 | - | - | - | - | - | - | - | - | - |
| 2026-10-31 | PM | 8682 | 6.0% / 60 | - | - | - | - | - | - | 15.7% / 48 | 3.7% / 69 | 6.0% / 60 | 3.9% / 64 | 5.3% / 63 | 5.5% / 60 | 5.5% / 61 | 3.0% / 66 | 1.4% / 69 | 1.5% / 71 |
| 2026-11-01 | AM | 6100 | 9.9% / 51 | - | - | - | - | - | - | 14.6% / 47 | - | - | - | - | - | - | - | - | - |
| 2026-11-01 | PM | 4180 | 18.0% / 45 | - | - | - | - | - | - | 16.0% / 48 | 17.4% / 39 | 18.0% / 45 | 17.2% / 41 | 17.9% / 45 | 17.9% / 44 | 18.0% / 44 | 19.8% / 30 | 19.2% / 31 | 17.4% / 39 |
| 2026-11-02 | AM | 5778 | 10.2% / 54 | - | - | - | - | - | - | 10.0% / 52 | - | - | - | - | - | - | - | - | - |
| 2026-11-02 | PM | 12894 | 11.8% / 46 | - | - | - | - | - | - | 16.2% / 45 | 3.8% / 61 | 11.8% / 46 | 7.3% / 52 | 6.6% / 55 | 11.5% / 47 | 12.5% / 45 | 7.1% / 58 | 11.4% / 43 | 3.4% / 62 |
| 2026-11-04 | AM | 9480 | 20.4% / 44 | - | - | - | - | - | - | 11.9% / 43 | - | - | - | - | - | - | - | - | - |
| 2026-11-04 | PM | 11868 | 10.0% / 58 | - | - | - | - | - | - | 10.8% / 45 | 10.5% / 54 | 10.0% / 58 | 10.0% / 57 | 10.0% / 58 | 11.0% / 57 | 11.0% / 57 | 18.6% / 45 | 12.8% / 51 | 9.9% / 55 |
| 2026-11-05 | AM | 6776 | 9.8% / 48 | - | - | - | - | - | - | 9.6% / 45 | - | - | - | - | - | - | - | - | - |
| 2026-11-05 | PM | 13716 | 8.6% / 49 | - | - | - | - | - | - | 6.9% / 47 | 21.2% / 41 | - | 10.1% / 44 | 17.9% / 47 | 9.5% / 48 | 9.2% / 48 | 20.9% / 34 | 38.2% / 27 | 21.8% / 41 |
| 2026-11-06 | AM | 6090 | 10.8% / 50 | - | - | - | - | - | - | 7.5% / 54 | - | - | - | - | - | - | - | - | - |
| 2026-11-06 | PM | 14706 | 7.0% / 57 | - | - | - | - | - | - | 6.0% / 57 | 35.0% / 27 | 10.4% / 54 | 5.0% / 58 | 5.9% / 60 | 8.5% / 54 | 16.0% / 41 | 23.4% / 38 | 37.3% / 30 | 38.0% / 26 |
| 2026-11-07 | AM | 7806 | 12.5% / 45 | - | - | - | - | - | - | 11.5% / 42 | - | - | - | - | - | - | - | - | - |
| 2026-11-07 | PM | 10764 | 10.2% / 49 | - | - | - | - | - | - | 16.2% / 42 | 24.7% / 35 | 10.2% / 49 | 13.1% / 47 | 10.3% / 50 | 10.2% / 49 | 10.2% / 49 | 25.0% / 39 | 16.8% / 42 | 25.1% / 35 |
| 2026-11-08 | AM | 3210 | 12.5% / 47 | - | - | - | - | - | - | 14.2% / 50 | - | - | - | - | - | - | - | - | - |
| 2026-11-08 | PM | 7074 | 15.7% / 35 | - | - | - | - | - | - | 14.2% / 49 | 5.2% / 53 | 15.7% / 35 | 10.7% / 42 | 11.3% / 39 | 16.4% / 34 | 16.8% / 34 | 17.4% / 40 | 17.0% / 36 | 5.5% / 52 |
| 2026-11-09 | AM | 5940 | 10.4% / 50 | - | - | - | - | - | - | 14.2% / 46 | - | - | - | - | - | - | - | - | - |
| 2026-11-09 | PM | 12720 | 15.4% / 38 | 2.3% / 61 | 15.4% / 38 | 3.1% / 52 | 11.8% / 41 | 12.1% / 45 | 15.1% / 39 | 17.1% / 43 | 2.7% / 58 | 15.4% / 38 | 15.4% / 38 | 14.2% / 39 | 12.0% / 45 | 16.1% / 38 | 11.5% / 48 | 1.5% / 60 | 3.3% / 56 |
| 2026-11-10 | AM | 7344 | 20.3% / 35 | 13.4% / 42 | 20.3% / 35 | 20.3% / 35 | 16.7% / 39 | 20.3% / 35 | 15.8% / 39 | 8.7% / 53 | - | - | - | - | - | - | - | - | - |
| 2026-11-10 | PM | 13488 | 13.8% / 48 | 14.9% / 47 | 13.8% / 48 | 13.7% / 48 | 13.8% / 48 | 13.8% / 48 | 14.9% / 47 | 11.0% / 46 | 14.5% / 44 | 13.8% / 48 | 22.0% / 41 | 11.2% / 52 | 13.5% / 49 | 16.1% / 46 | 4.7% / 61 | 8.0% / 50 | 13.3% / 45 |
| 2026-11-11 | AM | 11076 | 10.5% / 48 | 5.1% / 63 | 7.3% / 50 | 9.8% / 53 | 10.3% / 49 | 7.2% / 56 | 9.0% / 51 | 14.2% / 44 | - | - | - | - | - | - | - | - | - |
| 2026-11-11 | PM | 9774 | 10.2% / 46 | 3.0% / 69 | 10.2% / 46 | 9.6% / 48 | 9.8% / 46 | 5.7% / 61 | 6.2% / 57 | 15.5% / 41 | 1.0% / 78 | 10.2% / 46 | 10.6% / 46 | 10.2% / 46 | 9.6% / 46 | 4.9% / 59 | 4.3% / 70 | 2.4% / 76 | 1.2% / 78 |
| 2026-11-12 | AM | 6336 | 24.6% / 29 | 20.5% / 36 | 24.6% / 29 | 14.3% / 41 | 25.6% / 30 | 25.4% / 28 | 30.8% / 25 | 9.7% / 49 | - | - | - | - | - | - | - | - | - |
| 2026-11-12 | PM | 11508 | 5.6% / 54 | 17.1% / 38 | 6.0% / 46 | 8.8% / 51 | 5.7% / 54 | 11.2% / 50 | 12.5% / 50 | 12.0% / 46 | 24.4% / 32 | 6.0% / 46 | 6.2% / 54 | 2.3% / 60 | 5.6% / 54 | 8.7% / 52 | 8.2% / 42 | 29.7% / 26 | 24.9% / 34 |
| 2026-11-13 | AM | 5694 | 14.7% / 40 | 11.3% / 38 | 14.7% / 40 | 13.4% / 36 | 15.5% / 40 | 12.1% / 42 | 12.5% / 42 | 9.6% / 47 | - | - | - | - | - | - | - | - | - |
| 2026-11-13 | PM | 14658 | 16.3% / 33 | 33.4% / 23 | 16.3% / 33 | 16.3% / 33 | 34.5% / 22 | 15.7% / 34 | 15.6% / 33 | 8.4% / 54 | 24.5% / 25 | 16.3% / 33 | 15.2% / 33 | 25.8% / 26 | 16.3% / 33 | 17.0% / 32 | 29.6% / 26 | 25.5% / 26 | 24.3% / 25 |
| 2026-11-14 | PM | 16410 | 9.6% / 48 | 9.6% / 48 | 9.6% / 48 | 9.6% / 48 | 9.6% / 48 | 9.6% / 48 | 9.6% / 48 | 8.3% / 52 | 10.8% / 48 | 9.6% / 48 | 8.8% / 56 | 9.6% / 48 | 9.5% / 48 | 10.2% / 47 | 9.6% / 48 | 8.9% / 51 | 7.6% / 59 |
| 2026-11-16 | AM | 6156 | 22.4% / 33 | 16.5% / 44 | 22.4% / 33 | 14.2% / 46 | 22.4% / 33 | 27.7% / 30 | 21.7% / 35 | 10.5% / 53 | - | - | - | - | - | - | - | - | - |
| 2026-11-16 | PM | 12420 | 8.2% / 48 | 8.0% / 48 | 8.2% / 48 | 7.8% / 51 | 7.5% / 49 | 8.2% / 48 | 9.5% / 46 | 5.4% / 57 | 46.0% / 16 | 8.2% / 48 | 9.3% / 46 | 7.7% / 48 | 8.2% / 48 | 16.2% / 40 | 4.0% / 60 | 19.4% / 29 | 45.9% / 16 |

