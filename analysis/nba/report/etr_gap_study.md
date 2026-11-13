# Why our morning Proj differs from ETR's final upload (study, 2026-11-13)

The morning Proj's job is to match ETR's final number before the market does. 15 six- and four-drafter slates
(10-28 to 11-12) where Lock AM came before ETR's first file; top 60 by morning ADP; each player's value is his
projection minus the average of his 6 ADP neighbours (nba_etr_match.py). Target: ETR's last upload before lock
(its first carries a random multiplier: first/final ratios cluster at a daily level of 0.96-1.07, with 2-3%
player-to-player spread; uploads after 2pm PT don't have it).

## Are we getting closer?

- Against the final upload: correlation 0.72 (first 7 slates) to 0.81 (last 8), average gap 2.0 to 2.1 points,
  big gaps (3+) 24% both halves. Ranking agreement up, size of the gaps not.
- ETR's own first upload lands within 0.8 points of its final on average (correlation 0.95); ours 2.1.
  ETR barely moves during the day, so most of our gap is real model disagreement, not the multiplier.
- ETR doesn't drift toward us: where we were 2+ off its first upload (no news), its final moved toward ours
  on 122 of 249 (49%).
- Our CLV (value against the ADP move to lock) 0.15 against ETR's 0.33.
- The one fix so far (rookies on their last 3 ETR nights, 11-07) worked: gap +2.5 to +0.3 against the first upload.

## Where the gaps are (no tag on the player; ETR final minus ours, value points)

26 of 90 players seen 4+ times are off the same way more than chance allows.

**We're under ETR, and it's minutes.** Our minutes sit at his usual; ETR's number implies (at our per-minute rate)
about what he has played lately:

| player | n | our min | last 3 | ETR's number implies | gap |
|---|---|---|---|---|---|
| Ayo Dosunmu | 7 | 29.8 | 33.1 | 32.5 | +3.0 |
| Jaden McDaniels | 7 | 33.1 | 35.0 | 35.5 | +2.4 |
| Kyshawn George | 6 | 33.3 | 35.0 | 34.8 | +1.1 |
| Jeremiah Fears | 6 | 26.7 | 29.6 | 31.6 | +6.0 |
| Cooper Flagg | 8 | 33.0 | 34.9 | 35.1 | +2.5 |
| Anthony Black | 4 | 29.4 | 32.1 | 31.5 | +3.0 |
| Onyeka Okongwu | 7 | 28.7 | 30.9 | 30.5 | +2.0 |

Under test as H5 (hypotheses.json): raise the morning Proj half a point per minute when the last 3 games ran 4+
over his usual, graded against ETR's final. Backtest +0.48 closer on 53 players (picked from 4 versions on these
slates; the forward test decides). Avdija (+3.1) and Caleb Wilson (+4.9) are under ETR too, on a mix of minutes and rate.

**We're over ETR, and it's points per minute.** Our minutes match his recent ones; ETR projects less per minute:
LaMelo Ball (-2.6), Gobert (-2.2), Trae Young (-2.1), Sarr (-2.4), Davis (-1.8), Harden (-1.8), Mitchell (-1.3),
Castle (-2.3), Hartenstein (-2.7), Sabonis (-4.2; ETR also implies fewer minutes, 33.8 against his 36).
Centers as a group: we're 0.4 above ETR (149 player-nights); wings 0.3-0.4 below.

**Team splits.** Minnesota: over on Ball and Gobert, under on McDaniels and Dosunmu. Washington: over on Sarr,
Young and Davis, under on Kyshawn George. Cleveland: over on Harden, Mitchell and Allen. The team totals are close;
the split isn't.

## Reading ETR's weights from its numbers

ETR publishes no minutes, so the split is read across players instead: ETR final over ours (log) against recent
minutes over our minutes and this season's actual points per minute over our rate (783 untagged player-nights):

- recent minutes: 0.27 (80% range over slates 0.22 to 0.32). Last 3 games 10% over our minutes puts ETR about
  2.7% over us, about 0.35 points a minute on a 40-point player: the same size as H5's half point.
- this season's rate: 0.17 (0.14 to 0.20), rising with games played (0.11 under 6 games, 0.20 after). A player
  producing 10% under our rate this season sits about 2% under us at ETR: our rate leans on the prior more than ETR's.
- the two explain about a fifth of the spread (R2 0.21); the rest is ETR's own reads.

Next idea in line (not yet under test; needs a yes): blend our points per minute toward this season's actual, more
as games pile up, graded against ETR's final like H5. Then review ours and ETR's against the box scores.
