# Pod replay: my NBA rankings graded by team outcomes

Results only. Generated 2026-11-17 16:11 from 25 nights (2026-10-21 to 2026-11-16).

## Plain English

- **My locked list, replayed through every real seat** (25 nights, 420872 seats): top 1% 1.33%, top 10% 12.8%, mean finish percentile 45.3 (an average team: 1%, 10%, 50).
- **Against the button's list** (7 nights): my list +0.53 pts top-10% (80% range -2.78 to +3.69), -0.76 pts top-1%, mean finish -3.6.
- **Against ADP** (25 nights): my list +1.81 pts top-10% (80% range +0.64 to +2.90), +0.27 pts top-1%, mean finish -3.3.
- **Against ETR's order (PM)** (25 nights, PM): my list -2.77 pts top-10% (80% range -5.70 to +0.05), -0.73 pts top-1%, mean finish +0.6.
- **My manual moves, tier by tier** (top-10% points my moves added, 80% range): T1 +0.24 (-0.05 to +0.53); T2 +2.20 (+0.68 to +3.96); T3 -1.41 (-3.72 to +0.98); T4 +0.16 (-0.67 to +1.12); T5 +0.06 (-0.90 to +0.90).
- **Round 6 fidelity:** 30% of my real round-6 picks were (a)'s #1 still available, 80% were in its top 6 (an even draw: 17% and 100%).
- **My real teams** (1926): top 10% 13.0% against 14.7% for (a) replayed at the same seats; they beat 49% of (a)'s replayed teams on average (50% = in line with the list).

## How it was run

- Every real pod in every main-slate contest, every seat, each window's pods (the lock nearest the draft time, as the money engine sorts them). That seat's drafter becomes me, drafting off a list: the highest available at each of my picks.
- The other drafters keep their real picks; when I've taken one of theirs, they take the next available by the window's ADP (their later picks stay as they were unless taken too).
- **Pick order is estimated.** Underdog doesn't publish draft slots. Each team's picks, sorted by the ADP each was taken at, are its rounds 1-6; the pod's seats are the snake slots that fit those ADPs best (the swap crediting's fit).
- Rounds 1-5 follow the list strictly. Round 6: drawn evenly from the top 6 still available on the list, one seeded draw per pod and seat, the same for every list.
- Scored on the night's box scores as Underdog scored them: a player's box score is corrected where the leaderboards' team totals disagree (stat corrections, 1-4.5 points, one or two players most nights; every night's teams then reconcile to within 3). A scratched player (0 minutes for a team that played, swapped at least as often as he was left on a real roster: a DNP kept on rosters scores 0) is swapped to the highest player on the same list left undrafted in the replayed pod whose game hadn't started at the swap (the earliest real swap target's tip, else his own team's tip).
- Placed in the contest's real standings: my seat's real score is replaced, everyone else's stays as it was (the pod-mates who lost a player to me aren't re-scored). Ties ignored. Top X%: place <= ceil(X% of entries). Cash: any payout. ROI: payout over fees.
- (c) undoes one tier's manual moves: that tier's players (by the button's tier) go back to their button positions and everyone else keeps my order around them. A list identical to (a) reuses (a)'s results.
- (b) and (c) need the button's list at the lock: on file from 2026-11-09 (PM) and 2026-11-10 (AM). (e) is ETR's PM projections, highest first (ETR's own rank isn't kept). 11/15 had no locks on file and is out.

## Season: Both windows

| List | Nights | Seats | Top 1% | Top 10% | Mean finish pct | Cash | ROI |
|---|---|---|---|---|---|---|---|
| (a) my locked list | 25 | 420872 | 1.33% | 12.8% | 45.3 | 23% | +39% |
| (b) the button's list | 7 | 127584 | 1.87% | 12.4% | 47.5 | 22% | +37% |
| (c1) mine, T1's moves undone | 7 | 127584 | 1.10% | 12.7% | 43.2 | 24% | +3% |
| (c2) mine, T2's moves undone | 7 | 127584 | 0.87% | 10.7% | 46.9 | 21% | -16% |
| (c3) mine, T3's moves undone | 7 | 127584 | 2.10% | 14.4% | 43.2 | 26% | +69% |
| (c4) mine, T4's moves undone | 7 | 127584 | 1.19% | 12.8% | 45.4 | 24% | +13% |
| (c5) mine, T5's moves undone | 7 | 127584 | 1.17% | 12.9% | 44.5 | 24% | +5% |
| (d) ADP | 25 | 420872 | 1.05% | 11.0% | 48.6 | 20% | -3% |
| (e) ETR (PM) | 25 | 296794 | 2.02% | 15.4% | 44.8 | 26% | +77% |

Paired: (a) minus each list, same pods and seats, nights resampled for the 80% ranges.

| (a) minus | Nights | Top 1% (pts) | 80% range | Top 10% (pts) | 80% range | Mean finish pct (lower is better) | 80% range |
|---|---|---|---|---|---|---|---|
| (b) the button's list | 7 | -0.76 | -1.84 to +0.32 | +0.53 | -2.78 to +3.69 | -3.65 | -8.48 to +1.00 |
| (c1) mine, T1's moves undone | 7 | +0.01 | +0.00 to +0.03 | +0.24 | -0.05 to +0.53 | +0.60 | -0.29 to +1.57 |
| (c2) mine, T2's moves undone | 7 | +0.24 | +0.10 to +0.39 | +2.20 | +0.68 to +3.96 | -3.02 | -5.06 to -1.18 |
| (c3) mine, T3's moves undone | 7 | -0.99 | -2.16 to +0.16 | -1.41 | -3.72 to +0.98 | +0.63 | -0.91 to +2.10 |
| (c4) mine, T4's moves undone | 7 | -0.08 | -0.20 to +0.02 | +0.16 | -0.67 to +1.12 | -1.50 | -3.21 to +0.10 |
| (c5) mine, T5's moves undone | 7 | -0.06 | -0.22 to +0.08 | +0.06 | -0.90 to +0.90 | -0.62 | -1.61 to +0.42 |
| (d) ADP | 25 | +0.27 | -0.02 to +0.56 | +1.81 | +0.64 to +2.90 | -3.30 | -5.25 to -1.23 |
| (e) ETR (PM) | 25 | -0.73 | -1.36 to -0.09 | -2.77 | -5.70 to +0.05 | +0.57 | -3.17 to +4.25 |

## Season: AM

| List | Nights | Seats | Top 1% | Top 10% | Mean finish pct | Cash | ROI |
|---|---|---|---|---|---|---|---|
| (a) my locked list | 20 | 124078 | 1.42% | 13.2% | 45.3 | 23% | +21% |
| (b) the button's list | 5 | 36606 | 1.24% | 11.9% | 47.6 | 22% | -1% |
| (c1) mine, T1's moves undone | 5 | 36606 | 1.89% | 15.2% | 40.7 | 28% | +60% |
| (c2) mine, T2's moves undone | 5 | 36606 | 1.34% | 12.7% | 45.4 | 23% | +16% |
| (c3) mine, T3's moves undone | 5 | 36606 | 1.72% | 15.8% | 41.3 | 28% | +51% |
| (c4) mine, T4's moves undone | 5 | 36606 | 2.10% | 16.5% | 40.4 | 29% | +99% |
| (c5) mine, T5's moves undone | 5 | 36606 | 1.95% | 16.0% | 41.1 | 28% | +67% |
| (d) ADP | 20 | 124078 | 1.18% | 11.1% | 48.8 | 20% | +5% |

Paired: (a) minus each list, same pods and seats, nights resampled for the 80% ranges.

| (a) minus | Nights | Top 1% (pts) | 80% range | Top 10% (pts) | 80% range | Mean finish pct (lower is better) | 80% range |
|---|---|---|---|---|---|---|---|
| (b) the button's list | 5 | +0.69 | +0.36 to +1.05 | +4.22 | +3.29 to +5.11 | -7.41 | -10.06 to -3.90 |
| (c1) mine, T1's moves undone | 5 | +0.04 | +0.00 to +0.08 | +0.93 | +0.00 to +1.70 | -0.56 | -1.02 to +0.01 |
| (c2) mine, T2's moves undone | 5 | +0.59 | +0.14 to +1.13 | +3.43 | +1.41 to +5.90 | -5.28 | -8.00 to -1.87 |
| (c3) mine, T3's moves undone | 5 | +0.22 | -0.03 to +0.49 | +0.30 | -0.38 to +0.95 | -1.16 | -1.75 to -0.52 |
| (c4) mine, T4's moves undone | 5 | -0.17 | -0.47 to +0.09 | -0.40 | -2.12 to +0.85 | -0.31 | -1.84 to +1.71 |
| (c5) mine, T5's moves undone | 5 | -0.02 | -0.35 to +0.33 | +0.10 | -1.06 to +1.20 | -0.92 | -1.90 to +0.12 |
| (d) ADP | 20 | +0.24 | -0.10 to +0.57 | +2.07 | +0.14 to +3.85 | -3.48 | -6.05 to -0.77 |

## Season: PM

| List | Nights | Seats | Top 1% | Top 10% | Mean finish pct | Cash | ROI |
|---|---|---|---|---|---|---|---|
| (a) my locked list | 25 | 296794 | 1.29% | 12.7% | 45.3 | 23% | +47% |
| (b) the button's list | 7 | 90978 | 2.13% | 12.6% | 47.5 | 23% | +52% |
| (c1) mine, T1's moves undone | 7 | 90978 | 0.78% | 11.7% | 44.3 | 23% | -19% |
| (c2) mine, T2's moves undone | 7 | 90978 | 0.68% | 10.0% | 47.5 | 20% | -29% |
| (c3) mine, T3's moves undone | 7 | 90978 | 2.25% | 13.8% | 44.0 | 25% | +76% |
| (c4) mine, T4's moves undone | 7 | 90978 | 0.82% | 11.3% | 47.3 | 22% | -20% |
| (c5) mine, T5's moves undone | 7 | 90978 | 0.85% | 11.6% | 45.8 | 23% | -19% |
| (d) ADP | 25 | 296794 | 1.00% | 11.0% | 48.6 | 20% | -6% |
| (e) ETR (PM) | 25 | 296794 | 2.02% | 15.4% | 44.8 | 26% | +77% |

Paired: (a) minus each list, same pods and seats, nights resampled for the 80% ranges.

| (a) minus | Nights | Top 1% (pts) | 80% range | Top 10% (pts) | 80% range | Mean finish pct (lower is better) | 80% range |
|---|---|---|---|---|---|---|---|
| (b) the button's list | 7 | -1.35 | -2.92 to +0.17 | -0.96 | -5.47 to +3.40 | -2.14 | -8.35 to +3.56 |
| (c1) mine, T1's moves undone | 7 | +0.00 | +0.00 to +0.00 | -0.04 | -0.08 to +0.00 | +1.07 | +0.00 to +2.32 |
| (c2) mine, T2's moves undone | 7 | +0.10 | -0.05 to +0.25 | +1.70 | -0.54 to +4.08 | -2.12 | -4.66 to +0.10 |
| (c3) mine, T3's moves undone | 7 | -1.47 | -3.09 to +0.10 | -2.10 | -5.51 to +1.18 | +1.35 | -0.68 to +3.39 |
| (c4) mine, T4's moves undone | 7 | -0.05 | -0.14 to +0.03 | +0.38 | -0.66 to +1.37 | -1.98 | -3.91 to -0.26 |
| (c5) mine, T5's moves undone | 7 | -0.07 | -0.21 to +0.04 | +0.04 | -1.03 to +1.04 | -0.49 | -1.74 to +0.70 |
| (d) ADP | 25 | +0.29 | -0.12 to +0.69 | +1.69 | +0.04 to +3.20 | -3.23 | -5.38 to -0.78 |
| (e) ETR (PM) | 25 | -0.73 | -1.36 to -0.09 | -2.77 | -5.70 to +0.05 | +0.57 | -3.17 to +4.25 |

## Round 6 fidelity

My real round-6 pick (each of my real teams' sixth by ADP-at-draft), placed among (a)'s top still available at that seat's round-6 pick in the replay. An even draw over the top 6 would put about 17% at each of places 1-6.

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
| BOTH | 1926 | 0.88% | 1.35% | 13.0% | 14.7% | 44.9 | 43.4 | 49% |
| AM | 563 | 0.71% | 0.53% | 14.0% | 14.6% | 46.2 | 44.9 | 49% |
| PM | 1363 | 0.95% | 1.69% | 12.5% | 14.8% | 44.4 | 42.7 | 49% |

## By night

Top 10% / mean finish percentile for each list; seats are every seat in that window's pods.

| Night | Window | Seats | (a) | (b) | (c1) | (c2) | (c3) | (c4) | (c5) | (d) | (e) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-21 | PM | 16254 | 16.3% / 39 | - | - | - | - | - | - | 7.5% / 51 | 22.4% / 32 |
| 2026-10-22 | PM | 15740 | 13.7% / 45 | - | - | - | - | - | - | 11.6% / 52 | 13.5% / 49 |
| 2026-10-23 | PM | 15732 | 15.3% / 39 | - | - | - | - | - | - | 9.2% / 46 | 2.5% / 60 |
| 2026-10-24 | AM | 6714 | 3.0% / 51 | - | - | - | - | - | - | 12.0% / 42 | - |
| 2026-10-24 | PM | 7860 | 26.2% / 43 | - | - | - | - | - | - | 11.2% / 44 | 24.8% / 50 |
| 2026-10-25 | AM | 3366 | 8.6% / 40 | - | - | - | - | - | - | 4.2% / 52 | - |
| 2026-10-25 | PM | 7782 | 3.0% / 49 | - | - | - | - | - | - | 4.4% / 55 | 4.4% / 47 |
| 2026-10-26 | PM | 13530 | 26.0% / 31 | - | - | - | - | - | - | 13.6% / 42 | 19.1% / 33 |
| 2026-10-27 | AM | 5046 | 10.1% / 57 | - | - | - | - | - | - | 11.0% / 44 | - |
| 2026-10-27 | PM | 10704 | 9.9% / 47 | - | - | - | - | - | - | 13.5% / 46 | 11.2% / 49 |
| 2026-10-28 | AM | 4032 | 14.3% / 43 | - | - | - | - | - | - | 14.4% / 45 | - |
| 2026-10-28 | PM | 11718 | 2.8% / 60 | - | - | - | - | - | - | 15.0% / 44 | 1.9% / 72 |
| 2026-10-29 | AM | 4708 | 11.9% / 41 | - | - | - | - | - | - | 6.8% / 62 | - |
| 2026-10-29 | PM | 8848 | 11.7% / 44 | - | - | - | - | - | - | 4.1% / 60 | 24.8% / 31 |
| 2026-10-30 | AM | 7104 | 9.6% / 44 | - | - | - | - | - | - | 8.7% / 55 | - |
| 2026-10-30 | PM | 13764 | 17.2% / 33 | - | - | - | - | - | - | 9.1% / 52 | 17.4% / 29 |
| 2026-10-31 | AM | 5322 | 18.6% / 44 | - | - | - | - | - | - | 12.6% / 49 | - |
| 2026-10-31 | PM | 8682 | 6.2% / 60 | - | - | - | - | - | - | 13.9% / 49 | 3.9% / 69 |
| 2026-11-01 | AM | 6100 | 11.1% / 51 | - | - | - | - | - | - | 15.3% / 50 | - |
| 2026-11-01 | PM | 4180 | 16.2% / 48 | - | - | - | - | - | - | 16.5% / 49 | 14.6% / 43 |
| 2026-11-02 | AM | 5778 | 10.7% / 53 | - | - | - | - | - | - | 9.0% / 56 | - |
| 2026-11-02 | PM | 12894 | 12.9% / 45 | - | - | - | - | - | - | 16.5% / 45 | 3.9% / 62 |
| 2026-11-04 | AM | 9480 | 21.1% / 43 | - | - | - | - | - | - | 12.0% / 43 | - |
| 2026-11-04 | PM | 11868 | 11.2% / 55 | - | - | - | - | - | - | 10.4% / 46 | 12.2% / 51 |
| 2026-11-05 | AM | 6776 | 10.1% / 47 | - | - | - | - | - | - | 10.7% / 46 | - |
| 2026-11-05 | PM | 13716 | 10.0% / 47 | - | - | - | - | - | - | 8.5% / 46 | 22.1% / 41 |
| 2026-11-06 | AM | 6090 | 11.6% / 51 | - | - | - | - | - | - | 7.7% / 53 | - |
| 2026-11-06 | PM | 14706 | 8.1% / 55 | - | - | - | - | - | - | 6.6% / 58 | 31.2% / 30 |
| 2026-11-07 | AM | 7806 | 12.8% / 46 | - | - | - | - | - | - | 13.5% / 40 | - |
| 2026-11-07 | PM | 10764 | 10.9% / 48 | - | - | - | - | - | - | 16.2% / 42 | 25.9% / 34 |
| 2026-11-08 | AM | 3210 | 12.0% / 48 | - | - | - | - | - | - | 16.9% / 49 | - |
| 2026-11-08 | PM | 7074 | 16.2% / 35 | - | - | - | - | - | - | 15.7% / 49 | 4.8% / 54 |
| 2026-11-09 | AM | 5940 | 9.4% / 53 | - | - | - | - | - | - | 15.2% / 46 | - |
| 2026-11-09 | PM | 12720 | 16.7% / 37 | 2.3% / 62 | 16.7% / 37 | 3.0% / 51 | 12.3% / 40 | 13.2% / 45 | 15.1% / 40 | 17.7% / 42 | 3.1% / 57 |
| 2026-11-10 | AM | 7344 | 17.6% / 38 | 12.1% / 44 | 17.6% / 38 | 17.6% / 38 | 14.9% / 41 | 17.6% / 38 | 15.0% / 41 | 7.7% / 54 | - |
| 2026-11-10 | PM | 13488 | 12.4% / 50 | 13.7% / 48 | 12.4% / 50 | 12.4% / 50 | 12.4% / 50 | 12.4% / 50 | 13.7% / 48 | 11.9% / 45 | 13.3% / 45 |
| 2026-11-11 | AM | 11076 | 9.6% / 48 | 5.7% / 60 | 6.5% / 50 | 8.9% / 54 | 9.5% / 50 | 7.7% / 52 | 9.1% / 50 | 11.7% / 48 | - |
| 2026-11-11 | PM | 9774 | 9.4% / 49 | 2.7% / 69 | 9.4% / 49 | 8.7% / 51 | 9.1% / 50 | 6.6% / 60 | 6.1% / 57 | 12.9% / 44 | 1.9% / 75 |
| 2026-11-12 | AM | 6336 | 24.8% / 29 | 18.9% / 37 | 24.8% / 29 | 13.8% / 42 | 25.6% / 31 | 24.5% / 29 | 28.4% / 26 | 9.4% / 51 | - |
| 2026-11-12 | PM | 11508 | 5.2% / 56 | 14.3% / 41 | 5.5% / 47 | 8.0% / 53 | 5.3% / 56 | 9.4% / 53 | 10.1% / 53 | 10.7% / 48 | 20.8% / 33 |
| 2026-11-13 | AM | 5694 | 12.9% / 42 | 12.7% / 38 | 12.9% / 42 | 12.2% / 38 | 13.5% / 42 | 13.7% / 41 | 13.8% / 42 | 11.3% / 47 | - |
| 2026-11-13 | PM | 14658 | 16.3% / 34 | 32.6% / 24 | 16.3% / 34 | 16.3% / 34 | 34.0% / 23 | 15.6% / 35 | 14.9% / 34 | 10.3% / 52 | 24.6% / 26 |
| 2026-11-14 | PM | 16410 | 9.4% / 48 | 9.4% / 48 | 9.4% / 48 | 9.4% / 48 | 9.4% / 48 | 9.4% / 48 | 9.4% / 48 | 8.2% / 52 | 10.3% / 49 |
| 2026-11-16 | AM | 6156 | 20.1% / 37 | 14.7% / 48 | 20.1% / 37 | 12.7% / 49 | 20.1% / 37 | 25.4% / 33 | 18.7% / 39 | 11.3% / 52 | - |
| 2026-11-16 | PM | 12420 | 11.0% / 45 | 9.0% / 48 | 11.0% / 45 | 10.5% / 48 | 10.2% / 46 | 11.0% / 45 | 10.7% / 45 | 5.7% / 56 | 40.5% / 19 |

