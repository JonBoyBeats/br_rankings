# Points per minute, rebuilt from a clean base (2026-11-25)

Analysis only; nothing ships. The coordinator's per-minute build (the operator's model: tonight's minutes x tonight's DraftKings
points a minute, nothing outside), on the clean-base method (every old fix re-earns its place). Script:
`scripts/dk_ppm_study.py` (assemble, select, oldplus); results in `per_minute_2026-11-25/select.json`.

## Verdict

**The rebuilt points-a-minute half does not beat today's, held out, so nothing ships.** On the same rebuilt minutes
(dk_qmin_rebuild.py, held out), over 14 graded slates (1,932 player-nights; 181 stars, 771 rotation):

| | stars 25+ points MAE | rotation 10-25 points MAE |
|---|---|---|
| today's projection | 8.725 | 7.649 |
| today's points a minute x rebuilt minutes | 8.769 | 7.477 |
| clean per-minute base x rebuilt minutes | 8.560 | 7.788 |
| **rebuilt (base + kept layers) x rebuilt minutes** | **8.536** | **7.488** |

- Rebuilt vs today's projection: stars +0.189 ± 0.180 (better on 8 of 14), rotation +0.161 ± 0.130 (9 of 14). Under the
  Lab bar (10 of 14 and 2 x SE) on both.
- Rebuilt vs today's points a minute on the same rebuilt minutes: stars +0.232 ± 0.156 (9 of 14), rotation -0.011 ± 0.096
  (8 of 14). Directional on stars only.
- Most of the gain over today's projection is the minutes rebuild, which ships separately.

**Why: the per-minute half is already at the noise floor.** One game's points a minute for a player at 20+ minutes varies
around his own season rate with an SD of 0.29 (221 players with 6+ such games). Our per-minute miss on the same kind of
player-nights has an SD of 0.28 (rotation) and 0.29 (stars). Nearly all of the per-minute miss is single-game variance:
shooting and game flow that no rate estimate removes. Split-half reliability of a season's points a minute is r 0.49 for
one half (0.66 Spearman-Brown to the full season) at 20+ minute games, so early-season rates carry real but modest signal,
and a layer that moves a rate a few percent can't show up against 0.29.

## The split (reproduced)

Miss = (min_act - min_proj) x (fp / min_proj) + min_act x (act / min_act - fp / min_proj); squared shares, players who
played, projected 10+.

| | 12 slates (the coordinator's) | 14 slates |
|---|---|---|
| rotation: minutes / per minute | 43% / 57% (n 592) | 42% / 58% (n 751) |
| stars: minutes / per minute | 32% / 68% (n 134) | 32% / 68% (n 180) |

It reproduces the coordinator's 42 / 58 and 32 / 68. The per-minute half is the larger share of the squared miss, but it
is almost all irreducible (above), so the minutes half is where the projection can still improve.

## Each fix and layer, added alone to the clean base (held out by slate)

Gain = clean base's MAE minus with the fix (positive is better), ± SE of the slate gains, slates better. The parameter is chosen on
the other 13 slates. Pass = the Lab bar on one band with the other band not worse beyond noise. IN / OUT is after forward
selection and the backward check.

| fix / layer | in today's | stars gain | rotation gain | passes alone | final |
|---|---|---|---|---|---|
| miya_prior | yes | +0.160 ± 0.102 (10/14) | +0.128 ± 0.065 (11/14) | no | OUT |
| carry | yes | +0.037 ± 0.137 (9/14) | +0.072 ± 0.064 (9/14) | no | OUT |
| miya_rate | yes | +0.106 ± 0.086 (10/14) | +0.094 ± 0.044 (10/14) | yes | OUT |
| form_raw | yes | -0.047 ± 0.023 (4/14) | +0.001 ± 0.009 (7/14) | no | OUT |
| form_clean | no (L2) | -0.030 ± 0.075 (6/14) | +0.009 ± 0.030 (6/14) | no | OUT |
| vegas_last | yes | -0.145 ± 0.149 (8/14) | +0.119 ± 0.031 (13/14) | yes | IN |
| vegas_this | no (L4) | -0.148 ± 0.146 (6/14) | +0.207 ± 0.057 (12/14) | yes | OUT |
| game_adj | yes | +0.073 ± 0.052 (9/14) | +0.114 ± 0.028 (13/14) | yes | IN |
| dd | yes | -0.045 ± 0.018 (4/14) | -0.009 ± 0.002 (2/14) | no | OUT |
| gate | yes (page) | -0.069 ± 0.057 (8/14) | +0.031 ± 0.019 (9/14) | no | OUT |
| opp_pts | no (L3) | +0.047 ± 0.073 (10/14) | +0.141 ± 0.028 (14/14) | yes | IN |
| opp_tpm | no (L3) | +0.009 ± 0.005 (8/14) | +0.011 ± 0.002 (13/14) | yes | IN |
| opp_reb | no (L3) | +0.099 ± 0.048 (9/14) | +0.106 ± 0.020 (13/14) | yes | IN |
| opp_ast | no (L3) | +0.016 ± 0.043 (7/14) | +0.081 ± 0.019 (13/14) | yes | IN |
| opp_stl | no (L3) | +0.003 ± 0.020 (6/14) | +0.035 ± 0.013 (12/14) | yes | OUT |
| opp_blk | no (L3) | +0.015 ± 0.025 (7/14) | +0.025 ± 0.008 (13/14) | yes | OUT |
| opp_to | no (L3) | +0.010 ± 0.012 (8/14) | +0.009 ± 0.003 (11/14) | yes | OUT |
| opp_all | no (L3) | -0.133 ± 0.176 (8/14) | +0.249 ± 0.061 (13/14) | yes | OUT |

Forward selection (each step's gain over the set before it):
1. opp_reb: stars +0.099 ± 0.048 (9), rotation +0.106 ± 0.020 (13).
2. game_adj: stars +0.023 (9), rotation +0.091 ± 0.030 (11).
3. vegas_last (slope 0.006, half today's 0.0123): stars -0.032 (7), rotation +0.055 ± 0.022 (11).
4. opp_tpm: rotation +0.008 ± 0.002 (11).
5. opp_ast: rotation +0.014 ± 0.006 (12), stars -0.026.
6. opp_pts: rotation +0.026 ± 0.009 (11), stars -0.039.

The backward check kept all six. Every later addition is a rotation gain of a few hundredths, with stars flat or
slightly worse.

Notes on the fixes that are out:
- **EvanMiya prior (MIYA_W) and ongoing rate (MIYA_RATE_W)**: closest to the bar on the clean base. miya_rate passes alone
  (stars +0.106, rotation +0.094), but after the opponent and Vegas layers neither adds anything that passes.
- **CARRY (last season through the stayed/transfer fit)**: adds nothing on top of EvanMiya and hurts stars once the other
  layers are in (-0.13 to -0.17).
- **FORM, raw and on competitive minutes (L2)**: both slightly worse than unweighted season rates for stars (-0.05 and
  -0.03). Recency adds no per-minute signal this early; consistent with the noise floor above.
- **Vegas baseline, this season vs last (L4)**: this season's schedule-adjusted scoring, faded from last season, gives the
  bigger rotation gain alone (+0.207 vs +0.119). Once the opponent layers are in it loses to last season's baseline at a
  smaller slope; the two overlap (the opponent's defense is in both).
- **Double-double bonus**: slightly worse in both bands (stars -0.045, rotation -0.009). Our dd_chance overstates it at these
  minutes. Out.
- **DraftKings-average gate at $6k+**: re-tested on the new projection; worse for stars (-0.069), so out.
- **L3 opponent matchup**: the per-category versions pass alone mostly on rotation (rebounds, points, assists consistently
  better on 13-14 of 14 slates, gains 0.08-0.14). Stars move little (rebounds +0.10 best).
  - Applied to today's points a minute instead of the clean base, it adds about nothing: rotation +0.002 to +0.043, stars
    -0.007 to -0.172 (the opponent's defense is already in today's Vegas factor). Not worth shipping on its own.

## Worked example: one star, two matchups (the rebuilt model's L3)

The model's matchup factor is the opponent's allowed rates (rebounds, assists, points, threes) against what its
opponents usually produce, weighted by his own category profile.
- **Unfavorable: Tyran Stokes, 11-19 (157139).** The opponent allows less than its opponents usually produce in his
  categories: factor 0.907. 29.2 projected without the matchup, 26.5 with it; he scored 38.75.
- **Neutral to favorable: Tariq Francis, 11-19 (157139).** Factor 1.003: 23.8 without, 23.9 with; he scored 34.75. No
  star on these slates drew a matchup factor above about 1.003, because slate games are mostly high-majors against
  good defenses.

Both misses are single-game swings far larger than anything the matchup moves (above).

## The stored breakdown

Nothing ships, so the nightly is unchanged. The rebuild's per-player breakdown (`project()` returns it: baseline points a
minute, matchup, EvanMiya, pace, GAME_ADJ, final) is ready to store as `ppm_parts` if a later version passes. The future
200-minute sheet would read it beside the minutes half's `min_parts`.

## Not run

The same-seed bank check and the banded proxy lenses gate shipping. The rebuild fails the banded grade first, so it
never reaches them.

## Follow-on (not built)

A per-team "200 minutes" sheet on the page, for hand tweaks with the projection updating live, reading `min_parts`
(and `ppm_parts` when there is one). Noted only.

## Data

- ESPN box scores of all 1,359 D1 games before 2026-11-25 12Z (per category), the QMIN study's parsed games (competitive
  minutes), ESPN careers (last season), the lock-time `_proj.json` files (spread, total, EvanMiya, DraftKings average), and
  the rebuilt minutes held out (`rb_mins.json`).
- Bands are by today's projection (fp_dk), so every candidate is scored on the same players.
- Parameters are chosen on the equal-weighted mean of the two bands' MAE over the other slates.
