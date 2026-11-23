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

Reproduce: `python3 scripts/dk_field_bands.py build|score|owner|banks --cache DIR`. These build on
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

