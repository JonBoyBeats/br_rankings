# Monday lock review: ownership (2026-11-23)

> **Headline lens from 2026-11-24 (the operator): the chalk band.** Players with max(ours, actual) at or over 15%,
> graded on MAE in points, the share off by 10+ points and the signed bias, by contest size and by slate
> (`dk_eval.py owngrade`, first in `dk_own_review.py`). The |log| error, overall MAE and the band ratios below are
> secondary. On the 9 graded slates (45 contests) the band is 26% of player-contests and 69% of all absolute error:
> MAE 11.3 points, 47% off by 10+, 14% off by 20+, bias +0.7. **The rule: an ownership-model change counts as an
> improvement only if it lowers the chalk band's MAE and its off-by-10+ share, held out by slate.** Held out that way,
> the candidates below move the chalk band little: mix+big 11.13 vs ours 11.42 MAE and 46.1% vs 47.9% off by 10+,
> better on both on 7 of 9 slates; flat+big 11.20 / 45.7%, 7 of 9.


Our projected ownership (the field doc's own, what the DK page shows) against real ownership on every graded contest,
and the watchlist. Analysis only: nothing here changes what the pipeline or the page reads until the operator approves.
Computed by `scripts/dk_own_review.py` and `dk_eval.py ownaudit` / `ownwatch`; every number below is from those runs.

**Sample:** 45 contests on 9 slates (11-16 to 11-22; 156662 and 157032 have no standings). By the operator's bands:
Large (300+) 31 contests on 9 slates; Medium (30-299) 12 contests on 7 slates; Small (under 30) 2 contests on 2 slates
(7 and 10 entries, both under-10). Small is too thin to fit; it is reported, not fit. Nine slates is a thin sample.

## Verdict

| Item | Call |
|---|---|
| Ownership shape (as is) | **LOCK** the current model for the week, with the gap below on record |
| Flattening exponent (own^a) | **No change**: held out it doesn't help (|log| 0.476 vs 0.476, MAE 4.53 vs 4.50) |
| Mix toward even, b = 0.04 | **CHANGE candidate (A2 pass)**, coordinated with the field study (see below) |
| "Coming off a big game" x1.22 | **CHANGE candidate (confirmed on the watchlist; A2 pass with the mix)** |
| Per-band settings | **One shared setting**: Large and Medium agree within noise; Small too thin |
| Display | Stays whole numbers |

## 1. The shape audit (baseline contest per night, `ownaudit`)

```
Ownership audit by shape (projected vs the baseline contest's real; a player nobody drafted counts 0%):
  2026-11-16 156660 CBB $6K Pull Up Jumper [$2K to 1st] (quiet): teams 12, rank 0.944, a team's sum off by 14.0 pts, our top 3 teams real/proj UCLA:0.60 STMRY:1.02 VT:1.09; within a team: our most-owned the real one 6/10, order (top 4) 0.52, #1-#2 gap ours 14.7 vs real 19.3; top-5 owned hit 4 of 5; bands real/proj under 5 1.42, 5-20 0.83, 20+ 1.02; duplication real 6.8% vs sim 0.5%
  2026-11-17 156663 CBB $1.5K And-One (quiet): teams 14, rank 0.495, a team's sum off by 23.2 pts, our top 3 teams real/proj IL:0.65 PITT:0.79 UNLV:0.46; within a team: our most-owned the real one 8/14, order (top 4) 0.643, #1-#2 gap ours 13.6 vs real 8.9; top-5 owned hit 1 of 5; bands real/proj under 5 2.07, 5-20 1.02, 20+ 0.77; duplication real 11.8% vs sim 4.6%
  2026-11-18 157033 CBB $7K Pull Up Jumper [$2K to 1st] (news): teams 8, rank 0.238, a team's sum off by 37.3 pts, our top 3 teams real/proj LY-IL:0.52 WICH:1.01 UCONN:1.09; within a team: our most-owned the real one 4/8, order (top 4) 0.6, #1-#2 gap ours 19.7 vs real 0.6; top-5 owned hit 2 of 5; bands real/proj under 5 1.51, 5-20 1.45, 20+ 0.84; duplication real 10.8% vs sim 7.6%
  2026-11-19 157138 CBB $750 And-One (Early) (quiet): teams 6, rank 0.486, a team's sum off by 44.2 pts, our top 3 teams real/proj MURR:0.96 ND:0.64 NCST:1.17; within a team: our most-owned the real one 5/6, order (top 4) 0.533, #1-#2 gap ours 11.0 vs real 17.7; top-5 owned hit 3 of 5; bands real/proj under 5 2.18, 5-20 1.15, 20+ 0.86; duplication real 18.4% vs sim 7.2%
  2026-11-19 157139 CBB $6K Pull Up Jumper [$2K to 1st] (news): teams 12, rank 0.755, a team's sum off by 21.1 pts, our top 3 teams real/proj TCU:0.75 STC:0.97 RU:1.44; within a team: our most-owned the real one 6/12, order (top 4) 0.682, #1-#2 gap ours 7.6 vs real 3.4; top-5 owned hit 3 of 5; bands real/proj under 5 1.6, 5-20 0.71, 20+ 1.04; duplication real 11.2% vs sim 2.5%
  2026-11-20 157013 CBB $750 And-One (Early) (quiet): teams 6, rank 0.943, a team's sum off by 11.3 pts, our top 3 teams real/proj NW:0.93 MINN:1.01 DAY:0.89; within a team: our most-owned the real one 5/6, order (top 4) 0.833, #1-#2 gap ours 17.6 vs real 17.1; top-5 owned hit 3 of 5; bands real/proj under 5 2.43, 5-20 1.04, 20+ 0.94; duplication real 27.1% vs sim 19.8%
  2026-11-20 157015 CBB $6K Pull Up Jumper [$2K to 1st] (quiet): teams 16, rank 0.806, a team's sum off by 12.6 pts, our top 3 teams real/proj STMRY:1.04 GT:1.16 TLSA:0.98; within a team: our most-owned the real one 14/16, order (top 4) 0.815, #1-#2 gap ours 14.4 vs real 18.9; top-5 owned hit 3 of 5; bands real/proj under 5 1.24, 5-20 1.0, 20+ 0.92; duplication real 12.2% vs sim 2.2%
  2026-11-21 157017 CBB $1.5K Pull Up Jumper (quiet): teams 8, rank 0.833, a team's sum off by 20.8 pts, our top 3 teams real/proj USF:1.18 GMU:1.20 WICH:1.11; within a team: our most-owned the real one 6/8, order (top 4) 0.779, #1-#2 gap ours 9.9 vs real 13.5; top-5 owned hit 5 of 5; bands real/proj under 5 1.38, 5-20 0.63, 20+ 1.05; duplication real 14.0% vs sim 4.8%
  2026-11-22 157019 CBB $1K Pull Up Jumper [$200 to 1st] (quiet): teams 10, rank 0.758, a team's sum off by 21.0 pts, our top 3 teams real/proj MCNE:0.85 BUTLE:1.04 NW:0.71; within a team: our most-owned the real one 7/10, order (top 4) 0.561, #1-#2 gap ours 8.7 vs real 15.6; top-5 owned hit 4 of 5; bands real/proj under 5 1.16, 5-20 0.83, 20+ 0.98; duplication real 3.5% vs sim 3.8%
All 9 slates: team rank 0.695, a team's sum off by 22.8 pts; most-owned on a team right 61 of 90; order 0.663; #1-#2 gap ours 13.0 vs real 12.8; top-5 hit 3.1 of 5; bands real/proj under 5 1.67, 5-20 0.96, 20+ 0.94
Duplication on news nights (10 contest-nights, 2 nights): real 11.0%, simulated 5.0% of entries holding a lineup another user entered
Duplication on quiet nights (35 contest-nights, 6 nights): real 12.9%, simulated 6.1% of entries holding a lineup another user entered
```

Pooled over all contests by band (real / projected in our under-5 / 5-20 / 20+ bands; |log error|; MAE in points):

```
== Real vs ours by band (all contests; real/projected in our <5 / 5-20 / 20+ bands; |log error|; MAE points) ==
  Large  n 2923 players  bands [1.92, 0.98, 0.91]  |log| 0.446  MAE 3.61
  Medium n  631 players  bands [2.22, 0.96, 0.95]  |log| 0.610  MAE 6.67
  Small  n   46 players  bands [7.14, 1.79, 1.11]  |log| 0.602  MAE 14.48
  (under 10 entries: 1 contests, n 19, bands [11.9, 1.73, 1.14], |log| 0.539)
```

Per slate (all its contests):

```
  2026-11-16 156660  4 contests (L)  bands [2.05, 0.9, 0.95]  |log| 0.443  MAE 3.01
  2026-11-17 156663  4 contests (L)  bands [2.12, 0.97, 0.81]  |log| 0.459  MAE 3.33
  2026-11-18 157033  5 contests (L/M)  bands [1.7, 1.39, 0.85]  |log| 0.479  MAE 5.25
  2026-11-19 157138  4 contests (L/M)  bands [2.32, 1.13, 0.86]  |log| 0.570  MAE 7.28
  2026-11-19 157139  5 contests (L/M)  bands [2.34, 0.76, 1.02]  |log| 0.541  MAE 4.48
  2026-11-20 157015  5 contests (L/M)  bands [1.41, 1.01, 0.89]  |log| 0.476  MAE 3.57
  2026-11-20 157013  5 contests (L/M)  bands [2.21, 0.96, 0.96]  |log| 0.380  MAE 3.70
  2026-11-21 157017  6 contests (L/M/S)  bands [2.47, 0.85, 1.0]  |log| 0.450  MAE 5.03
  2026-11-22 157019  7 contests (L/M/S)  bands [2.11, 1.06, 0.96]  |log| 0.486  MAE 4.86
```

Reading it: the 5-20% and 20%+ bands are close to right in every band (0.96-0.99 and 0.91-0.95 pooled). The miss is the
low end: players we project under 5% are owned about twice as much as we say (1.92x Large, 2.22x Medium). Ranks are
decent (team rank 0.695, most-owned on a team right 61 of 90, top-5 hit 3.1 of 5) and the #1-#2 gap is right on
average (ours 13.0 vs real 12.8), so the shape is mostly a floor problem, not a steepness problem.

## 2. Calibration candidates, held out by slate (fit on the other 8 slates, scored on the ninth)

```
== Candidates held out by slate (fit on the other slates, scored on the slate) ==
  big alone: f by slate 1.23, 1.22, 1.22, 1.18, 1.16, 1.23, 1.23, 1.22, 1.22; mix: b by slate 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04
  2026-11-16 156660  held out: |log| ours 0.443, mix 0.389, mix+big 0.389; MAE ours 3.01, mix 2.91, mix+big 2.91; bands mix [1.52, 0.91, 0.98]
  2026-11-17 156663  held out: |log| ours 0.459, mix 0.417, mix+big 0.417; MAE ours 3.33, mix 3.20, mix+big 3.20; bands mix [1.7, 0.99, 0.83]
  2026-11-18 157033  held out: |log| ours 0.479, mix 0.439, mix+big 0.435; MAE ours 5.25, mix 5.12, mix+big 4.98; bands mix [1.25, 1.38, 0.87]
  2026-11-19 157138  held out: |log| ours 0.570, mix 0.550, mix+big 0.542; MAE ours 7.28, mix 7.20, mix+big 7.17; bands mix [1.8, 1.11, 0.88]
  2026-11-19 157139  held out: |log| ours 0.541, mix 0.515, mix+big 0.507; MAE ours 4.48, mix 4.41, mix+big 4.28; bands mix [1.89, 0.76, 1.05]
  2026-11-20 157015  held out: |log| ours 0.476, mix 0.460, mix+big 0.451; MAE ours 3.57, mix 3.57, mix+big 3.41; bands mix [1.19, 1.03, 0.92]
  2026-11-20 157013  held out: |log| ours 0.380, mix 0.296, mix+big 0.299; MAE ours 3.70, mix 3.58, mix+big 3.59; bands mix [1.37, 0.94, 0.98]
  2026-11-21 157017  held out: |log| ours 0.450, mix 0.405, mix+big 0.399; MAE ours 5.03, mix 5.07, mix+big 5.16; bands mix [1.8, 0.84, 1.02]
  2026-11-22 157019  held out: |log| ours 0.486, mix 0.412, mix+big 0.411; MAE ours 4.86, mix 4.75, mix+big 4.66; bands mix [1.55, 1.06, 0.98]
  flat     held-out |log| 0.476 vs ours 0.476, better on 6 of 9 slates; MAE 4.53 vs 4.50 (better on 5); bands [1.87, 0.97, 0.95] vs ours [2.08, 1.0, 0.92]
  flat+big held-out |log| 0.473 vs ours 0.476, better on 8 of 9 slates; MAE 4.48 vs 4.50 (better on 7); bands [1.88, 0.97, 0.95] vs ours [2.08, 1.0, 0.92]
  big      held-out |log| 0.473 vs ours 0.476, better on 6 of 9 slates; MAE 4.46 vs 4.50 (better on 5); bands [2.09, 1.01, 0.92] vs ours [2.08, 1.0, 0.92]
  mix      held-out |log| 0.431 vs ours 0.476, better on 9 of 9 slates; MAE 4.42 vs 4.50 (better on 8); bands [1.56, 1.0, 0.95] vs ours [2.08, 1.0, 0.92]
  mix+big  held-out |log| 0.428 vs ours 0.476, better on 9 of 9 slates; MAE 4.37 vs 4.50 (better on 8); bands [1.57, 1.01, 0.94] vs ours [2.08, 1.0, 0.92]
  fitted on every slate: a 0.94, big-game f 1.22; pooled bands ours [2.01, 0.99, 0.93] -> flat [1.76, 0.95, 0.96] -> flat+big [1.77, 0.95, 0.95]
```

- **Flattening (own^a):** a 0.94 everywhere, but it doesn't help held out (better on 6 of 9 slates by |log|, worse on
  MAE). A power can't lift a player we project near 0, which is where the gap is.
- **Mix toward even (b = 0.04):** own' = 0.96 x ours + 0.04 x the contest's total spread evenly over its listed players.
  b came out 0.04 on every held-out fit. Better on **9 of 9** slates (|log| 0.476 -> 0.431) and MAE on 8 of 9
  (4.50 -> 4.42); the under-5 band 2.08x -> 1.56x; 5-20% unchanged (1.00); 20%+ 0.92 -> 0.95. No lens worse.
- **Big-game factor alone:** f 1.16-1.23 by slate; small but positive (|log| 0.473, MAE 4.46).
- **Mix + big:** the best: |log| 0.428, MAE 4.37, better on 9 of 9 / 8 of 9.

**A2:** the mix (with or without the big-game factor) passes: it helps held out by slate on every slate and no lens is
noticeably worse. It moves only 0.9 players a contest across the page's 10% / 20% lines, so the leverage reads
(lean core / leverage, the bank-gap flags) barely change; the ordering of players is untouched (the mix is monotone).

## 3. By contest-size band

```
== One exponent or per band? (a fitted per band on every slate; 200 bootstrap resamples of slates) ==
  Large  31 contests on 9 slates: a 0.94 (bootstrap 90%: 0.88-1.00); held-out |log| at it 0.444 vs ours 0.446
  Medium 12 contests on 7 slates: a 1.02 (bootstrap 90%: 0.92-1.12); held-out |log| at it 0.609 vs ours 0.610
  Small  2 contests on 2 slates: too thin to fit (fit with the neighbouring band)

== The mix by band (b fitted per band; 200 slate bootstraps) and what it moves ==
  Large  b 0.04 (bootstrap 90%: 0.02-0.04); |log| 0.446 -> 0.406, MAE 3.61 -> 3.53, bands [1.92, 0.98, 0.91] -> [1.47, 0.99, 0.93]
  Medium b 0.08 (bootstrap 90%: 0.04-0.10); |log| 0.610 -> 0.542, MAE 6.67 -> 6.67, bands [2.22, 0.96, 0.95] -> [1.39, 0.93, 1.0]
  Small  2 contests on 2 slates: too thin to fit; at the pooled b 0.04 |log| 0.602 -> 0.562, MAE 14.48 -> 14.43, bands [7.14, 1.79, 1.11] -> [5.37, 1.71, 1.12]
  mix b 0.04 on every slate moves 0.9 players a contest across 10% / 20%
== The mix by band (b fitted per band; 200 slate bootstraps) and what it moves ==
  Large  b 0.04 (bootstrap 90%: 0.02-0.04); |log| 0.446 -> 0.406, MAE 3.61 -> 3.53, bands [1.92, 0.98, 0.91] -> [1.47, 0.99, 0.93]
  Medium b 0.08 (bootstrap 90%: 0.04-0.10); |log| 0.610 -> 0.542, MAE 6.67 -> 6.67, bands [2.22, 0.96, 0.95] -> [1.39, 0.93, 1.0]
  Small  2 contests on 2 slates: too thin to fit; at the pooled b 0.04 |log| 0.602 -> 0.562, MAE 14.48 -> 14.43, bands [7.14, 1.79, 1.11] -> [5.37, 1.71, 1.12]
  mix b 0.04 on every slate moves 0.9 players a contest across 10% / 20%

== What it would move on the page (players crossing 10% or 20% a contest, mean): flat 1.7, flat+big 1.3, big alone (f 1.21) 1.2 ==
  big-game f in Large: 1.19; |log| ours 0.446 -> big 0.443
  big-game f in Medium: 1.31; |log| ours 0.610 -> big 0.601
```

- **One setting fits Large and Medium.** The exponent's bootstrap ranges overlap (0.88-1.00 vs 0.92-1.12). The mix's
  b is 0.04 in Large (0.02-0.04) and 0.08 in Medium (0.04-0.10): the ranges touch at 0.04, so a shared 0.04 holds for
  now. Medium is the one to watch (it may want a bit more), and it is also where our errors are larger (|log| 0.61 vs
  0.45).
- **Small (under 30)** is two contests, both under 10 entries: too thin to fit. In a 7- or 10-entry contest one entry
  is 10-14% ownership, so the under-5 ratio (7.1x) is mostly arithmetic. Fit with the shared setting; no separate one.

## 4. The watchlist (`dk_eval.py ownwatch`, own_watch.json)

| Pattern | Status | Player-nights | Nights | Real/proj vs the rest | Same direction |
|---|---|---|---|---|---|
| top-2 projected in the highest-total game | dead | 18 | 9 | x0.98 | 4 of 9 |
| blue bloods | dead | 182 | 6 | x1.03 | 3 of 6 |
| coming off a big game | confirmed | 49 | 7 | x1.25 | 6 of 7 |
| top-2 projected on the biggest favourite | emerging | 18 | 9 | x1.17 | 6 of 9 |
| the 5 highest salaries | watching | 45 | 9 | x0.88 | 6 of 9 |
| round-number salaries | dead | 391 | 9 | x0.95 | 6 of 9 |
| ranked teams (AP, else coaches) | dead | 239 | 8 | x1.06 | 6 of 8 |
| the national TV games | dead | 626 | 7 | x1.02 | 4 of 7 |
| salary down $300+ from his last slate | dead | 111 | 7 | x0.91 | 6 of 7 |

Rule: confirmed = 30+ player-nights on 5+ nights, the same direction on 75%+, 25%+ off 1; dead = 5+ nights and the
direction under 60% or within 10%.

- **Confirmed: "coming off a big game"** (last game's DK points 10+ over his season average): 49 player-nights on 7
  nights, x1.25, the same direction on 6 of 7. **Proposed for adoption** as part of the mix: x1.22 (the held-out fit;
  1.16-1.23 by slate; 1.19 in Large, 1.31 in Medium), renormalized. Its own A2 above: better on 6 of 9 alone, and it
  adds to the mix on 7 of 9 (|log| 0.431 -> 0.428, MAE 4.42 -> 4.37).
- **Emerging: top-2 projected on the biggest favourite** (x1.17, 6 of 9 nights, 18 player-nights): keep watching.
- **Watching: the 5 highest salaries** (x0.88, 6 of 9, 45 player-nights): keep watching.
- **Dead:** top-2 in the highest-total game, blue bloods, round-number salaries, ranked teams, the national TV games,
  salary down $300+.

## 5. Proposal and coordination with the field study

Our projected ownership is the simulated field's own output (dk_cbb_field.py), which the field study
(field_study_2026-11-23.md) is recalibrating. So:

1. If the field study's calibrated field brings the under-5 band to within ~1.2x on its own, the mix isn't needed.
2. Otherwise, apply **mix b = 0.04 + big game x1.22** as a post-step on the field's ownership (one shared setting, all
   bands), shown in whole numbers as now. Re-fit b and f at each Friday review; watch Medium's b.
3. Friday review: re-run `scripts/dk_own_review.py`; keep it if the held-out |log| is still better on at least 2/3 of
   the week's slates.
