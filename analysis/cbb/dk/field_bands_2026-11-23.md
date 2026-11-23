# Field by contest size, with the ownership rules inside it: retest (2026-11-23)

The operator approved the lock review's recommendation (2026-11-23): build a field for each contest-size band, put both
ownership rules inside it, and retest under the realism bar. The bands are Large (300+ entries), Medium (30-299) and
Small (under 30).

Each band's field had these parts:

- **Chalk style.** DraftKings' average with noise .08, at the band's share: Large 0.2, Medium 0.3, Small 0.4. Small's
  0.4 is the operator's prior and was not fitted.
- **The no-punt pool.**
- **A casual style** at noise 0.8 (w 0.5, as in the original style). Its share was fitted held out by night over
  0 / .04 / .08 / .12, on the ownership bands.
- **Coming off a big game.** A player whose last game was 10+ DK points over his season average gets x1.22 on his field
  projection. This is ownwatch's rule (dk_cbb_field.big_game).

Each field was 1,000 lineups at seed 7. The retest ran on 9 nights and 45 graded contests: Large 31 on 9 nights,
Medium 12 on 7, Small 2 on 2. Every comparison is against the current field (FIELD_STYLES: chalk 0.2 at noise .10,
punts allowed, no big-game rule).

Reproduce: `python3 scripts/dk_field_bands.py build|score|owner|banks --cache DIR --variants nopunt`. These build on
`scripts/dk_field_study.py`'s cache.

## Verdict: every band fails, and the field stays as it is

**Large fails.** Five of its seven targeted measures miss the 6-of-9 bar:

| Targeted measure | Nights moving toward real (of 9) |
|---|---|
| Under-5% | 3 |
| Punts | 4 |
| Top trio | 5 |
| At the cap | 2 |
| 3+ from a team | 1 |

The 5-20% band is worse on 7 nights and the 20%+ band on 6.

**Medium fails.** Four measures miss 4 of 7: under-5% (2), trio lift (3), at the cap (2) and 3+ from a team (1).

**Small is report only.** It also misses on duplication, under-5%, at the cap and 3+ from a team.

**The banks are worse too.** Same-seed rule-free banks were cut against the Large band field at casual .12, the held-out
choice:

| Measure | Current | Band field | Nights better / worse |
|---|---|---|---|
| Top 10% | 15.9% | 13.9% | 2 / 7 |
| Cash | 30.3% | 28.6% | 3 / 6 |
| Percentile | 56.1 | 55.3 | 3 / 6 |

The decision:

- `battle-royale-research scripts/dk_cbb_field.py` main() keeps building the single current field. No `bands` key is
  written, so the page's fieldFor() falls back to F.field.
- field() gains opt-in `punts=False` and `big=True` switches, both off by default. Its output with the defaults is
  unchanged (checked: the first lineups match the cached current field at seed 7). The switches exist so that this
  retest can be reproduced.

## Why: the no-punt pool pushes the floor the wrong way

The casual style does what it was meant to. In the Large band, the under-5% ratio (real ownership divided by the
field's) falls with each step up in casual share. Real is 1.00 and the current field is 1.93.

| Casual share | Under-5% ratio |
|---|---|
| 0 | 2.81 |
| .04 | 2.56 |
| .08 | 2.35 |
| .12 | 2.26 |

The base it starts from is worse than the current field, though. The study's no-punt fields, without the big-game rule
and without a casual style, already moved the under-5% ratio from 1.93 to 2.66 on Large and from 1.75 to 2.82 on Medium.
Taking the punts out of the pool takes most of the field's near-0 players with them. Real fields do still play some of
them: 7.3% of Large entries hold a sub-$3.5k punt.

The held-out casual share sat on the edge of the grid (.12) on every Large and Medium night, and the gain shrinks with
each step. A larger share would not get back to 1.93 before it breaks the measures that the chalk style fixed:
duplication and the top trio.

## Owner duplication

How often another user held the same 8 as one of the owner's entries (dk_eval.USER), against each field's expected
rate. The expected rate is 1-(1-f)^(entries-1), where f is the lineup's share of the 1,000.

| Band | Owner entries | Real | Current field | New field (cas .12) |
|---|---|---|---|---|
| Large | 367 | 21 (5.7%) | 3.8% | 3.7% |
| Medium | 25 | 1 (4.0%) | 8.8% | 8.8% |
| Small | 2 | 0 | 0 | 0 |

On Large, both fields understate the owner's real duplication by about a third, and the new field doesn't help. Medium's
count is too thin to read.

## Per-band tables (scripts/dk_field_bands.py score)

The casual share in each band's "new" column is the share fitted on all nights pooled. The per-night counts use the
held-out choice for each night.

## Large: 31 contests, 9 nights
Casual share held out by night: 11-16 0.12, 11-17 0.12, 11-18 0.12, 11-19 0.12, 11-19 0.12, 11-20 0.12, 11-20 0.12, 11-21 0.12, 11-22 0.12; on all nights: 0.12.

| Measure | toward real | away | same | real / current / new (band means) |
|---|---|---|---|---|
| duplication % | 6 | 3 | 0 | 13.40 / 8.03 / 14.21 |
| under-5% real/field (to 1) | 3 | 6 | 0 | 1.00 / 1.93 / 2.26 |
| a sub-$3.5k punt % | 4 | 5 | 0 | 7.32 / 16.80 / 14.74 |
| most common trio % | 5 | 2 | 2 | 28.65 / 23.36 / 28.08 |
| top-20 trio lift | 9 | 0 | 0 | 1.40 / 1.08 / 1.22 |
| at the cap % | 2 | 7 | 0 | 39.93 / 33.47 / 31.87 |
| 3+ from a team % | 1 | 8 | 0 | 36.93 / 36.13 / 38.97 |
| 5-20% real/field (to 1) (not targeted) | 2 | 7 | 0 | 1.00 / 1.01 / 1.07 |
| 20%+ real/field (to 1) (not targeted) | 3 | 6 | 0 | 1.00 / 0.90 / 0.86 |

Bar (9 nights, need 6 toward real on each targeted measure, and no other measure worse on 6+): targeted FAIL (under-5% real/field (to 1), a sub-$3.5k punt %, most common trio %, at the cap %, 3+ from a team %); others FAIL (5-20% real/field (to 1), 20%+ real/field (to 1)).

## Medium: 12 contests, 7 nights
Casual share held out by night: 11-18 0.12, 11-19 0.12, 11-19 0.12, 11-20 0.12, 11-20 0.12, 11-21 0.12, 11-22 0.12; on all nights: 0.12.

| Measure | toward real | away | same | real / current / new (band means) |
|---|---|---|---|---|
| duplication % | 6 | 1 | 0 | 12.29 / 3.84 / 13.86 |
| under-5% real/field (to 1) | 2 | 5 | 0 | 1.00 / 1.75 / 1.99 |
| a sub-$3.5k punt % | 5 | 2 | 0 | 6.07 / 11.43 / 10.60 |
| most common trio % | 6 | 1 | 0 | 38.52 / 23.61 / 36.21 |
| top-20 trio lift | 3 | 3 | 1 | 1.24 / 1.09 / 1.25 |
| at the cap % | 2 | 5 | 0 | 38.31 / 32.48 / 31.35 |
| 3+ from a team % | 1 | 6 | 0 | 44.33 / 44.07 / 50.86 |
| 5-20% real/field (to 1) (not targeted) | 3 | 4 | 0 | 1.00 / 0.95 / 1.05 |
| 20%+ real/field (to 1) (not targeted) | 3 | 4 | 0 | 1.00 / 0.96 / 0.90 |

Bar (7 nights, need 4 toward real on each targeted measure, and no other measure worse on 4+): targeted FAIL (under-5% real/field (to 1), top-20 trio lift, at the cap %, 3+ from a team %); others FAIL (5-20% real/field (to 1), 20%+ real/field (to 1)).

## Small: 2 contests, 2 nights (thin: report only; chalk 0.4 is the operator's prior)
Casual share held out by night: 11-21 0.12, 11-22 0.00; on all nights: 0.08.

| Measure | toward real | away | same | real / current / new (band means) |
|---|---|---|---|---|
| duplication % | 0 | 1 | 1 | 0.00 / 0.50 / 3.00 |
| under-5% real/field (to 1) | 0 | 2 | 0 | 1.00 / 1.11 / 1.65 |
| a sub-$3.5k punt % | 2 | 0 | 0 | 0.00 / 1.50 / 0.00 |
| most common trio % | 2 | 0 | 0 | 62.86 / 22.40 / 37.10 |
| top-20 trio lift | 2 | 0 | 0 | 1.55 / 1.15 / 1.25 |
| at the cap % | 0 | 2 | 0 | 34.30 / 32.70 / 32.95 |
| 3+ from a team % | 0 | 2 | 0 | 24.30 / 36.35 / 47.15 |
| 5-20% real/field (to 1) (not targeted) | 2 | 0 | 0 | 1.00 / 0.65 / 0.97 |
| 20%+ real/field (to 1) (not targeted) | 1 | 1 | 0 | 1.00 / 1.10 / 0.97 |

Bar (2 nights, need 2 toward real on each targeted measure, and no other measure worse on 2+): targeted FAIL (duplication %, under-5% real/field (to 1), at the cap %, 3+ from a team %); others PASS.


# Clean retest: punts kept in the pool, each rule separately and together (2026-11-23, afternoon)

The operator approved this retest. It is analysis only, and nothing ships from it.

Setup:

- The pool keeps its punts (`punts=True`).
- Bands: Large chalk 0.2, Medium 0.3, Small 0.4. Small stays report only.
- The bar, the bank test, the nights and the seeds are the same as in the first retest.

The four variants:

- **(a) Casual floor style only.** The share was fitted held out over 0 / .04 / .08 / .12. The pick sat on the .12 edge,
  so the grid was extended to .16 / .20.
- **(b) Big-game x1.22 only.**
- **(c) Both rules.**
- **(d) The band's chalk only**, as the baseline.

Every comparison is against the current field. Note that (d) Large differs from the current field only in the chalk
style's noise (.08 against .10).

Reproduce: `python3 scripts/dk_field_bands.py build|score|owner|banks --cache DIR --variants a,b,c,d`.

## Verdict: nothing passes, and the casual style carries the ownership side

| Variant | Large: toward real of 9 (dup u5 punt trio lift cap 3tm; need 6) | 5-20 / 20+ worse | Medium: toward real of 7 (need 4) | 5-20 / 20+ worse | Small (report) | Bar |
|---|---|---|---|---|---|---|
| (a) casual only (.20, ext) | 5 **9** 3 2 **9** 1 **7** | 1 / 1 | **6 6** 1 **7** 3 1 2 | 3 / 4 | 0 1 0 2 1 0 0 | FAIL / FAIL |
| (b) big-game only | 5 1 4 4 **8** 5 4 | 5 / 8 | **5** 0 **4 6 5** 3 1 | 4 / 5 | 1 0 2 2 2 1 0 | FAIL / FAIL |
| (c) both (.20, ext) | 5 **9** 4 4 **9** 1 5 | 5 / 4 | **5 5** 2 **6** 3 0 1 | 4 / 4 | 1 1 2 2 2 1 0 | FAIL / FAIL |
| (d) band chalk only | **6** 2 3 5 **9** 5 5 | 5 / 7 | **6** 2 2 **7 5 4** 2 | 2 / 5 | 0 0 2 2 1 0 0 | FAIL / FAIL |

The Bar column gives Large first, then Medium.

Bank test: the Large band's field against the current field, top 10% / cash / percentile. The cut is the same as in the
first retest.

| Variant | Top 10% | Cash | Percentile | Nights better / worse (top 10%, cash, percentile) | Same kept lineups |
|---|---|---|---|---|---|
| (a) | 15.9% -> 16.1% | 30.3% -> 30.2% | 56.1 -> 56.0 | 3/4, 3/5, 4/5 | 87% |
| (b) | 15.9% -> 15.1% | 30.3% -> 28.9% | 56.1 -> 55.1 | 3/4, 4/5, 5/4 | 67% |
| (c) | 15.9% -> 15.1% | 30.3% -> 29.3% | 56.1 -> 55.4 | 3/5, 3/5, 4/5 | 67% |
| (d) | 15.9% -> 16.4% | 30.3% -> 30.8% | 56.1 -> 56.3 | 4/1, 4/2, 6/3 | 95% |

Owner duplication, expected rate in each field. Real is Large 21 of 367 (5.7%) and Medium 1 of 25 (4.0%).

| Band | Current | (a) | (b) | (c) | (d) |
|---|---|---|---|---|---|
| Large | 3.8% | 3.6% | 3.7% | 3.6% | 3.8% |
| Medium | 8.8% | 8.3% | 12.6% | 10.6% | 9.9% |

## What each rule does

**(a) The casual style is the rule that fixes ownership.** On Large, the under-5% ratio falls from 1.93 to 1.30
(real is 1.00) and moves toward real on all 9 nights. The 5-20% and 20%+ ratios also improve, on 8 of 9 nights each. On
Medium it is under-5% toward real on 6 of 7 nights and the top trio on 7.

The share still sits on the edge of the extended grid (.20 on every Large and Medium night), so the right share is .20
or more. That is untested.

It fails the bar on lineup shape:

- **Duplication** reaches only 11.0% against a real 13.4% (5 of 9).
- **The top trio** is 2 of 9.
- **Punts** are untouched (16.6% against a real 7.3%).
- **At the cap** gets worse (1 of 9).

**(b) The big-game rule is the one that hurts.** On its own it pushes the under-5% ratio the wrong way (1.93 to 2.14;
1 of 9 nights toward real). The 20%+ ratio is worse on 8 of 9 nights. Its banks are the worst of the four (top 10%
15.1%, cash 28.9%). Adding it to the casual style in (c) undoes part of (a): the 5-20% and 20%+ ratios turn worse on
5 and 4 nights, and the banks drop. The ownwatch pattern (x1.25 real ownership) is real, but inside the field it
concentrates the chalk rather than spreading it.

**(d) The band's chalk alone** lifts duplication (6 of 9) and trio lift (9 of 9), but it leaves the floor as it was.
Its banks are the only ones better than current (4 better / 1 worse at top 10%). The cut keeps the same lineups as
current 95% of the time, so that edge is thin.

**No variant fixes punts or salary at the cap.** Those need a mechanism on salary use, not on ownership. In the first
retest, the no-punt pool fixed punts but broke the floor.

## Per-variant tables (scripts/dk_field_bands.py score --variants a,b,c,d)

### (a) casual only

#### Large: 31 contests, 9 nights
Casual share over 0.00/0.04/0.08/0.12/0.16/0.20 (extended: .12 was the edge), held out by night: 11-16 0.20, 11-17 0.20, 11-18 0.20, 11-19 0.20, 11-19 0.20, 11-20 0.20, 11-20 0.20, 11-21 0.20, 11-22 0.20; on all nights: 0.20.

| Measure | toward real | away | same | real / current / new (band means) |
|---|---|---|---|---|
| duplication % | 5 | 4 | 0 | 13.40 / 8.03 / 11.00 |
| under-5% real/field (to 1) | 9 | 0 | 0 | 1.00 / 1.93 / 1.30 |
| a sub-$3.5k punt % | 3 | 5 | 1 | 7.32 / 16.80 / 16.57 |
| most common trio % | 2 | 6 | 1 | 28.65 / 23.36 / 23.26 |
| top-20 trio lift | 9 | 0 | 0 | 1.40 / 1.08 / 1.32 |
| at the cap % | 1 | 7 | 1 | 39.93 / 33.47 / 31.78 |
| 3+ from a team % | 7 | 2 | 0 | 36.93 / 36.13 / 36.28 |
| 5-20% real/field (to 1) (not to be worse) | 8 | 1 | 0 | 1.00 / 1.01 / 1.02 |
| 20%+ real/field (to 1) (not to be worse) | 8 | 1 | 0 | 1.00 / 0.90 / 0.94 |

Bar (9 nights, need 6 toward real on each targeted measure, and neither ownership band worse on 6+): targeted FAIL (dup, punt, trio, cap); others PASS.

#### Medium: 12 contests, 7 nights
Casual share over 0.00/0.04/0.08/0.12/0.16/0.20 (extended: .12 was the edge), held out by night: 11-18 0.20, 11-19 0.20, 11-19 0.20, 11-20 0.20, 11-20 0.20, 11-21 0.20, 11-22 0.20; on all nights: 0.20.

| Measure | toward real | away | same | real / current / new (band means) |
|---|---|---|---|---|
| duplication % | 6 | 1 | 0 | 12.29 / 3.84 / 9.26 |
| under-5% real/field (to 1) | 6 | 1 | 0 | 1.00 / 1.75 / 1.16 |
| a sub-$3.5k punt % | 1 | 6 | 0 | 6.07 / 11.43 / 12.07 |
| most common trio % | 7 | 0 | 0 | 38.52 / 23.61 / 29.84 |
| top-20 trio lift | 3 | 4 | 0 | 1.24 / 1.09 / 1.35 |
| at the cap % | 1 | 6 | 0 | 38.31 / 32.48 / 31.49 |
| 3+ from a team % | 2 | 5 | 0 | 44.33 / 44.07 / 46.78 |
| 5-20% real/field (to 1) (not to be worse) | 4 | 3 | 0 | 1.00 / 0.95 / 1.02 |
| 20%+ real/field (to 1) (not to be worse) | 3 | 4 | 0 | 1.00 / 0.96 / 0.97 |

Bar (7 nights, need 4 toward real on each targeted measure, and neither ownership band worse on 4+): targeted FAIL (punt, lift, cap, 3tm); others FAIL (20+).

#### Small: 2 contests, 2 nights (thin: report only; chalk 0.4 is the operator's prior)
Casual share over 0.00/0.04/0.08/0.12/0.16/0.20 (extended: .12 was the edge), held out by night: 11-21 0.20, 11-22 0.16; on all nights: 0.20.

| Measure | toward real | away | same | real / current / new (band means) |
|---|---|---|---|---|
| duplication % | 0 | 1 | 1 | 0.00 / 0.50 / 1.21 |
| under-5% real/field (to 1) | 1 | 1 | 0 | 1.00 / 1.11 / 1.00 |
| a sub-$3.5k punt % | 0 | 2 | 0 | 0.00 / 1.50 / 2.25 |
| most common trio % | 2 | 0 | 0 | 62.86 / 22.40 / 37.35 |
| top-20 trio lift | 1 | 1 | 0 | 1.55 / 1.15 / 1.45 |
| at the cap % | 0 | 2 | 0 | 34.30 / 32.70 / 32.45 |
| 3+ from a team % | 0 | 2 | 0 | 24.30 / 36.35 / 43.75 |
| 5-20% real/field (to 1) (not to be worse) | 1 | 1 | 0 | 1.00 / 0.65 / 0.78 |
| 20%+ real/field (to 1) (not to be worse) | 1 | 1 | 0 | 1.00 / 1.10 / 1.08 |

Bar (2 nights, need 2 toward real on each targeted measure, and neither ownership band worse on 2+): targeted FAIL (dup, u5, punt, lift, cap, 3tm); others PASS.

### (b) big-game only

#### Large: 31 contests, 9 nights

| Measure | toward real | away | same | real / current / new (band means) |
|---|---|---|---|---|
| duplication % | 5 | 4 | 0 | 13.40 / 8.03 / 14.18 |
| under-5% real/field (to 1) | 1 | 8 | 0 | 1.00 / 1.93 / 2.14 |
| a sub-$3.5k punt % | 4 | 3 | 2 | 7.32 / 16.80 / 18.34 |
| most common trio % | 4 | 5 | 0 | 28.65 / 23.36 / 29.67 |
| top-20 trio lift | 8 | 1 | 0 | 1.40 / 1.08 / 1.14 |
| at the cap % | 5 | 3 | 1 | 39.93 / 33.47 / 34.20 |
| 3+ from a team % | 4 | 5 | 0 | 36.93 / 36.13 / 38.80 |
| 5-20% real/field (to 1) (not to be worse) | 4 | 5 | 0 | 1.00 / 1.01 / 1.09 |
| 20%+ real/field (to 1) (not to be worse) | 1 | 8 | 0 | 1.00 / 0.90 / 0.83 |

Bar (9 nights, need 6 toward real on each targeted measure, and neither ownership band worse on 6+): targeted FAIL (dup, u5, punt, trio, cap, 3tm); others FAIL (20+).

#### Medium: 12 contests, 7 nights

| Measure | toward real | away | same | real / current / new (band means) |
|---|---|---|---|---|
| duplication % | 5 | 2 | 0 | 12.29 / 3.84 / 13.45 |
| under-5% real/field (to 1) | 0 | 7 | 0 | 1.00 / 1.75 / 2.10 |
| a sub-$3.5k punt % | 4 | 3 | 0 | 6.07 / 11.43 / 12.93 |
| most common trio % | 6 | 1 | 0 | 38.52 / 23.61 / 37.92 |
| top-20 trio lift | 5 | 1 | 1 | 1.24 / 1.09 / 1.16 |
| at the cap % | 3 | 3 | 1 | 38.31 / 32.48 / 33.58 |
| 3+ from a team % | 1 | 6 | 0 | 44.33 / 44.07 / 50.78 |
| 5-20% real/field (to 1) (not to be worse) | 3 | 4 | 0 | 1.00 / 0.95 / 1.02 |
| 20%+ real/field (to 1) (not to be worse) | 2 | 5 | 0 | 1.00 / 0.96 / 0.89 |

Bar (7 nights, need 4 toward real on each targeted measure, and neither ownership band worse on 4+): targeted FAIL (u5, cap, 3tm); others FAIL (5-20, 20+).

#### Small: 2 contests, 2 nights (thin: report only; chalk 0.4 is the operator's prior)

| Measure | toward real | away | same | real / current / new (band means) |
|---|---|---|---|---|
| duplication % | 1 | 1 | 0 | 0.00 / 0.50 / 3.57 |
| under-5% real/field (to 1) | 0 | 2 | 0 | 1.00 / 1.11 / 1.63 |
| a sub-$3.5k punt % | 2 | 0 | 0 | 0.00 / 1.50 / 1.00 |
| most common trio % | 2 | 0 | 0 | 62.86 / 22.40 / 37.10 |
| top-20 trio lift | 2 | 0 | 0 | 1.55 / 1.15 / 1.19 |
| at the cap % | 1 | 1 | 0 | 34.30 / 32.70 / 33.85 |
| 3+ from a team % | 0 | 2 | 0 | 24.30 / 36.35 / 47.10 |
| 5-20% real/field (to 1) (not to be worse) | 2 | 0 | 0 | 1.00 / 0.65 / 0.96 |
| 20%+ real/field (to 1) (not to be worse) | 2 | 0 | 0 | 1.00 / 1.10 / 0.97 |

Bar (2 nights, need 2 toward real on each targeted measure, and neither ownership band worse on 2+): targeted FAIL (dup, u5, cap, 3tm); others PASS.

### (c) casual + big-game

#### Large: 31 contests, 9 nights
Casual share over 0.00/0.04/0.08/0.12/0.16/0.20 (extended: .12 was the edge), held out by night: 11-16 0.20, 11-17 0.20, 11-18 0.20, 11-19 0.20, 11-19 0.20, 11-20 0.20, 11-20 0.20, 11-21 0.20, 11-22 0.20; on all nights: 0.20.

| Measure | toward real | away | same | real / current / new (band means) |
|---|---|---|---|---|
| duplication % | 5 | 4 | 0 | 13.40 / 8.03 / 13.38 |
| under-5% real/field (to 1) | 9 | 0 | 0 | 1.00 / 1.93 / 1.43 |
| a sub-$3.5k punt % | 4 | 2 | 3 | 7.32 / 16.80 / 18.18 |
| most common trio % | 4 | 4 | 1 | 28.65 / 23.36 / 27.03 |
| top-20 trio lift | 9 | 0 | 0 | 1.40 / 1.08 / 1.30 |
| at the cap % | 1 | 8 | 0 | 39.93 / 33.47 / 32.04 |
| 3+ from a team % | 5 | 4 | 0 | 36.93 / 36.13 / 38.29 |
| 5-20% real/field (to 1) (not to be worse) | 4 | 5 | 0 | 1.00 / 1.01 / 1.06 |
| 20%+ real/field (to 1) (not to be worse) | 5 | 4 | 0 | 1.00 / 0.90 / 0.88 |

Bar (9 nights, need 6 toward real on each targeted measure, and neither ownership band worse on 6+): targeted FAIL (dup, punt, trio, cap, 3tm); others PASS.

#### Medium: 12 contests, 7 nights
Casual share over 0.00/0.04/0.08/0.12/0.16/0.20 (extended: .12 was the edge), held out by night: 11-18 0.20, 11-19 0.20, 11-19 0.20, 11-20 0.20, 11-20 0.20, 11-21 0.20, 11-22 0.20; on all nights: 0.20.

| Measure | toward real | away | same | real / current / new (band means) |
|---|---|---|---|---|
| duplication % | 5 | 2 | 0 | 12.29 / 3.84 / 13.03 |
| under-5% real/field (to 1) | 5 | 2 | 0 | 1.00 / 1.75 / 1.30 |
| a sub-$3.5k punt % | 2 | 5 | 0 | 6.07 / 11.43 / 13.21 |
| most common trio % | 6 | 1 | 0 | 38.52 / 23.61 / 34.97 |
| top-20 trio lift | 3 | 3 | 1 | 1.24 / 1.09 / 1.31 |
| at the cap % | 0 | 7 | 0 | 38.31 / 32.48 / 31.18 |
| 3+ from a team % | 1 | 5 | 1 | 44.33 / 44.07 / 50.51 |
| 5-20% real/field (to 1) (not to be worse) | 3 | 4 | 0 | 1.00 / 0.95 / 1.04 |
| 20%+ real/field (to 1) (not to be worse) | 3 | 4 | 0 | 1.00 / 0.96 / 0.94 |

Bar (7 nights, need 4 toward real on each targeted measure, and neither ownership band worse on 4+): targeted FAIL (punt, lift, cap, 3tm); others FAIL (5-20, 20+).

#### Small: 2 contests, 2 nights (thin: report only; chalk 0.4 is the operator's prior)
Casual share over 0.00/0.04/0.08/0.12, held out by night: 11-21 0.08, 11-22 0.08; on all nights: 0.08.

| Measure | toward real | away | same | real / current / new (band means) |
|---|---|---|---|---|
| duplication % | 1 | 1 | 0 | 0.00 / 0.50 / 3.57 |
| under-5% real/field (to 1) | 1 | 1 | 0 | 1.00 / 1.11 / 1.32 |
| a sub-$3.5k punt % | 2 | 0 | 0 | 0.00 / 1.50 / 1.40 |
| most common trio % | 2 | 0 | 0 | 62.86 / 22.40 / 36.35 |
| top-20 trio lift | 2 | 0 | 0 | 1.55 / 1.15 / 1.25 |
| at the cap % | 1 | 1 | 0 | 34.30 / 32.70 / 33.05 |
| 3+ from a team % | 0 | 2 | 0 | 24.30 / 36.35 / 47.50 |
| 5-20% real/field (to 1) (not to be worse) | 2 | 0 | 0 | 1.00 / 0.65 / 0.95 |
| 20%+ real/field (to 1) (not to be worse) | 2 | 0 | 0 | 1.00 / 1.10 / 0.99 |

Bar (2 nights, need 2 toward real on each targeted measure, and neither ownership band worse on 2+): targeted FAIL (dup, u5, cap, 3tm); others PASS.

### (d) band chalk only

#### Large: 31 contests, 9 nights

| Measure | toward real | away | same | real / current / new (band means) |
|---|---|---|---|---|
| duplication % | 6 | 3 | 0 | 13.40 / 8.03 / 11.66 |
| under-5% real/field (to 1) | 2 | 7 | 0 | 1.00 / 1.93 / 1.98 |
| a sub-$3.5k punt % | 3 | 3 | 3 | 7.32 / 16.80 / 16.73 |
| most common trio % | 5 | 4 | 0 | 28.65 / 23.36 / 25.62 |
| top-20 trio lift | 9 | 0 | 0 | 1.40 / 1.08 / 1.16 |
| at the cap % | 5 | 4 | 0 | 39.93 / 33.47 / 33.69 |
| 3+ from a team % | 5 | 3 | 1 | 36.93 / 36.13 / 36.58 |
| 5-20% real/field (to 1) (not to be worse) | 4 | 5 | 0 | 1.00 / 1.01 / 1.01 |
| 20%+ real/field (to 1) (not to be worse) | 2 | 7 | 0 | 1.00 / 0.90 / 0.89 |

Bar (9 nights, need 6 toward real on each targeted measure, and neither ownership band worse on 6+): targeted FAIL (u5, punt, trio, cap, 3tm); others FAIL (20+).

#### Medium: 12 contests, 7 nights

| Measure | toward real | away | same | real / current / new (band means) |
|---|---|---|---|---|
| duplication % | 6 | 1 | 0 | 12.29 / 3.84 / 9.70 |
| under-5% real/field (to 1) | 2 | 5 | 0 | 1.00 / 1.75 / 2.00 |
| a sub-$3.5k punt % | 2 | 4 | 1 | 6.07 / 11.43 / 11.83 |
| most common trio % | 7 | 0 | 0 | 38.52 / 23.61 / 31.96 |
| top-20 trio lift | 5 | 1 | 1 | 1.24 / 1.09 / 1.20 |
| at the cap % | 4 | 3 | 0 | 38.31 / 32.48 / 33.36 |
| 3+ from a team % | 2 | 5 | 0 | 44.33 / 44.07 / 46.86 |
| 5-20% real/field (to 1) (not to be worse) | 4 | 2 | 1 | 1.00 / 0.95 / 1.00 |
| 20%+ real/field (to 1) (not to be worse) | 2 | 5 | 0 | 1.00 / 0.96 / 0.92 |

Bar (7 nights, need 4 toward real on each targeted measure, and neither ownership band worse on 4+): targeted FAIL (u5, punt, 3tm); others FAIL (20+).

#### Small: 2 contests, 2 nights (thin: report only; chalk 0.4 is the operator's prior)

| Measure | toward real | away | same | real / current / new (band means) |
|---|---|---|---|---|
| duplication % | 0 | 2 | 0 | 0.00 / 0.50 / 1.71 |
| under-5% real/field (to 1) | 0 | 2 | 0 | 1.00 / 1.11 / 1.88 |
| a sub-$3.5k punt % | 2 | 0 | 0 | 0.00 / 1.50 / 1.40 |
| most common trio % | 2 | 0 | 0 | 62.86 / 22.40 / 38.85 |
| top-20 trio lift | 1 | 1 | 0 | 1.55 / 1.15 / 1.29 |
| at the cap % | 0 | 2 | 0 | 34.30 / 32.70 / 34.20 |
| 3+ from a team % | 0 | 2 | 0 | 24.30 / 36.35 / 43.40 |
| 5-20% real/field (to 1) (not to be worse) | 1 | 1 | 0 | 1.00 / 0.65 / 0.70 |
| 20%+ real/field (to 1) (not to be worse) | 2 | 0 | 0 | 1.00 / 1.10 / 1.03 |

Bar (2 nights, need 2 toward real on each targeted measure, and neither ownership band worse on 2+): targeted FAIL (dup, u5, lift, cap, 3tm); others PASS.


## Friday review: the field test plan (operator, via the coordinator, 2026-11-23)

The candidates, each against the current field:

1. **The casual floor alone**, at shares 0.20, 0.25, 0.30, 0.35 and 0.40. The 0.20 result sat on the edge of the grid.
2. **The casual floor plus size-band chalk**: Large 0.2, Medium 0.3, Small 0.4.
3. **A salary-use rule** for the punt and at-the-cap gaps.

Big-game x1.22 is dropped as a field rule. It hurt every lens in the clean retest above.

For each candidate, report:

- the realism measures against current: ownership by band (under 5%, 5-20%, 20%+), duplication, trio lift, punts and salary at the cap;
- the bank test on real results.

Decision framing: if no candidate improves the banks, still say whether the casual floor alone, at its best share, is strictly more realistic than current with the banks neutral. The operator may adopt it on that basis as the better foundation.
