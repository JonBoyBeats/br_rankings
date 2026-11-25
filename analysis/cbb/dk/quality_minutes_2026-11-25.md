# Quality minutes (QMIN), 2026-11-25

The question: blowouts and overtime pollute a player's minutes and their trend, and coaches differ in whether the starters come
back in a blowout. Does rebuilding each player's court time from ESPN's play-by-play, split by game state, project minutes better
than today's model? Step 6 (the operator's addition) asks the same with lineup context: who was available.

Script: `scripts/dk_qmin_study.py` (data: every D1 game's ESPN summary to date, cached outside the repo). Results:
`analysis/cbb/dk/quality_minutes_2026-11-25/`. Bank check: `scripts/dk_qmin_bank.js` + `scripts/dk_qmin_bank_score.py`.
Proxy lenses: `scripts/dk_qmin_lenses.py`.

## Verdict

**(b) SIMPLE passes and ships. Full QMIN (c) and QMIN + lineup context (d) fail. QMIN is not more stable game to game.**

**The clean rebuild passes but is not shipped yet** (the section below).
- **What it is:** QMIN on spread-free win-probability states with lineup context, plus raw FORM minutes at 0.5 and steepen 0.18. Every other old minutes fix is out.
- **Against today:** rotation minutes 6.918 → 6.519 (gain 0.398, SE 0.115, better on 12 of 14).
- **Against shipped (b):** gain 0.241 (SE 0.091, better on 11 of 14).
- **Banks:** better on 6-7 of 9 nights.
- **Why not shipped:** it needs the play-by-play in the nightly, a separate build.

- **(b) SIMPLE** counts an overtime game scaled to regulation and a blowout (final margin 20+) at half its FORM weight, then
  applies MIN_BY_SPREAD as today. Held out on 14 slates, rotation minutes MAE went from 6.918 to 6.761, better on 10 of 14,
  a gain of 0.157 against a 2×SE bar of 0.150. Star points MAE improved by 0.24, and top-5 and rank were flat. The same-seed
  banks were better on 9 of 9 nights by percentile. Ownership agreement and the minutes lenses also improved. Ships in
  `cbb_nightly` with the old minutes logged as `min_old`.
- **(b) + lineup context** passed as well (gain 0.179, SE 0.072, 10 of 14), but its gain over (b) is 0.022, inside 1 SE. The
  simpler (b) ships.
- **(c) full QMIN on win-probability states** is much worse: 7.732 against 6.918, better on 1 of 14. Its variants fail the bar:
  plain margin buckets gained 0.177 (SE 0.130, better on 9 of 14), and win probability without the spread gained 0.152
  (SE 0.137, better on 8 of 14).
- **(d) QMIN + context**, built on (c), fails the same way: 7.731, better on 1 of 14.
- **Stability.** QMIN's game-to-game SD is 5.01 against 5.06 for raw minutes and 4.92 per 40 of game: not lower, and its CV is
  higher. It is the more reliable season number, though: odd vs even games r 0.806 against 0.748. So it ranks roles better
  without being steadier from night to night.

### Why (c) fails: the pieces

- **State rates (the main failure).** A win probability that includes the pregame spread calls a 20-point favorite's opening
  minutes LEANING or DECIDED at tip. Starters' opening stints then land in the DECIDED rates. At a -15 spread the state model
  expects 18.9 minutes DECIDED-leading and only 9.0 COMPETITIVE, so a heavy favorite's starters are projected off those
  contaminated rates. Dropping the spread from the win probability (c_wp0), or using plain margin buckets (c_margin), removes
  most of the damage, but neither then clears the bar.
- **Shrinkage.** Players have 2–8 games, so most state cells are thin. The team role rates carry most of the weight.
- **Trend.** The best fade held out was 0.9 for (c), 0.6 for c_wp0, and 0.8 for (b), today's FORM. A role-change flag (last 2
  clean games' competitive rate 0.15+ away from the earlier ones) fires on 639 of 2,114 players with 4+ games. At this point in
  the season that is noise, not a signal, and it was not used.

### Two checks the coordinator asked for

- **No double FORM weighting in (c) and (d).** The state-rate minutes replace the FORM-weighted raw minutes outright. They carry
  their own recency fade, chosen held out. FORM's weight sum only sets the blend against the prior season's MIN_FILL (0.25 of a
  game), the same blend as today.
- **GAME_ADJ** (x1.08 for a 25+ favorite down to x0.947 for a 10+ underdog, on points) tested kept vs dropped inside the same
  held-out test when the state model replaces MIN_BY_SPREAD. Stars' points MAE against today:
  - (c): kept +0.256 (SE 0.182), dropped +0.279 (SE 0.197);
  - (d): kept +0.321 (SE 0.179), dropped +0.331 (SE 0.200).
  Kept is the better of the two, and neither rescues (c) or (d). They fail on rotation minutes, which GAME_ADJ doesn't touch. (b)
  keeps MIN_BY_SPREAD, so GAME_ADJ stays as fitted.

## Worked example: two coaches at the same spread

Two starters with the same QMIN, about 34 minutes a 40 of competitive play, on teams with opposite blowout habits:

| Team | Raw mpg | Blowouts in his games | QMIN | LEANING-lead rate | DECIDED-lead rate | (c) at -15 | (b) |
|---|---|---|---|---|---|---|---|
| Southern Utah (top QMIN player) | 20.8 | 5 of 6 | 33.8 | 0.46 | 0.20 | 17.1 | 25.9 |
| Drake (top QMIN player) | 34.4 | 0 of 5 | 33.8 | 0.79 | 1.00 | 36.3 | 34.7 |

Southern Utah's coach sits the starters once the game is decided, and Drake's doesn't. The state model separates the two (17 vs
36 minutes). But Drake's 1.00 rate in decided time rests on early-game seconds the spread-based win probability calls
"decided". That is the contamination above, and why (c) loses on the slates. (b) gets most of the benefit by down-weighting
Southern Utah's 5 blowouts, without modelling states.

## Step 6: lineup context

- **6a. Availability:** every D1 team-game to date (1,353 games). A team's top 5 / top 8 by QMIN are those with 3+ clean games.
- **6b. Returns:** 32 cases of a top-5 player out 2+ straight games and then back, with 96 teammate observations.
  - Persistence of the gain during the absence after he returns: minutes rate 0.39, DK per minute 0.39 (pooled slope).
  - By case: median 0.25, quartiles 0.02 to 0.77. Roles mostly snap back, but in a quarter of cases most of the gain sticks.
    Example: St. Thomas, 3 games missed, persistence 0.81; Belmont, 2 games missed, 0.02.
  - **BYU / Robert Wright III** was still out through 11-24, the last graded slate, so his return is not in the window.
- **The mirror (first missed game):** teammates absorbed 603 of his 721 minutes the night he sat.
  - By role: 115 to other top-5 players, 270 to the 6-8 group, 218 to the 9+ group.
  - By position: 408 to the same position, 195 to others.
  - This matches today's hand-off, which puts the same position group first (1.0 vs 0.5) and a bench tilt through m×(40-m).
    No change is indicated. The 11-21 thin signal (hand-off teammates +5.31 over projection, n 8) is not tested again here.
- **6c / 6d. Context-matched projection:** games matching tonight's top-5 availability blended with the season at
  n_match/(n_match + k), k chosen held out (4 for (b)+context, 8 for (d)). Absence games are carried at 0.39, and a
  Questionable key teammate is blended by p_play. It helps (b) by 0.022 (inside noise) and cannot rescue (c).
- **Player-nights where a key teammate's availability changed from his last game** (rotation band, n 30), minutes MAE:
  - today 7.87;
  - (b) 7.53;
  - (b) + context 7.54;
  - (c) 8.57;
  - (d) 8.62.
  Context does not beat (b) even where it should matter most. The sample is thin.

## Checks on (b)

**Banded proxy lenses** (dk_eval projaudit), (b) minus today, mean over slates (SE). Band membership is held at today's
projection; with it moving, (b) projects about 2.5 more players a slate at 25+.

| Lens | Rotation 10-25 | Stars 25+ |
|---|---|---|
| Ownership agreement (rank) | +0.075 (0.023) better | +0.066 (0.037) better |
| Salary gaps, count | +0.50 (0.39) within noise | +0.14 (0.14) within noise |
| Salary gaps, unexplained | +0.21 (0.37) within noise | 0.00 (0.18) |
| Mean distance from the salary line | +0.18 (0.06) | +0.26 (0.11) |
| Minutes rank agreement | +0.016 (0.011) | -0.018 (0.031) within noise |
| Top-5 minutes match | +0.005 (0.004) | 0.000 |

The mean distance from the salary line grows beyond noise: (b) moves the top players further from DraftKings' price line. The
gap counts and unexplained gaps (the lens's tests) do not worsen beyond noise, and the ownership and minutes lenses improve.

**Same-seed banks** (rule-free, bank noise 0.35, 9 nights with standings), today vs (b):

| | Top 10% | Cash | Percentile |
|---|---|---|---|
| Today | 10.0% | 19.7% | 43.9% |
| (b) | 11.5% | 21.9% | 46.4% |
| Nights (b) better | 7 of 9 | 7 of 9 | 9 of 9 |

## The clean rebuild (the operator's method change: every fix re-earns its place)

Script: `scripts/dk_qmin_rebuild.py`. Results: `quality_minutes_2026-11-25/rebuild.json` and `bank_rebuild.json`.

**Clean base:** QMIN minutes only.
- His on-court rates by game state, with win probability from margin and time left. The spread-based version contaminates decided-state rates (above).
- Tonight's expected time in each state at tonight's spread.
- Step 6 context: games matching tonight's top-5 availability, absence games carried at 0.39, Questionable teammates by p_play.
- Each team scaled to 200 in proportion.
- Today's points per minute held.

On its own the base is not better than today: rotation minutes 6.809 against 6.918 (gain +0.109, SE 0.133, better on 7 of 14), and stars' points worse by +0.506 (SE 0.213).

**Forward selection, held out by slate.** Each fix's parameter and the base's are chosen on the other 13. The Lab bar applies; the gain is on the base at the step where the fix was first tried.

| Fix | In today's projection | Held-out gain on the clean base (SE) | Better | Stars points | Result |
|---|---|---|---|---|---|
| prior: prior season / CARRY / crowd_keep / MISSED_SEASON blended in at MIN_FILL (players with a prior season) | yes | -0.276 (0.082) | 2 of 14 | -0.012 | OUT |
| newcomer: MIN_BY_BPR_RANK / Underdog start for players with no prior season (EvanMiya newcomers), at MIN_FILL | yes | -0.068 (0.029) | 3 of 14 | +0.036 | OUT |
| form: raw FORM 0.8 minutes blended into the QMIN minutes at weight w | yes | +0.013 (0.048) | 9 of 14 | -0.089 | IN (0.5) |
| spread: MIN_BY_SPREAD x his tier | yes | +0.025 (0.029) | 7 of 14 | -0.040 | OUT |
| game_adj: GAME_ADJ as a minutes factor by the spread | yes | -0.000 (0.000) | 1 of 14 | +0.000 | OUT |
| outhand: OUT_REG_MIN hand-off: OUT_SHARE of an Out regular's minutes to teammates by m(40-m), position-weighted | yes | -0.007 (0.004) | 1 of 14 | -0.002 | OUT |
| fitw: fit_minutes (excess off by 40-m, shortfall on by m(40-m)) instead of proportional | yes | +0.146 (0.053) | 11 of 14 | -0.291 | OUT |
| steep: steepen m^(1+g) after the fit | yes | +0.168 (0.071) | 11 of 14 | -0.306 | IN (0.18) |
| zero_gp (availability): zero-games cut: x ZERO_GP_F for a player with no games while his team has 3+ | yes | +0.010 (0.007) on the final set | 3 of 14 | -0.009 | OUT |
| q_play (availability): a Questionable player's minutes x p_play (today: x 1.0, the operator's call) | no | -0.008 (0.018) on the final set | 1 of 14 | -0.040 | OUT |

**Selection order.**
1. steepen (g 0.18) +0.168 (SE 0.071, 11 of 14). fit_minutes' weighting also passed (+0.146), with the smaller gain.
2. FORM raw minutes at 0.5 +0.121 (SE 0.058, 11 of 14).
3. fit_minutes' weighting then +0.126 (SE 0.065): under 2 x SE, so it stays out. Nothing else passed.

**Backward check:** both kept fixes hold (steepen +0.241, FORM +0.121 when removed from the final set).

**Notable OUTs:**
- **Prior-season / CARRY / crowding blend:** -0.28; it hurts. Most of that is likely the players with no games this season, who carry a prior-season number but mostly don't play; the newcomer bundle hurts too (-0.07).
- **MIN_BY_SPREAD:** +0.025 at step 1, then about 0. The states cover the spread.
- **GAME_ADJ as a minutes factor:** exactly 0, since the 200 fit cancels it within a team. It stays in the per-minute half (above).
- **OUT_REG_MIN hand-off:** -0.007, subsumed by context.
- **Zero-games cut:** +0.010 (SE 0.007, only 3 slates touched).
- **Questionable x p_play:** -0.008.

**The final minutes half:** QMIN states + context, FORM raw minutes blended at 0.5, scaled to 200 in proportion, steepened at 0.18.

| Against | Rotation minutes MAE | Gain (SE) | Better | Stars points | Top-5 | Rank |
|---|---|---|---|---|---|---|
| today's (a) | 6.519 | +0.398 (0.115) | 12 of 14 | +0.044 (SE 0.092) | +0.120 | +0.028 |
| shipped (b) | | +0.241 (0.091) | 11 of 14 | | | |

Same-seed banks against today: top 10% 11.7% vs 10.0% (better on 7 of 9); cash 22.8% vs 19.7% (7 of 9); percentile 48.8% vs 43.9% (6 of 9). The means gain more than (b)'s, but less consistently (b: percentile better on 9 of 9).

**Status: it passes but is not shipped yet.**
- **What it needs:** the play-by-play in the nightly. That means each run fetching and parsing tonight's teams' games, state-time and league role tables built from every D1 game (committed, refreshed), and the page's Out re-fit (dk_sim.js fitMinutes) matched to the proportional fit.
- **What it removes from the code path:** MIN_FILL prior minutes, MIN_BY_SPREAD on minutes, the Out hand-off, fit_minutes' weighting and the zero-games cut.
- **Until then:** (b) stays live, logged against the old minutes with the 7-slate warning.

## The minutes half, as shipped (projection = tonight's minutes x tonight's DK points per minute, nothing else)

Each DraftKings row carries `min_parts`, for example Ivan Kharchenkov on 157293:
form 33.2 → quality 33.6 → spread 35.0 → final 36.2.

| Layer | What it is | Status |
|---|---|---|
| form | this season's raw minutes, FORM 0.8 recency weights, plus MIN_FILL of the prior season | kept only as the base of `min_old`; no longer used for the projection |
| quality | the same blend with overtime scaled to regulation and 20+ blowouts at half weight (`min_q`) | new |
| spread | x MIN_BY_SPREAD by his tier | kept: the state model meant to replace it failed held out |
| final | the team fit: Out regulars' minutes, the 200 fit, steepen | unchanged |

What was removed or moved:
- **Raw FORM on minutes:** replaced by quality minutes. Raw FORM still feeds points per minute, which uses his raw minutes.
- **MIN_BY_SPREAD:** stays. Its replacement (the state model) failed held out.
- **GAME_ADJ:** moved from multiplying the points into tonight's points per minute, with the same numbers.
  - Dropped instead, held out on (b): rotation points +0.059 (SE 0.034, kept better on 10 of 14) and stars +0.056 (SE 0.055)
    worse.
  - Moved into minutes instead: rotation minutes +0.042 (SE 0.042) worse.
  - It is a points-per-minute effect of the spread, so its refit belongs to the per-minute build.
- **Not shipped:** QMIN, state weighting and lineup context. The `min_parts` layers for them (`qmin`, `states`, `context`)
  get added if a later build passes.

## What shipped

- **battle-royale-research `scripts/cbb_nightly.py`:**
  - `form()` also returns `min_q`: FORM-weighted minutes with overtime scaled to regulation and blowouts at BLOWOUT_W 0.5.
    Overtime comes from each team's ESPN schedule (`event_periods`) and the margin from the game log.
  - `project()` takes its minutes from `min_q`; points per minute keep the raw minutes.
  - `min_old` is the projection without `min_q`, through the same team fit, on every DraftKings row.
  - Test: `tests/cbb_nightly_qmin.py`.
- **br_rankings:**
  - `cbb_daily.py` records `min_old` in the night record.
  - `dk_proj_grade.py` prints live vs old rotation minutes MAE per slate, with a plain warning when live trails old over the last
    7 slates. There is no automatic revert.
- **Not shipped:** the QMIN column and the checks' minutes box switch were conditional on (c) winning, and it didn't.

## Tables

### Coverage

1353 games with play-by-play (every D1 game played to date); 30631 player-games played, 27628 clean (90.2%): 1242 dropped (rebuilt minutes off the box score by more than 2), 1623 foul-limited, 138 injury exits.

### Stability (players with 4+ clean games, 10+ minutes)

| Measure | Players | Game-to-game SD | CV | Odd vs even games r |
|---|---|---|---|---|
| raw minutes | 1814 | 5.06 | 0.258 | 0.748 |
| minutes per 40 | 1814 | 4.92 | 0.255 | 0.758 |
| QMIN | 1814 | 5.01 | 0.278 | 0.806 |
| H1 | 1783 | 5.33 | 0.295 | 0.760 |
| H2 | 738 | 6.79 | 0.398 | 0.727 |

### Held out by slate (14 graded slates; rotation 10-25 minutes MAE; parameters chosen on the other 13)

| Model | Today | Model | Gain | SE | Better | Stars points (model - today) | Top-5 | Rank | Parameters (all slates) |
|---|---|---|---|---|---|---|---|---|---|
| b | 6.918 | 6.761 | +0.157 | 0.075 | 10 of 14 | -0.242 (SE 0.163) | +0.001 | +0.013 | {"fade_b": 0.8, "wb": 0.5, "ot": true} |
| b_no_ot | 6.918 | 6.778 | +0.140 | 0.081 | 10 of 14 | -0.199 (SE 0.139) | -0.006 | +0.011 | {"fade_b": 0.7, "wb": 1.0, "ot": false} |
| c | 6.918 | 7.732 | -0.814 | 0.201 | 1 of 14 | +0.256 (SE 0.182) | -0.185 | -0.128 | {"fade_c": 0.9, "k_player": 15} |
| c_wp0 | 6.918 | 6.766 | +0.152 | 0.137 | 8 of 14 | +0.101 (SE 0.105) | +0.066 | -0.004 | {"fade_c": 0.6, "k_player": 15} |
| c_margin | 6.918 | 6.741 | +0.177 | 0.130 | 9 of 14 | +0.213 (SE 0.142) | +0.059 | +0.011 | {"fade_c": 0.9, "k_player": 15} |
| b_ctx | 6.918 | 6.739 | +0.179 | 0.072 | 10 of 14 | -0.147 (SE 0.146) | +0.017 | +0.016 | {"fade_b": 0.7, "wb": 1.0, "ot": true, "k_ctx": 4, "p_keep": 0.3908173147928009} |
| d | 6.918 | 7.731 | -0.813 | 0.199 | 1 of 14 | +0.321 (SE 0.179) | -0.185 | -0.126 | {"fade_c": 0.9, "k_player": 15, "k_ctx": 8, "p_keep": 0.3908173147928009} |

### (b) per slate

| Slate | Parameters | Today | (b) | Stars today | Stars (b) | Players moved |
|---|---|---|---|---|---|---|
| 2026-11-16_156660 | {"fade_b": 0.8, "wb": 0.5, "ot": true} | 6.38 | 5.95 | 10.70 | 10.83 | 154 |
| 2026-11-17_156662 | {"fade_b": 0.8, "wb": 0.5, "ot": true} | 6.62 | 6.43 | 8.91 | 8.24 | 58 |
| 2026-11-17_156663 | {"fade_b": 0.8, "wb": 0.5, "ot": true} | 6.63 | 6.57 | 13.44 | 14.20 | 186 |
| 2026-11-18_157032 | {"fade_b": 0.7, "wb": 1.0, "ot": true} | 7.85 | 7.03 | 9.08 | 8.62 | 58 |
| 2026-11-18_157033 | {"fade_b": 0.8, "wb": 0.5, "ot": true} | 7.65 | 7.27 | 11.18 | 9.23 | 105 |
| 2026-11-19_157138 | {"fade_b": 0.7, "wb": 0.5, "ot": true} | 7.20 | 7.48 | 7.28 | 6.66 | 83 |
| 2026-11-19_157139 | {"fade_b": 0.7, "wb": 1.0, "ot": true} | 7.41 | 6.95 | 10.33 | 10.12 | 163 |
| 2026-11-20_157013 | {"fade_b": 0.8, "wb": 0.5, "ot": true} | 5.86 | 5.93 | 7.21 | 7.32 | 77 |
| 2026-11-20_157015 | {"fade_b": 0.8, "wb": 0.5, "ot": true} | 6.37 | 6.36 | 7.18 | 7.29 | 224 |
| 2026-11-21_157017 | {"fade_b": 0.7, "wb": 1.0, "ot": true} | 6.92 | 6.84 | 7.48 | 7.58 | 108 |
| 2026-11-22_157019 | {"fade_b": 0.8, "wb": 0.5, "ot": true} | 6.56 | 6.53 | 10.83 | 10.62 | 134 |
| 2026-11-23_157021 | {"fade_b": 0.8, "wb": 0.5, "ot": true} | 8.68 | 8.50 | 9.10 | 8.98 | 102 |
| 2026-11-24_157024 | {"fade_b": 0.7, "wb": 1.0, "ot": true} | 6.57 | 6.58 | 10.42 | 10.19 | 215 |
| 2026-11-24_157026 | {"fade_b": 0.8, "wb": 0.5, "ot": true} | 6.15 | 6.22 | 10.77 | 10.65 | 186 |

### State time by tonight's spread (minutes of the game, from the team's side; all games)

| Spread bin | Games | COMP | LEAN_L | LEAN_T | DEC_L | DEC_T | OT |
|---|---|---|---|---|---|---|---|
| <-20 | 272 | 1.2 | 3.2 | 0.0 | 35.6 | 0.0 | 0.1 |
| -20..-12 | 182 | 9.0 | 11.6 | 0.3 | 18.9 | 0.2 | 0.1 |
| -12..-6 | 220 | 22.8 | 8.1 | 0.8 | 7.6 | 0.7 | 0.5 |
| -6..-2 | 247 | 28.1 | 3.7 | 2.3 | 4.4 | 1.5 | 0.2 |
| -2..2 | 862 | 18.4 | 2.6 | 2.6 | 8.2 | 8.2 | 0.2 |
| 2..6 | 245 | 28.1 | 2.3 | 3.7 | 1.5 | 4.4 | 0.2 |
| 6..12 | 219 | 22.7 | 0.8 | 8.2 | 0.7 | 7.7 | 0.5 |
| 12..20 | 182 | 9.0 | 0.3 | 11.6 | 0.2 | 18.9 | 0.1 |
| 20+ | 273 | 1.2 | 0.0 | 3.2 | 0.0 | 35.6 | 0.1 |

### Returns (6b)

32 cases (a top-5 QMIN player out 2+ straight games, then back), 96 teammate observations. Persistence (slope of return - before on during - before): minutes rate 0.39, DK per minute 0.39; by case, minutes median 0.25 (quartiles 0.02 to 0.77).

The mirror (his first missed game): his 721 minutes before; teammates gained 603: top 5 115, 6-8 270, 9+ 218; same position 408, other 195.

### Availability changed since his last game (rotation, n 30)

| Model | Minutes MAE |
|---|---|
| a | 7.87 |
| b | 7.53 |
| c | 8.57 |
| b_ctx | 7.54 |
| d | 8.62 |
