# Lock review 2026-11-23: the sim (everything but the field calibration)

The sim section of the Monday lock review (the coordinator's 11-23 request). Analysis only: nothing here changes the page
or the pipeline. The field calibration is its own study (analysis/cbb/dk/field_study_2026-11-23.md).

**Sample.** Builds with standings: 7 nights (11-16, 11-17, 11-18, 11-19 early, 11-19 main, 11-20 early, 11-20 main); the
11-21 and 11-22 builds weren't uploaded, so those nights enter only the build-free tests (bank noise: 9 nights). Seven
nights is thin: a sign test can't reach p < 0.05 unless every night agrees, so read the per-night rows and their
direction. Every number below is computed by the scripts named.

## Summary

| Item | Verdict | Evidence (short) |
|---|---|---|
| Bank noise 0.35 | **LOCK** | Best of 1 / 0.5 / 0.35 pooled on 9 nights: top 10% 4.9 / 8.0 / **9.2**%, cash 10.7 / 16.5 / **18.5**%; 0.35 beats 1 on cash 9 of 9, beats 0.5 on cash 6 of 9 |
| Bank size (~12,500) | **LOCK** | Half the bank cut worse on real fills both new nights (11-20 early -$12.53 vs +$5.77; main $65.08 vs $74.98), lower best value both; 11-19 main slices (11-20 test) the same way |
| Cut: merit, floor 5 | **LOCK** | Merit vs equal share on the two new nights: real random fills +$5.77 vs -$8.77 (early), +$74.98 vs +$34.29 (main); same tier A; merit leaves more short in the sim fill on 11-20 early (11 vs 2) |
| Cut: keep 2,000 / 10% a round / 2,000 nights | **LOCK (not re-tested)** | Kept beat cut every night on mean points (7 of 7) and on top 10% 5 of 7; no alternative setting run this week |
| Tiers | **WATCH + de-emphasize** | A > B > C on 3 of 7 nights; A-B +4.7 points (4 of 7), B-C +8.2 (4 of 7), sign-test p 1.00 both; pooled A 54.6 / B 49.9 / C 41.7 percentile, driven by 11-20 early |
| Variants (of the top) | **LOCK** | Kept variants vs all kept: cash higher 4 of 4 nights, mean points 3 of 4, top 10% 3 of 4; as a fill group $13.07 vs $12.35 (11-19 main), $337 vs $170 (11-20 main) |
| Fill caps | **LOCK, WATCH** | The Max ROI fill with today's caps (Auto-fill benchmark) tracks the entries (5 nights) and beats a random kept fill on 2, loses on 2, even on 1: no cap shows binding to bad effect |
| Draw the 9 cells | **WATCH** (one night) | 11-20 main only: leverage 0 > 0.1 > 0.2 on banked top 10% (11.4-12.4 / 7.5-8.8 / 4.2-5.0%) and cash; under 0/1/2 makes little difference |
| Template-5 spread | **no data** | No build saved since the spread shipped (11-21) is on file |
| B.3 shared-lineup credit | **REJECT for now** | Pooled percentile 48.5 -> 48.3; on the one night with real sharing (11-20 early, 1,849 shared) worse: 56.2 -> 55.4, top 10% 14.8 -> 14.1, cash 27.1 -> 26.1 |

## Bank noise (scripts/dk_bank_noise_study.py / .js, extended to 11-20 early / main, 11-21, 11-22)

Rule-free banks of 2,000 at each noise on each night's lock-time slate (the deep bench and punts left out, as the page),
scored on real points against the night's largest contest: top 10% and cash lines, the real field's percentile.

| Night | Field top10 / cash | s=1 | s=0.5 | s=0.35 |
|---|---|---|---|---|
| 11-16 | 11.5 / 22.9 | 0.5 / 1.3 | 1.5 / 3.5 | 1.4 / 4.0 |
| 11-17 | 11.4 / 25.6 | 7.6 / 17.1 | 13.5 / 27.9 | **16.4 / 32.2** |
| 11-18 | 10.2 / 19.3 | 0.8 / 2.0 | **1.6 / 3.0** | 1.2 / 2.8 |
| 11-19 early | 12.3 / 23.3 | 1.9 / 8.5 | 3.2 / 11.6 | 2.9 / 11.8 |
| 11-19 main | 10.3 / 22.8 | 1.9 / 4.8 | **2.2 / 5.5** | 1.7 / 5.1 |
| 11-20 early | 10.3 / 23.2 | 6.0 / 14.0 | 12.3 / 25.1 | **16.2 / 30.2** |
| 11-20 main | 10.0 / 23.6 | 4.6 / 11.0 | 11.1 / 22.6 | **15.7 / 30.4** |
| 11-21 | 10.2 / 23.9 | 15.6 / 28.4 | **18.5 / 33.6** | 16.7 / 30.5 |
| 11-22 | 10.2 / 23.3 | 5.0 / 9.6 | 8.3 / 15.7 | **10.8 / 19.1** |
| Pooled (nights equal) | | 4.9 / 10.7 | 8.0 / 16.5 | **9.2 / 18.5** |

0.35 beats 1 on cash on all 9 nights, and 0.5 on cash on 6 of 9 (top 10% 4 of 9). Lock 0.35. Watch: a lower setting
(0.25) is untested.

## Bank size and the cut (scripts/dk_cut_study.js on the 11-20 builds)

| Night | Run | Bank | Rounds | Tier A (ideas) | Best value | Sim Max ROI fill net (short) | Real random fills mean (positive %) |
|---|---|---|---|---|---|---|---|
| 11-20 early | equal | 12,500 | 18 | 20 (6) | 1.458 | $5.91 (2) | -$8.77 (21%) |
| 11-20 early | **merit** | 12,500 | 15 | 20 (6) | 1.458 | $7.75 (11) | **+$5.77 (27%)** |
| 11-20 early | merit, half bank | 6,253 | 10 | 12 (4) | 1.434 | $10.23 (4) | -$12.53 (18.5%) |
| 11-20 main | equal | 12,452 | 18 | 20 (5) | 2.392 | $25.66 (0) | $34.29 (52.5%) |
| 11-20 main | **merit** | 12,452 | 18 | 20 (5) | 2.392 | $25.13 (0) | **$74.98 (53%)** |
| 11-20 main | merit, half bank | 6,229 | 11 | 33 (6) | 2.155 | $26.40 (0) | $65.08 (52%) |

Merit beats equal share on real fills on both new nights (it did on the 11-17 to 11-19 nights in the C2 test too); the
full bank beats half of it on real fills and best value on both. The cut's own check (dk_eval cutcheck, every night):
kept beat cut on mean points 7 of 7 and on top 10% 5 of 7 (11-20 early 10.6% vs 5.5%, main 16.9% vs 6.7%).

Watch: merit's extra "short" entries in the sim fill on 11-20 early (11 vs 2): the kept pool can run thin for some
contest's caps; the stranded-seat offer covers it on the page.

## Tiers (scripts/dk_tier_signal_study.py / .js, rebuilt, 7 nights)

| Tier | Pooled percentile | Top 10% | Top 1% | Cash |
|---|---|---|---|---|
| A | 54.6 | 18.8 | 5.9 | 33.7 |
| B | 49.9 | 9.8 | 2.3 | 20.4 |
| C | 41.7 | 6.5 | 1.0 | 14.6 |

A > B > C on 3 of 7 nights; A-B +4.7 points (4 of 7 positive), B-C +8.2 (4 of 7), sign-test p 1.00 both. Tier A is 3-16
lineups a night; 11-20 early's 6 (92.5 percentile) carries the pooled A. The continuous value (every kept lineup) is the
steadier signal: rank correlation with the real percentile positive on 6 of 7 nights (mean +0.14, sign-test p 0.12), the
top tenth by value ahead of the other 90% by 6.8 percentile points on average (ahead on 6 of 7). Within tier A, played vs not played: no signal (played behind by 3.7 points, ahead on 1 of 4).

**De-emphasis proposal (display only; the operator decides):**
1. **Variants of the top N by value**, not of tier A: the button reads "Variants of the top 15", Top kept defaults to 15
   (today: the tier-A size, clamped to 10-25), so the variants don't move with a noisy tier boundary.
2. **Cut table:** replace the Tier A column with **Top 10%**: the share of each idea's kept lineups in the kept pool's
   top tenth by value; the red "Tier A tonight: n lineups, one idea" flag becomes a plain note "one idea holds over half
   of the top tenth" (same warning, a steadier set).
3. **Builder and one-screen list:** sort by value by default (tier sort stays as an option); show the tier letter in
   muted text with its hover "within the sim's noise of the best: treat as level"; group the one-screen list by value
   (top 10%, next 40%, rest) instead of A / B / C.
4. **Under-exposed line:** compare exposures against the top tenth by value instead of tier A.
5. **Quick sim:** keep its tiers: there they only say which proposals are level, which is what they're good for.

## Variants (dk_eval cutcheck, the kept "variant of #k" lineups)

| Night | Variants kept | Variants: mean / top 10% / cash | All kept: mean / top 10% / cash |
|---|---|---|---|
| 11-19 early | 21 | 188.3 / 14.3 / 35.7 | 174.4 / 3.2 / 16.9 |
| 11-19 main | 97 | 190.5 / 3.3 / 10.1 | 189.5 / 3.5 / 8.7 |
| 11-20 early | 4 | 182.4 / 25.0 / 25.0 | 186.8 / 10.6 / 20.2 |
| 11-20 main | 278 | 219.4 / 24.8 / 43.5 | 213.5 / 16.9 / 34.9 |

Variants ahead on cash 4 of 4, mean points 3 of 4, top 10% 3 of 4. Lock (with the "top N by value" base above).

## Fills and caps (dk_eval fills / eval.csv: entries, the Auto-fill benchmark, random fills)

| Night | Fees | Entries $ back | Auto-fill (caps) $ back / fees | Random kept fill avg | Random bank fill avg |
|---|---|---|---|---|---|
| 11-16 | 27.0 | 0.2 | – | 2.99 | 3.57 |
| 11-17 | 18.7 | 8.0 | – | 12.35 | 8.43 |
| 11-18 | 35.0 | 131.4 | 128 / 34 | 12.82 | 4.60 |
| 11-19 early | 31.0 | 27.5 | 9 / 24 | 7.32 | 7.22 |
| 11-19 main | 77.0 | 4.4 | 4 / 41 | 12.35 | 18.54 |
| 11-20 early | 58.2 | 46.25 | 44 / 58 | 47.15 | 32.71 |
| 11-20 main | 77.0 | 139.75 | 131 / 72 | 169.63 | 85.77 |

The capped Max ROI fill lands near the entries every night (it is what Fill all contests builds); against a random fill
of the same kept pool it is ahead on 2 nights (11-18, 11-19 early), behind on 2 (11-19 main, 11-20 main), even on 1.
Nothing shows a cap binding to bad effect. Lock: Max ROI, 60% exposure / 60% night, min unique 3, core 15%, a lineup in
at most 3 contests. Watch: a cap-by-cap test needs the nights with a saved Auto-fill and more of them.

## Draw the 9 (idea_eval.csv; one night: 11-20 main, 28 ideas x 9 cells, 5 contests)

| Cell | Banked | Kept | Banked top 10% | Banked cash |
|---|---|---|---|---|
| L0 U0 | 7,000 | 2,755 | 11.4 | 25.5 |
| L0 U1 | 7,000 | 2,970 | 12.3 | 27.4 |
| L0 U2 | 7,000 | 2,295 | 12.4 | 25.0 |
| L0.1 U0 | 7,000 | 920 | 8.8 | 19.9 |
| L0.1 U1 | 7,000 | 850 | 8.4 | 20.3 |
| L0.1 U2 | 7,000 | 725 | 7.5 | 18.3 |
| L0.2 U0 | 7,000 | 170 | 5.0 | 13.2 |
| L0.2 U1 | 7,000 | 115 | 4.8 | 13.4 |
| L0.2 U2 | 7,000 | 100 | 4.2 | 10.5 |

One night: leverage 0.2 was the worst row on both rates and the cut kept little of it; the under setting barely moved
anything. Watch (one night): if the next nights agree, the sweep default could drop 0.2 (e.g. 0, 0.05, 0.1).

## Template-5 spread

No build saved since the spread shipped (11-21) is on file (the 11-21 and 11-22 builds weren't uploaded), so spread on
against off can't be graded yet. Builds record each tag's spread map, so it will be gradeable from the first one.

## B.3, the shared-lineup cut credit (scripts/dk_shared_credit_study.js / .py)

Today the cut credits a lineup to the idea that drew it first (dk.html lineupGroup); a lineup two or more ideas drew
counts for only that one in the merit cut's floor and the near-copy skip. The proposal: credit a shared lineup to the
idea where its first-round value ranks best. Both cuts on the same nights (each build's seed, Keep, Cut % and nights),
kept pools scored on real results in every entered contest, entries-weighted.

| Night | Bank | Shared | Moved | Overlap | Percentile A -> B | Top 10% A -> B | Cash A -> B | Only-A vs only-B (n, pctl) |
|---|---|---|---|---|---|---|---|---|
| 11-19 early | 8,555 | 63 | 42 | 1,492 of 1,500 | 47.1 -> 47.2 | 3.3 -> 3.3 | 18.0 -> 18.0 | 8 (33.3) vs 8 (49.7) |
| 11-19 main | 13,132 | 160 | 91 | 1,918 of 2,000 | 33.1 -> 33.2 | 5.4 -> 5.5 | 13.2 -> 13.3 | 82 (38.7) vs 82 (39.6) |
| 11-20 early | 12,500 | 1,849 | 772 | 1,732 of 2,000 | 56.2 -> 55.4 | 14.8 -> 14.1 | 27.1 -> 26.1 | 268 (59.5) vs 268 (53.6) |
| 11-20 main | 12,452 | 33 | 25 | 1,986 of 2,000 | 57.3 -> 57.3 | 14.9 -> 15.0 | 32.3 -> 32.1 | 14 (73.1) vs 14 (62.0) |

Pooled (nights equal): percentile 48.5 -> 48.3, top 10% 9.6 -> 9.5, cash 22.6 -> 22.4; higher on 2 of 4 nights. The
only night where it matters (11-20 early) got worse. Doesn't pass the A2 rule: keep today's credit; revisit if
sharing grows (Draw the 9 makes more of it).
